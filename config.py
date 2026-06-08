# ============================================================
# config.py
# PURPOSE: Stores all project settings in one place.
# We read secret values from the .env file so they never
# get accidentally shared on GitHub.
# ============================================================

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- Database ---
    # Default to SQLite so the app can run on free hosts without PostgreSQL.
    # Override this with DATABASE_URL in a .env file or environment variable.
    DATABASE_URL: str = "sqlite:///./recruitment_db.sqlite3"

    # --- Server / deployment ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- JWT Authentication ---
    # SECRET_KEY: Used to sign JWT tokens. Keep this secret!
    # NEVER share this value publicly or commit it to GitHub
    SECRET_KEY: str = "change-this-to-a-long-random-string-in-production"
    ALGORITHM: str = "HS256"
    # Token expires after 30 minutes by default
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- File Upload ---
    # Where uploaded resumes are stored on your computer
    UPLOAD_DIR: str = "uploads"
    # Maximum file size: 10MB (in bytes)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    # --- ML Model ---
    # Where trained ML models are saved
    MODEL_DIR: str = "models_saved"

    # --- App Settings ---
    APP_NAME: str = "AI Recruitment System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    class Config:
        # This tells pydantic to read from a .env file
        env_file = ".env"
        env_file_encoding = "utf-8"


# lru_cache means this function only runs ONCE and reuses the result
# This is efficient - we don't reload settings on every request
@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Create a global settings object that other files can import
settings = get_settings()
