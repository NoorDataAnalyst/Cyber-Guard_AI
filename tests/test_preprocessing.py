"""
Unit tests for src/preprocessing.py module.
"""

import pytest
from src.preprocessing import clean_text, truncate_text, extract_metadata_features


def test_clean_text_normal():
    raw = "  Hello   world!  This is a   test message.  "
    expected = "Hello world! This is a test message."
    assert clean_text(raw) == expected


def test_clean_text_html_and_control_chars():
    raw = "<b>Warning:</b> Stop it right now!<script>alert(1)</script>\u200b"
    cleaned = clean_text(raw)
    assert "<script>" not in cleaned
    assert "<b>" not in cleaned
    assert "Stop it right now!" in cleaned


def test_clean_text_empty_and_non_string():
    assert clean_text("") == ""
    assert clean_text(None) == ""
    assert clean_text(12345) == ""


def test_truncate_text():
    text = "This is a long sentence meant for testing text truncation functionality."
    truncated = truncate_text(text, max_length=25)
    assert len(truncated) <= 25
    assert truncated.endswith("...")


def test_extract_metadata_features():
    text = "HEY @user YOU ARE AN IDIOT! Check http://example.com"
    meta = extract_metadata_features(text)
    assert meta["has_all_caps_word"] is True
    assert meta["mention_count"] == 1
    assert meta["url_count"] == 1
    assert meta["exclamation_count"] == 1
