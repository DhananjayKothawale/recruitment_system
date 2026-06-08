# ============================================================
# backend/models/resume.py
# PURPOSE: Defines the "resumes" table in PostgreSQL.
# Stores both the original PDF file path AND the extracted data.
# ============================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.connection import Base


class Resume(Base):
    """
    DATABASE TABLE: resumes

    When a candidate uploads a PDF resume:
    1. The PDF file is saved to the /uploads folder
    2. NLP extracts info from the PDF
    3. All extracted info is saved in this table
    """
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Original filename and where it's stored on disk
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)

    # ---- EXTRACTED INFORMATION (from NLP parsing) ----
    # These fields are filled automatically when the PDF is parsed

    # Personal Info
    extracted_name = Column(String(255), nullable=True)
    extracted_email = Column(String(255), nullable=True)
    extracted_phone = Column(String(50), nullable=True)

    # Professional Info
    extracted_skills = Column(Text, nullable=True)      # "Python,SQL,Machine Learning"
    extracted_experience_years = Column(Float, default=0.0)
    extracted_education = Column(String(100), nullable=True)  # "Bachelor", "Master", "PhD"
    extracted_certifications = Column(Text, nullable=True)
    extracted_projects = Column(Text, nullable=True)

    # The full raw text extracted from PDF (for ML matching)
    raw_text = Column(Text, nullable=True)

    # How complete is the resume? (0-100)
    completeness_score = Column(Float, default=0.0)

    is_parsed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="resumes")
    ats_results = relationship("ATSResult", back_populates="resume", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="resume")

    def get_skills_list(self):
        """Returns extracted skills as a Python list"""
        if self.extracted_skills:
            return [s.strip() for s in self.extracted_skills.split(",")]
        return []

    def __repr__(self):
        return f"<Resume id={self.id} user_id={self.user_id}>"


# Need to add Boolean import
from sqlalchemy import Boolean
