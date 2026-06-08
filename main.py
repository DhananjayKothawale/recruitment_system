# ============================================================
# main.py
# PURPOSE: The main entry point of the application.
# This file:
# 1. Creates the FastAPI app
# 2. Registers all routes
# 3. Sets up CORS (allows frontend to talk to backend)
# 4. Serves frontend HTML files
# 5. Starts the server when you run: python main.py
# ============================================================

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from config import settings

# ---- CREATE THE FASTAPI APP ----
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Recruitment & Resume Screening System",
    # Swagger docs available at /docs
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---- CORS MIDDLEWARE ----
# CORS = Cross-Origin Resource Sharing
# This allows the frontend (running on one port) to talk to the backend (another port)
# Without this, the browser would block the requests for security reasons
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],         # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],         # Allow all headers
)

# ---- SERVE STATIC FILES ----
# CSS, JavaScript, and images in the frontend/static folder
# will be available at /static/css/style.css, /static/js/app.js, etc.
if os.path.exists("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Create upload directory if it doesn't exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MODEL_DIR, exist_ok=True)

# Ensure the database tables exist automatically on startup.
from backend.database.connection import create_tables

@app.on_event("startup")
def startup_event():
    create_tables()

# ---- REGISTER ROUTES ----
# Each router handles a group of related endpoints
from backend.routes.auth import router as auth_router
from backend.routes.jobs import router as jobs_router
from backend.routes.resume import router as resume_router
from backend.routes.analytics import router as analytics_router
from backend.routes.interview import router as interview_router
from backend.routes.ml import router as ml_router

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(resume_router)
app.include_router(analytics_router)
app.include_router(interview_router)
app.include_router(ml_router)


# ---- SERVE HTML PAGES ----
# These routes return HTML pages for the frontend

@app.get("/")
def serve_home():
    """Serves the landing page"""
    return FileResponse("frontend/templates/index.html")

@app.get("/login")
def serve_login():
    return FileResponse("frontend/templates/login.html")

@app.get("/register")
def serve_register():
    return FileResponse("frontend/templates/register.html")

@app.get("/dashboard")
def serve_dashboard():
    return FileResponse("frontend/templates/dashboard.html")

@app.get("/jobs")
def serve_jobs():
    return FileResponse("frontend/templates/jobs.html")

@app.get("/upload-resume")
def serve_upload():
    return FileResponse("frontend/templates/upload_resume.html")

@app.get("/analytics")
def serve_analytics():
    return FileResponse("frontend/templates/analytics.html")

@app.get("/profile")
def serve_profile():
    return FileResponse("frontend/templates/profile.html")


# ---- HEALTH CHECK ----
@app.get("/health")
def health_check():
    """Quick endpoint to check if server is running"""
    return {"status": "healthy", "app": settings.APP_NAME}


# ---- RUN THE SERVER ----
# This block runs when you execute: python main.py
# uvicorn is an ASGI server (handles web requests efficiently)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT))
    host = os.environ.get("HOST", settings.HOST)
    debug = settings.DEBUG

    print(f"\n{'='*50}")
    print(f"🚀 Starting {settings.APP_NAME}")
    print(f"📖 API Docs: http://{host}:{port}/docs")
    print(f"🌐 App: http://{host}:{port}")
    print(f"{'='*50}\n")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
    )
