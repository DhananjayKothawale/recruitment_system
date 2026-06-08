# ============================================================
# tests/test_core.py
# PURPOSE: Basic tests to verify the system works.
# Run with: python -m pytest tests/ -v
# ============================================================

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# TEST: ATS ENGINE
# ============================================================
class TestATSEngine:
    """Tests for the ATS scoring engine"""

    def setup_method(self):
        from backend.services.ats_engine import ATSEngine
        self.engine = ATSEngine()

    def test_skills_score_perfect_match(self):
        """When candidate has all required skills, score should be 100"""
        required = ["Python", "SQL", "FastAPI"]
        candidate = ["Python", "SQL", "FastAPI", "React"]  # Extra skill is OK
        score, matched, missing = self.engine.calculate_skills_score(candidate, required)
        assert score == 100.0
        assert len(matched) == 3
        assert len(missing) == 0

    def test_skills_score_partial_match(self):
        """When candidate has 2/4 skills, score should be 50"""
        required = ["Python", "SQL", "Power BI", "Machine Learning"]
        candidate = ["Python", "SQL"]
        score, matched, missing = self.engine.calculate_skills_score(candidate, required)
        assert score == 50.0
        assert len(matched) == 2
        assert len(missing) == 2
        assert "Power BI" in missing
        assert "Machine Learning" in missing

    def test_skills_score_no_required(self):
        """If job has no required skills, any candidate scores 100"""
        score, matched, missing = self.engine.calculate_skills_score(["Python"], [])
        assert score == 100.0

    def test_experience_score_exceeds(self):
        """If candidate has more exp than required, they still get 100"""
        score = self.engine.calculate_experience_score(10, 2, 5)
        assert score == 100.0

    def test_experience_score_partial(self):
        """If candidate has 1 year, required is 2, score should be 50"""
        score = self.engine.calculate_experience_score(1.0, 2, 5)
        assert score == 50.0

    def test_education_score_meets(self):
        """Bachelor candidate for Bachelor role = 100"""
        score = self.engine.calculate_education_score("Bachelor", "Bachelor")
        assert score == 100.0

    def test_education_score_exceeds(self):
        """Master candidate for Bachelor role = 100"""
        score = self.engine.calculate_education_score("Master", "Bachelor")
        assert score == 100.0

    def test_education_score_below(self):
        """Diploma candidate for Bachelor role = 70 (one level below)"""
        score = self.engine.calculate_education_score("Diploma", "Bachelor")
        assert score == 70.0

    def test_completeness_score(self):
        """Completeness score passes through correctly"""
        score = self.engine.calculate_completeness_score(85.0)
        assert score == 85.0

    def test_certifications_none(self):
        """No certifications = 0 score"""
        assert self.engine.calculate_certifications_score([]) == 0.0

    def test_certifications_some(self):
        """Having certifications gives bonus"""
        assert self.engine.calculate_certifications_score(["AWS Certified"]) == 50.0
        assert self.engine.calculate_certifications_score(["AWS", "GCP"]) == 100.0


# ============================================================
# TEST: RESUME PARSER
# ============================================================
class TestResumeParser:
    """Tests for the NLP resume parser"""

    def setup_method(self):
        from backend.nlp.resume_parser import ResumeParser
        self.parser = ResumeParser()

    def test_extract_email(self):
        text = "Contact me at john.doe@gmail.com for more info"
        assert self.parser.extract_email(text) == "john.doe@gmail.com"

    def test_extract_email_none(self):
        text = "No email here"
        assert self.parser.extract_email(text) is None

    def test_extract_phone_10digit(self):
        text = "Call me at 9876543210"
        phone = self.parser.extract_phone(text)
        assert phone is not None
        assert "9876543210" in phone

    def test_extract_skills_python(self):
        text = "I have 3 years of Python experience and know SQL and Machine Learning"
        skills = self.parser.extract_skills(text)
        skill_names = [s.lower() for s in skills]
        assert "python" in skill_names
        assert "sql" in skill_names
        assert "machine learning" in skill_names

    def test_extract_education_bachelor(self):
        text = "I completed my Bachelor of Engineering from Mumbai University"
        edu = self.parser.extract_education(text)
        assert edu == "Bachelor"

    def test_extract_education_master(self):
        text = "Master of Computer Science from IIT Bombay"
        edu = self.parser.extract_education(text)
        assert edu == "Master"

    def test_extract_experience_years(self):
        text = "I have 5 years of experience in software development"
        years = self.parser.extract_experience_years(text)
        assert years == 5.0

    def test_completeness_full(self):
        data = {
            "name": "John Doe",
            "email": "john@gmail.com",
            "phone": "9876543210",
            "skills": ["Python", "SQL"],
            "experience": 3.0,
            "education": "Bachelor",
            "certifications": ["AWS"],
        }
        score = self.parser.calculate_completeness(data)
        assert score >= 80  # Should be mostly complete


# ============================================================
# TEST: JOB MATCHER
# ============================================================
class TestJobMatcher:

    def test_tfidf_similarity_identical(self):
        """Identical texts should have similarity near 1.0"""
        from backend.services.job_matcher import calculate_tfidf_similarity
        text = "Python developer with SQL and machine learning experience"
        score = calculate_tfidf_similarity(text, text)
        assert score > 0.9

    def test_tfidf_similarity_different(self):
        """Completely different texts should have low similarity"""
        from backend.services.job_matcher import calculate_tfidf_similarity
        text1 = "Python developer machine learning data science"
        text2 = "Chef cooking recipes food restaurant kitchen"
        score = calculate_tfidf_similarity(text1, text2)
        assert score < 0.3

    def test_tfidf_empty_text(self):
        """Empty text should return 0"""
        from backend.services.job_matcher import calculate_tfidf_similarity
        assert calculate_tfidf_similarity("", "some text") == 0.0

    def test_rank_candidates(self):
        """Higher combined score should rank first"""
        from backend.services.job_matcher import rank_candidates
        candidates = [
            {"candidate_id": 1, "ats_score": 70, "match_score": 60},
            {"candidate_id": 2, "ats_score": 90, "match_score": 85},
            {"candidate_id": 3, "ats_score": 55, "match_score": 50},
        ]
        ranked = rank_candidates(candidates)
        assert ranked[0]["candidate_id"] == 2  # Highest scores first
        assert ranked[2]["candidate_id"] == 3  # Lowest scores last
        assert ranked[0]["rank"] == 1


# ============================================================
# TEST: AUTH
# ============================================================
class TestAuth:

    def test_password_hashing(self):
        """Hashed password should not equal plain password"""
        from backend.auth.jwt_handler import hash_password, verify_password
        plain = "mypassword123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert len(hashed) > 30  # bcrypt hashes are 60 chars

    def test_password_verify_correct(self):
        from backend.auth.jwt_handler import hash_password, verify_password
        plain = "testpassword"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_password_verify_wrong(self):
        from backend.auth.jwt_handler import hash_password, verify_password
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_create_verify_token(self):
        """Created token should be verifiable"""
        from backend.auth.jwt_handler import create_access_token, verify_token
        token = create_access_token({"sub": "test@example.com", "role": "candidate"})
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == "candidate"

    def test_verify_invalid_token(self):
        """Invalid token should return None"""
        from backend.auth.jwt_handler import verify_token
        payload = verify_token("this.is.not.a.valid.token")
        assert payload is None


# ============================================================
# RUN TESTS
# ============================================================
if __name__ == "__main__":
    print("Running tests...")
    print("Use: python -m pytest tests/test_core.py -v")
    print("Or:  python -m pytest tests/ -v --tb=short")
