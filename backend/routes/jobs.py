# ============================================================
# backend/routes/jobs.py
# PURPOSE: Job posting CRUD endpoints
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from backend.database.connection import get_db
from backend.models.job import Job
from backend.models.user import User
from backend.auth.jwt_handler import get_current_user, require_role

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


class JobCreate(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    job_type: Optional[str] = "Full-time"
    description: str
    responsibilities: Optional[str] = None
    requirements: Optional[str] = None
    required_skills: Optional[str] = None   # "Python,SQL,FastAPI"
    min_experience: Optional[int] = 0
    max_experience: Optional[int] = 10
    required_education: Optional[str] = "Bachelor"
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None


@router.post("/", status_code=201)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter", "admin"))
):
    """
    Create a new job posting.
    Only recruiters and admins can post jobs.

    POST /api/jobs/
    """
    new_job = Job(
        recruiter_id=current_user.id,
        title=job_data.title,
        company=job_data.company,
        location=job_data.location,
        job_type=job_data.job_type,
        description=job_data.description,
        responsibilities=job_data.responsibilities,
        requirements=job_data.requirements,
        required_skills=job_data.required_skills,
        min_experience=job_data.min_experience,
        max_experience=job_data.max_experience,
        required_education=job_data.required_education,
        salary_min=job_data.salary_min,
        salary_max=job_data.salary_max,
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return {"message": "Job created", "job_id": new_job.id}


@router.get("/")
def get_all_jobs(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by title or company"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50)
):
    """
    Get all active jobs with optional search and pagination.

    GET /api/jobs/?search=python&page=1&per_page=10
    """
    query = db.query(Job).filter(Job.is_active == True)

    if search:
        query = query.filter(
            Job.title.ilike(f"%{search}%") |
            Job.company.ilike(f"%{search}%") |
            Job.required_skills.ilike(f"%{search}%")
        )

    total = query.count()
    jobs = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "job_type": j.job_type,
                "required_skills": j.required_skills,
                "min_experience": j.min_experience,
                "required_education": j.required_education,
                "created_at": j.created_at,
            }
            for j in jobs
        ]
    }


@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a single job by ID"""
    job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "job_type": job.job_type,
        "description": job.description,
        "responsibilities": job.responsibilities,
        "requirements": job.requirements,
        "required_skills": job.required_skills,
        "skills_list": job.get_skills_list(),
        "min_experience": job.min_experience,
        "max_experience": job.max_experience,
        "required_education": job.required_education,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "created_at": job.created_at,
    }


@router.put("/{job_id}")
def update_job(
    job_id: int,
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter", "admin"))
):
    """Update a job posting (only by the recruiter who created it)"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Only allow the recruiter who created it (or admin) to edit
    if job.recruiter_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="You can only edit your own jobs")

    for field, value in job_data.dict(exclude_unset=True).items():
        setattr(job, field, value)

    db.commit()
    return {"message": "Job updated successfully"}


@router.delete("/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter", "admin"))
):
    """Soft delete a job (marks as inactive, doesn't actually delete)"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.recruiter_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="You can only delete your own jobs")

    job.is_active = False
    db.commit()
    return {"message": "Job deleted successfully"}
