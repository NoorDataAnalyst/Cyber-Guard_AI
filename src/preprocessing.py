"""
Text preprocessing and cleaning utilities for Cyberbullying Detection System.
Handles text normalization, whitespace cleanup, HTML stripping, and text truncation
while preserving punctuation, casing, and semantic structure needed for sarcasm/emotion analysis.
"""

import re
import unicodedata
from typing import Dict, List


def clean_text(text: str) -> str:
    """
    Cleans raw text for signal models and retrieval indexing.
    - Normalizes Unicode characters.
    - Strips raw HTML tags.
    - Replaces zero-width and invisible control characters.
    - Collapses consecutive whitespace into a single space.
    - Preserves punctuation and capitalization essential for emotion and sarcasm detection.

    Args:
        text: Raw input text string.

    Returns:
        Cleaned and normalized text string.
    """
    if not isinstance(text, str):
        return ""

    # Normalize Unicode characters (NFC form)
    text = unicodedata.normalize("NFC", text)

    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Replace zero-width spaces and control characters (except standard newline/tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b-\u200d\ufeff]", "", text)

    # Collapse multiple spaces and newlines into single spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncates a string to max_length characters without breaking mid-word if possible.

    Args:
        text: Input text string.
        max_length: Maximum target length including suffix.
        suffix: Suffix to append if truncated.

    Returns:
        Truncated text string.
    """
    if not text or len(text) <= max_length:
        return text

    target_len = max_length - len(suffix)
    if target_len <= 0:
        return text[:max_length]

    # Truncate at nearest word boundary
    truncated = text[:target_len]
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]

    return truncated + suffix


def extract_metadata_features(text: str) -> Dict[str, object]:
    """
    Extracts metadata features such as URL count, mention count, and ALL CAPS ratio
    which may serve as signals for aggressive tone.

    Args:
        text: Input text string.

    Returns:
        Dictionary containing extracted metadata features.
    """
    if not text:
        return {
            "all_caps_ratio": 0.0,
            "has_all_caps_word": False,
            "mention_count": 0,
            "url_count": 0,
            "exclamation_count": text.count("!") if text else 0,
        }

    words = text.split()
    caps_words = [w for w in words if len(w) > 2 and w.isupper() and w.isalpha()]
    all_caps_ratio = len(caps_words) / max(len(words), 1)

    urls = re.findall(r"https?://\S+|www\.\S+", text)
    mentions = re.findall(r"@\w+", text)

    return {
        "all_caps_ratio": round(all_caps_ratio, 2),
        "has_all_caps_word": len(caps_words) > 0,
        "mention_count": len(mentions),
        "url_count": len(urls),
        "exclamation_count": text.count("!"),
    }
