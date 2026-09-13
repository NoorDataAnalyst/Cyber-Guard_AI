"""
Unit tests for src/policy.py module.
"""

import pytest
from src.policy import map_severity_to_action, apply_admin_override


def test_map_severity_to_action():
    assert map_severity_to_action("none") == ("no action", "none")
    assert map_severity_to_action("mild") == ("soft warning", "logged only")
    assert map_severity_to_action("moderate") == ("mute sender", "admin notified")
    assert map_severity_to_action("severe") == ("block message", "admin notified with full report")


def test_apply_admin_override():
    record = {
        "id": 1,
        "message_text": "Test message",
        "severity": "mild",
        "action_taken": "soft warning",
        "admin_status": "pending"
    }

    updated = apply_admin_override(record, "block_message", admin_note="Manual block enforced")
    assert updated["action_taken"] == "block message (admin forced)"
    assert updated["admin_status"] == "manually_blocked"
    assert updated["admin_note"] == "Manual block enforced"

    unblocked = apply_admin_override(record, "unblock_message", admin_note="False alarm")
    assert unblocked["action_taken"] == "unblocked (admin override)"
    assert unblocked["admin_status"] == "manually_unblocked"


def test_enforce_user_policy_action_auto_creates_appeal():
    from src.db import get_or_create_user, get_pending_appeals
    from src.policy import enforce_user_policy_action

    user = get_or_create_user("restricted_user_test")
    user_id = user["user_id"]

    # Enforce severe restriction
    enforce_user_policy_action(user_id=user_id, message_id=100, severity="severe", reason="Severe cyberbullying detected")

    pending = get_pending_appeals()
    user_appeals = [a for a in pending if a["user_id"] == user_id]

    assert len(user_appeals) >= 1
    assert "[System Auto-Notification]" in user_appeals[0]["appeal_text"]
    assert "SEVERE" in user_appeals[0]["appeal_text"]

