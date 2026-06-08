# ============================================================
# backend/routes/interview.py
# PURPOSE: Generates interview questions based on skills
# ============================================================

from fastapi import APIRouter, Depends
from backend.models.user import User
from backend.auth.jwt_handler import get_current_user

router = APIRouter(prefix="/api/interview", tags=["Interview"])

# Pre-defined question bank
# In a real system, you could expand this or use an LLM
QUESTION_BANK = {
    "python": {
        "beginner": [
            "What is the difference between a list and a tuple in Python?",
            "What is a dictionary in Python? Give an example.",
            "Explain what a function is and write a simple example.",
        ],
        "intermediate": [
            "What are Python decorators? Write a simple example.",
            "Explain list comprehensions with an example.",
            "What is the difference between *args and **kwargs?",
        ],
        "advanced": [
            "Explain Python's GIL (Global Interpreter Lock).",
            "What are Python generators? How are they different from lists?",
            "Explain metaclasses in Python.",
        ]
    },
    "sql": {
        "beginner": [
            "What is the difference between WHERE and HAVING clause?",
            "Explain the difference between INNER JOIN and LEFT JOIN.",
            "What is a primary key?",
        ],
        "intermediate": [
            "What are window functions in SQL? Give an example.",
            "Explain database normalization (1NF, 2NF, 3NF).",
            "What is the difference between DELETE, TRUNCATE, and DROP?",
        ],
        "advanced": [
            "How do you optimize a slow SQL query?",
            "Explain query execution plans and how to read them.",
            "What are CTEs and when would you use them?",
        ]
    },
    "machine learning": {
        "beginner": [
            "What is the difference between supervised and unsupervised learning?",
            "Explain what overfitting is and how to prevent it.",
            "What is a confusion matrix?",
        ],
        "intermediate": [
            "Explain the bias-variance tradeoff.",
            "What is cross-validation and why is it important?",
            "What is gradient descent? Explain intuitively.",
        ],
        "advanced": [
            "Explain attention mechanisms in transformers.",
            "How does backpropagation work mathematically?",
            "Compare L1 and L2 regularization.",
        ]
    },
    "fastapi": {
        "beginner": [
            "What is FastAPI and what makes it different from Flask?",
            "What is Pydantic and how does FastAPI use it?",
            "How do you create a simple GET endpoint in FastAPI?",
        ],
        "intermediate": [
            "What is dependency injection in FastAPI?",
            "How do you handle file uploads in FastAPI?",
            "Explain async/await in FastAPI.",
        ],
        "advanced": [
            "How would you implement background tasks in FastAPI?",
            "Explain middleware in FastAPI with an example.",
            "How do you implement rate limiting in FastAPI?",
        ]
    },
    "react": {
        "beginner": [
            "What is JSX in React?",
            "What is the difference between state and props?",
            "What is a React component?",
        ],
        "intermediate": [
            "Explain the React component lifecycle.",
            "What are React hooks? Give examples of useState and useEffect.",
            "What is the virtual DOM?",
        ],
        "advanced": [
            "Explain React context and when to use it.",
            "What are higher-order components (HOCs)?",
            "How does React reconciliation work?",
        ]
    },
}


@router.get("/questions")
def get_interview_questions(
    skills: str = "python",
    current_user: User = Depends(get_current_user)
):
    """
    Generate interview questions for given skills.

    GET /api/interview/questions?skills=python,sql,machine learning

    Returns beginner, intermediate, and advanced questions for each skill.
    """
    skills_list = [s.strip().lower() for s in skills.split(",")]
    questions = {}

    for skill in skills_list:
        if skill in QUESTION_BANK:
            questions[skill] = QUESTION_BANK[skill]
        else:
            # Generic questions for skills not in our bank
            questions[skill] = {
                "beginner": [
                    f"What is {skill} and what is it used for?",
                    f"What are the main features of {skill}?",
                ],
                "intermediate": [
                    f"Describe a project where you used {skill}.",
                    f"What are best practices when working with {skill}?",
                ],
                "advanced": [
                    f"What are the limitations or challenges of {skill}?",
                    f"How would you optimize performance when using {skill}?",
                ]
            }

    return {
        "skills": skills_list,
        "questions": questions,
        "total_questions": sum(
            len(levels.get("beginner", [])) +
            len(levels.get("intermediate", [])) +
            len(levels.get("advanced", []))
            for levels in questions.values()
        )
    }
