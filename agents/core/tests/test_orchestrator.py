"""Tests for Orchestrator event parsing."""

import json
import pytest

from agents.core.orchestrator import parse_event, GitHubEvent


def write_event(tmp_path, payload: dict) -> str:
    p = tmp_path / "event.json"
    p.write_text(json.dumps(payload))
    return str(p)


@pytest.fixture(autouse=True)
def set_required_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")


# ------------------------------------------------------------------
# Issue events
# ------------------------------------------------------------------

def test_parses_issue_opened(tmp_path, monkeypatch):
    payload = {"action": "opened", "issue": {"number": 5}}
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issues")
    monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
    event = parse_event()
    assert event is not None
    assert event.issue_number == 5
    assert event.pr_number is None


def test_parses_issue_edited(tmp_path, monkeypatch):
    payload = {"action": "edited", "issue": {"number": 10}}
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issues")
    monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
    event = parse_event()
    assert event is not None
    assert event.action == "edited"


def test_skips_issue_deleted(tmp_path, monkeypatch):
    payload = {"action": "deleted", "issue": {"number": 1}}
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issues")
    monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
    assert parse_event() is None


# ------------------------------------------------------------------
# PR events
# ------------------------------------------------------------------

def test_parses_pr_opened(tmp_path, monkeypatch):
    payload = {"action": "opened", "pull_request": {"number": 42}}
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
    event = parse_event()
    assert event is not None
    assert event.pr_number == 42
    assert event.issue_number is None


def test_parses_pr_synchronize(tmp_path, monkeypatch):
    payload = {"action": "synchronize", "pull_request": {"number": 7}}
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
    event = parse_event()
    assert event is not None
    assert event.action == "synchronize"


def test_skips_pr_closed(tmp_path, monkeypatch):
    payload = {"action": "closed", "pull_request": {"number": 1}}
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")
    monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
    assert parse_event() is None


# ------------------------------------------------------------------
# Unsupported events
# ------------------------------------------------------------------

def test_skips_push_event(tmp_path, monkeypatch):
    payload = {"ref": "refs/heads/main"}
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, payload))
    assert parse_event() is None


def test_missing_token_exits(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issues")
    monkeypatch.setenv("GITHUB_EVENT_PATH", write_event(tmp_path, {}))
    with pytest.raises(SystemExit):
        parse_event()
