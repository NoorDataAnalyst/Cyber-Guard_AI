"""
Emotion Classifier Module.
Provides inference wrapper for pretrained HuggingFace 'SamLowe/roberta-base-go_emotions' model,
predicting emotion signals across 28 GoEmotions fine-grained categories.
"""

import time
import logging
from typing import Dict, Any
from src.config import EMOTION_MODEL_NAME
from src.preprocessing import clean_text

logger = logging.getLogger(__name__)

# Heuristic emotion keyword lookup for fallback mode when HuggingFace model is offline/loading
EMOTION_KEYWORDS = {
    "anger": ["hate", "angry", "furious", "idiot", "destroy", "annoying", "shut up", "mad"],
    "disgust": ["gross", "disgusting", "revolting", "scum", "trash", "nasty"],
    "fear": ["scared", "terrified", "afraid", "threat", "watch your back", "fear"],
    "sadness": ["depressed", "sad", "unhappy", "cry", "lonely", "miserable"],
    "joy": ["happy", "great", "love", "wonderful", "awesome", "good", "thanks"],
    "surprise": ["wow", "shocked", "surprised", "unbelievable", "really"],
}


class EmotionClassifier:
    """
    Inference wrapper around pretrained HuggingFace emotion model (roberta-base-go_emotions).
    """

    def __init__(self, model_name: str = EMOTION_MODEL_NAME):
        self.model_name = model_name
        self._pipeline = None
        self._is_loaded = False
        self._init_model()

    def _init_model(self) -> None:
        """Attempts to load pretrained HuggingFace emotion pipeline lazily."""
        try:
            from transformers import pipeline
            logger.info(f"Loading pretrained emotion model '{self.model_name}'...")
            self._pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                top_k=None,  # Return all 28 emotion scores
                tokenizer=self.model_name,
                device=-1    # CPU inference
            )
            self._is_loaded = True
            logger.info("Emotion model loaded successfully.")
        except Exception as e:
            logger.warning(f"Unable to load HuggingFace emotion model '{self.model_name}': {e}. Using deterministic heuristic fallback.")
            self._is_loaded = False

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Runs emotion classification on input text.

        Args:
            text: Input text string.

        Returns:
            Dict containing:
            - top_emotion: str (e.g. 'anger', 'disgust', 'neutral', 'joy')
            - probability: float (0.0 to 1.0)
            - all_emotions: Dict[str, float] top 5 emotion probabilities
            - latency_ms: float
        """
        start_time = time.time()
        cleaned = clean_text(text)

        if not cleaned:
            return {
                "top_emotion": "neutral",
                "probability": 1.0,
                "all_emotions": {"neutral": 1.0},
                "latency_ms": round((time.time() - start_time) * 1000, 2)
            }

        if self._is_loaded and self._pipeline is not None:
            try:
                results = self._pipeline(cleaned[:512])[0]
                all_emotions = {item["label"].lower(): float(item["score"]) for item in results}
                
                # Sort emotions by score descending
                sorted_emotions = sorted(all_emotions.items(), key=lambda x: x[1], reverse=True)
                top_label, top_score = sorted_emotions[0]
                top_5_dict = {k: round(v, 4) for k, v in sorted_emotions[:5]}

                return {
                    "top_emotion": top_label,
                    "probability": round(top_score, 4),
                    "all_emotions": top_5_dict,
                    "latency_ms": round((time.time() - start_time) * 1000, 2)
                }
            except Exception as e:
                logger.error(f"Error during transformer emotion inference: {e}")

        # Fallback keyword-based emotion classifier
        lowered = cleaned.lower()
        detected_emotion = "neutral"
        max_prob = 0.50

        for emotion, keywords in EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in lowered:
                    detected_emotion = emotion
                    max_prob = 0.85
                    break
            if detected_emotion != "neutral":
                break

        return {
            "top_emotion": detected_emotion,
            "probability": round(max_prob, 4),
            "all_emotions": {detected_emotion: round(max_prob, 4), "neutral": round(1.0 - max_prob, 4)},
            "latency_ms": round((time.time() - start_time) * 1000, 2)
        }
