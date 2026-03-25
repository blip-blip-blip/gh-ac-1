"""Tests for Linker."""

import pytest
from unittest.mock import MagicMock

from agents.core.base_agent import AGENT_COMMENT_MARKER
from agents.reporting.linker import Linker, CommentData


def _agent_comment(body_extra: str = "", pull_request_url: str | None = None,
                   issue_number: int = 1) -> dict:
    return {
        "body": f"{AGENT_COMMENT_MARKER}\n{body_extra}",
        "issue_number": issue_number,
        "pull_request_url": pull_request_url,
    }


@pytest.fixture
def client():
    return MagicMock()


def test_linker_skips_non_agent_comments(client):
    client.get_issue_comments.return_value = [
        {"body": "Just a regular comment", "issue_number": 1, "pull_request_url": None}
    ]
    linker = Linker(client)
    assert linker.collect() == []


def test_linker_returns_agent_comments(client):
    client.get_issue_comments.return_value = [_agent_comment()]
    linker = Linker(client)
    assert len(linker.collect()) == 1


def test_linker_marks_pr_comment_by_pull_request_url(client):
    client.get_issue_comments.return_value = [
        _agent_comment(pull_request_url="https://api.github.com/repos/x/y/pulls/3")
    ]
    linker = Linker(client)
    result = linker.collect()
    assert result[0].kind == "pr"


def test_linker_marks_issue_comment_when_no_pull_request_url(client):
    client.get_issue_comments.return_value = [_agent_comment()]
    linker = Linker(client)
    result = linker.collect()
    assert result[0].kind == "issue"


# ------------------------------------------------------------------
# CommentData parsing
# ------------------------------------------------------------------

def test_parses_issue_type():
    body = f"{AGENT_COMMENT_MARKER}\n**Type**: Bug (90% confidence)"
    cd = CommentData("issue", 1, body)
    assert cd.issue_type == "bug"


def test_parses_findings_count():
    body = f"{AGENT_COMMENT_MARKER}\n**Findings**: 3 issue(s) found"
    cd = CommentData("pr", 2, body)
    assert cd.findings_count == 3


def test_parses_fix_pr_references():
    body = f"{AGENT_COMMENT_MARKER}\n🔧 Opened fix PR #42 for: SQL injection"
    cd = CommentData("pr", 2, body)
    assert cd.fix_pr_count == 1


def test_unknown_issue_type_stays_none():
    body = f"{AGENT_COMMENT_MARKER}\n**Type**: Gibberish"
    cd = CommentData("issue", 1, body)
    assert cd.issue_type is None
