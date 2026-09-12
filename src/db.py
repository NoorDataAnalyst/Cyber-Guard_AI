"""
SQLite Database Layer Module.
Manages persistent storage for messages, automated verdicts, policy actions,
user-facing reports, manual user reports, and Admin override actions.

Privacy Note:
A real-world production deployment would require data retention and deletion policies
(e.g., GDPR right-to-be-forgotten compliance and automatic 30-day purge cycles).
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import DB_PATH

logger = logging.getLogger(__name__)


def get_db_connection() -> sqlite3.Connection:
    """Returns a SQLite connection with dict row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Creates database schema tables if they do not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                is_flagged INTEGER NOT NULL DEFAULT 0,
                report_type TEXT NOT NULL DEFAULT 'automatic'
            )
        """)

        # Verdicts & Reports Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verdicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                is_true_positive INTEGER NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                toxicity_score REAL NOT NULL,
                top_emotion TEXT NOT NULL,
                explanation TEXT NOT NULL,
                action_taken TEXT NOT NULL,
                user_report TEXT NOT NULL,
                admin_status TEXT NOT NULL DEFAULT 'pending',
                admin_note TEXT DEFAULT '',
                context_retrieved TEXT DEFAULT '[]',
                examples_retrieved TEXT DEFAULT '[]',
                policy_retrieved TEXT DEFAULT '[]',
                FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        logger.info(f"SQLite database initialized at {DB_PATH}.")


def save_message(sender: str, text: str, is_flagged: bool = False, report_type: str = "automatic") -> int:
    """Saves incoming message to database and returns its row ID."""
    now_iso = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (timestamp, sender, text, is_flagged, report_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            (now_iso, sender, text, 1 if is_flagged else 0, report_type)
        )
        conn.commit()
        return cursor.lastrowid


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
    """Saves analysis verdict and generated report to database."""
    now_iso = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO verdicts (
                message_id, timestamp, is_true_positive, category, severity, confidence,
                toxicity_score, top_emotion, explanation, action_taken, user_report,
                admin_status, admin_note, context_retrieved, examples_retrieved, policy_retrieved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                now_iso,
                1 if verdict.get("is_true_positive", True) else 0,
                verdict.get("category", "not_bullying"),
                verdict.get("severity", "none"),
                float(verdict.get("confidence", 1.0)),
                float(toxicity_score),
                str(top_emotion),
                str(verdict.get("explanation", "")),
                str(action_taken),
                str(user_report),
                "pending",
                "",
                json.dumps(context_retrieved or [], default=str),
                json.dumps(examples_retrieved or [], default=str),
                json.dumps(policy_retrieved or [], default=str)
            )
        )
        conn.commit()
        return cursor.lastrowid


def get_conversation_thread(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves recent conversation messages for chat display and RAG thread context."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.timestamp, m.sender, m.text, m.is_flagged, m.report_type,
                   v.category, v.severity, v.action_taken, v.user_report, v.explanation
            FROM messages m
            LEFT JOIN verdicts v ON m.id = v.message_id
            ORDER BY m.id ASC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_flagged_verdicts(
    severity_filter: Optional[str] = None,
    category_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves all flagged message verdicts for Admin Dashboard view with optional filters."""
    query = """
        SELECT v.id AS verdict_id, v.message_id, v.timestamp, m.sender, m.text AS message_text,
               m.report_type, v.is_true_positive, v.category, v.severity, v.confidence,
               v.toxicity_score, v.top_emotion, v.explanation, v.action_taken, v.user_report,
               v.admin_status, v.admin_note, v.context_retrieved, v.examples_retrieved, v.policy_retrieved
        FROM verdicts v
        JOIN messages m ON v.message_id = m.id
        WHERE 1=1
    """
    params = []

    if severity_filter and severity_filter != "all":
        query += " AND v.severity = ?"
        params.append(severity_filter)

    if category_filter and category_filter != "all":
        query += " AND v.category = ?"
        params.append(category_filter)

    query += " ORDER BY v.id DESC"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for r in rows:
            item = dict(r)
            item["context_retrieved"] = json.loads(item.get("context_retrieved") or "[]")
            item["examples_retrieved"] = json.loads(item.get("examples_retrieved") or "[]")
            item["policy_retrieved"] = json.loads(item.get("policy_retrieved") or "[]")
            results.append(item)

        return results


def update_admin_status(
    verdict_id: int,
    admin_status: str,
    action_taken: str,
    admin_note: str = ""
) -> bool:
    """Updates admin decision override status for a verdict record."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE verdicts
            SET admin_status = ?, action_taken = ?, admin_note = ?
            WHERE id = ?
            """,
            (admin_status, action_taken, admin_note, verdict_id)
        )
        conn.commit()
        return cursor.rowcount > 0


# Ensure database tables exist on module load
init_db()
