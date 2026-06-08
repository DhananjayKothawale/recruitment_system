# ============================================================
# backend/routes/analytics.py
# PURPOSE: Dashboard analytics and candidate ranking endpoints
# ============================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.database.connection import get_db
from backend.models.user import User, UserRole
from backend.models.job import Job
from backend.models.resume import Resume
from backend.models.application import Application, ApplicationStatus
from backend.auth.jwt_handler import get_current_user, require_role

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter", "admin"))
):
    """
    Main dashboard statistics for recruiters.

    Returns:
    - Total counts
    - Average scores
    - Top skills in demand
    - Applications per job
    """
    # Basic counts
    total_candidates = db.query(User).filter(User.role == UserRole.CANDIDATE).count()
    total_jobs = db.query(Job).filter(Job.is_active == True).count()
    total_applications = db.query(Application).count()

    # Average ATS score across all applications
    avg_ats = db.query(func.avg(Application.ats_score)).scalar() or 0

    # Applications per job (for chart)
    apps_per_job = db.query(
        Job.title,
        func.count(Application.id).label("count")
    ).join(Application, Job.id == Application.job_id, isouter=True)\
     .filter(Job.recruiter_id == current_user.id)\
     .group_by(Job.title)\
     .all()

    # Application status distribution
    status_counts = db.query(
        Application.status,
        func.count(Application.id).label("count")
    ).group_by(Application.status).all()

    # Score distribution for histogram
    score_ranges = {
        "0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0
    }
    all_scores = db.query(Application.ats_score).all()
    for (score,) in all_scores:
        if score is None:
            continue
        if score <= 20:
            score_ranges["0-20"] += 1
        elif score <= 40:
            score_ranges["21-40"] += 1
        elif score <= 60:
            score_ranges["41-60"] += 1
        elif score <= 80:
            score_ranges["61-80"] += 1
        else:
            score_ranges["81-100"] += 1

    return {
        "overview": {
            "total_candidates": total_candidates,
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "avg_ats_score": round(float(avg_ats), 1),
        },
        "apps_per_job": [
            {"job": row.title, "count": row.count}
            for row in apps_per_job
        ],
        "status_distribution": [
            {"status": row.status.value if row.status else "unknown", "count": row.count}
            for row in status_counts
        ],
        "score_distribution": [
            {"range": k, "count": v}
            for k, v in score_ranges.items()
        ],
    }


@router.get("/candidates/{job_id}")
def get_ranked_candidates(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter", "admin"))
):
    """
    Get ranked list of candidates for a specific job.

    GET /api/analytics/candidates/5
    Returns candidates sorted by ATS score (best first)
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return {"error": "Job not found"}

    # Get all applications for this job with candidate info
    applications = db.query(Application)\
        .filter(Application.job_id == job_id)\
        .join(User, Application.candidate_id == User.id)\
        .join(Resume, Application.resume_id == Resume.id, isouter=True)\
        .order_by(desc(Application.ats_score))\
        .all()

    ranked_candidates = []
    for rank, app in enumerate(applications, 1):
        candidate = db.query(User).filter(User.id == app.candidate_id).first()
        resume = db.query(Resume).filter(Resume.id == app.resume_id).first()

        # Predict suitability using ML
        from backend.ml.trainer import predict_candidate_suitability
        prediction = predict_candidate_suitability(
            ats_score=app.ats_score or 0,
            skills_count=len(resume.get_skills_list()) if resume else 0,
            experience_years=resume.extracted_experience_years if resume else 0,
            has_certifications=1 if (resume and resume.extracted_certifications) else 0,
            education_level={"high school": 1, "diploma": 2, "bachelor": 4, "master": 5, "phd": 6}.get(
                (resume.extracted_education or "").lower(), 3
            ),
            match_score=app.match_score or 0,
        )

        ranked_candidates.append({
            "rank": rank,
            "candidate_id": app.candidate_id,
            "name": candidate.full_name if candidate else "Unknown",
            "email": candidate.email if candidate else "",
            "ats_score": round(app.ats_score or 0, 1),
            "match_score": round(app.match_score or 0, 1),
            "combined_score": round(((app.ats_score or 0) * 0.6) + ((app.match_score or 0) * 0.4), 1),
            "experience_years": resume.extracted_experience_years if resume else 0,
            "education": resume.extracted_education if resume else "Unknown",
            "skills": resume.get_skills_list()[:5] if resume else [],  # Top 5 skills
            "status": app.status.value,
            "prediction": prediction["prediction_label"],
            "prediction_probability": prediction["probability"],
            "applied_at": app.applied_at,
        })

    return {
        "job_title": job.title,
        "total_applicants": len(ranked_candidates),
        "candidates": ranked_candidates,
    }


@router.put("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("recruiter", "admin"))
):
    """Update candidate application status (shortlist, reject, hire)"""
    valid_statuses = [s.value for s in ApplicationStatus]
    if new_status not in valid_statuses:
        return {"error": f"Status must be one of: {valid_statuses}"}

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        return {"error": "Application not found"}

    app.status = ApplicationStatus(new_status)
    db.commit()
    return {"message": f"Status updated to: {new_status}"}
