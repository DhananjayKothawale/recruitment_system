# ============================================================
# backend/routes/auth.py
# PURPOSE: Authentication endpoints - register, login, logout
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from backend.database.connection import get_db
from backend.models.user import User, UserRole
from backend.auth.jwt_handler import hash_password, verify_password, create_access_token, get_current_user

# APIRouter is like a "mini app" for grouping related routes
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ---- REQUEST/RESPONSE SCHEMAS ----
# Pydantic models define what data to expect and return
class RegisterRequest(BaseModel):
    email: EmailStr           # FastAPI validates this is a real email
    full_name: str
    password: str
    role: Optional[str] = "candidate"
    phone: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    full_name: str
    role: str


@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    POST /api/auth/register
    Body: {"email": "...", "full_name": "...", "password": "...", "role": "candidate"}
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate role
    valid_roles = ["candidate", "recruiter", "admin"]
    if request.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of: {valid_roles}")

    # Create new user
    new_user = User(
        email=request.email,
        full_name=request.full_name,
        hashed_password=hash_password(request.password),  # NEVER store plain password!
        role=UserRole(request.role),
        phone=request.phone,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Registration successful",
        "user_id": new_user.id,
        "email": new_user.email,
    }


@router.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login and get JWT token.

    POST /api/auth/login
    Form data: username (email) + password

    Returns JWT token to use for all future requests.
    """
    # Find user by email
    user = db.query(User).filter(User.email == form_data.username).first()

    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is disabled")

    # Create JWT token
    token = create_access_token(data={"sub": user.email, "role": user.role.value})

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
    )


@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile.
    Requires: Authorization: Bearer <token>
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "phone": current_user.phone,
        "created_at": current_user.created_at,
    }
