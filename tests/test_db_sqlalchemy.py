"""
test_db_sqlalchemy.py — Unit tests for the SQLAlchemy ORM persistence layer.

Uses in-memory SQLite only — no live Supabase connection required.
All tests patch the module-level `SessionLocal` factory in src.db to point
at an isolated in-memory engine so tests are fully self-contained.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.db as db_module
from src.db import (
    Base,
    UserModel,
    MessageModel,
    VerdictModel,
    RestrictedUserModel,
    AppealModel,
    get_or_create_user,
    get_user_status,
    set_restriction,
    log_action,
    create_appeal,
    get_pending_appeals,
    resolve_appeal,
    save_message,
    save_verdict,
    get_conversation_thread,
    get_analytics_data,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def in_memory_session_factory():
    """Creates a fresh in-memory SQLite engine and returns a patched SessionLocal."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestSession


@pytest.fixture(autouse=True)
def patch_session(in_memory_session_factory):
    """Patch the module-level SessionLocal in src.db for every test function."""
    with patch.object(db_module, "SessionLocal", in_memory_session_factory):
        yield


# ── User CRUD ─────────────────────────────────────────────────────────────────

class TestGetOrCreateUser:
    def test_creates_new_user(self):
        result = get_or_create_user("alice")
        assert result["username"] == "alice"
        assert result["status"] == "active"
        assert "user_id" in result

    def test_returns_existing_user(self):
        r1 = get_or_create_user("bob")
        r2 = get_or_create_user("bob")
        assert r1["user_id"] == r2["user_id"]

    def test_blank_username_defaults(self):
        result = get_or_create_user("")
        assert result["username"] == "Anonymous_User"

    def test_strips_whitespace(self):
        result = get_or_create_user("  charlie  ")
        assert result["username"] == "charlie"


class TestGetUserStatus:
    def test_active_user_has_active_status(self):
        u = get_or_create_user("david")
        status = get_user_status(u["user_id"])
        assert status["status"] == "active"
        assert status["mute_expires_at"] is None

    def test_nonexistent_user_returns_active(self):
        status = get_user_status(99999)
        assert status["status"] == "active"

    def test_blocked_user_returns_blocked(self):
        u = get_or_create_user("eve")
        set_restriction(u["user_id"], "blocked", "test block", "severe", "system")
        status = get_user_status(u["user_id"])
        assert status["status"] == "blocked"

    def test_expired_mute_auto_clears(self):
        u = get_or_create_user("frank")
        # Set mute with already-expired timestamp
        set_restriction(u["user_id"], "muted", "mute test", "moderate", "system", mute_minutes=0)
        # Manually force mute_expires_at to the past
        session = db_module.SessionLocal()
        restriction = session.query(RestrictedUserModel).filter(
            RestrictedUserModel.user_id == u["user_id"]
        ).first()
        if restriction:
            restriction.mute_expires_at = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
            session.commit()
        session.close()
        status = get_user_status(u["user_id"])
        assert status["status"] == "active"


# ── Restriction Management ────────────────────────────────────────────────────

class TestSetRestriction:
    def test_block_sets_status(self):
        u = get_or_create_user("grace")
        result = set_restriction(u["user_id"], "blocked", "violated TOS", "severe", "admin")
        assert result["status"] == "blocked"
        assert result["severity"] == "severe"

    def test_mute_sets_expiry(self):
        u = get_or_create_user("hank")
        result = set_restriction(u["user_id"], "muted", "mild warning", "moderate", "system", mute_minutes=30)
        assert result["mute_expires_at"] is not None
        expires_dt = datetime.fromisoformat(result["mute_expires_at"])
        assert expires_dt > datetime.utcnow()

    def test_overwrite_existing_restriction(self):
        u = get_or_create_user("irene")
        set_restriction(u["user_id"], "muted", "first mute", "moderate", "system")
        set_restriction(u["user_id"], "blocked", "escalated", "severe", "admin")
        status = get_user_status(u["user_id"])
        assert status["status"] == "blocked"


# ── Action Logging ────────────────────────────────────────────────────────────

class TestLogAction:
    def test_log_action_returns_id(self):
        u = get_or_create_user("jack")
        action_id = log_action(message_id=None, user_id=u["user_id"], action_type="warn", taken_by="system")
        assert isinstance(action_id, int)
        assert action_id > 0

    def test_log_action_with_admin_note(self):
        u = get_or_create_user("karen")
        action_id = log_action(None, u["user_id"], "block", "admin", admin_note="Repeat offender")
        assert action_id > 0


# ── Message Persistence ───────────────────────────────────────────────────────

class TestSaveMessage:
    def test_save_message_returns_id(self):
        msg_id = save_message("leo", "hello world", is_flagged=False)
        assert isinstance(msg_id, int)
        assert msg_id > 0

    def test_save_flagged_message(self):
        msg_id = save_message("mike", "you are ugly", is_flagged=True)
        assert msg_id > 0

    def test_get_conversation_thread_includes_message(self):
        save_message("nina", "test message content", is_flagged=False)
        thread = get_conversation_thread(limit=10)
        assert len(thread) >= 1
        assert any(m["text"] == "test message content" for m in thread)

    def test_get_conversation_thread_no_duplicate_messages_on_multiple_verdicts(self):
        msg_id = save_message("oscar", "duplicate test message", is_flagged=True)
        # Add multiple verdicts for the same message_id
        save_verdict(msg_id, {"is_true_positive": True, "category": "harassment", "severity": "mild"}, 0.6, "anger", "soft warning", "User report 1")
        save_verdict(msg_id, {"is_true_positive": True, "category": "cyberbullying", "severity": "severe"}, 0.9, "anger", "block message", "User report 2")

        thread = get_conversation_thread(limit=10)
        matching_messages = [m for m in thread if m["id"] == msg_id]
        # Must return exactly 1 message entry with the latest verdict severity ('severe')
        assert len(matching_messages) == 1
        assert matching_messages[0]["severity"] == "severe"

    def test_get_context_history_for_message_retrieves_prior_5_messages(self):
        from src.db import get_context_history_for_message
        m1 = save_message("User1", "Message 1")
        m2 = save_message("User2", "Message 2")
        m3 = save_message("User3", "Message 3")
        m4 = save_message("User4", "Message 4")
        m5 = save_message("User5", "Message 5")
        m6 = save_message("User6", "Message 6 (Reported)")
        m7 = save_message("User7", "Message 7 (Subsequent)")

        # Prior context for m6 must return m1..m5 (excluding m6 and m7)
        context = get_context_history_for_message(target_message_id=m6, limit=5)
        context_ids = [m["id"] for m in context]
        assert context_ids == [m1, m2, m3, m4, m5]
        assert m6 not in context_ids
        assert m7 not in context_ids



# ── Analytics ─────────────────────────────────────────────────────────────────

class TestGetAnalyticsData:
    def test_returns_expected_keys(self):
        data = get_analytics_data()
        assert "total_messages" in data
        assert "flagged_messages" in data
        assert "total_appeals" in data
        assert "pending_appeals" in data
        assert "severity_counts" in data
        assert "category_counts" in data

    def test_zero_counts_on_empty_db(self):
        data = get_analytics_data()
        assert data["total_messages"] == 0
        assert data["flagged_messages"] == 0


class TestAuthenticateOrRegisterUser:
    def test_admin_authentication_success(self):
        from src.db import authenticate_or_register_user
        res = authenticate_or_register_user(username="Admin", email="admin@cyberguard.ai", password="admin123")
        assert res["authenticated"] is True
        assert res["role"] == "admin"

    def test_admin_authentication_wrong_password(self):
        from src.db import authenticate_or_register_user
        res = authenticate_or_register_user(username="Admin", email="admin@cyberguard.ai", password="wrongpassword")
        assert res["authenticated"] is False
        assert "error" in res

    def test_user_registration_and_authentication(self):
        from src.db import authenticate_or_register_user
        # Register user
        reg = authenticate_or_register_user(username="test_user", email="user@example.com", password="mypassword123")
        assert reg["authenticated"] is True
        assert reg["role"] == "user"

        # Correct password login
        login_ok = authenticate_or_register_user(email="user@example.com", password="mypassword123")
        assert login_ok["authenticated"] is True

        # Incorrect password login
        login_bad = authenticate_or_register_user(email="user@example.com", password="wrongpassword")
        assert login_bad["authenticated"] is False
