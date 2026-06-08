# ============================================================
# backend/database/connection.py
# PURPOSE: Sets up the connection between Python and PostgreSQL.
# SQLAlchemy is the "translator" between Python code and SQL queries.
#
# WHAT THIS FILE DOES:
# 1. Creates an "engine" - the actual connection to PostgreSQL
# 2. Creates a "SessionLocal" - a way to open/close DB sessions
# 3. Creates "Base" - the parent class for all our DB models
# 4. Provides get_db() - used by FastAPI to inject DB sessions
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# ---- CREATE ENGINE ----
# The engine is the actual database connection.
# SQLite is the default so the app can run on free hosts without PostgreSQL.
engine_args = {
    "pool_pre_ping": True,
    "pool_size": 5,
    "max_overflow": 10,
}

if settings.DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
    engine_args["pool_size"] = 2
    engine_args["max_overflow"] = 0

engine = create_engine(settings.DATABASE_URL, **engine_args)

# ---- CREATE SESSION ----
# Each database operation happens inside a "session"
# autocommit=False: we manually commit changes (safer)
# autoflush=False: don't automatically write to DB on every operation
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---- CREATE BASE ----
# All our database model classes will inherit from this Base
# This is how SQLAlchemy knows which classes represent database tables
Base = declarative_base()


# ---- DATABASE SESSION DEPENDENCY ----
# This function is used with FastAPI's dependency injection
# It ensures the DB session is always properly opened AND closed
# Even if an error occurs, the session gets closed (try/finally)
def get_db():
    """
    Usage in routes:
        @app.get("/jobs")
        def get_jobs(db: Session = Depends(get_db)):
            # db is now a database session
    """
    db = SessionLocal()
    try:
        yield db          # Give the session to the route function
    finally:
        db.close()        # Always close after the request is done


def create_tables():
    """
    Creates all tables in PostgreSQL based on our model definitions.
    Run this ONCE when setting up the project for the first time.

    Usage:
        python -c "from backend.database.connection import create_tables; create_tables()"
    """
    # Import all models so SQLAlchemy knows about them
    from backend.models import user, job, resume, application, skill

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    print("Tables:", list(Base.metadata.tables.keys()))
