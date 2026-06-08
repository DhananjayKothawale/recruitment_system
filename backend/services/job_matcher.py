# ============================================================
# backend/services/job_matcher.py
# PURPOSE: Calculates how well a resume matches a job description.
#
# TWO METHODS USED:
#
# 1. TF-IDF (Term Frequency-Inverse Document Frequency)
#    - A math technique to compare documents
#    - Gives importance to words that appear in resume but not everywhere
#    - Example: "Python" in a Python job is very important
#    - Fast and doesn't need internet or downloads
#
# 2. Sentence Transformers (Semantic Similarity)
#    - Uses AI to understand meaning, not just word matching
#    - "I built machine learning models" matches "ML development experience"
#    - More accurate but requires downloading a model (~80MB)
#
# FINAL SCORE = (TF-IDF × 40%) + (Semantic × 60%)
# ============================================================

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Optional

# We'll load sentence transformers lazily (only when needed)
_sentence_model = None


def get_sentence_model():
    """
    Loads the Sentence Transformer model.
    Only loads once (lazy loading) to save memory.
    """
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print("Loading Sentence Transformer model (first time may take a moment)...")
            # all-MiniLM-L6-v2 is small but very accurate
            _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✅ Sentence Transformer loaded")
        except Exception as e:
            print(f"⚠️ Sentence Transformer not available: {e}")
            _sentence_model = None
    return _sentence_model


def calculate_tfidf_similarity(text1: str, text2: str) -> float:
    """
    Calculates similarity between two texts using TF-IDF + Cosine Similarity.

    HOW IT WORKS:
    1. Convert both texts to TF-IDF vectors (lists of numbers)
    2. Calculate the "angle" between the two vectors
    3. If vectors point in the same direction → similar (score near 1.0)
    4. If vectors point in different directions → dissimilar (score near 0.0)

    Returns: similarity score (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0

    try:
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(
            stop_words='english',  # Remove common words like "the", "is", "and"
            ngram_range=(1, 2),    # Consider single words AND pairs of words
            max_features=5000      # Use only top 5000 most important words
        )

        # Fit and transform both texts
        tfidf_matrix = vectorizer.fit_transform([text1, text2])

        # Calculate cosine similarity
        # Result is a 2x2 matrix, we want [0][1] = similarity between text1 and text2
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

        return float(similarity)
    except Exception as e:
        print(f"TF-IDF error: {e}")
        return 0.0


def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Calculates semantic similarity using Sentence Transformers.

    HOW IT WORKS:
    1. Convert both texts to "embeddings" (vectors of 384 numbers)
    2. The AI model understands meaning, so "Python developer" and
       "software engineer using Python" get similar embeddings
    3. Calculate cosine similarity between the embeddings

    Returns: similarity score (0.0 to 1.0)
    """
    model = get_sentence_model()
    if model is None:
        return 0.0

    try:
        # Truncate texts (model has a max token limit)
        text1 = text1[:512]
        text2 = text2[:512]

        # Encode both texts to embeddings
        embeddings = model.encode([text1, text2])

        # Calculate cosine similarity
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

        return float(similarity)
    except Exception as e:
        print(f"Semantic similarity error: {e}")
        return 0.0


def calculate_job_match(resume_text: str, job_description: str) -> dict:
    """
    MAIN FUNCTION: Calculates overall match between resume and job.

    Args:
        resume_text: Full text of the resume
        job_description: Full job description

    Returns:
        {
            "match_percentage": 85.5,    # Final score (0-100)
            "tfidf_score": 78.3,         # TF-IDF component
            "semantic_score": 89.2,      # Semantic component
        }
    """
    if not resume_text or not job_description:
        return {"match_percentage": 0.0, "tfidf_score": 0.0, "semantic_score": 0.0}

    # Calculate both similarity scores
    tfidf_similarity = calculate_tfidf_similarity(resume_text, job_description)
    semantic_similarity = calculate_semantic_similarity(resume_text, job_description)

    # Convert from 0-1 range to 0-100 percentage
    tfidf_score = round(tfidf_similarity * 100, 2)
    semantic_score = round(semantic_similarity * 100, 2)

    # Weighted combination
    # If sentence transformer is available, use both
    # If not available (semantic_score = 0), use only TF-IDF
    if semantic_score > 0:
        final_score = (tfidf_score * 0.40) + (semantic_score * 0.60)
    else:
        final_score = tfidf_score

    return {
        "match_percentage": round(final_score, 2),
        "tfidf_score": tfidf_score,
        "semantic_score": semantic_score,
    }


def rank_candidates(candidates_data: list) -> list:
    """
    Ranks candidates for a job from best to worst.

    Args:
        candidates_data: List of dicts with candidate info
            [{"candidate_id": 1, "ats_score": 80, "match_score": 75, ...}]

    Returns:
        Same list but sorted by combined score (best first)
    """
    for candidate in candidates_data:
        # Combined ranking score: 60% ATS + 40% match
        ats = candidate.get("ats_score", 0)
        match = candidate.get("match_score", 0)
        candidate["combined_score"] = round((ats * 0.6) + (match * 0.4), 2)

    # Sort by combined score (highest first)
    ranked = sorted(candidates_data, key=lambda x: x["combined_score"], reverse=True)

    # Add rank number
    for i, candidate in enumerate(ranked, 1):
        candidate["rank"] = i

    return ranked
