# ============================================================
# backend/models/skill.py
# PURPOSE: Master list of skills in the system.
# ============================================================

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from backend.database.connection import Base


class Skill(Base):
    """
    DATABASE TABLE: skills
    A master list of all skills recognized by the system.
    Used for skill gap analysis and autocomplete.
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True)  # e.g., "Programming", "Database", "Framework"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Skill name={self.name}>"
