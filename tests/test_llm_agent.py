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
