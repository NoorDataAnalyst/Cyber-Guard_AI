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
