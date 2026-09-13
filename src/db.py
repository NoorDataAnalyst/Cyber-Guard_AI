"""
Database Persistence Layer Module using SQLAlchemy.
Unified ORM Schema supporting Supabase Managed Postgres and local SQLite fallback.
"""

import os
import random
import string
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    select,
    update,
    desc,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from src.config import DB_PATH, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD

logger = logging.getLogger(__name__)

Base = declarative_base()

# ==============================================================================
# SQLAlchemy ORM Models
# ==============================================================================

class UserModel(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    role = Column(String(20), default="user", nullable=False)  # active: 'user' or 'admin'
    status = Column(String(20), default="active", nullable=False)  # active, muted, blocked
    created_at = Column(String(50), default=lambda: datetime.utcnow().isoformat())


class MessageModel(Base):
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    conversation_id = Column(String(50), default="main", nullable=False)
    text = Column(Text, nullable=False)
    timestamp = Column(String(50), nullable=False)
    source = Column(String(30), default="automatic", nullable=False)  # automatic, manual_report
    toxicity_score = Column(Float, default=0.0)
    toxicity_category = Column(String(50), default="clean")
    emotion_label = Column(String(50), default="neutral")
    emotion_score = Column(Float, default=0.0)
    is_flagged = Column(Boolean, default=False, nullable=False)


class VerdictModel(Base):
    __tablename__ = "verdicts"

    verdict_id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.message_id"), nullable=False)
    is_true_positive = Column(Boolean, default=True, nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    confidence = Column(Float, default=1.0)
    internal_explanation = Column(Text, default="")
    user_facing_report = Column(Text, default="")
    created_at = Column(String(50), nullable=False)
    admin_status = Column(String(50), default="pending")  # pending, manually_blocked, manually_unblocked, dismissed
    admin_note = Column(Text, default="")
    context_retrieved = Column(Text, default="[]")
    examples_retrieved = Column(Text, default="[]")
    policy_retrieved = Column(Text, default="[]")


class ActionModel(Base):
    __tablename__ = "actions"

    action_id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer, ForeignKey("messages.message_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    action_type = Column(String(30), nullable=False)  # warn, mute, block, unblock, dismiss
    taken_by = Column(String(20), nullable=False)     # system, admin
    admin_note = Column(Text, nullable=True)
    timestamp = Column(String(50), nullable=False)


class RestrictedUserModel(Base):
    __tablename__ = "restricted_users"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    blocked_at = Column(String(50), nullable=False)
    reason = Column(Text, default="")
    severity = Column(String(20), default="severe")
    blocked_by = Column(String(20), default="system")  # system, admin
    status = Column(String(20), default="blocked")     # blocked, muted, unblocked
    mute_expires_at = Column(String(50), nullable=True)


class AppealModel(Base):
    __tablename__ = "appeals"

    appeal_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    submitted_at = Column(String(50), nullable=False)
    appeal_text = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(String(50), nullable=True)
    admin_note = Column(Text, nullable=True)


# ==============================================================================
# Database Engine Initialization & Fallback Handler
# ==============================================================================

def _get_database_uri() -> str:
    """Attempts to read DATABASE_URL from Streamlit secrets or environment variables."""
    raw_url = ""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
            raw_url = str(st.secrets["DATABASE_URL"]).strip()
    except Exception:
        pass

    if not raw_url:
        raw_url = os.getenv("DATABASE_URL", "").strip()

    # Ignore dummy/placeholder example URIs
    if "postgres.xxxx" in raw_url or "your_password" in raw_url:
        return ""

    return raw_url


def _probe_sqlite_schema(engine) -> bool:
    """
    SQLite-only: run a trivial SELECT on every ORM-mapped table to verify
    that all expected columns exist.  Returns True if schema is healthy,
    False if any OperationalError (e.g. 'no such column') is caught.
    """
    probe_queries = [
        "SELECT user_id, username, email, password, role, status FROM users LIMIT 1",
        "SELECT message_id, user_id, text, is_flagged FROM messages LIMIT 1",
        "SELECT verdict_id, message_id, severity, category, confidence FROM verdicts LIMIT 1",
        "SELECT action_id, action_type, taken_by, timestamp FROM actions LIMIT 1",
        "SELECT user_id, status, mute_expires_at FROM restricted_users LIMIT 1",
        "SELECT appeal_id, user_id, appeal_text, status FROM appeals LIMIT 1",
    ]
    from sqlalchemy import text as sa_text
    from sqlalchemy.exc import OperationalError
    with engine.connect() as conn:
        for q in probe_queries:
            try:
                conn.execute(sa_text(q))
            except OperationalError as exc:
                logger.warning(f"SQLite schema probe failed ({exc}). Stale schema detected.")
                return False
    return True


def _create_db_engine():
    """Initializes SQLAlchemy Engine targeting Supabase Postgres or local SQLite fallback."""
    raw_uri = _get_database_uri()

    if raw_uri and ("postgresql://" in raw_uri or "postgres://" in raw_uri):
        # Normalize postgres:// to postgresql:// for SQLAlchemy 2.0 compatibility
        pg_uri = raw_uri.replace("postgres://", "postgresql://")
        try:
            logger.info("Attempting to connect to Supabase Postgres database...")
            engine = create_engine(pg_uri, pool_pre_ping=True, echo=False)
            Base.metadata.create_all(engine)
            logger.info("Successfully connected to Supabase Postgres database!")
            return engine, "supabase"
        except Exception as e:
            logger.warning(f"Unable to connect to Supabase Postgres database ({e}). Falling back to local SQLite.")

    # SQLite Local Fallback
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    sqlite_uri = f"sqlite:///{DB_PATH.resolve()}"
    logger.info(f"Using local SQLite database at {sqlite_uri}")
    engine = create_engine(sqlite_uri, echo=False)
    Base.metadata.create_all(engine)

    # Defensive schema check (SQLite only) ─────────────────────────────────
    if not _probe_sqlite_schema(engine):
        logger.warning(
            "Stale SQLite schema detected — missing columns found. "
            f"Deleting '{DB_PATH}' and recreating with current schema."
        )
        engine.dispose()
        try:
            DB_PATH.unlink(missing_ok=True)
        except Exception as del_err:
            logger.error(f"Could not delete stale DB file: {del_err}")
        # Recreate fresh
        engine = create_engine(sqlite_uri, echo=False)
        Base.metadata.create_all(engine)
        logger.info("SQLite database recreated with current schema successfully.")

    return engine, "sqlite"


engine, DB_BACKEND_TYPE = _create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Ensures database tables are created, migrated, and seeded with Admin account."""
    Base.metadata.create_all(bind=engine)
    from sqlalchemy import text as sa_text
    with engine.connect() as conn:
        try:
            conn.execute(sa_text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sa_text("ALTER TABLE users ADD COLUMN password VARCHAR(255)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(sa_text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
            conn.commit()
        except Exception:
            pass

    # Pre-seed Admin Account using configurable credentials
    session = SessionLocal()
    try:
        admin_user = session.query(UserModel).filter(
            (UserModel.email == DEFAULT_ADMIN_EMAIL) | (UserModel.username == DEFAULT_ADMIN_USERNAME)
        ).first()

        if not admin_user:
            now_iso = datetime.utcnow().isoformat()
            admin_user = UserModel(
                username=DEFAULT_ADMIN_USERNAME,
                email=DEFAULT_ADMIN_EMAIL,
                password=DEFAULT_ADMIN_PASSWORD,
                role="admin",
                status="active",
                created_at=now_iso,
            )
            session.add(admin_user)
            session.commit()
        else:
            if admin_user.role != "admin":
                admin_user.role = "admin"
                session.commit()
    except Exception as e:
        logger.warning(f"Note during admin seeding: {e}")
    finally:
        session.close()


def get_db_session():
    """Returns a new SQLAlchemy database session."""
    return SessionLocal()


# ==============================================================================
# Specific Named DB Functions Required
# ==============================================================================

def authenticate_or_register_user(
    username: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Authenticates an existing user by email/username + password, or registers a new user.
    User roles are dynamically fetched from the database table.
    """
    clean_email = str(email).strip().lower() if email and str(email).strip() else ""
    clean_pass = str(password).strip() if password else ""
    clean_name = str(username).strip() if username and str(username).strip() else ""

    session = SessionLocal()
    try:
        user = None
        if clean_email:
            user = session.query(UserModel).filter(UserModel.email == clean_email).first()
        if not user and clean_name:
            user = session.query(UserModel).filter(UserModel.username == clean_name).first()

        if user:
            # Validate password if user has a password configured
            if user.password and clean_pass and user.password != clean_pass:
                return {"authenticated": False, "error": "Incorrect password for this account."}
            # Set password if missing
            if not user.password and clean_pass:
                user.password = clean_pass
                session.commit()
            # Update email if missing
            if clean_email and not user.email:
                user.email = clean_email
                session.commit()

            session.refresh(user)
            role = getattr(user, "role", "user") or "user"
            return {
                "authenticated": True,
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": role,
                "status": user.status,
                "created_at": user.created_at,
            }

        # User does not exist — register new account
        if not clean_name:
            clean_name = clean_email.split("@")[0] if clean_email else "Anonymous_User"

        final_name = clean_name
        existing = session.query(UserModel).filter(UserModel.username == final_name).first()
        if existing:
            suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
            final_name = f"{clean_name}_{suffix}"

        # Assign admin role if registering with configured admin email or username
        is_default_admin = (clean_email and clean_email == DEFAULT_ADMIN_EMAIL.lower()) or (clean_name.lower() == DEFAULT_ADMIN_USERNAME.lower())
        if is_default_admin and clean_pass != DEFAULT_ADMIN_PASSWORD:
            return {"authenticated": False, "error": "Invalid password for admin account."}

        role = "admin" if is_default_admin else "user"
        now_iso = datetime.utcnow().isoformat()
        new_user = UserModel(
            username=final_name,
            email=clean_email if clean_email else None,
            password=clean_pass if clean_pass else None,
            role=role,
            status="active",
            created_at=now_iso,
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return {
            "authenticated": True,
            "user_id": new_user.user_id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "status": new_user.status,
            "created_at": new_user.created_at,
        }
    finally:
        session.close()


def get_or_create_user(username: str, email: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns user row dictionary. Creates user if missing.
    Compatible wrapper delegating to authenticate_or_register_user.
    """
    auth_res = authenticate_or_register_user(username=username, email=email, password=password)
    if auth_res.get("authenticated"):
        return auth_res

    # Fallback read
    clean_name = str(username).strip() or "Anonymous_User"
    session = SessionLocal()
    try:
        user = session.query(UserModel).filter(UserModel.username == clean_name).first()
        if user:
            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "role": getattr(user, "role", "user") or "user",
                "status": user.status,
                "created_at": user.created_at,
            }
        return {
            "user_id": 1,
            "username": clean_name,
            "email": email,
            "role": "admin" if (email and email.lower() == DEFAULT_ADMIN_EMAIL.lower()) else "user",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        }
    finally:
        session.close()


def get_user_status(user_id: int) -> Dict[str, Any]:
    """
    Fresh non-cached read returning current status + mute_expires_at.
    Auto-clears 30-minute mutes if mute_expires_at has passed.
    """
    session = SessionLocal()
    try:
        user = session.query(UserModel).filter(UserModel.user_id == user_id).first()
        if not user:
            return {"status": "active", "mute_expires_at": None, "reason": "", "severity": "none"}

        restriction = session.query(RestrictedUserModel).filter(RestrictedUserModel.user_id == user_id).first()
        if not restriction or restriction.status == "unblocked":
            return {"status": "active", "mute_expires_at": None, "reason": "", "severity": "none"}

        now_utc = datetime.utcnow()

        # Check 30-minute mute auto-expiry
        if restriction.status == "muted" and restriction.mute_expires_at:
            try:
                expires_dt = datetime.fromisoformat(restriction.mute_expires_at)
                if now_utc >= expires_dt:
                    # Mute self-resolved! Update status to active
                    user.status = "active"
                    restriction.status = "unblocked"
                    session.commit()
                    logger.info(f"Mute automatically expired for user_id={user_id}.")
                    return {"status": "active", "mute_expires_at": None, "reason": "Mute auto-expired", "severity": "none"}
            except Exception as e:
                logger.error(f"Error parsing mute_expires_at '{restriction.mute_expires_at}': {e}")

        return {
            "status": user.status,
            "mute_expires_at": restriction.mute_expires_at,
            "reason": restriction.reason or "Account restricted",
            "severity": restriction.severity or "moderate",
            "blocked_by": restriction.blocked_by,
        }
    finally:
        session.close()


def set_restriction(user_id: int, status: str, reason: str, severity: str, blocked_by: str, mute_minutes: int = 30) -> Dict[str, Any]:
    """Writes to restricted_users and updates users.status."""
    session = SessionLocal()
    try:
        user = session.query(UserModel).filter(UserModel.user_id == user_id).first()
        if user:
            user.status = status

        now_utc = datetime.utcnow()
        now_iso = now_utc.isoformat()
        mute_expires_iso = None

        if status == "muted":
            mute_expires_iso = (now_utc + timedelta(minutes=mute_minutes)).isoformat()

        restriction = session.query(RestrictedUserModel).filter(RestrictedUserModel.user_id == user_id).first()
        if not restriction:
            restriction = RestrictedUserModel(
                user_id=user_id,
                blocked_at=now_iso,
                reason=reason,
                severity=severity,
                blocked_by=blocked_by,
                status=status,
                mute_expires_at=mute_expires_iso,
            )
            session.add(restriction)
        else:
            restriction.blocked_at = now_iso
            restriction.reason = reason
            restriction.severity = severity
            restriction.blocked_by = blocked_by
            restriction.status = status
            restriction.mute_expires_at = mute_expires_iso

        session.commit()
        return {
            "user_id": user_id,
            "status": status,
            "reason": reason,
            "severity": severity,
            "mute_expires_at": mute_expires_iso,
        }
    finally:
        session.close()


def log_action(message_id: Optional[int], user_id: Optional[int], action_type: str, taken_by: str, admin_note: Optional[str] = None) -> int:
    """Logs an auditable action entry in actions table."""
    session = SessionLocal()
    try:
        now_iso = datetime.utcnow().isoformat()
        act = ActionModel(
            message_id=message_id,
            user_id=user_id,
            action_type=action_type,
            taken_by=taken_by,
            admin_note=admin_note,
            timestamp=now_iso,
        )
        session.add(act)
        session.commit()
        return act.action_id
    finally:
        session.close()


def create_appeal(user_id: int, appeal_text: str) -> Dict[str, Any]:
    """Creates a new pending appeal record in appeals table."""
    session = SessionLocal()
    try:
        now_iso = datetime.utcnow().isoformat()
        appeal = AppealModel(
            user_id=user_id,
            submitted_at=now_iso,
            appeal_text=appeal_text,
            status="pending",
            admin_note="",
        )
        session.add(appeal)
        session.commit()
        session.refresh(appeal)
        return {
            "appeal_id": appeal.appeal_id,
            "user_id": appeal.user_id,
            "submitted_at": appeal.submitted_at,
            "appeal_text": appeal.appeal_text,
            "status": appeal.status,
        }
    finally:
        session.close()


def get_pending_appeals() -> List[Dict[str, Any]]:
    """Retrieves all pending appeals for Admin review."""
    session = SessionLocal()
    try:
        query = (
            session.query(AppealModel, UserModel, RestrictedUserModel)
            .join(UserModel, AppealModel.user_id == UserModel.user_id)
            .outerjoin(RestrictedUserModel, AppealModel.user_id == RestrictedUserModel.user_id)
            .filter(AppealModel.status == "pending")
            .order_by(desc(AppealModel.appeal_id))
        )
        rows = query.all()
        results = []
        for appeal, user, restriction in rows:
            results.append({
                "appeal_id": appeal.appeal_id,
                "user_id": appeal.user_id,
                "username": user.username if user else "Unknown",
                "submitted_at": appeal.submitted_at,
                "appeal_text": appeal.appeal_text,
                "status": appeal.status,
                "blocked_reason": restriction.reason if restriction else "Account restricted",
                "severity": restriction.severity if restriction else "severe",
            })
        return results
    finally:
        session.close()


def resolve_appeal(appeal_id: int, decision: str, admin_note: Optional[str] = None) -> bool:
    """
    Resolves appeal with 'approved' or 'rejected'.
    If approved, clears restriction via set_restriction and sets user status to active.
    """
    session = SessionLocal()
    try:
        appeal = session.query(AppealModel).filter(AppealModel.appeal_id == appeal_id).first()
        if not appeal:
            return False

        now_iso = datetime.utcnow().isoformat()
        appeal.status = decision
        appeal.reviewed_by = "admin"
        appeal.reviewed_at = now_iso
        appeal.admin_note = admin_note or ""

        user_id = appeal.user_id

        if decision == "approved":
            # Clear restriction
            user = session.query(UserModel).filter(UserModel.user_id == user_id).first()
            if user:
                user.status = "active"

            restriction = session.query(RestrictedUserModel).filter(RestrictedUserModel.user_id == user_id).first()
            if restriction:
                restriction.status = "unblocked"
                restriction.mute_expires_at = None

            log_action(message_id=None, user_id=user_id, action_type="unblock", taken_by="admin", admin_note=admin_note)
        else:
            log_action(message_id=None, user_id=user_id, action_type="reject_appeal", taken_by="admin", admin_note=admin_note)

        session.commit()
        return True
    finally:
        session.close()


# ==============================================================================
# Preserved Function Signatures (Compatible with pipeline.py and app.py)
# ==============================================================================

def save_message(sender: str, text: str, is_flagged: bool = False, report_type: str = "automatic", user_id: Optional[int] = None) -> int:
    """Saves incoming message and returns its message_id."""
    if not user_id:
        user_info = get_or_create_user(sender)
        user_id = user_info["user_id"]

    session = SessionLocal()
    try:
        now_iso = datetime.utcnow().isoformat()
        msg = MessageModel(
            user_id=user_id,
            conversation_id="main",
            text=text,
            timestamp=now_iso,
            source=report_type,
            is_flagged=is_flagged,
        )
        session.add(msg)
        session.commit()
        return msg.message_id
    finally:
        session.close()


def flag_existing_message(message_id: int, report_type: str = "manual_user_report") -> bool:
    """Flags an existing message row for manual report without creating a duplicate message."""
    session = SessionLocal()
    try:
        msg = session.query(MessageModel).filter(MessageModel.message_id == message_id).first()
        if msg:
            msg.is_flagged = True
            msg.source = report_type
            session.commit()
            return True
        return False
    finally:
        session.close()


def save_verdict(
    message_id: int,
    verdict: Dict[str, Any],
    toxicity_score: float,
    top_emotion: str,
    action_taken: str,
    user_report: str,
    context_retrieved: List[Dict[str, Any]] = None,
    examples_retrieved: List[Dict[str, Any]] = None,
    policy_retrieved: List[Dict[str, Any]] = None
) -> int:
    """Saves verdict details to database."""
    import json
    session = SessionLocal()
    try:
        now_iso = datetime.utcnow().isoformat()
        verd = VerdictModel(
            message_id=message_id,
            is_true_positive=bool(verdict.get("is_true_positive", True)),
            category=str(verdict.get("category", "not_bullying")),
            severity=str(verdict.get("severity", "none")),
            confidence=float(verdict.get("confidence", 1.0)),
            internal_explanation=str(verdict.get("explanation", "")),
            user_facing_report=str(user_report),
            created_at=now_iso,
            admin_status="pending",
            admin_note="",
            context_retrieved=json.dumps(context_retrieved or [], default=str),
            examples_retrieved=json.dumps(examples_retrieved or [], default=str),
            policy_retrieved=json.dumps(policy_retrieved or [], default=str),
        )
        session.add(verd)

        # Update message toxicity and emotion
        msg = session.query(MessageModel).filter(MessageModel.message_id == message_id).first()
        if msg:
            msg.toxicity_score = float(toxicity_score)
            msg.toxicity_category = str(verdict.get("category", "clean"))
            msg.emotion_label = str(top_emotion)
            msg.is_flagged = bool(verdict.get("is_true_positive", False))

        session.commit()
        return verd.verdict_id
    finally:
        session.close()


def get_conversation_thread(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent conversation messages joined with verdict details without duplicate entries."""
    import json
    session = SessionLocal()
    try:
        messages = (
            session.query(MessageModel)
            .order_by(MessageModel.message_id.desc())
            .limit(limit)
            .all()
        )
        msg_ids = [m.message_id for m in messages]
        user_ids = list({m.user_id for m in messages if m.user_id})

        users_by_id = {}
        if user_ids:
            user_rows = session.query(UserModel).filter(UserModel.user_id.in_(user_ids)).all()
            users_by_id = {u.user_id: u for u in user_rows}

        verdicts_by_msg_id = {}
        if msg_ids:
            verdict_rows = (
                session.query(VerdictModel)
                .filter(VerdictModel.message_id.in_(msg_ids))
                .order_by(VerdictModel.verdict_id.desc())
                .all()
            )
            for v in verdict_rows:
                if v.message_id not in verdicts_by_msg_id:
                    verdicts_by_msg_id[v.message_id] = v

        results = []
        for msg in reversed(messages):
            user = users_by_id.get(msg.user_id)
            verd = verdicts_by_msg_id.get(msg.message_id)
            results.append({
                "id": msg.message_id,
                "timestamp": msg.timestamp,
                "sender": user.username if user else "Anonymous",
                "text": msg.text,
                "is_flagged": msg.is_flagged,
                "report_type": msg.source,
                "category": verd.category if verd else "not_bullying",
                "severity": verd.severity if verd else "none",
                "action_taken": verd.admin_status if verd and verd.admin_status != "pending" else (
                    "block message" if verd and verd.severity == "severe" else (
                    "mute sender" if verd and verd.severity == "moderate" else (
                    "soft warning" if verd and verd.severity == "mild" else "no action"))
                ),
                "user_report": verd.user_facing_report if verd else "",
                "explanation": verd.internal_explanation if verd else "",
            })
        return results
    finally:
        session.close()


def get_flagged_verdicts(
    severity_filter: Optional[str] = None,
    category_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves all flagged verdicts for Admin Dashboard."""
    import json
    session = SessionLocal()
    try:
        query = (
            session.query(VerdictModel, MessageModel, UserModel)
            .join(MessageModel, VerdictModel.message_id == MessageModel.message_id)
            .outerjoin(UserModel, MessageModel.user_id == UserModel.user_id)
            .filter(VerdictModel.is_true_positive == True)
        )

        if severity_filter and severity_filter != "all":
            query = query.filter(VerdictModel.severity == severity_filter)

        if category_filter and category_filter != "all":
            query = query.filter(VerdictModel.category == category_filter)

        query = query.order_by(desc(VerdictModel.verdict_id))
        rows = query.all()

        results = []
        for verd, msg, user in rows:
            results.append({
                "verdict_id": verd.verdict_id,
                "message_id": verd.message_id,
                "timestamp": verd.created_at,
                "sender": user.username if user else "User",
                "user_id": user.user_id if user else None,
                "message_text": msg.text,
                "report_type": msg.source,
                "is_true_positive": verd.is_true_positive,
                "category": verd.category,
                "severity": verd.severity,
                "confidence": verd.confidence,
                "toxicity_score": msg.toxicity_score,
                "top_emotion": msg.emotion_label,
                "explanation": verd.internal_explanation,
                "action_taken": verd.admin_status if verd.admin_status != "pending" else (
                    "block message" if verd.severity == "severe" else (
                    "mute sender" if verd.severity == "moderate" else (
                    "soft warning" if verd.severity == "mild" else "no action"))
                ),
                "user_report": verd.user_facing_report,
                "admin_status": verd.admin_status,
                "admin_note": verd.admin_note,
                "context_retrieved": json.loads(verd.context_retrieved or "[]"),
                "examples_retrieved": json.loads(verd.examples_retrieved or "[]"),
                "policy_retrieved": json.loads(verd.policy_retrieved or "[]"),
            })
        return results
    finally:
        session.close()


def update_admin_status(
    verdict_id: int,
    admin_status: str,
    action_taken: str,
    admin_note: str = ""
) -> bool:
    """Updates admin status override for a verdict."""
    session = SessionLocal()
    try:
        verd = session.query(VerdictModel).filter(VerdictModel.verdict_id == verdict_id).first()
        if not verd:
            return False

        verd.admin_status = admin_status
        verd.admin_note = admin_note

        # Log action
        msg = session.query(MessageModel).filter(MessageModel.message_id == verd.message_id).first()
        user_id = msg.user_id if msg else None

        log_action(message_id=verd.message_id, user_id=user_id, action_type=admin_status, taken_by="admin", admin_note=admin_note)
        session.commit()
        return True
    finally:
        session.close()


def get_analytics_data() -> Dict[str, Any]:
    """Retrieves aggregated metrics for Plotly charts."""
    session = SessionLocal()
    try:
        # Severity breakdown
        sev_counts = session.query(VerdictModel.severity, func.count(VerdictModel.verdict_id)).group_by(VerdictModel.severity).all()
        severity_data = {s: c for s, c in sev_counts}

        # Category breakdown
        cat_counts = session.query(VerdictModel.category, func.count(VerdictModel.verdict_id)).group_by(VerdictModel.category).all()
        category_data = {c: count for c, count in cat_counts}

        # Total counts
        total_messages = session.query(MessageModel).count()
        flagged_messages = session.query(MessageModel).filter(MessageModel.is_flagged == True).count()
        total_appeals = session.query(AppealModel).count()
        pending_appeals = session.query(AppealModel).filter(AppealModel.status == "pending").count()

        return {
            "total_messages": total_messages,
            "flagged_messages": flagged_messages,
            "total_appeals": total_appeals,
            "pending_appeals": pending_appeals,
            "severity_counts": severity_data,
            "category_counts": category_data,
        }
    finally:
        session.close()


# Ensure DB tables exist on load
init_db()
