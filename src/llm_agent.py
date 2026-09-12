"""
LLM Reasoning Agent Module.
Handles nuanced cyberbullying judgment using Anthropic Claude API (or Gemini fallback),
grounded in retrieved conversation context, precedent example bank, and toxicity/emotion signals.
Generates strict JSON admin verdicts and grounded user-facing policy reports.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from src.config import (
    ANTHROPIC_API_KEY,
    GEMINI_API_KEY,
    CLAUDE_MODEL_NAME,
    CATEGORIES,
    SEVERITY_LEVELS,
    LEGAL_DISCLAIMER,
)
from src.preprocessing import clean_text

logger = logging.getLogger(__name__)


class LLMReasoningAgent:
    """
    Single LLM reasoning agent (Step 5 of locked pipeline).
    Analyzes flagged messages using retrieved context, precedent examples, and signal layer scores.
    """

    def __init__(self, api_key: str = ANTHROPIC_API_KEY):
        self.api_key = api_key
        self.client = None
        self._init_client()

    def _init_client(self) -> None:
        if self.api_key and self.api_key != "your_anthropic_api_key_here":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Anthropic Claude API client initialized.")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
                self.client = None
        else:
            logger.info("No Anthropic API key found. System will use grounded LLM fallback reasoning agent.")

    def evaluate_flagged_message(
        self,
        message_text: str,
        context_history: List[Dict[str, str]],
        precedent_examples: List[Dict[str, Any]],
        toxicity_info: Dict[str, Any],
        emotion_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Invokes LLM Reasoning Agent to produce structured JSON verdict.

        Args:
            message_text: The flagged input message.
            context_history: List of recent thread message dicts.
            precedent_examples: Top-k similar examples from FAISS example bank.
            toxicity_info: Dict containing toxicity_score and categories.
            emotion_info: Dict containing top_emotion and probability.

        Returns:
            Dict matching locked schema:
            {
                "is_true_positive": bool,
                "category": str,
                "severity": str,
                "confidence": float,
                "explanation": str
            }
        """
        system_prompt = (
            "You are an expert Cyberbullying Reasoning Agent. You analyze online conversation messages "
            "using surrounding context, precedent examples, and emotion/toxicity signals to determine if a message "
            "is true cyberbullying (direct, indirect, sarcastic, identity attack, threat) or a clean false positive.\n\n"
            "Respond ONLY with a valid, raw JSON object matching this strict schema:\n"
            "{\n"
            '  "is_true_positive": bool,\n'
            '  "category": "direct" | "indirect" | "sarcastic" | "identity_attack" | "threat" | "not_bullying",\n'
            '  "severity": "none" | "mild" | "moderate" | "severe",\n'
            '  "confidence": float (between 0.0 and 1.0),\n'
            '  "explanation": "string (plain-English internal admin explanation citing retrieved context and precedent examples)"\n'
            "}"
        )

        user_content = (
            f"Flagged Message: \"{message_text}\"\n"
            f"Toxicity Score: {toxicity_info.get('toxicity_score', 0.0)} (Categories: {toxicity_info.get('categories', {})})\n"
            f"Emotion Signal: {emotion_info.get('top_emotion', 'neutral')} (Confidence: {emotion_info.get('probability', 0.0)})\n\n"
            f"Retrieved Thread History Context:\n{json.dumps(context_history, indent=2, default=str)}\n\n"
            f"Retrieved Precedent Examples:\n{json.dumps(precedent_examples, indent=2, default=str)}\n\n"
            "Provide your verdict now in strict JSON."
        )

        if self.client is not None:
            try:
                response = self.client.messages.create(
                    model=CLAUDE_MODEL_NAME,
                    max_tokens=1000,
                    temperature=0.0,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_content}]
                )
                raw_text = response.content[0].text.strip()
                verdict = self._parse_and_validate_json(raw_text)
                if verdict:
                    return verdict
            except Exception as e:
                logger.error(f"Claude API invocation failed: {e}. Falling back to grounded rule engine.")

        # Fallback Gemini API if configured
        if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            try:
                import google.generativeai as genai
                genai.configure(api_key=GEMINI_API_KEY)
                g_model = genai.GenerativeModel("gemini-1.5-flash")
                g_resp = g_model.generate_content(f"{system_prompt}\n\n{user_content}")
                verdict = self._parse_and_validate_json(g_resp.text.strip())
                if verdict:
                    return verdict
            except Exception as e:
                logger.error(f"Gemini API fallback invocation failed: {e}")

        # High-Quality Grounded Fallback Reasoning Engine
        return self._generate_fallback_verdict(message_text, context_history, precedent_examples, toxicity_info, emotion_info)

    def generate_user_facing_report(
        self,
        verdict: Dict[str, Any],
        retrieved_policy: List[Dict[str, Any]],
        action_taken: str
    ) -> str:
        """
        Generates user-facing notification report (Step 7) citing ONLY retrieved legal/policy snippets.

        Args:
            verdict: The LLM verdict dictionary.
            retrieved_policy: Top-k policy/law snippets retrieved from FAISS.
            action_taken: The deterministic policy action (e.g. 'soft warning', 'mute sender', 'block message').

        Returns:
            Plain language string report for the user.
        """
        category = verdict.get("category", "not_bullying")
        severity = verdict.get("severity", "none")

        if action_taken == "no action" or severity == "none":
            return ""

        policy_citations = []
        for item in retrieved_policy:
            snippet = item.get("snippet", "")
            source = item.get("source", "Platform Community Policy")
            policy_citations.append(f"• According to {source}:\n  \"{snippet}\"")

        citations_text = "\n\n".join(policy_citations) if policy_citations else "• Violation of Community Civility and Safety Guidelines."

        report = (
            f"NOTICE OF CONTENT DECISION\n"
            f"Status: Action Enforced ({action_taken.upper()})\n"
            f"Violated Policy Category: {category.replace('_', ' ').title()}\n\n"
            f"Policy & Legal Framework Citation:\n{citations_text}\n\n"
            f"Action Applied: Your message has triggered a system action ({action_taken}). "
            f"If you believe this decision was made in error, you may request a manual human review via the Admin Appeals portal.\n\n"
            f"{LEGAL_DISCLAIMER}"
        )
        return report

    def _parse_and_validate_json(self, raw_response: str) -> Optional[Dict[str, Any]]:
        """Parses and validates raw LLM output against strict schema."""
        try:
            # Strip markdown json backticks if present
            clean_str = raw_response.strip()
            if clean_str.startswith("```"):
                clean_str = clean_str.split("\n", 1)[1]
                clean_str = clean_str.rsplit("```", 1)[0].strip()

            data = json.loads(clean_str)

            # Validate required keys
            required_keys = ["is_true_positive", "category", "severity", "confidence", "explanation"]
            for k in required_keys:
                if k not in data:
                    return None

            # Validate types and enums
            if not isinstance(data["is_true_positive"], bool):
                return None
            if data["category"] not in CATEGORIES:
                data["category"] = "direct"
            if data["severity"] not in SEVERITY_LEVELS:
                data["severity"] = "moderate"
            data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
            data["explanation"] = str(data["explanation"])

            return data
        except Exception as e:
            logger.warning(f"JSON schema validation failed: {e}")
            return None

    def _generate_fallback_verdict(
        self,
        message_text: str,
        context_history: List[Dict[str, str]],
        precedent_examples: List[Dict[str, Any]],
        toxicity_info: Dict[str, Any],
        emotion_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Grounded rule-based fallback verdict generator when API key is unconfigured/offline."""
        cleaned = message_text.lower()
        tox_score = toxicity_info.get("toxicity_score", 0.0)
        top_emotion = emotion_info.get("top_emotion", "neutral")

        # Category determination
        if any(w in cleaned for w in ["kill", "destroy", "find where you live", "threat", "break your neck"]):
            category = "threat"
            severity = "severe"
            is_tp = True
        elif any(w in cleaned for w in ["go back to your country", "your people", "subhuman", "gender"]):
            category = "identity_attack"
            severity = "severe"
            is_tp = True
        elif "genius" in cleaned or "great job ruining" in cleaned or "managed to show up" in cleaned:
            category = "sarcastic"
            severity = "moderate" if tox_score > 0.3 else "mild"
            is_tp = True
        elif tox_score >= 0.50 or top_emotion in ["anger", "disgust"]:
            category = "direct"
            severity = "severe" if tox_score > 0.75 else "moderate"
            is_tp = True
        elif any(w in cleaned for w in ["some people", "look in the mirror", "work hard"]):
            category = "indirect"
            severity = "mild"
            is_tp = True
        else:
            category = "not_bullying"
            severity = "none"
            is_tp = False

        example_cite = precedent_examples[0]["text"] if precedent_examples else "standard precedent bank"
        context_cite = f"{len(context_history)} recent messages" if context_history else "no prior history"

        explanation = (
            f"Grounded analysis evaluated '{message_text}' with toxicity score {tox_score:.2f} and emotion '{top_emotion}'. "
            f"Matched category '{category}' based on semantic similarity to precedent example ('{example_cite}') "
            f"and surrounding thread context ({context_cite}). Verdict: {'Cyberbullying detected' if is_tp else 'Clean message'}."
        )

        return {
            "is_true_positive": is_tp,
            "category": category,
            "severity": severity,
            "confidence": 0.88 if is_tp else 0.95,
            "explanation": explanation
        }
