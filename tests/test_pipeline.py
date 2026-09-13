"""
Unit tests for src/pipeline.py module.
"""

import pytest
from src.pipeline import CyberbullyingPipeline


def test_pipeline_clean_message():
    pipe = CyberbullyingPipeline()
    res = pipe.process_message(sender="Alice", text="Hi everyone, hope you are having a nice day!")
    assert res["is_flagged"] is False
    assert res["action_taken"] == "no action"


def test_pipeline_toxic_message():
    pipe = CyberbullyingPipeline()
    import uuid
    test_user = f"Bob_{uuid.uuid4().hex[:6]}"
    res = pipe.process_message(sender=test_user, text="You are completely stupid, shutdown your account idiot!")
    assert res["is_flagged"] is True
    assert res["action_taken"] in ["soft warning", "mute sender", "block message"]
    assert "explanation" in res


def test_pipeline_manual_user_report():
    pipe = CyberbullyingPipeline()
    res = pipe.process_message(
        sender="Charlie",
        text="Oh wow, what a brilliant contribution, genius.",
        report_type="manual_user_report"
    )
    assert res["is_flagged"] is True
    assert res["report_type"] == "manual_user_report"
    assert "user_report" in res


def test_pipeline_manual_report_casual_message_returns_clean():
    from src.db import save_message, get_conversation_thread
    pipe = CyberbullyingPipeline()

    msg_id = save_message(sender="Dave", text="hi, how are you today?", is_flagged=False)
    res = pipe.process_existing_message(message_id=msg_id, report_type="manual_user_report")

    assert res["is_flagged"] is False
    assert res["category"] == "not_bullying"
    assert res["severity"] == "none"

    thread = get_conversation_thread(limit=10)
    matching = [m for m in thread if m["id"] == msg_id]
    assert len(matching) == 1
    assert matching[0]["is_flagged"] is False
    assert matching[0]["is_reported"] is True

