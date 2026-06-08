# ============================================================
# backend/auth/jwt_handler.py
# PURPOSE: Handles JWT (JSON Web Token) authentication.
#
# HOW JWT WORKS (Simple Explanation):
# 1. User logs in with email + password
# 2. Server verifies credentials
# 3. Server creates a "token" - a signed string that contains user info
# 4. User sends this token with every future request (in the header)
# 5. Server verifies the token to know who is making the request
#
# The token looks like: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ...
# It has 3 parts separated by dots:
# Part 1: Header (algorithm used)
# Part 2: Payload (user data - NOT secret, just encoded)
# Part 3: Signature (proves the server created it - secret!)
# ============================================================

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from config import settings
from backend.database.connection import get_db

# ---- PASSWORD HASHING ----
# Never store plain passwords! Always hash them.
# bcrypt is a one-way hashing algorithm - you can't reverse it
# When user logs in, we hash their input and compare to stored hash
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# This tells FastAPI: "look for a token in the Authorization header"
# When user logs in, they get a token
# For protected routes, they send: Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(plain_password: str) -> str:
    """
    Converts plain password to a secure hash.
    Example: "mypassword123" → "$2b$12$abc...xyz" (60 characters)
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain password matches its hash.
    Returns True if they match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT token containing user information.

    Args:
        data: Dictionary with user info (e.g., {"sub": "user@email.com", "role": "candidate"})
        expires_delta: How long the token is valid (default: 30 minutes)

    Returns:
        JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # "exp" (expiry) is a standard JWT field
    to_encode.update({"exp": expire})

    # Create the actual JWT token
    # This is cryptographically signed with our SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verifies a JWT token and returns its payload.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    FastAPI dependency: gets the currently logged-in user from their JWT token.

    Usage in a route:
        @app.get("/profile")
        def get_profile(current_user = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    from backend.models.user import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_role(*roles):
    """
    Factory function that creates a role-checking dependency.

    Usage:
        @app.post("/jobs")
        def create_job(user = Depends(require_role("recruiter", "admin"))):
            ...
    """
    async def role_checker(current_user=Depends(get_current_user)):
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {roles}"
            )
        return current_user
    return role_checker
