"""Tests for IssueAggregator."""

import pytest
from unittest.mock import MagicMock

from agents.core.base_agent import AgentResult, AGENT_COMMENT_MARKER
from agents.issue_triage.aggregator import IssueAggregator


def _ok(agent_type: str, data: dict) -> AgentResult:
    return AgentResult(agent_type=agent_type, success=True, data=data)


def _fail(agent_type: str) -> AgentResult:
    return AgentResult(agent_type=agent_type, success=False, data=None, error="timed out")


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture
def aggregator(client):
    return IssueAggregator(client)


# ------------------------------------------------------------------
# Label determination
# ------------------------------------------------------------------

def test_bug_label_applied(aggregator):
    results = {
        "classifier": _ok("classifier", {"type": "bug", "confidence": 0.9, "rationale": ""}),
    }
    labels = aggregator._determine_labels(results)
    assert "aidlc: bug" in labels


def test_severity_label_applied(aggregator):
    results = {
        "severity": _ok("severity", {"severity": "critical", "rationale": ""}),
    }
    labels = aggregator._determine_labels(results)
    assert "aidlc: critical" in labels


def test_needs_info_label_when_info_missing(aggregator):
    results = {
        "reproduction": _ok("reproduction", {"has_enough_info": False, "questions": []}),
    }
    labels = aggregator._determine_labels(results)
    assert "aidlc: needs-info" in labels


def test_no_needs_info_label_when_info_sufficient(aggregator):
    results = {
        "reproduction": _ok("reproduction", {"has_enough_info": True, "questions": []}),
    }
    labels = aggregator._determine_labels(results)
    assert "aidlc: needs-info" not in labels


def test_no_labels_on_all_failures(aggregator):
    results = {"classifier": _fail("classifier"), "severity": _fail("severity")}
    assert aggregator._determine_labels(results) == []


# ------------------------------------------------------------------
# Comment building
# ------------------------------------------------------------------

def test_comment_includes_marker(aggregator):
    comment = aggregator._build_comment({})
    assert AGENT_COMMENT_MARKER in comment


def test_comment_includes_classifier_output(aggregator):
    results = {
        "classifier": _ok("classifier", {"type": "bug", "confidence": 0.9, "rationale": "crash"}),
    }
    comment = aggregator._build_comment(results)
    assert "Bug" in comment
    assert "90%" in comment


def test_comment_notes_failed_agents(aggregator):
    results = {"classifier": _fail("classifier")}
    comment = aggregator._build_comment(results)
    assert "classifier" in comment


def test_comment_includes_duplicate_reference(aggregator):
    results = {
        "duplicate": _ok("duplicate", {"is_duplicate": True, "duplicate_of": 7, "rationale": "same"}),
    }
    comment = aggregator._build_comment(results)
    assert "#7" in comment


# ------------------------------------------------------------------
# run() calls GitHub client
# ------------------------------------------------------------------

def test_run_posts_labels_and_comment(aggregator, client):
    results = {
        "classifier": _ok("classifier", {"type": "feature", "confidence": 0.8, "rationale": ""}),
    }
    aggregator.run(results, 1)
    client.apply_labels.assert_called_once()
    client.post_comment.assert_called_once()
