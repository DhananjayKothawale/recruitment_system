# ============================================================
# backend/models/user.py
# PURPOSE: Defines the "users" table in PostgreSQL.
#
# Think of this class as a blueprint for one row in the users table.
# Each attribute = one column in the table.
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from backend.database.connection import Base


# UserRole defines the 3 types of users in our system
class UserRole(str, enum.Enum):
    CANDIDATE = "candidate"
    RECRUITER = "recruiter"
    ADMIN = "admin"


class User(Base):
    """
    DATABASE TABLE: users

    Columns:
    - id: Auto-incrementing primary key (1, 2, 3...)
    - email: Unique email address (used for login)
    - full_name: User's full name
    - hashed_password: Password stored as a hash (NEVER store plain passwords!)
    - role: One of: candidate, recruiter, admin
    - is_active: Can this user log in? (False = banned)
    - created_at: When did they register?
    - updated_at: When was their profile last updated?
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CANDIDATE, nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)

    # server_default=func.now() means PostgreSQL sets this automatically
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ---- RELATIONSHIPS ----
    # These tell SQLAlchemy how tables connect to each other
    # "back_populates" creates a two-way link
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    jobs_posted = relationship("Job", back_populates="recruiter")

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
