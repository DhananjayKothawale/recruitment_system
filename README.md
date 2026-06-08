# 🤖 AI-Powered Recruitment & Resume Screening System

> A full-stack, production-style recruitment platform that uses NLP and Machine Learning to automatically screen resumes, calculate ATS scores, rank candidates, and predict hiring suitability.

---

## ✨ Features

| Feature | Technology |
|---|---|
| 📄 Resume Parsing (PDF) | SpaCy NLP + PyMuPDF + pdfplumber |
| 🎯 ATS Score (0-100) | Custom weighted scoring engine |
| 🔍 Job Matching | TF-IDF + Sentence Transformers + Cosine Similarity |
| 🤖 Candidate Prediction | Logistic Regression + Random Forest + XGBoost |
| 📊 Analytics Dashboard | Chart.js (Bar, Pie, Doughnut charts) |
| 🔒 Authentication | JWT (JSON Web Tokens) + bcrypt |
| 👥 Role-Based Access | Candidate / Recruiter / Admin |
| 🌓 Dark/Light Mode | CSS variables |
| 📱 Responsive Design | CSS Grid + Flexbox |

---

## 🛠️ Tech Stack

**Backend:** Python 3.11 · FastAPI · SQLAlchemy · PostgreSQL  
**Frontend:** HTML5 · CSS3 · Vanilla JavaScript · Chart.js  
**NLP:** SpaCy · Sentence Transformers (`all-MiniLM-L6-v2`)  
**ML:** Scikit-Learn · XGBoost · Pandas · NumPy  
**PDF:** PyMuPDF · pdfplumber  
**Auth:** JWT · passlib (bcrypt)  

---

## 📁 Project Structure

```
recruitment_system/
├── main.py                         ← Start server here
├── config.py                       ← App settings
├── requirements.txt                ← Python packages
├── .env                            ← Secret keys (create this!)
│
├── backend/
│   ├── auth/
│   │   └── jwt_handler.py          ← JWT login/logout
│   ├── database/
│   │   └── connection.py           ← PostgreSQL connection
│   ├── models/
│   │   ├── user.py                 ← Users table
│   │   ├── job.py                  ← Jobs table
│   │   ├── resume.py               ← Resumes table
│   │   ├── application.py          ← Applications + ATSResults tables
│   │   └── skill.py                ← Skills table
│   ├── routes/
│   │   ├── auth.py                 ← /api/auth/* endpoints
│   │   ├── jobs.py                 ← /api/jobs/* endpoints
│   │   ├── resume.py               ← /api/resume/* endpoints
│   │   ├── analytics.py            ← /api/analytics/* endpoints
│   │   ├── interview.py            ← /api/interview/* endpoints
│   │   └── ml.py                   ← /api/ml/* endpoints
│   ├── services/
│   │   ├── ats_engine.py           ← ATS scoring logic
│   │   └── job_matcher.py          ← TF-IDF + semantic matching
│   ├── nlp/
│   │   └── resume_parser.py        ← PDF parsing with SpaCy
│   └── ml/
│       └── trainer.py              ← Train/save/load ML models
│
├── frontend/
│   ├── templates/
│   │   ├── index.html              ← Landing page
│   │   ├── login.html              ← Login page
│   │   ├── register.html           ← Register page
│   │   ├── dashboard.html          ← Main dashboard
│   │   ├── jobs.html               ← Job listings
│   │   ├── upload_resume.html      ← Resume upload + NLP results
│   │   ├── analytics.html          ← Analytics + ranking
│   │   └── profile.html            ← User profile + interview prep
│   └── static/
│       ├── css/style.css           ← All styles
│       └── js/app.js               ← Shared JS utilities
│
├── uploads/                        ← Uploaded PDF resumes saved here
├── models_saved/                   ← Trained ML models (.pkl)
└── tests/
    └── test_core.py                ← Pytest test suite
```

---

## 🚀 Setup Guide (Beginner Friendly)

### Prerequisites
- Python 3.11+ → [python.org](https://python.org)
- PostgreSQL 16 → [postgresql.org](https://postgresql.org/download)
- VS Code → [code.visualstudio.com](https://code.visualstudio.com)
- Git → [git-scm.com](https://git-scm.com)

### Step 1: Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/recruitment_system.git
cd recruitment_system
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 4: Choose your database
This project now supports SQLite out of the box so you can deploy it for free without PostgreSQL.

- For local development or free hosting, use the default SQLite URL in `.env`.
- If you want PostgreSQL, keep the database creation step below.

#### Option A: Free SQLite (recommended for quick deploy)
No database server required.

#### Option B: PostgreSQL
Open pgAdmin 4 or psql and run:
```sql
CREATE DATABASE recruitment_db;
```

### Step 5: Create `.env` File
Use one of these values depending on your choice.

#### Free SQLite mode
```env
DATABASE_URL=sqlite:///./recruitment_db.sqlite3
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
PORT=8000
HOST=0.0.0.0
```

#### PostgreSQL mode
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/recruitment_db
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
PORT=8000
HOST=0.0.0.0
```

### Step 6: Initialize Database
```bash
python -c "from backend.database.connection import create_tables; create_tables()"
```

### Step 7: Train ML Model
```bash
python -c "from backend.ml.trainer import train_and_save_model; train_and_save_model()"
```

### Step 8: Run the Server
```bash
python main.py
```

Open browser: **http://localhost:8000**

## Docker (optional, recommended for production)

There is a `Dockerfile` included to build a small production image. For local testing and fast deploys, see `DEPLOY_DOCKER.md`.


---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login, get JWT token | No |
| GET | `/api/auth/me` | Get current user | Yes |
| GET | `/api/jobs/` | List all jobs | No |
| POST | `/api/jobs/` | Create job | Recruiter |
| GET | `/api/jobs/{id}` | Get job details | No |
| POST | `/api/resume/upload` | Upload PDF resume | Yes |
| GET | `/api/resume/my-resume` | Get my resume | Yes |
| POST | `/api/resume/apply/{job_id}` | Apply to job | Candidate |
| GET | `/api/resume/skill-gap/{job_id}` | Skill gap analysis | Yes |
| GET | `/api/analytics/dashboard` | Dashboard stats | Recruiter |
| GET | `/api/analytics/candidates/{job_id}` | Ranked candidates | Recruiter |
| GET | `/api/interview/questions?skills=python` | Interview questions | Yes |
| GET | `/api/ml/model-info` | ML model performance | Yes |
| POST | `/api/ml/predict` | Predict suitability | Yes |

**Interactive API Docs:** http://localhost:8000/docs

---

## 🧪 Running Tests
```bash
python -m pytest tests/ -v
```

---

## 📖 What I Learned Building This
- FastAPI dependency injection and async patterns
- SQLAlchemy ORM relationships and migrations
- JWT authentication flow (sign → send → verify)
- NLP with SpaCy (Named Entity Recognition, regex patterns)
- TF-IDF vectorization and cosine similarity
- Sentence Transformers for semantic text matching
- ML model training, evaluation, and serialization
- PostgreSQL schema design (FKs, indexes, relationships)
- Responsive frontend without any framework

---

## 👨‍💻 Author
Made with ❤️ as a Final Year / Portfolio Project

---

## 📄 License
MIT License — free to use for learning and portfolio purposes.
