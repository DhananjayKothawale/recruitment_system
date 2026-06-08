# ============================================================
# backend/ml/trainer.py
# PURPOSE: Trains ML models to predict candidate suitability.
#
# WHAT IT DOES:
# Given features about a candidate (ATS score, skills count, etc.)
# the model predicts whether they are "suitable" (1) or "not suitable" (0)
#
# We train 3 models and compare them:
# 1. Logistic Regression - Simple, fast, interpretable
# 2. Random Forest - More complex, handles non-linear patterns
# 3. XGBoost - Very powerful, wins most ML competitions
#
# The best model is saved as a .pkl file for later use.
# ============================================================

import numpy as np
import pandas as pd
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score,
                             recall_score, f1_score, confusion_matrix)
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
from config import settings


def generate_training_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generates synthetic training data since we don't have real data yet.

    In a real system, you'd use actual application data from your database.

    Features:
    - ats_score: 0-100 (ATS matching score)
    - skills_count: 0-20 (number of skills)
    - experience_years: 0-15
    - has_certifications: 0 or 1
    - education_level: 1-5 (1=HighSchool, 5=PhD)
    - match_score: 0-100 (job matching score)

    Target:
    - suitable: 1 = good candidate, 0 = not suitable
    """
    np.random.seed(42)  # For reproducible results

    data = {
        "ats_score": np.random.uniform(20, 100, n_samples),
        "skills_count": np.random.randint(0, 20, n_samples),
        "experience_years": np.random.uniform(0, 15, n_samples),
        "has_certifications": np.random.randint(0, 2, n_samples),
        "education_level": np.random.randint(1, 6, n_samples),
        "match_score": np.random.uniform(20, 100, n_samples),
    }

    df = pd.DataFrame(data)

    # Create a realistic "suitable" label
    # A candidate is suitable if they have good scores
    df["suitable"] = (
        (df["ats_score"] >= 60) &
        (df["skills_count"] >= 5) &
        (df["experience_years"] >= 1) &
        (df["match_score"] >= 55)
    ).astype(int)

    # Add some noise to make it more realistic
    noise_mask = np.random.random(n_samples) < 0.1  # 10% noise
    df.loc[noise_mask, "suitable"] = 1 - df.loc[noise_mask, "suitable"]

    print(f"Generated {n_samples} samples")
    print(f"Suitable: {df['suitable'].sum()} ({df['suitable'].mean()*100:.1f}%)")
    print(f"Not suitable: {(1-df['suitable']).sum()} ({(1-df['suitable']).mean()*100:.1f}%)")

    return df


def train_and_save_model():
    """
    MAIN FUNCTION: Trains all models, compares them, saves the best one.

    Usage:
        python -c "from backend.ml.trainer import train_and_save_model; train_and_save_model()"
    """
    print("\n" + "="*50)
    print("STARTING ML MODEL TRAINING")
    print("="*50)

    # Step 1: Generate/Load training data
    df = generate_training_data(1000)

    # Step 2: Separate features (X) from target (y)
    feature_columns = ["ats_score", "skills_count", "experience_years",
                       "has_certifications", "education_level", "match_score"]
    X = df[feature_columns]
    y = df["suitable"]

    # Step 3: Split into training (80%) and testing (20%) sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Step 4: Scale features (important for Logistic Regression)
    # StandardScaler converts all features to have mean=0 and std=1
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)  # Use fit from training data!

    print(f"\nTraining set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")

    # Step 5: Define models to train
    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        ),
    }

    # Step 6: Train and evaluate each model
    results = {}

    for model_name, model in models.items():
        print(f"\n--- Training {model_name} ---")

        # Train the model
        if model_name == "Logistic Regression":
            model.fit(X_train_scaled, y_train)
            y_pred = model.predict(X_test_scaled)
        else:
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)

        results[model_name] = {
            "model": model,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "confusion_matrix": cm.tolist(),
        }

        print(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.1f}%)")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1 Score:  {f1:.4f}")

    # Step 7: Find the best model (by F1 score)
    best_model_name = max(results, key=lambda k: results[k]["f1_score"])
    best_model = results[best_model_name]["model"]

    print(f"\n🏆 Best Model: {best_model_name}")
    print(f"   F1 Score: {results[best_model_name]['f1_score']:.4f}")

    # Step 8: Save best model and scaler to disk
    os.makedirs(settings.MODEL_DIR, exist_ok=True)

    model_path = os.path.join(settings.MODEL_DIR, "best_model.pkl")
    scaler_path = os.path.join(settings.MODEL_DIR, "scaler.pkl")
    results_path = os.path.join(settings.MODEL_DIR, "model_results.pkl")

    with open(model_path, "wb") as f:
        pickle.dump(best_model, f)

    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    # Save results without the actual model objects (for display)
    results_to_save = {
        name: {k: v for k, v in data.items() if k != "model"}
        for name, data in results.items()
    }
    results_to_save["best_model_name"] = best_model_name
    results_to_save["feature_columns"] = feature_columns

    with open(results_path, "wb") as f:
        pickle.dump(results_to_save, f)

    print(f"\n✅ Model saved to: {model_path}")
    print(f"✅ Scaler saved to: {scaler_path}")
    print(f"✅ Results saved to: {results_path}")
    print("\n" + "="*50)

    return results_to_save


def load_model():
    """
    Loads the saved ML model from disk.
    Returns (model, scaler) tuple.
    """
    model_path = os.path.join(settings.MODEL_DIR, "best_model.pkl")
    scaler_path = os.path.join(settings.MODEL_DIR, "scaler.pkl")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            "ML model not found! Run: python -c \"from backend.ml.trainer import train_and_save_model; train_and_save_model()\""
        )

    with open(model_path, "rb") as f:
        model = pickle.load(f)

    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)

    return model, scaler


def predict_candidate_suitability(
    ats_score: float,
    skills_count: int,
    experience_years: float,
    has_certifications: int,
    education_level: int,
    match_score: float
) -> dict:
    """
    Uses the trained model to predict if a candidate is suitable.

    Args:
        ats_score: ATS score (0-100)
        skills_count: Number of skills
        experience_years: Years of experience
        has_certifications: 1 if has certs, 0 otherwise
        education_level: 1-5 (1=HighSchool, 5=PhD)
        match_score: Job match score (0-100)

    Returns:
        {"suitable": True/False, "probability": 0.85, "prediction_label": "Highly Suitable"}
    """
    try:
        model, scaler = load_model()
    except FileNotFoundError:
        # If model not trained yet, use simple rule-based fallback
        suitable = (ats_score >= 60 and match_score >= 55 and skills_count >= 5)
        return {
            "suitable": suitable,
            "probability": ats_score / 100.0,
            "prediction_label": "Suitable" if suitable else "Not Suitable",
            "method": "rule-based (train model for ML prediction)"
        }

    # Create feature array
    features = np.array([[
        ats_score, skills_count, experience_years,
        has_certifications, education_level, match_score
    ]])

    # Check if this model needs scaling (Logistic Regression does)
    from sklearn.linear_model import LogisticRegression
    if isinstance(model, LogisticRegression):
        features = scaler.transform(features)

    # Make prediction
    prediction = model.predict(features)[0]
    probability = model.predict_proba(features)[0][1]  # Probability of class 1 (suitable)

    # Create human-readable label
    if probability >= 0.8:
        label = "Highly Suitable"
    elif probability >= 0.6:
        label = "Suitable"
    elif probability >= 0.4:
        label = "Borderline"
    else:
        label = "Not Suitable"

    return {
        "suitable": bool(prediction),
        "probability": round(float(probability), 4),
        "prediction_label": label,
        "method": "ml-model"
    }
