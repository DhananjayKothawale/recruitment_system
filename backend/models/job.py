# ============================================================
# backend/models/job.py
# PURPOSE: Defines the "jobs" table in PostgreSQL.
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.connection import Base


class Job(Base):
    """
    DATABASE TABLE: jobs
    Represents a job posting created by a recruiter.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    # ForeignKey links this job to the recruiter who posted it
    # When recruiter is deleted, their jobs are also deleted (CASCADE)
    recruiter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    job_type = Column(String(50), default="Full-time")  # Full-time, Part-time, Contract
    description = Column(Text, nullable=False)
    responsibilities = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)

    # Skills required for this job (stored as comma-separated: "Python,SQL,FastAPI")
    required_skills = Column(Text, nullable=True)

    # Experience in years
    min_experience = Column(Integer, default=0)
    max_experience = Column(Integer, default=10)

    # Education: Bachelor, Master, PhD, Any
    required_education = Column(String(100), default="Bachelor")

    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)

    is_active = Column(Boolean, default=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    recruiter = relationship("User", back_populates="jobs_posted")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    def get_skills_list(self):
        """Returns skills as a Python list instead of a comma-separated string"""
        if self.required_skills:
            return [s.strip() for s in self.required_skills.split(",")]
        return []

    def __repr__(self):
        return f"<Job id={self.id} title={self.title}>"
