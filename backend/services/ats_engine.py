# ============================================================
# backend/services/ats_engine.py
# PURPOSE: Calculates ATS (Applicant Tracking System) score.
#
# An ATS score tells you HOW WELL a resume matches a job.
# Real companies like Google, Amazon use ATS to filter resumes.
#
# OUR SCORING FORMULA:
# Total Score = (Skills × 35%) + (Experience × 25%) +
#               (Education × 20%) + (Completeness × 10%) +
#               (Certifications × 5%) + (Projects × 5%)
# ============================================================

from typing import Dict, List, Tuple
from backend.models.resume import Resume
from backend.models.job import Job


class ATSEngine:
    """
    Calculates ATS score between a resume and a job posting.

    Usage:
        engine = ATSEngine()
        result = engine.calculate_score(resume, job)
        print(result["total_score"])  # 78.5
    """

    # Weights for each scoring component (must add up to 1.0 = 100%)
    WEIGHTS = {
        "skills": 0.35,         # 35% - Most important
        "experience": 0.25,     # 25% - Second most important
        "education": 0.20,      # 20%
        "completeness": 0.10,   # 10%
        "certifications": 0.05, # 5%
        "projects": 0.05,       # 5%
    }

    def calculate_skills_score(
        self,
        candidate_skills: List[str],
        required_skills: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculates how many required skills the candidate has.

        Returns:
            - score (0-100)
            - matched_skills (list of skills candidate HAS)
            - missing_skills (list of skills candidate is MISSING)

        Example:
            Required: [Python, SQL, Power BI, ML]
            Candidate: [Python, SQL]
            Score: 2/4 = 50%
            Matched: [Python, SQL]
            Missing: [Power BI, ML]
        """
        if not required_skills:
            return 100.0, [], []

        # Convert to lowercase for case-insensitive comparison
        candidate_lower = [s.lower() for s in candidate_skills]
        required_lower = [s.lower() for s in required_skills]

        matched = []
        missing = []

        for req_skill in required_skills:
            if req_skill.lower() in candidate_lower:
                matched.append(req_skill)
            else:
                missing.append(req_skill)

        # Score = (matched / total required) * 100
        score = (len(matched) / len(required_skills)) * 100 if required_skills else 100

        return round(score, 2), matched, missing

    def calculate_experience_score(
        self,
        candidate_years: float,
        min_required: int,
        max_required: int
    ) -> float:
        """
        Calculates experience match score.

        Rules:
        - If candidate has MORE than required: 100 (they're overqualified but still good)
        - If candidate has EXACTLY required: 100
        - If candidate has LESS: proportional score

        Example:
            Required: 2-5 years, Candidate has: 3 years → 100
            Required: 2-5 years, Candidate has: 1 year → 50
        """
        if candidate_years >= min_required:
            return 100.0
        elif min_required == 0:
            return 100.0
        else:
            # Give partial credit based on how close they are
            score = (candidate_years / min_required) * 100
            return round(min(score, 100.0), 2)

    def calculate_education_score(
        self,
        candidate_education: str,
        required_education: str
    ) -> float:
        """
        Checks if candidate's education meets the requirement.

        Education hierarchy (higher = better):
        PhD > Master > Bachelor > Diploma > High School
        """
        # Map education levels to numeric values
        education_levels = {
            "high school": 1,
            "diploma": 2,
            "not specified": 3,
            "bachelor": 4,
            "master": 5,
            "phd": 6,
        }

        candidate_level = education_levels.get(candidate_education.lower(), 3)
        required_level = education_levels.get(required_education.lower(), 4)

        if candidate_level >= required_level:
            return 100.0
        elif candidate_level == required_level - 1:
            return 70.0  # One level below = partial credit
        else:
            return 30.0  # Two or more levels below = low score

    def calculate_completeness_score(self, completeness: float) -> float:
        """
        Returns the completeness score directly (already 0-100).
        """
        return round(min(completeness, 100.0), 2)

    def calculate_certifications_score(self, certifications: List[str]) -> float:
        """
        Bonus score for having certifications.
        0 certs = 0, 1 cert = 50, 2+ certs = 100
        """
        if not certifications:
            return 0.0
        elif len(certifications) == 1:
            return 50.0
        else:
            return 100.0

    def calculate_projects_score(self, raw_text: str) -> float:
        """
        Estimates project experience from resume text.
        Looks for project section keywords.
        """
        if not raw_text:
            return 0.0

        text_lower = raw_text.lower()
        project_keywords = ["project", "built", "developed", "created", "implemented", "deployed"]

        count = sum(1 for kw in project_keywords if kw in text_lower)

        if count >= 5:
            return 100.0
        elif count >= 3:
            return 75.0
        elif count >= 1:
            return 50.0
        else:
            return 0.0

    def calculate_score(self, resume: Resume, job: Job) -> Dict:
        """
        MAIN FUNCTION: Calculates the complete ATS score.

        Args:
            resume: Resume object from database
            job: Job object from database

        Returns:
            Dictionary with all scores and breakdown:
            {
                "total_score": 78.5,
                "skills_score": 75.0,
                "experience_score": 100.0,
                "education_score": 100.0,
                "completeness_score": 80.0,
                "certifications_score": 50.0,
                "projects_score": 75.0,
                "matched_skills": ["Python", "SQL"],
                "missing_skills": ["Power BI"],
            }
        """
        # Get candidate's skills
        candidate_skills = resume.get_skills_list()
        # Get job's required skills
        required_skills = job.get_skills_list()

        # Calculate each component
        skills_score, matched_skills, missing_skills = self.calculate_skills_score(
            candidate_skills, required_skills
        )

        experience_score = self.calculate_experience_score(
            resume.extracted_experience_years or 0,
            job.min_experience or 0,
            job.max_experience or 10
        )

        education_score = self.calculate_education_score(
            resume.extracted_education or "Not Specified",
            job.required_education or "Bachelor"
        )

        completeness_score = self.calculate_completeness_score(
            resume.completeness_score or 0
        )

        certifications_list = []
        if resume.extracted_certifications:
            certifications_list = [c.strip() for c in resume.extracted_certifications.split(",")]
        certifications_score = self.calculate_certifications_score(certifications_list)

        projects_score = self.calculate_projects_score(resume.raw_text or "")

        # Calculate weighted total score
        total_score = (
            skills_score * self.WEIGHTS["skills"] +
            experience_score * self.WEIGHTS["experience"] +
            education_score * self.WEIGHTS["education"] +
            completeness_score * self.WEIGHTS["completeness"] +
            certifications_score * self.WEIGHTS["certifications"] +
            projects_score * self.WEIGHTS["projects"]
        )

        return {
            "total_score": round(total_score, 2),
            "skills_score": skills_score,
            "experience_score": experience_score,
            "education_score": education_score,
            "completeness_score": completeness_score,
            "certifications_score": certifications_score,
            "projects_score": projects_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
        }


# Singleton instance
ats_engine = ATSEngine()
