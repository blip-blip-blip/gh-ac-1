"""Tests for PRAggregator."""

import pytest
from unittest.mock import MagicMock

from agents.core.base_agent import AgentResult, AGENT_COMMENT_MARKER
from agents.core.github_client import GitHubPR
from agents.pr_review.aggregator import PRAggregator


def _ok(agent_type: str, data: dict) -> AgentResult:
    return AgentResult(agent_type=agent_type, success=True, data=data)


def _fail(agent_type: str) -> AgentResult:
    return AgentResult(agent_type=agent_type, success=False, data=None, error="timed out")


@pytest.fixture
def pr():
    return GitHubPR(
        number=10, title="Add auth", body="Fixes #3",
        head_branch="feat/auth", base_branch="main",
        diff="", changed_files=[], linked_issue=3,
    )


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def aggregator(client):
    return PRAggregator(client)


# ------------------------------------------------------------------
# Event determination
# ------------------------------------------------------------------

def test_no_findings_gives_approve(aggregator):
    assert aggregator._determine_event([]) == "APPROVE"


def test_critical_finding_gives_request_changes(aggregator):
    findings = [{"severity": "critical", "message": "SQL injection", "file": "db.py"}]
    assert aggregator._determine_event(findings) == "REQUEST_CHANGES"


def test_high_finding_gives_request_changes(aggregator):
    findings = [{"severity": "high", "message": "XSS", "file": "view.py"}]
    assert aggregator._determine_event(findings) == "REQUEST_CHANGES"


def test_medium_finding_gives_comment(aggregator):
    findings = [{"severity": "medium", "message": "missing test", "file": "foo.py"}]
    assert aggregator._determine_event(findings) == "COMMENT"


# ------------------------------------------------------------------
# Findings collection
# ------------------------------------------------------------------

def test_findings_sorted_by_severity(aggregator):
    results = {
        "security": _ok("security", {"findings": [
            {"severity": "low", "message": "a", "file": "x.py"},
            {"severity": "critical", "message": "b", "file": "y.py"},
        ]}),
    }
    findings = aggregator._collect_findings(results)
    assert findings[0]["severity"] == "critical"
    assert findings[1]["severity"] == "low"


def test_failed_agent_contributes_no_findings(aggregator):
    results = {"security": _fail("security")}
    assert aggregator._collect_findings(results) == []


# ------------------------------------------------------------------
# Comment building
# ------------------------------------------------------------------

def test_review_body_includes_marker(aggregator):
    body = aggregator._build_review_body({}, [])
    assert AGENT_COMMENT_MARKER in body


def test_review_body_notes_approve_when_no_findings(aggregator):
    body = aggregator._build_review_body({}, [])
    assert "No issues found" in body


def test_review_body_mentions_fix_prs(aggregator):
    findings = [{"severity": "high", "message": "SQL", "file": "db.py",
                 "fix_code": "safe_query()", "rule_id": "SEC-01", "_agent": "security"}]
    body = aggregator._build_review_body({}, findings)
    assert "fix PR" in body


def test_review_body_notes_failed_agents(aggregator):
    results = {"security": _fail("security")}
    body = aggregator._build_review_body(results, [])
    assert "security" in body


# ------------------------------------------------------------------
# run() submits review and triggers fix service
# ------------------------------------------------------------------

def test_run_submits_review(aggregator, client, pr):
    aggregator.run({}, pr)
    client.post_review.assert_called_once()


def test_run_calls_fix_service_for_fixable_findings(client, pr):
    fix_service = MagicMock()
    agg = PRAggregator(client, fix_service=fix_service)
    results = {
        "security": _ok("security", {"findings": [
            {"severity": "high", "message": "SQL", "file": "db.py",
             "fix_code": "safe()", "rule_id": "SEC-01"},
        ]}),
    }
    agg.run(results, pr)
    fix_service.run.assert_called_once()


def test_run_skips_fix_service_when_no_fix_code(client, pr):
    fix_service = MagicMock()
    agg = PRAggregator(client, fix_service=fix_service)
    results = {
        "security": _ok("security", {"findings": [
            {"severity": "high", "message": "SQL", "file": "db.py"},
        ]}),
    }
    agg.run(results, pr)
    fix_service.run.assert_not_called()
