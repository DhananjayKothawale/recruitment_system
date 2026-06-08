# ============================================================
# backend/models/application.py
# PURPOSE: Tracks which candidate applied to which job.
# This is the "junction" table connecting users and jobs.
# ============================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.database.connection import Base


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    REVIEWING = "reviewing"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    HIRED = "hired"


class Application(Base):
    """
    DATABASE TABLE: applications
    One row = one candidate applied to one job
    """
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)

    # Which candidate applied?
    candidate_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Which job did they apply to?
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    # Which resume did they use?
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)

    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.APPLIED)
    cover_letter = Column(Text, nullable=True)

    # Scores calculated by AI
    ats_score = Column(Float, default=0.0)         # ATS matching score (0-100)
    match_score = Column(Float, default=0.0)       # Semantic similarity score (0-100)
    overall_rank = Column(Integer, nullable=True)   # Rank among all applicants (1 = best)

    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    candidate = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")

    def __repr__(self):
        return f"<Application candidate={self.candidate_id} job={self.job_id} status={self.status}>"


# ============================================================
# backend/models/ats_result.py
# PURPOSE: Stores detailed ATS scoring breakdown.
# ============================================================

class ATSResult(Base):
    """
    DATABASE TABLE: ats_results
    Stores the breakdown of how the ATS score was calculated.
    """
    __tablename__ = "ats_results"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    # Individual score components (each out of 100)
    skills_score = Column(Float, default=0.0)          # How many required skills does candidate have?
    education_score = Column(Float, default=0.0)       # Does education level match requirement?
    experience_score = Column(Float, default=0.0)      # Does years of experience match?
    certifications_score = Column(Float, default=0.0)  # Bonus for certifications
    projects_score = Column(Float, default=0.0)        # Bonus for project count
    completeness_score = Column(Float, default=0.0)    # Is resume complete?

    # Final weighted score (0-100)
    total_score = Column(Float, default=0.0)

    # What skills are missing?
    matched_skills = Column(Text, nullable=True)       # "Python,SQL"
    missing_skills = Column(Text, nullable=True)       # "Power BI,Machine Learning"

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    resume = relationship("Resume", back_populates="ats_results")

    def get_matched_skills_list(self):
        if self.matched_skills:
            return [s.strip() for s in self.matched_skills.split(",")]
        return []

    def get_missing_skills_list(self):
        if self.missing_skills:
            return [s.strip() for s in self.missing_skills.split(",")]
        return []
