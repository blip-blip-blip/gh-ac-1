"""Tests for ClassifierAgent."""

import pytest
from unittest.mock import MagicMock, patch

from agents.core.base_agent import AgentResult
from agents.issue_triage.classifier import ClassifierAgent


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def agent(client, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    return ClassifierAgent(client)


@pytest.fixture
def issue():
    return {
        "number": 42,
        "title": "App crashes on login",
        "body": "Clicking login causes a 500 error.",
        "labels": [],
    }


def test_valid_classification_returns_success(agent, issue):
    model_response = {"type": "bug", "confidence": 0.95, "rationale": "Error on login"}
    with patch.object(agent, "call_model", return_value=model_response):
        result = agent.run(issue)
    assert result.success is True
    assert result.data["type"] == "bug"


def test_invalid_type_falls_back_to_question(agent, issue):
    model_response = {"type": "nonsense", "confidence": 0.5, "rationale": "?"}
    with patch.object(agent, "call_model", return_value=model_response):
        result = agent.run(issue)
    assert result.success is True
    assert result.data["type"] == "question"


def test_model_failure_returns_failure_result(agent, issue):
    with patch.object(agent, "call_model", return_value=None):
        result = agent.run(issue)
    assert result.success is False


def test_agent_type_is_classifier(agent):
    assert agent.agent_type == "classifier"
