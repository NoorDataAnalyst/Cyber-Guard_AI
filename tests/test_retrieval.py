"""
Unit tests for src/retrieval.py module.
"""

import pytest
from src.retrieval import RAGRetrievalManager


def test_retrieval_manager_init():
    rag = RAGRetrievalManager()
    assert rag.example_store is not None
    assert rag.policy_store is not None


def test_retrieve_similar_examples():
    rag = RAGRetrievalManager()
    results = rag.retrieve_similar_examples("You are completely stupid and useless", top_k=2)
    assert isinstance(results, list)
    assert len(results) > 0
    assert "text" in results[0]
    assert "category" in results[0]


def test_retrieve_policy_snippets():
    rag = RAGRetrievalManager()
    results = rag.retrieve_policy_snippets("threat", top_k=2)
    assert isinstance(results, list)
    assert len(results) > 0
    assert "snippet" in results[0]
    assert "source" in results[0]


def test_retrieve_context():
    rag = RAGRetrievalManager()
    history = [
        {"sender": "UserA", "text": "Hello"},
        {"sender": "UserB", "text": "Hi there"},
        {"sender": "UserA", "text": "Are you ready?"},
    ]
    recent = rag.retrieve_context(history, n_recent=2)
    assert len(recent) == 2
    assert recent[0]["text"] == "Hi there"
    assert recent[1]["text"] == "Are you ready?"
