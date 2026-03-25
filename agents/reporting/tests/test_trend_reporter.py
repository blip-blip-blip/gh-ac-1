"""Tests for TrendReporter."""

import pytest
from agents.reporting.linker import CommentData
from agents.reporting.trend_reporter import TrendReporter
from agents.core.base_agent import AGENT_COMMENT_MARKER


def _issue_comment(issue_type: str = "bug", severities: list | None = None) -> CommentData:
    cd = CommentData("issue", 1, AGENT_COMMENT_MARKER)
    cd.issue_type = issue_type
    cd.severities = severities or ["high"]
    return cd


def _pr_comment(findings: int = 2, fix_prs: int = 1,
                rules: list | None = None) -> CommentData:
    cd = CommentData("pr", 2, AGENT_COMMENT_MARKER)
    cd.findings_count = findings
    cd.fix_pr_count = fix_prs
    cd.rules_violated = rules or ["SEC-01"]
    return cd


@pytest.fixture
def reporter():
    return TrendReporter()


def test_report_includes_repo_name(reporter):
    report = reporter.build([], "owner/repo")
    assert "owner/repo" in report


def test_report_includes_date_header(reporter):
    report = reporter.build([], "owner/repo")
    assert "Weekly Trend Report" in report


def test_report_no_issues_shows_placeholder(reporter):
    report = reporter.build([], "owner/repo")
    assert "No issues triaged this week" in report


def test_report_no_prs_shows_placeholder(reporter):
    report = reporter.build([], "owner/repo")
    assert "No PRs reviewed this week" in report


def test_report_counts_issues_by_type(reporter):
    comments = [_issue_comment("bug"), _issue_comment("bug"), _issue_comment("feature")]
    report = reporter.build(comments, "owner/repo")
    assert "Bug" in report
    assert "Feature" in report


def test_report_counts_pr_findings(reporter):
    comments = [_pr_comment(findings=3), _pr_comment(findings=1)]
    report = reporter.build(comments, "owner/repo")
    assert "4" in report  # total findings


def test_report_includes_fix_pr_count(reporter):
    comments = [_pr_comment(fix_prs=2)]
    report = reporter.build(comments, "owner/repo")
    assert "2" in report


def test_report_includes_top_rules(reporter):
    comments = [_pr_comment(rules=["SEC-01", "SEC-02"]), _pr_comment(rules=["SEC-01"])]
    report = reporter.build(comments, "owner/repo")
    assert "SEC-01" in report


def test_report_omits_rules_section_when_no_violations(reporter):
    comments = [_pr_comment(rules=[])]
    report = reporter.build(comments, "owner/repo")
    assert "Rule Violations" not in report


def test_report_ends_with_generated_note(reporter):
    report = reporter.build([], "owner/repo")
    assert "AI-DLC GitHub Agent" in report
