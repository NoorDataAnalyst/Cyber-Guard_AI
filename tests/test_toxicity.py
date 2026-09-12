"""
Unit tests for src/toxicity_classifier.py module.
"""

import pytest
from src.toxicity_classifier import ToxicityClassifier


def test_toxicity_classifier_clean_text():
    clf = ToxicityClassifier()
    res = clf.predict("Thank you for sharing this informative document.")
    assert "toxicity_score" in res
    assert "is_toxic" in res
    assert res["is_toxic"] is False
    assert res["toxicity_score"] < 0.50


def test_toxicity_classifier_toxic_text():
    clf = ToxicityClassifier()
    res = clf.predict("You are completely stupid and nobody likes you.")
    assert "toxicity_score" in res
    assert res["is_toxic"] is True
    assert res["toxicity_score"] >= 0.50


def test_toxicity_classifier_empty():
    clf = ToxicityClassifier()
    res = clf.predict("")
    assert res["toxicity_score"] == 0.0
    assert res["is_toxic"] is False
