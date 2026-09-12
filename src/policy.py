"""
Policy Engine Module.
Provides deterministic, explicit rule-based severity-to-action mapping per Section 6,
and handles Admin manual override authorities (Block, Unblock, Dismiss, Override Verdict).
"""

from typing import Dict, Any, Tuple
from src.config import SEVERITY_ACTION_MAP, SEVERITY_LEVELS


def map_severity_to_action(severity: str) -> Tuple[str, str]:
    """
    Maps LLM verdict severity to deterministic system action and notification target.

    Args:
        severity: "none" | "mild" | "moderate" | "severe"

    Returns:
        Tuple of (action_string, notification_target_string)
    """
    sev_clean = str(severity).strip().lower()

    if sev_clean == "none":
        return ("no action", "none")
    elif sev_clean == "mild":
        return ("soft warning", "logged only")
    elif sev_clean == "moderate":
        return ("mute sender", "admin notified")
    elif sev_clean == "severe":
        return ("block message", "admin notified with full report")
    else:
        # Default fallback for unknown severity
        return ("no action", "none")


def apply_admin_override(
    current_record: Dict[str, Any],
    override_action: str,
    admin_note: str = ""
) -> Dict[str, Any]:
    """
    Applies Admin manual authority override to a flagged message record.

    Supported override_action choices:
    - "block_message": Forces immediate message block and sender restriction.
    - "unblock_message": Restores message and removes sender mute/block.
    - "dismiss_flag": Marks message as false positive clean.
    - "override_severity_mild" / "override_severity_moderate" / "override_severity_severe"

    Args:
        current_record: The database record dict for the flagged message.
        override_action: The admin action command string.
        admin_note: Optional explanation note from admin.

    Returns:
        Updated record dict with new action, admin status, and timestamp.
    """
    record = dict(current_record)

    if override_action == "block_message":
        record["action_taken"] = "block message (admin forced)"
        record["severity"] = "severe"
        record["admin_status"] = "manually_blocked"
    elif override_action == "unblock_message":
        record["action_taken"] = "unblocked (admin override)"
        record["admin_status"] = "manually_unblocked"
    elif override_action == "dismiss_flag":
        record["action_taken"] = "dismissed (false positive)"
        record["severity"] = "none"
        record["is_true_positive"] = False
        record["admin_status"] = "dismissed"
    elif override_action.startswith("override_severity_"):
        new_sev = override_action.replace("override_severity_", "")
        if new_sev in SEVERITY_LEVELS:
            record["severity"] = new_sev
            action, _ = map_severity_to_action(new_sev)
            record["action_taken"] = f"{action} (admin severity override)"
            record["admin_status"] = f"severity_overridden_{new_sev}"

    record["admin_note"] = admin_note
    return record
