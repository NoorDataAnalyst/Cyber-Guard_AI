"""
Unit tests for src/llm_agent.py module.
"""

import pytest
from src.llm_agent import LLMReasoningAgent


def test_llm_agent_evaluate_flagged_message():
    agent = LLMReasoningAgent()
    verdict = agent.evaluate_flagged_message(
        message_text="You are completely stupid and nobody likes you.",
        context_history=[],
        precedent_examples=[],
        toxicity_info={"toxicity_score": 0.85, "categories": {"toxic": 0.85}},
        emotion_info={"top_emotion": "anger", "probability": 0.90}
    )
    assert isinstance(verdict, dict)
    assert verdict["is_true_positive"] is True
    assert verdict["category"] in ["direct", "indirect", "sarcastic", "identity_attack", "threat", "not_bullying"]
    assert verdict["severity"] in ["none", "mild", "moderate", "severe"]
    assert "explanation" in verdict


def test_generate_user_facing_report():
    agent = LLMReasoningAgent()
    verdict = {
        "is_true_positive": True,
        "category": "threat",
        "severity": "severe",
        "confidence": 0.95,
        "explanation": "Threat detected."
    }
    policy_snippets = [{
        "snippet": "Threats of violence are prohibited under PECA Section 24.",
        "source": "Pakistan PECA 2016"
    }]
    report = agent.generate_user_facing_report(verdict, policy_snippets, action_taken="block message")
    assert "NOTICE OF CONTENT DECISION" in report
    assert "Threats of violence are prohibited" in report
    assert "DISCLAIMER" in report


def test_claude_failure_fallbacks_to_gemini(monkeypatch):
    """Verifies that when Claude API fails, execution falls back to Gemini API."""
    from unittest.mock import MagicMock
    agent = LLMReasoningAgent()

    # Mock Claude client to throw an Exception
    mock_claude_client = MagicMock()
    mock_claude_client.messages.create.side_effect = Exception("Claude Rate Limit Exceeded")
    agent.client = mock_claude_client

    # Mock Gemini API
    mock_gemini_resp = MagicMock()
    mock_gemini_resp.text = '{"is_true_positive": true, "category": "threat", "severity": "severe", "confidence": 0.99, "explanation": "Gemini threat evaluation"}'

    mock_g_model = MagicMock()
    mock_g_model.generate_content.return_value = mock_gemini_resp

    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_g_model

    import sys
    monkeypatch.setitem(sys.modules, "google.generativeai", mock_genai)
    monkeypatch.setattr("src.llm_agent.get_config_val", lambda key, default="": "test_gemini_key" if key in ["GEMINI_API_KEY", "GOOGLE_API_KEY"] else default)

    verdict = agent.evaluate_flagged_message(
        message_text="I will destroy you",
        context_history=[],
        precedent_examples=[],
        toxicity_info={"toxicity_score": 0.9},
        emotion_info={"top_emotion": "anger"}
    )

    assert verdict["is_true_positive"] is True
    assert verdict["category"] == "threat"
    assert verdict["explanation"] == "Gemini threat evaluation"


def test_both_apis_failure_fallbacks_to_rule_engine(monkeypatch):
    """Verifies that when both Claude and Gemini fail, grounded rule engine fallback is used."""
    from unittest.mock import MagicMock
    agent = LLMReasoningAgent()

    # Mock Claude failure
    mock_claude_client = MagicMock()
    mock_claude_client.messages.create.side_effect = Exception("Claude Auth Error")
    agent.client = mock_claude_client

    # Mock Gemini failure
    mock_genai = MagicMock()
    mock_genai.configure.side_effect = Exception("Gemini Network Timeout")

    import sys
    monkeypatch.setitem(sys.modules, "google.generativeai", mock_genai)
    monkeypatch.setattr("src.llm_agent.get_config_val", lambda key, default="": "test_gemini_key" if key in ["GEMINI_API_KEY", "GOOGLE_API_KEY"] else default)

    verdict = agent.evaluate_flagged_message(
        message_text="You are awful",
        context_history=[],
        precedent_examples=[],
        toxicity_info={"toxicity_score": 0.8},
        emotion_info={"top_emotion": "anger"}
    )

    assert verdict["is_true_positive"] is True
    assert "Grounded analysis" in verdict["explanation"]

