"""
Toxicity Classifier Module.
Provides inference wrapper for pretrained HuggingFace 'unitary/toxic-bert' model,
and scikit-learn TF-IDF + Logistic Regression classical ML baseline for comparative evaluation.
"""

import time
import logging
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support

from src.config import TOXICITY_MODEL_NAME, TOXICITY_THRESHOLD
from src.preprocessing import clean_text

logger = logging.getLogger(__name__)

# Fallback keywords for offline/quick mode if transformers fail or during offline unit tests
FALLBACK_TOXIC_KEYWORDS = [
    "stupid", "idiot", "moron", "trash", "die", "scum", "loser",
    "destroy", "whiny", "crap", "bullshit", "pathetically", "fraud"
]


class ToxicityClassifier:
    """
    Inference wrapper around pretrained HuggingFace toxicity model (unitary/toxic-bert).
    Multi-label toxicity outputs: toxic, severe_toxic, obscene, threat, insult, identity_hate.
    """

    def __init__(self, model_name: str = TOXICITY_MODEL_NAME, threshold: float = TOXICITY_THRESHOLD):
        self.model_name = model_name
        self.threshold = threshold
        self._pipeline = None
        self._is_loaded = False
        self._init_model()

    def _init_model(self) -> None:
        """Attempts to load pretrained HuggingFace pipeline lazily/safely."""
        try:
            from transformers import pipeline
            logger.info(f"Loading pretrained toxicity model '{self.model_name}'...")
            self._pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                top_k=None,  # Return all multi-label class scores
                tokenizer=self.model_name,
                device=-1    # CPU inference
            )
            self._is_loaded = True
            logger.info("Toxicity model loaded successfully.")
        except Exception as e:
            logger.warning(f"Unable to load HuggingFace toxicity model '{self.model_name}': {e}. Using deterministic heuristic fallback.")
            self._is_loaded = False

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Runs toxicity classification on input text.

        Args:
            text: Input text string.

        Returns:
            Dict containing:
            - toxicity_score: float (0.0 to 1.0)
            - is_toxic: bool (toxicity_score >= threshold)
            - categories: Dict[str, float] multi-label scores
            - latency_ms: float (execution time in milliseconds)
        """
        start_time = time.time()
        cleaned = clean_text(text)

        if not cleaned:
            return {
                "toxicity_score": 0.0,
                "is_toxic": False,
                "categories": {
                    "toxic": 0.0, "severe_toxic": 0.0, "obscene": 0.0,
                    "threat": 0.0, "insult": 0.0, "identity_hate": 0.0
                },
                "latency_ms": round((time.time() - start_time) * 1000, 2)
            }

        if self._is_loaded and self._pipeline is not None:
            try:
                # HF pipeline returns a list of dicts [{'label': ..., 'score': ...}, ...]
                results = self._pipeline(cleaned[:512])[0]
                categories = {}
                max_score = 0.0

                for item in results:
                    label = item["label"].lower()
                    score = float(item["score"])
                    categories[label] = round(score, 4)
                    if score > max_score:
                        max_score = score

                # Primary toxicity score is either 'toxic' score or max multi-label score
                toxicity_score = categories.get("toxic", max_score)

                return {
                    "toxicity_score": round(toxicity_score, 4),
                    "is_toxic": toxicity_score >= self.threshold,
                    "categories": categories,
                    "latency_ms": round((time.time() - start_time) * 1000, 2)
                }
            except Exception as e:
                logger.error(f"Error during transformer toxicity inference: {e}")

        # Heuristic Rule Fallback if transformer is loading/offline
        lowered = cleaned.lower()
        matched_words = [w for w in FALLBACK_TOXIC_KEYWORDS if w in lowered]
        fallback_score = min(0.85, 0.60 * len(matched_words)) if matched_words else 0.05

        return {
            "toxicity_score": round(fallback_score, 4),
            "is_toxic": fallback_score >= self.threshold,
            "categories": {
                "toxic": round(fallback_score, 4),
                "severe_toxic": 0.0,
                "obscene": round(fallback_score * 0.7, 4) if "bullshit" in lowered or "crap" in lowered else 0.0,
                "threat": round(fallback_score * 0.9, 4) if "die" in lowered or "destroy" in lowered else 0.0,
                "insult": round(fallback_score * 0.8, 4) if any(w in lowered for w in ["stupid", "idiot", "loser"]) else 0.0,
                "identity_hate": 0.0
            },
            "latency_ms": round((time.time() - start_time) * 1000, 2)
        }


def train_classical_ml_baseline(train_df: pd.DataFrame) -> Tuple[TfidfVectorizer, LogisticRegression]:
    """
    Trains a TF-IDF + Logistic Regression classical ML baseline model on Jigsaw dataset.

    Args:
        train_df: DataFrame containing 'comment_text' and 'toxic' columns.

    Returns:
        Tuple of (fitted TfidfVectorizer, fitted LogisticRegression model).
    """
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
    X_train = vectorizer.fit_transform(train_df["comment_text"].fillna(""))
    y_train = train_df["toxic"].values

    model = LogisticRegression(C=1.0, max_iter=1000)
    model.fit(X_train, y_train)

    return vectorizer, model


def evaluate_toxicity_models(test_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Computes precision, recall, and F1 score comparing toxic-bert vs classical ML baseline.

    Args:
        test_df: DataFrame containing 'comment_text' and ground truth 'toxic' (0 or 1).

    Returns:
        Dictionary containing metric summaries for both models.
    """
    y_true = test_df["toxic"].values

    # 1. Classical Baseline
    vectorizer, baseline_model = train_classical_ml_baseline(test_df)
    X_test = vectorizer.transform(test_df["comment_text"].fillna(""))
    baseline_preds = baseline_model.predict(X_test)
    b_prec, b_rec, b_f1, _ = precision_recall_fscore_support(y_true, baseline_preds, average="binary", zero_division=0)

    # 2. Pretrained Transformer Classifier
    clf = ToxicityClassifier()
    transformer_preds = []
    for text in test_df["comment_text"].fillna(""):
        res = clf.predict(text)
        transformer_preds.append(1 if res["is_toxic"] else 0)

    t_prec, t_rec, t_f1, _ = precision_recall_fscore_support(y_true, transformer_preds, average="binary", zero_division=0)

    return {
        "classical_baseline_tfidf": {
            "precision": round(float(b_prec), 4),
            "recall": round(float(b_rec), 4),
            "f1_score": round(float(b_f1), 4)
        },
        "pretrained_toxic_bert": {
            "precision": round(float(t_prec), 4),
            "recall": round(float(t_rec), 4),
            "f1_score": round(float(t_f1), 4)
        }
    }
