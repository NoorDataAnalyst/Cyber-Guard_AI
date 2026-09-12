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
    res = pipe.process_message(sender="Bob", text="You are completely stupid, shutdown your account idiot!")
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
