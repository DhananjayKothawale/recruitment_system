# ============================================================
# backend/nlp/resume_parser.py
# PURPOSE: Extracts structured information from PDF resumes.
#
# HOW IT WORKS:
# 1. Read the PDF file using PyMuPDF
# 2. Get all text from the PDF
# 3. Use Regex to find email, phone number
# 4. Use SpaCy NLP to find names (Named Entity Recognition)
# 5. Use keyword matching to find skills
# 6. Use pattern matching to find years of experience
# ============================================================

import re
import fitz  # PyMuPDF
import pdfplumber
import spacy
from typing import Dict, List, Optional, Tuple


# ---- SKILLS DATABASE ----
# List of skills we recognize. Add more as needed!
KNOWN_SKILLS = [
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "kotlin", "swift",
    "r", "matlab", "scala", "php", "ruby", "dart", "bash",

    # Web Frameworks
    "fastapi", "django", "flask", "react", "angular", "vue", "nextjs", "express", "spring boot",
    "node.js", "nodejs", "laravel",

    # Databases
    "postgresql", "mysql", "mongodb", "redis", "sqlite", "oracle", "cassandra", "elasticsearch",
    "sql", "nosql",

    # Data Science / ML
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
    "keras", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn", "xgboost",
    "random forest", "neural network",

    # Cloud & DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "github", "linux", "jenkins", "ci/cd",

    # Data Tools
    "power bi", "tableau", "excel", "spark", "hadoop", "airflow", "dbt",

    # Other
    "rest api", "graphql", "microservices", "agile", "scrum", "jira", "figma",
]

# Education level keywords
EDUCATION_KEYWORDS = {
    "phd": "PhD",
    "doctorate": "PhD",
    "master": "Master",
    "mba": "Master",
    "m.tech": "Master",
    "m.sc": "Master",
    "bachelor": "Bachelor",
    "b.tech": "Bachelor",
    "b.sc": "Bachelor",
    "b.e": "Bachelor",
    "undergraduate": "Bachelor",
    "diploma": "Diploma",
    "10th": "High School",
    "12th": "High School",
}


class ResumeParser:
    """
    Main class that handles resume parsing.

    Usage:
        parser = ResumeParser()
        result = parser.parse_resume("/path/to/resume.pdf")
        print(result["skills"])  # ['Python', 'SQL', ...]
    """

    def __init__(self):
        # Load SpaCy English model
        # "en_core_web_sm" = small English model (fast, good enough for resume parsing)
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ SpaCy model loaded")
        except OSError:
            print("❌ SpaCy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extracts all text from a PDF file.
        Tries PyMuPDF first, falls back to pdfplumber.
        """
        text = ""
        try:
            # Method 1: PyMuPDF (faster)
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"PyMuPDF failed: {e}, trying pdfplumber...")
            try:
                # Method 2: pdfplumber (better for complex PDFs)
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
            except Exception as e2:
                print(f"pdfplumber also failed: {e2}")

        return text.strip()

    def extract_email(self, text: str) -> Optional[str]:
        """
        Finds email address using regex pattern.
        Example: finds "john.doe@gmail.com" in text
        """
        # Regex pattern for email addresses
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(pattern, text)
        return matches[0] if matches else None

    def extract_phone(self, text: str) -> Optional[str]:
        """
        Finds phone number using regex pattern.
        Handles formats like: +91-9876543210, (123) 456-7890, 9876543210
        """
        patterns = [
            r'\+?[\d\s\-\(\)]{10,15}',    # General phone pattern
            r'\b\d{10}\b',                  # 10 digit number
            r'\+91[\s\-]?\d{10}',          # India: +91 format
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Clean up: remove extra spaces and dashes
                phone = re.sub(r'[\s]', '', matches[0]).strip()
                if len(phone) >= 10:
                    return phone
        return None

    def extract_name(self, text: str) -> Optional[str]:
        """
        Extracts person's name using SpaCy Named Entity Recognition.
        SpaCy can identify "PERSON" entities in text.
        """
        if not self.nlp:
            return None

        # Look at the first 500 characters (name is usually at the top)
        doc = self.nlp(text[:500])

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Return first PERSON entity found
                name = ent.text.strip()
                if len(name.split()) >= 2:  # Must have at least first + last name
                    return name

        return None

    def extract_skills(self, text: str) -> List[str]:
        """
        Finds skills mentioned in the resume text.
        Simple but effective: checks if each known skill appears in the text.
        """
        text_lower = text.lower()
        found_skills = []

        for skill in KNOWN_SKILLS:
            # Check if skill name appears in text
            # Use word boundary \b to avoid partial matches
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                # Add to found skills (in Title Case)
                found_skills.append(skill.title())

        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in found_skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)

        return unique_skills

    def extract_experience_years(self, text: str) -> float:
        """
        Estimates total years of experience from text.
        Looks for patterns like "3 years experience", "5+ years", etc.
        """
        text_lower = text.lower()

        # Patterns to find experience mentions
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s+)?experience',
            r'experience\s*(?:of\s+)?(\d+)\+?\s*years?',
            r'(\d+)\+?\s*yrs?\s*(?:of\s+)?experience',
        ]

        years_found = []
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                years_found.append(int(match))

        if years_found:
            return float(max(years_found))  # Return the highest number found

        # Try to count years from date ranges (e.g., 2020 - 2023)
        date_pattern = r'(20\d{2})\s*[-–]\s*(20\d{2}|present|current)'
        date_matches = re.findall(date_pattern, text_lower)
        if date_matches:
            total_years = 0
            import datetime
            current_year = datetime.datetime.now().year
            for start, end in date_matches:
                end_year = current_year if end in ['present', 'current'] else int(end)
                total_years += end_year - int(start)
            return float(min(total_years, 30))  # Cap at 30 years

        return 0.0

    def extract_education(self, text: str) -> str:
        """
        Determines the highest education level from the resume.
        Returns: "PhD", "Master", "Bachelor", "Diploma", "High School", or "Not Specified"
        """
        text_lower = text.lower()

        # Check from highest to lowest education
        for keyword, level in EDUCATION_KEYWORDS.items():
            if keyword in text_lower:
                return level

        return "Not Specified"

    def extract_certifications(self, text: str) -> List[str]:
        """
        Finds certifications mentioned in the resume.
        """
        cert_keywords = [
            "certified", "certification", "certificate", "aws certified",
            "azure certified", "google certified", "pmp", "cissp", "ccna",
            "coursera", "udemy", "edx", "microsoft certified"
        ]
        text_lower = text.lower()
        found_certs = []

        for cert in cert_keywords:
            if cert in text_lower:
                found_certs.append(cert.title())

        return found_certs[:5]  # Return max 5 certifications

    def calculate_completeness(self, parsed_data: Dict) -> float:
        """
        Calculates how complete the resume is (0-100).
        Checks if key sections are present.
        """
        score = 0
        checks = {
            "name": 15,
            "email": 15,
            "phone": 10,
            "skills": 25,
            "experience": 15,
            "education": 15,
            "certifications": 5,
        }

        for field, points in checks.items():
            value = parsed_data.get(field)
            if value and value != "Not Specified" and value != [] and value != 0.0:
                score += points

        return min(float(score), 100.0)

    def parse_resume(self, pdf_path: str) -> Dict:
        """
        MAIN FUNCTION: Parses a resume PDF and returns all extracted info.

        Returns a dictionary like:
        {
            "name": "John Doe",
            "email": "john@gmail.com",
            "phone": "9876543210",
            "skills": ["Python", "SQL", "Machine Learning"],
            "experience_years": 3.0,
            "education": "Bachelor",
            "certifications": ["AWS Certified"],
            "raw_text": "full text of resume...",
            "completeness_score": 85.0
        }
        """
        print(f"Parsing resume: {pdf_path}")

        # Step 1: Extract text from PDF
        raw_text = self.extract_text_from_pdf(pdf_path)

        if not raw_text:
            return {"error": "Could not extract text from PDF. Is the PDF text-based (not scanned)?"}

        # Step 2: Extract each piece of information
        parsed_data = {
            "name": self.extract_name(raw_text),
            "email": self.extract_email(raw_text),
            "phone": self.extract_phone(raw_text),
            "skills": self.extract_skills(raw_text),
            "experience_years": self.extract_experience_years(raw_text),
            "education": self.extract_education(raw_text),
            "certifications": self.extract_certifications(raw_text),
            "raw_text": raw_text[:5000],  # Store first 5000 chars
        }

        # Step 3: Calculate completeness
        parsed_data["completeness_score"] = self.calculate_completeness(parsed_data)

        print(f"✅ Parsing complete. Found {len(parsed_data['skills'])} skills.")
        return parsed_data


# Create a singleton instance (one parser shared across the app)
resume_parser = ResumeParser()
