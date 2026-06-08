# ============================================================
# backend/routes/ml.py
# PURPOSE: ML model info, predictions, and training results
# ============================================================

import os
import pickle
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.auth.jwt_handler import get_current_user
from backend.models.user import User
from config import settings

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])


class PredictionRequest(BaseModel):
    ats_score: float
    skills_count: int
    experience_years: float
    has_certifications: int  # 0 or 1
    education_level: int     # 1=HighSchool, 2=Diploma, 4=Bachelor, 5=Master, 6=PhD
    match_score: float


@router.get("/model-info")
def get_model_info(current_user: User = Depends(get_current_user)):
    """
    Returns info about the trained ML model and its performance.
    GET /api/ml/model-info
    """
    results_path = os.path.join(settings.MODEL_DIR, "model_results.pkl")

    if not os.path.exists(results_path):
        return {
            "status": "not_trained",
            "message": "Model not trained yet. Run: python -c \"from backend.ml.trainer import train_and_save_model; train_and_save_model()\""
        }

    with open(results_path, "rb") as f:
        results = pickle.load(f)

    best_name = results.get("best_model_name", "Unknown")

    models_data = []
    for name in ["Logistic Regression", "Random Forest", "XGBoost"]:
        if name in results:
            m = results[name]
            models_data.append({
                "name": name,
                "accuracy": round(m["accuracy"] * 100, 2),
                "precision": round(m["precision"] * 100, 2),
                "recall": round(m["recall"] * 100, 2),
                "f1_score": round(m["f1_score"] * 100, 2),
                "confusion_matrix": m["confusion_matrix"],
                "is_best": name == best_name,
            })

    return {
        "status": "trained",
        "best_model": best_name,
        "models": models_data,
        "features": results.get("feature_columns", []),
    }


@router.post("/predict")
def predict(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Predict candidate suitability using the trained ML model.
    POST /api/ml/predict
    """
    from backend.ml.trainer import predict_candidate_suitability
    result = predict_candidate_suitability(
        ats_score=request.ats_score,
        skills_count=request.skills_count,
        experience_years=request.experience_years,
        has_certifications=request.has_certifications,
        education_level=request.education_level,
        match_score=request.match_score
    )
    return result


@router.post("/train")
def train_model(current_user: User = Depends(get_current_user)):
    """
    Re-train the ML model. Admin only in real app.
    POST /api/ml/train
    """
    from backend.ml.trainer import train_and_save_model
    try:
        results = train_and_save_model()
        return {"status": "success", "best_model": results.get("best_model_name")}
    except Exception as e:
        return {"status": "error", "message": str(e)}
