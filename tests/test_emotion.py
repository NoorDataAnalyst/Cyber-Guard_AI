"""
Unit tests for src/emotion_classifier.py module.
"""

import pytest
from src.emotion_classifier import EmotionClassifier


def test_emotion_classifier_anger():
    clf = EmotionClassifier()
    res = clf.predict("I hate you so much, stop annoying me right now!")
    assert "top_emotion" in res
    assert "probability" in res
    assert res["top_emotion"] in ["anger", "annoyance", "disapproval"]


def test_emotion_classifier_neutral():
    clf = EmotionClassifier()
    res = clf.predict("What time is the meeting scheduled for tomorrow?")
    assert "top_emotion" in res
    assert res["top_emotion"] in ["neutral", "curiosity", "realization"]


def test_emotion_classifier_empty():
    clf = EmotionClassifier()
    res = clf.predict("")
    assert res["top_emotion"] == "neutral"
    assert res["probability"] == 1.0
