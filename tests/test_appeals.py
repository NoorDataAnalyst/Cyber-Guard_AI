"""
test_appeals.py — Unit tests for the full appeal workflow.

Covers: create → get_pending → resolve (approve/reject) → restriction cleared.
All tests use in-memory SQLite only — no Supabase connection required.
"""

import pytest
from unittest.mock import patch
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.db as db_module
from src.db import (
    Base,
    RestrictedUserModel,
    get_or_create_user,
    get_user_status,
    set_restriction,
    create_appeal,
    get_pending_appeals,
    resolve_appeal,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def in_memory_session_factory():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def patch_session(in_memory_session_factory):
    with patch.object(db_module, "SessionLocal", in_memory_session_factory):
        yield


@pytest.fixture
def blocked_user():
    """Creates a user, blocks them, and returns their user dict."""
    u = get_or_create_user("banned_user")
    set_restriction(u["user_id"], "blocked", "Severe cyberbullying violation", "severe", "system")
    return u


# ── Create Appeal ─────────────────────────────────────────────────────────────

class TestCreateAppeal:
    def test_creates_appeal_for_blocked_user(self, blocked_user):
        result = create_appeal(
            user_id=blocked_user["user_id"],
            appeal_text="I did not mean to be rude. Please unblock me."
        )
        assert result["user_id"] == blocked_user["user_id"]
        assert result["status"] == "pending"
        assert "appeal_id" in result
        assert result["appeal_id"] > 0

    def test_appeal_text_is_stored(self, blocked_user):
        appeal_text = "This was a misunderstanding."
        result = create_appeal(blocked_user["user_id"], appeal_text)
        assert result["appeal_text"] == appeal_text

    def test_submitted_at_is_iso_string(self, blocked_user):
        result = create_appeal(blocked_user["user_id"], "My appeal reason.")
        submitted_at = result["submitted_at"]
        # Must be parseable as ISO datetime
        parsed = datetime.fromisoformat(submitted_at)
        assert parsed is not None

    def test_multiple_appeals_have_unique_ids(self, blocked_user):
        a1 = create_appeal(blocked_user["user_id"], "First appeal")
        u2 = get_or_create_user("second_banned_user")
        set_restriction(u2["user_id"], "blocked", "Another violation", "severe", "system")
        a2 = create_appeal(u2["user_id"], "Second appeal")
        assert a1["appeal_id"] != a2["appeal_id"]


# ── Get Pending Appeals ───────────────────────────────────────────────────────

class TestGetPendingAppeals:
    def test_empty_when_no_appeals(self):
        result = get_pending_appeals()
        assert result == []

    def test_returns_pending_appeal(self, blocked_user):
        create_appeal(blocked_user["user_id"], "Please review my case.")
        pending = get_pending_appeals()
        assert len(pending) == 1
        assert pending[0]["user_id"] == blocked_user["user_id"]

    def test_includes_required_fields(self, blocked_user):
        create_appeal(blocked_user["user_id"], "I deserve another chance.")
        pending = get_pending_appeals()
        item = pending[0]
        required_fields = {
            "appeal_id", "user_id", "username", "submitted_at",
            "appeal_text", "status", "blocked_reason", "severity",
        }
        assert required_fields.issubset(set(item.keys()))

    def test_does_not_include_resolved_appeals(self, blocked_user):
        result = create_appeal(blocked_user["user_id"], "I want to appeal.")
        resolve_appeal(result["appeal_id"], decision="approved")
        pending = get_pending_appeals()
        assert all(a["status"] == "pending" for a in pending)

    def test_multiple_users_multiple_appeals(self):
        u1 = get_or_create_user("user_alpha")
        u2 = get_or_create_user("user_beta")
        set_restriction(u1["user_id"], "blocked", "violation 1", "severe", "system")
        set_restriction(u2["user_id"], "blocked", "violation 2", "severe", "system")
        create_appeal(u1["user_id"], "Alpha's appeal")
        create_appeal(u2["user_id"], "Beta's appeal")
        pending = get_pending_appeals()
        assert len(pending) == 2


# ── Resolve Appeal (Approve) ──────────────────────────────────────────────────

class TestResolveAppealApprove:
    def test_approve_marks_appeal_as_approved(self, blocked_user):
        appeal = create_appeal(blocked_user["user_id"], "Please unban me.")
        success = resolve_appeal(appeal["appeal_id"], decision="approved")
        assert success is True
        # Should no longer be in pending
        pending = get_pending_appeals()
        assert not any(a["appeal_id"] == appeal["appeal_id"] for a in pending)

    def test_approve_clears_user_restriction(self, blocked_user):
        appeal = create_appeal(blocked_user["user_id"], "I promise to behave.")
        resolve_appeal(appeal["appeal_id"], decision="approved")
        status = get_user_status(blocked_user["user_id"])
        assert status["status"] == "active"

    def test_approve_with_admin_note(self, blocked_user):
        appeal = create_appeal(blocked_user["user_id"], "My side of the story.")
        success = resolve_appeal(appeal["appeal_id"], decision="approved", admin_note="Reviewed and cleared.")
        assert success is True

    def test_approved_user_can_submit_again_if_reblocked(self, blocked_user):
        appeal = create_appeal(blocked_user["user_id"], "First appeal.")
        resolve_appeal(appeal["appeal_id"], decision="approved")
        # Re-block and re-appeal
        set_restriction(blocked_user["user_id"], "blocked", "New violation", "severe", "admin")
        appeal2 = create_appeal(blocked_user["user_id"], "Second appeal.")
        assert appeal2["status"] == "pending"


# ── Resolve Appeal (Reject) ───────────────────────────────────────────────────

class TestResolveAppealReject:
    def test_reject_marks_appeal_as_rejected(self, blocked_user):
        appeal = create_appeal(blocked_user["user_id"], "Unban me please.")
        success = resolve_appeal(appeal["appeal_id"], decision="rejected")
        assert success is True

    def test_reject_does_not_clear_restriction(self, blocked_user):
        appeal = create_appeal(blocked_user["user_id"], "I want to appeal.")
        resolve_appeal(appeal["appeal_id"], decision="rejected")
        status = get_user_status(blocked_user["user_id"])
        assert status["status"] == "blocked"

    def test_reject_removed_from_pending(self, blocked_user):
        appeal = create_appeal(blocked_user["user_id"], "My appeal statement.")
        resolve_appeal(appeal["appeal_id"], decision="rejected", admin_note="Insufficient grounds.")
        pending = get_pending_appeals()
        assert not any(a["appeal_id"] == appeal["appeal_id"] for a in pending)

    def test_resolve_nonexistent_appeal_returns_false(self):
        result = resolve_appeal(appeal_id=99999, decision="approved")
        assert result is False


# ── Edge Cases ────────────────────────────────────────────────────────────────

class TestAppealEdgeCases:
    def test_active_user_can_still_create_appeal(self):
        """System should not crash if a non-blocked user submits an appeal (DB allows it)."""
        u = get_or_create_user("normal_user")
        result = create_appeal(u["user_id"], "Preemptive appeal.")
        assert result["appeal_id"] > 0

    def test_appeal_username_in_pending_list(self, blocked_user):
        create_appeal(blocked_user["user_id"], "Check my username please.")
        pending = get_pending_appeals()
        assert pending[0]["username"] == blocked_user["username"]
