"""
Pipeline Orchestration Module.
Executes locked sequential architecture (Steps 2–8) end-to-end for every incoming chat message
or manual user report, with pipeline-level user restriction enforcement.
"""

import logging
from typing import Dict, Any, List, Optional

from src.config import TOXICITY_THRESHOLD, CONTEXT_HISTORY_N
from src.preprocessing import clean_text
from src.toxicity_classifier import ToxicityClassifier
from src.emotion_classifier import EmotionClassifier
from src.retrieval import RAGRetrievalManager
from src.llm_agent import LLMReasoningAgent
from src.policy import map_severity_to_action, enforce_user_policy_action
from src.db import save_message, save_verdict, get_conversation_thread, get_or_create_user, get_user_status

logger = logging.getLogger(__name__)


class CyberbullyingPipeline:
    """
    Monolithic end-to-end pipeline manager orchestrating Signal Layer, FAISS RAG,
    LLM Reasoning Agent, Policy Engine, DB Persistence, and User Restrictions.
    """

    def __init__(self):
        logger.info("Initializing Cyberbullying Pipeline components...")
        self.toxicity_classifier = ToxicityClassifier()
        self.emotion_classifier = EmotionClassifier()
        self.rag_manager = RAGRetrievalManager()
        self.llm_agent = LLMReasoningAgent()
        logger.info("Pipeline initialization complete.")

    def process_message(
        self,
        sender: str,
        text: str,
        report_type: str = "automatic",
        force_flag: bool = False
    ) -> Dict[str, Any]:
        """
        Executes end-to-end processing pipeline for a single message.
        Enforces user restrictions (blocked/muted) BEFORE message processing.

        Args:
            sender: Username of message author.
            text: Raw message text string.
            report_type: 'automatic' (signal layer check) or 'manual_user_report' (user clicked report).
            force_flag: If True, overrides signal gate and forces full RAG + LLM analysis.

        Returns:
            Dict containing full analysis output, verdict, action, and user report.
        """
        cleaned_msg = clean_text(text)
        if not cleaned_msg:
            return {"status": "empty", "is_flagged": False, "action_taken": "no action"}

        # Resolve or create user identity
        user_info = get_or_create_user(sender)
        user_id = user_info["user_id"]

        # Pipeline-Level Restriction Check (Correction #2)
        status_info = get_user_status(user_id)
        if status_info["status"] in ["blocked", "muted"]:
            logger.warning(f"Message rejected: user '{sender}' (id={user_id}) is currently {status_info['status']}.")
            return {
                "status": "restricted",
                "user_id": user_id,
                "username": user_info["username"],
                "user_status": status_info["status"],
                "reason": status_info["reason"],
                "mute_expires_at": status_info.get("mute_expires_at"),
                "is_flagged": True,
                "action_taken": f"rejected (user is {status_info['status']})",
                "explanation": f"Message processing rejected because user account is currently {status_info['status']}."
            }

        # Step 2: SIGNAL LAYER (Fast, pretrained inference, < 1 sec)
        toxicity_info = self.toxicity_classifier.predict(cleaned_msg)
        emotion_info = self.emotion_classifier.predict(cleaned_msg)

        tox_score = toxicity_info.get("toxicity_score", 0.0)
        top_emotion = emotion_info.get("top_emotion", "neutral")

        # Step 3: FLAG DECISION GATE
        is_signal_flagged = (
            tox_score >= TOXICITY_THRESHOLD or
            (top_emotion in ["anger", "disgust", "fear"] and emotion_info.get("probability", 0.0) >= 0.75)
        )
        is_flagged = is_signal_flagged or force_flag or (report_type == "manual_user_report")

        # Save base message to DB
        msg_id = save_message(sender=user_info["username"], text=cleaned_msg, is_flagged=is_flagged, report_type=report_type, user_id=user_id)

        if not is_flagged:
            # Clean message: log as clean and stop here
            save_verdict(
                message_id=msg_id,
                verdict={
                    "is_true_positive": False,
                    "category": "not_bullying",
                    "severity": "none",
                    "confidence": 1.0,
                    "explanation": f"Signal layer cleared message (Toxicity: {tox_score:.2f}, Emotion: {top_emotion})."
                },
                toxicity_score=tox_score,
                top_emotion=top_emotion,
                action_taken="no action",
                user_report=""
            )
            return {
                "message_id": msg_id,
                "user_id": user_id,
                "text": cleaned_msg,
                "is_flagged": False,
                "toxicity_score": tox_score,
                "top_emotion": top_emotion,
                "category": "not_bullying",
                "severity": "none",
                "action_taken": "no action",
                "user_report": "",
                "explanation": "Signal layer cleared message."
            }

        # Step 4: RETRIEVAL LAYER (FAISS - context history & precedent examples)
        recent_thread = get_conversation_thread(limit=CONTEXT_HISTORY_N + 1)
        context_history = [m for m in recent_thread if m.get("id") != msg_id]
        retrieved_context = self.rag_manager.retrieve_context(context_history, n_recent=CONTEXT_HISTORY_N)
        retrieved_examples = self.rag_manager.retrieve_similar_examples(cleaned_msg)

        # Step 5: LLM REASONING AGENT
        verdict = self.llm_agent.evaluate_flagged_message(
            message_text=cleaned_msg,
            context_history=retrieved_context,
            precedent_examples=retrieved_examples,
            toxicity_info=toxicity_info,
            emotion_info=emotion_info
        )

        # Step 6: POLICY ENGINE (Deterministic severity -> action mapping)
        severity = verdict.get("severity", "none")
        action_taken, notification_target = map_severity_to_action(severity)

        # Apply user account restrictions if moderate or severe
        if severity in ["moderate", "severe"]:
            enforce_user_policy_action(
                user_id=user_id,
                message_id=msg_id,
                severity=severity,
                reason=verdict.get("explanation", "Violation of community standards"),
                taken_by="system"
            )

        # Step 7: USER-FACING REPORT GENERATION (grounded in policy corpus)
        retrieved_policy = []
        user_report = ""
        category = verdict.get("category", "not_bullying")

        if action_taken != "no action" and severity != "none":
            retrieved_policy = self.rag_manager.retrieve_policy_snippets(category)
            user_report = self.llm_agent.generate_user_facing_report(verdict, retrieved_policy, action_taken)

        # Step 8: LOGGING & PERSISTENCE
        verdict_id = save_verdict(
            message_id=msg_id,
            verdict=verdict,
            toxicity_score=tox_score,
            top_emotion=top_emotion,
            action_taken=action_taken,
            user_report=user_report,
            context_retrieved=retrieved_context,
            examples_retrieved=retrieved_examples,
            policy_retrieved=retrieved_policy
        )

        return {
            "message_id": msg_id,
            "verdict_id": verdict_id,
            "user_id": user_id,
            "text": cleaned_msg,
            "is_flagged": True,
            "report_type": report_type,
            "toxicity_score": tox_score,
            "top_emotion": top_emotion,
            "is_true_positive": verdict.get("is_true_positive", True),
            "category": category,
            "severity": severity,
            "confidence": verdict.get("confidence", 0.90),
            "action_taken": action_taken,
            "notification_target": notification_target,
            "explanation": verdict.get("explanation", ""),
            "user_report": user_report,
            "retrieved_context": retrieved_context,
            "retrieved_examples": retrieved_examples,
            "retrieved_policy": retrieved_policy
        }
