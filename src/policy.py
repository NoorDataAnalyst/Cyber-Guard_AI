"""
Policy Engine Module.
Provides deterministic, explicit rule-based severity-to-action mapping per Section 6,
and handles Admin manual override authorities (Block, Unblock, Dismiss, Override Verdict).
"""

from typing import Dict, Any, Tuple, Optional
from src.config import SEVERITY_ACTION_MAP, SEVERITY_LEVELS
from src.db import set_restriction, log_action


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


def enforce_user_policy_action(
    user_id: Optional[int],
    message_id: Optional[int],
    severity: str,
    reason: str,
    taken_by: str = "system"
) -> Optional[Dict[str, Any]]:
    """
    Applies user-level restrictions (30-minute mute for moderate, severe block for severe)
    and automatically dispatches an admin review request to the Admin Queue.
    """
    if not user_id:
        return None

    sev_clean = str(severity).strip().lower()

    res = None
    if sev_clean == "moderate":
        # Mute user for 30 minutes
        res = set_restriction(user_id, status="muted", reason=reason, severity="moderate", blocked_by=taken_by, mute_minutes=30)
        log_action(message_id=message_id, user_id=user_id, action_type="mute", taken_by=taken_by, admin_note=reason)
    elif sev_clean == "severe":
        # Full account block (requires appeal)
        res = set_restriction(user_id, status="blocked", reason=reason, severity="severe", blocked_by=taken_by)
        log_action(message_id=message_id, user_id=user_id, action_type="block", taken_by=taken_by, admin_note=reason)

    if res and sev_clean in ["moderate", "severe"]:
        try:
            from src.db import get_pending_appeals, create_appeal
            pending = get_pending_appeals()
            user_pending = [a for a in pending if a["user_id"] == user_id]
            if not user_pending:
                create_appeal(
                    user_id=user_id,
                    appeal_text=f"[System Auto-Notification] Account restricted ({sev_clean.upper()}). Reason: {reason}"
                )
        except Exception as err:
            import logging
            logging.getLogger(__name__).warning(f"Could not auto-create admin appeal request: {err}")

    return res


def apply_admin_override(
    current_record: Dict[str, Any],
    override_action: str,
    admin_note: str = ""
) -> Dict[str, Any]:
    """
    Applies Admin manual authority override to a flagged message record.
    """
    record = dict(current_record)
    user_id = record.get("user_id")

    if override_action == "block_message":
        record["action_taken"] = "block message (admin forced)"
        record["severity"] = "severe"
        record["admin_status"] = "manually_blocked"
        if user_id:
            set_restriction(user_id, status="blocked", reason=admin_note or "Admin forced block", severity="severe", blocked_by="admin")

    elif override_action == "unblock_message":
        record["action_taken"] = "unblocked (admin override)"
        record["admin_status"] = "manually_unblocked"
        if user_id:
            set_restriction(user_id, status="unblocked", reason=admin_note or "Admin unblocked", severity="none", blocked_by="admin")

    elif override_action == "dismiss_flag":
        record["action_taken"] = "dismissed (false positive)"
        record["severity"] = "none"
        record["is_true_positive"] = False
        record["admin_status"] = "dismissed"
        if user_id:
            set_restriction(user_id, status="unblocked", reason=admin_note or "Flag dismissed", severity="none", blocked_by="admin")

    elif override_action.startswith("override_severity_"):
        new_sev = override_action.replace("override_severity_", "")
        if new_sev in SEVERITY_LEVELS:
            record["severity"] = new_sev
            action, _ = map_severity_to_action(new_sev)
            record["action_taken"] = f"{action} (admin severity override)"
            record["admin_status"] = f"severity_overridden_{new_sev}"
            if user_id and new_sev in ["moderate", "severe"]:
                enforce_user_policy_action(user_id, record.get("message_id"), new_sev, admin_note or f"Admin set severity to {new_sev}", taken_by="admin")

    record["admin_note"] = admin_note
    return record
