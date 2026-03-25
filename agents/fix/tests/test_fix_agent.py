"""Tests for FixAgent and FixService."""

import pytest
from unittest.mock import MagicMock, patch

from agents.core.github_client import GitHubPR
from agents.fix.fix_agent import FixAgent, _make_branch_name, _make_commit_message, _make_pr_title
from agents.fix.fix_service import FixService


@pytest.fixture
def client():
    c = MagicMock()
    c.create_branch.return_value = True
    c.commit_file.return_value = True
    c.create_pr.return_value = 99
    return c


@pytest.fixture
def pr():
    return GitHubPR(
        number=5, title="Fix auth", body="Fixes #1",
        head_branch="feat/auth", base_branch="main",
        diff="", changed_files=[], linked_issue=1,
    )


@pytest.fixture
def finding():
    return {
        "rule_id": "SEC-01",
        "severity": "high",
        "message": "SQL injection risk",
        "file": "app/db.py",
        "fix_code": "use_parameterized_query()",
    }


# ------------------------------------------------------------------
# FixAgent.run — happy path
# ------------------------------------------------------------------

def test_fix_agent_success(client, pr, finding):
    agent = FixAgent(client)
    result = agent.run(finding, pr)
    assert result.success is True
    assert result.fix_pr_number == 99


def test_fix_agent_creates_branch_off_pr_head(client, pr, finding):
    agent = FixAgent(client)
    agent.run(finding, pr)
    client.create_branch.assert_called_once()
    _, kwargs = client.create_branch.call_args
    # second positional arg is source branch
    args = client.create_branch.call_args[0]
    assert args[1] == pr.head_branch


def test_fix_agent_commits_to_fix_branch(client, pr, finding):
    agent = FixAgent(client)
    result = agent.run(finding, pr)
    client.commit_file.assert_called_once()
    args = client.commit_file.call_args[0]
    assert args[0] == result.fix_branch
    assert args[1] == finding["file"]
    assert args[2] == finding["fix_code"]


def test_fix_agent_posts_comment_on_original_pr(client, pr, finding):
    agent = FixAgent(client)
    agent.run(finding, pr)
    client.post_comment.assert_called_once()
    call_args = client.post_comment.call_args[0]
    assert call_args[0] == pr.number
    assert "99" in call_args[1]  # fix PR number in comment


# ------------------------------------------------------------------
# FixAgent.run — failure paths
# ------------------------------------------------------------------

def test_missing_fix_code_returns_failure(client, pr):
    agent = FixAgent(client)
    result = agent.run({"file": "app/db.py"}, pr)
    assert result.success is False
    assert "missing" in result.error


def test_missing_file_returns_failure(client, pr):
    agent = FixAgent(client)
    result = agent.run({"fix_code": "x()"}, pr)
    assert result.success is False


def test_branch_creation_failure_returns_failure(client, pr, finding):
    client.create_branch.return_value = False
    agent = FixAgent(client)
    result = agent.run(finding, pr)
    assert result.success is False
    assert "branch" in result.error


def test_commit_failure_returns_failure(client, pr, finding):
    client.commit_file.return_value = False
    agent = FixAgent(client)
    result = agent.run(finding, pr)
    assert result.success is False
    assert "commit" in result.error


def test_create_pr_failure_returns_failure(client, pr, finding):
    client.create_pr.return_value = None
    agent = FixAgent(client)
    result = agent.run(finding, pr)
    assert result.success is False
    assert "fix PR" in result.error


# ------------------------------------------------------------------
# Branch / commit message helpers
# ------------------------------------------------------------------

def test_branch_name_sanitises_special_chars():
    finding = {"rule_id": "SEC/01: test"}
    name = _make_branch_name(finding, 5)
    assert name.startswith("fix/")
    assert "/" not in name.replace("fix/", "", 1)


def test_branch_name_uses_pr_number():
    finding = {"rule_id": "SEC-01"}
    assert _make_branch_name(finding, 42).endswith("-pr-42")


def test_commit_message_includes_rule_and_message():
    finding = {"rule_id": "SEC-01", "message": "SQL injection"}
    msg = _make_commit_message(finding)
    assert "SEC-01" in msg
    assert "SQL injection" in msg


def test_pr_title_includes_pr_number():
    finding = {"rule_id": "SEC-01", "message": "SQL injection"}
    title = _make_pr_title(finding, 7)
    assert "PR #7" in title


# ------------------------------------------------------------------
# FixService
# ------------------------------------------------------------------

def test_fix_service_skips_findings_without_fix_code(client, pr):
    service = FixService(client)
    findings = [{"rule_id": "SEC-01", "severity": "high", "message": "x", "file": "f.py"}]
    results = service.run(findings, pr)
    assert results == []


def test_fix_service_runs_agent_for_each_fixable_finding(client, pr, finding):
    service = FixService(client)
    results = service.run([finding, finding], pr)
    assert len(results) == 2


def test_fix_service_continues_on_failure(client, pr, finding):
    client.create_pr.side_effect = [99, None]
    service = FixService(client)
    results = service.run([finding, finding], pr)
    assert len(results) == 2
    assert results[0].success is True
    assert results[1].success is False
