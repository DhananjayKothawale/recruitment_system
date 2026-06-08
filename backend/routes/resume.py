# ============================================================
# backend/routes/resume.py
# PURPOSE: Resume upload, parsing, and ATS scoring endpoints
# ============================================================

import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.resume import Resume
from backend.models.job import Job
from backend.models.application import Application, ApplicationStatus, ATSResult
from backend.models.user import User
from backend.auth.jwt_handler import get_current_user, require_role
from backend.nlp.resume_parser import resume_parser
from backend.services.ats_engine import ats_engine
from backend.services.job_matcher import calculate_job_match
from backend.ml.trainer import predict_candidate_suitability
from config import settings

router = APIRouter(prefix="/api/resume", tags=["Resume"])


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),  # ... means required
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a PDF resume.
    1. Save the file to /uploads folder
    2. Parse it with NLP
    3. Save extracted data to database

    POST /api/resume/upload
    Form data: file (PDF)
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Validate file size (< 10MB)
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")

    # Create unique filename to avoid conflicts
    # e.g., "1_john_resume.pdf" (user_id + original name)
    safe_filename = f"{current_user.id}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    # Save file to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Parse the resume with NLP
    parsed_data = resume_parser.parse_resume(file_path)

    if "error" in parsed_data:
        os.remove(file_path)  # Clean up failed file
        raise HTTPException(status_code=400, detail=parsed_data["error"])

    # Save to database
    # Check if user already has a resume (update instead of creating new)
    existing_resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()

    if existing_resume:
        # Update existing resume
        existing_resume.original_filename = file.filename
        existing_resume.file_path = file_path
        existing_resume.extracted_name = parsed_data.get("name")
        existing_resume.extracted_email = parsed_data.get("email")
        existing_resume.extracted_phone = parsed_data.get("phone")
        existing_resume.extracted_skills = ",".join(parsed_data.get("skills", []))
        existing_resume.extracted_experience_years = parsed_data.get("experience_years", 0)
        existing_resume.extracted_education = parsed_data.get("education", "Not Specified")
        existing_resume.extracted_certifications = ",".join(parsed_data.get("certifications", []))
        existing_resume.raw_text = parsed_data.get("raw_text", "")
        existing_resume.completeness_score = parsed_data.get("completeness_score", 0)
        existing_resume.is_parsed = True
        resume = existing_resume
    else:
        # Create new resume
        resume = Resume(
            user_id=current_user.id,
            original_filename=file.filename,
            file_path=file_path,
            extracted_name=parsed_data.get("name"),
            extracted_email=parsed_data.get("email"),
            extracted_phone=parsed_data.get("phone"),
            extracted_skills=",".join(parsed_data.get("skills", [])),
            extracted_experience_years=parsed_data.get("experience_years", 0),
            extracted_education=parsed_data.get("education", "Not Specified"),
            extracted_certifications=",".join(parsed_data.get("certifications", [])),
            raw_text=parsed_data.get("raw_text", ""),
            completeness_score=parsed_data.get("completeness_score", 0),
            is_parsed=True,
        )
        db.add(resume)

    db.commit()
    db.refresh(resume)

    return {
        "message": "Resume uploaded and parsed successfully",
        "resume_id": resume.id,
        "extracted": {
            "name": resume.extracted_name,
            "email": resume.extracted_email,
            "phone": resume.extracted_phone,
            "skills": parsed_data.get("skills", []),
            "experience_years": resume.extracted_experience_years,
            "education": resume.extracted_education,
            "completeness_score": resume.completeness_score,
        }
    }


@router.get("/my-resume")
def get_my_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's resume"""
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume uploaded yet")

    return {
        "id": resume.id,
        "name": resume.extracted_name,
        "email": resume.extracted_email,
        "phone": resume.extracted_phone,
        "skills": resume.get_skills_list(),
        "experience_years": resume.extracted_experience_years,
        "education": resume.extracted_education,
        "completeness_score": resume.completeness_score,
        "uploaded_at": resume.created_at,
    }


@router.post("/apply/{job_id}")
def apply_to_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("candidate"))
):
    """
    Candidate applies to a job.
    Automatically calculates ATS score and match score.

    POST /api/resume/apply/5
    """
    # Get the job
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get candidate's resume
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=400, detail="Please upload your resume first")

    # Check if already applied
    existing_app = db.query(Application).filter(
        Application.candidate_id == current_user.id,
        Application.job_id == job_id
    ).first()
    if existing_app:
        raise HTTPException(status_code=400, detail="You already applied to this job")

    # Calculate ATS score
    ats_result = ats_engine.calculate_score(resume, job)

    # Calculate job match score
    job_full_text = f"{job.title} {job.description} {job.required_skills or ''}"
    match_result = calculate_job_match(resume.raw_text or "", job_full_text)

    # Create application
    application = Application(
        candidate_id=current_user.id,
        job_id=job_id,
        resume_id=resume.id,
        ats_score=ats_result["total_score"],
        match_score=match_result["match_percentage"],
    )
    db.add(application)

    # Save ATS breakdown
    ats_record = ATSResult(
        resume_id=resume.id,
        job_id=job_id,
        skills_score=ats_result["skills_score"],
        education_score=ats_result["education_score"],
        experience_score=ats_result["experience_score"],
        certifications_score=ats_result["certifications_score"],
        projects_score=ats_result["projects_score"],
        completeness_score=ats_result["completeness_score"],
        total_score=ats_result["total_score"],
        matched_skills=",".join(ats_result["matched_skills"]),
        missing_skills=",".join(ats_result["missing_skills"]),
    )
    db.add(ats_record)
    db.commit()

    return {
        "message": "Application submitted successfully!",
        "ats_score": ats_result["total_score"],
        "match_score": match_result["match_percentage"],
        "matched_skills": ats_result["matched_skills"],
        "missing_skills": ats_result["missing_skills"],
    }


@router.get("/skill-gap/{job_id}")
def get_skill_gap(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Shows skill gap analysis - what skills you have vs what the job needs.

    GET /api/resume/skill-gap/5
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found")

    required_skills = job.get_skills_list()
    candidate_skills = resume.get_skills_list()

    candidate_lower = [s.lower() for s in candidate_skills]
    matched = [s for s in required_skills if s.lower() in candidate_lower]
    missing = [s for s in required_skills if s.lower() not in candidate_lower]

    # Generate learning recommendations
    recommendations = {
        "python": "Complete Python tutorial on python.org or Codecademy",
        "sql": "SQLZoo.net or Mode Analytics SQL Tutorial",
        "machine learning": "Andrew Ng's ML course on Coursera",
        "power bi": "Microsoft Learn Power BI documentation",
        "react": "React official docs (reactjs.org)",
        "fastapi": "FastAPI official tutorial (fastapi.tiangolo.com)",
    }

    missing_with_recs = [
        {
            "skill": skill,
            "recommendation": recommendations.get(skill.lower(), f"Search '{skill} tutorial' on YouTube or Udemy")
        }
        for skill in missing
    ]

    return {
        "job_title": job.title,
        "required_skills": required_skills,
        "your_skills": candidate_skills,
        "matched_skills": matched,
        "missing_skills": missing_with_recs,
        "match_percentage": round(len(matched) / len(required_skills) * 100, 1) if required_skills else 100
    }
