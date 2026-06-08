# 🚀 AI-Powered Recruitment & Resume Screening System
## Complete Beginner's Master Guide

---

## 📁 WHAT THIS PROJECT IS

This is a full-stack web application. Think of it like LinkedIn + ATS (Applicant Tracking System) built by you.

**What it does:**
- Recruiters post jobs
- Candidates upload resumes (PDF)
- AI reads the resumes and scores them
- AI ranks the best candidates for each job
- Analytics dashboard shows trends

---

## 🗂️ FOLDER STRUCTURE EXPLAINED

```
recruitment_system/
│
├── backend/                ← Python FastAPI server (the brain)
│   ├── routes/             ← URL endpoints (what happens when you visit /api/jobs)
│   ├── models/             ← Database table definitions
│   ├── services/           ← Business logic (ATS scoring, parsing, etc.)
│   ├── database/           ← PostgreSQL connection setup
│   ├── auth/               ← JWT login/logout logic
│   ├── ml/                 ← Machine Learning models
│   ├── nlp/                ← Resume parsing with SpaCy
│   └── utils/              ← Helper functions
│
├── frontend/               ← HTML/CSS/JS files (what users see)
│   ├── templates/          ← HTML pages
│   └── static/             ← CSS, JS, images
│
├── uploads/                ← Where uploaded resumes are saved
├── models_saved/           ← Where trained ML models are saved (.pkl files)
├── tests/                  ← Test files
│
├── main.py                 ← START THE SERVER FROM HERE
├── config.py               ← All settings (database URL, secret key, etc.)
├── requirements.txt        ← All Python packages to install
└── .env                    ← Secret values (never share this file!)
```

---

## ⚡ HOW TO SET UP (Step by Step for Absolute Beginners)

### STEP 1: Install Python
- Go to https://python.org
- Download Python 3.11 or 3.12
- During install: ✅ CHECK "Add Python to PATH"
- Open Command Prompt and type: `python --version`
- You should see: `Python 3.11.x`

### STEP 2: Install VS Code
- Go to https://code.visualstudio.com
- Download and install
- Install extension: "Python" by Microsoft

### STEP 3: Install PostgreSQL
- Go to https://postgresql.org/download
- Download PostgreSQL 16 for your OS
- During install, set password: `postgres123` (remember this!)
- Default port: 5432
- After install, open pgAdmin 4 (it installs automatically)
- Create a new database called: `recruitment_db`

### STEP 4: Create Project Folder
Open VS Code, then open terminal (Ctrl+`) and type:
```bash
cd Desktop
mkdir recruitment_system
cd recruitment_system
```

### STEP 5: Create Virtual Environment
```bash
python -m venv venv
```
Then activate it:
- Windows: `venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

You should see `(venv)` at the start of your terminal line. This means it's working!

### STEP 6: Install All Packages
```bash
pip install -r requirements.txt
```
This will install ~20 packages. Wait for it to finish (might take 5 minutes).

### STEP 7: Create .env File
Create a file called `.env` in the root folder with this content:
```
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/recruitment_db
SECRET_KEY=your-super-secret-key-change-this-in-production-minimum-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### STEP 8: Run Database Migration (Create Tables)
```bash
python -c "from backend.database.connection import create_tables; create_tables()"
```

### STEP 9: Train the ML Model
```bash
python -c "from backend.ml.trainer import train_and_save_model; train_and_save_model()"
```

### STEP 10: Start the Server
```bash
python main.py
```

Open browser: http://localhost:8000

---

## 🔑 API KEY SETUP

This project uses these services/libraries:

### Sentence Transformers (FREE - No API Key Needed)
- Downloads automatically when you first run
- Used for: semantic job matching
- Model: `all-MiniLM-L6-v2` (downloads ~80MB on first run)

### SpaCy Model (FREE - Download Once)
After installing requirements, run:
```bash
python -m spacy download en_core_web_sm
```
This downloads the English NLP model (~12MB)

### PostgreSQL (FREE - Local)
- No API key needed
- Runs locally on your computer

### NO paid APIs required in this project!

---

## 🧪 HOW TO TEST THE API

After starting the server, open:
http://localhost:8000/docs

This is Swagger UI - an automatic API documentation page where you can test every endpoint!

---

## 👤 DEFAULT TEST ACCOUNTS

After setup, you can create accounts through the UI or API.

Roles available:
- `candidate` - can upload resume, apply to jobs
- `recruiter` - can post jobs, view candidates
- `admin` - can manage everything

---

## 🆘 COMMON ERRORS & FIXES

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `connection refused` (PostgreSQL) | Make sure PostgreSQL is running |
| `relation does not exist` | Run the create_tables command in Step 8 |
| `spacy model not found` | Run `python -m spacy download en_core_web_sm` |
| Port 8000 already in use | Change port in main.py to 8001 |

---

## 📊 PROJECT FEATURES CHECKLIST

- [x] User Registration & Login (JWT)
- [x] Role-based Access (Candidate/Recruiter/Admin)
- [x] PDF Resume Upload & Parsing
- [x] SpaCy NLP - Extract Name, Email, Skills, Experience
- [x] ATS Score Engine (0-100)
- [x] Job Posting Management
- [x] Job Matching (TF-IDF + Sentence Transformers)
- [x] Candidate Ranking Dashboard
- [x] ML Prediction (Logistic Regression + Random Forest + XGBoost)
- [x] Skill Gap Analysis
- [x] AI Interview Question Generator
- [x] Analytics Dashboard with Chart.js
- [x] Dark/Light Mode
- [x] Responsive Design

---

## 🎓 WHAT YOU LEARN FROM THIS PROJECT

1. **FastAPI** - Modern Python web framework
2. **SQLAlchemy** - Working with databases in Python
3. **JWT Authentication** - Secure login systems
4. **NLP with SpaCy** - Natural language processing
5. **Machine Learning** - Training and using ML models
6. **REST APIs** - Building and consuming APIs
7. **Frontend Integration** - Connecting HTML/JS to a Python backend
8. **PDF Processing** - Reading and extracting text from PDFs
9. **PostgreSQL** - Relational database design
10. **Git** - Version control

---

## 📝 FOR YOUR RESUME

You can say:
- "Built an AI-powered recruitment platform using FastAPI and Python"
- "Implemented NLP-based resume parsing using SpaCy"
- "Developed ML models (Logistic Regression, Random Forest, XGBoost) for candidate prediction"
- "Designed RESTful APIs with JWT authentication and role-based access control"
- "Built semantic job-candidate matching using Sentence Transformers and cosine similarity"
