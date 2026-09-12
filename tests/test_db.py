"""
Unit tests for src/db.py module.
"""

import pytest
from src.db import init_db, save_message, save_verdict, get_conversation_thread, get_flagged_verdicts, update_admin_status


def test_db_read_write_flow():
    init_db()
    
    msg_id = save_message(sender="TestUser", text="Test message text for unit testing", is_flagged=True, report_type="manual_user_report")
    assert msg_id > 0

    verdict_id = save_verdict(
        message_id=msg_id,
        verdict={
            "is_true_positive": True,
            "category": "sarcastic",
            "severity": "moderate",
            "confidence": 0.90,
            "explanation": "Test explanation"
        },
        toxicity_score=0.45,
        top_emotion="anger",
        action_taken="mute sender",
        user_report="Test user report"
    )
    assert verdict_id > 0

    thread = get_conversation_thread(limit=10)
    assert len(thread) > 0

    flagged = get_flagged_verdicts()
    assert len(flagged) > 0

    updated = update_admin_status(verdict_id, "manually_blocked", "block message (admin forced)", "Blocked by admin")
    assert updated is True
