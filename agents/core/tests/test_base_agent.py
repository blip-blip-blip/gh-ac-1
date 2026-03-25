"""Tests for BaseAgent."""

import pytest
from unittest.mock import MagicMock, patch

from agents.core.base_agent import BaseAgent, AgentResult, CHARS_PER_TOKEN


class ConcreteAgent(BaseAgent):
    OUTPUT_SCHEMA = {
        "required": ["result"],
        "properties": {"result": {"type": "string"}},
    }

    def execute(self, text: str) -> AgentResult:
        data = self.call_model(self.build_system_prompt(), text)
        if data is None:
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error="model call failed")
        return AgentResult(agent_type=self.agent_type, success=True, data=data)


@pytest.fixture
def agent(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("MAX_INPUT_TOKENS", "100")
    monkeypatch.setenv("MAX_OUTPUT_TOKENS", "50")
    client = MagicMock()
    return ConcreteAgent("test", client)


# ------------------------------------------------------------------
# Token budget
# ------------------------------------------------------------------

def test_input_within_budget_not_truncated(agent):
    short_text = "a" * 10
    result, truncated = agent._apply_token_budget(short_text)
    assert result == short_text
    assert truncated is False


def test_input_over_budget_truncated(agent):
    long_text = "a" * (agent.max_input_tokens * CHARS_PER_TOKEN + 100)
    result, truncated = agent._apply_token_budget(long_text)
    assert truncated is True
    assert len(result) == agent.max_input_tokens * CHARS_PER_TOKEN


# ------------------------------------------------------------------
# Schema validation
# ------------------------------------------------------------------

def test_valid_output_passes_validation(agent):
    assert agent._validate_output({"result": "ok"}) == {"result": "ok"}


def test_missing_required_field_fails_validation(agent):
    assert agent._validate_output({"wrong_field": "value"}) is None


# ------------------------------------------------------------------
# Retry behaviour
# ------------------------------------------------------------------

def test_returns_none_after_all_retries_fail(agent):
    with patch.object(agent, "_call_api", return_value=None):
        with patch("agents.core.base_agent.time.sleep"):
            result = agent.call_model("system", "user")
    assert result is None


def test_succeeds_on_second_attempt(agent):
    with patch.object(agent, "_call_api",
                      side_effect=[None, {"result": "ok"}]):
        with patch("agents.core.base_agent.time.sleep"):
            result = agent.call_model("system", "user")
    assert result == {"result": "ok"}


# ------------------------------------------------------------------
# run() wraps exceptions
# ------------------------------------------------------------------

def test_run_catches_unhandled_exception(agent):
    with patch.object(agent, "execute", side_effect=RuntimeError("boom")):
        result = agent.run("anything")
    assert result.success is False
    assert "boom" in result.error
