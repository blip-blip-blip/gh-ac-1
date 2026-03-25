"""Linker — fetches AI-DLC agent comments from the past week and parses them."""

import re
from datetime import datetime, timedelta, timezone

from agents.core.github_client import GitHubClient
from agents.core.base_agent import AGENT_COMMENT_MARKER

# Patterns used to extract structured fields from agent comment bodies
_ISSUE_TYPE_RE = re.compile(r"\*\*Type\*\*:\s*(\w+)", re.IGNORECASE)
_SEVERITY_RE = re.compile(
    r"(?:\*\*Severity\*\*:.*?)(critical|high|medium|low)", re.IGNORECASE
)
# Matches both "3 issue(s) found" (review body) and plain "3" (summary comment)
_FINDINGS_COUNT_RE = re.compile(r"\*\*Findings\*\*:\s*(\d+)", re.IGNORECASE)
_FIX_PR_RE = re.compile(r"fix PR #(\d+)", re.IGNORECASE)
# Matches rules from the findings table OR from the summary comment "**Rules**: SEC-01, SEC-07"
_RULE_TABLE_RE = re.compile(r"\|\s*(?:🔴|🟠|🟡|🟢)\s*\w+\s*\|\s*\w+\s*\|\s*[^|]+\|\s*([^|]+)\|")
_RULE_SUMMARY_RE = re.compile(r"\*\*Rules\*\*:\s*([^\n]+)", re.IGNORECASE)
# Matches severity counts from summary comment: "🔴 **Critical**: 2"
_SEVERITY_COUNT_RE = re.compile(
    r"(?:🔴|🟠|🟡|🟢)\s*\*\*(critical|high|medium|low)\*\*:\s*(\d+)", re.IGNORECASE
)


def _week_ago() -> str:
    """ISO-8601 timestamp for 7 days ago (UTC)."""
    dt = datetime.now(timezone.utc) - timedelta(days=7)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class CommentData:
    """Parsed data from a single agent comment."""

    def __init__(self, kind: str, number: int, body: str) -> None:
        self.kind = kind        # "issue" or "pr"
        self.number = number
        self.issue_type: str | None = None
        self.severities: list[str] = []
        self.findings_count: int = 0
        self.fix_pr_count: int = 0
        self.rules_violated: list[str] = []
        self._parse(body)

    def _parse(self, body: str) -> None:
        if m := _ISSUE_TYPE_RE.search(body):
            raw = m.group(1).lower()
            if raw in ("bug", "feature", "question", "duplicate", "enhancement"):
                self.issue_type = raw

        # Severity from triage comment ("**Severity**: 🟠 High")
        self.severities = [m.lower() for m in _SEVERITY_RE.findall(body)]
        # Severity counts from PR summary comment ("🔴 **Critical**: 2")
        for sev, count in _SEVERITY_COUNT_RE.findall(body):
            self.severities.extend([sev.lower()] * int(count))

        if m := _FINDINGS_COUNT_RE.search(body):
            self.findings_count = int(m.group(1))

        self.fix_pr_count = len(_FIX_PR_RE.findall(body))

        # Rules from findings table
        for m in _RULE_TABLE_RE.finditer(body):
            rule_part = m.group(1).strip()
            if ":" in rule_part:
                self.rules_violated.append(rule_part.split(":")[0].strip())
        # Rules from summary comment ("**Rules**: SEC-01, SEC-07")
        if m := _RULE_SUMMARY_RE.search(body):
            for rule in m.group(1).split(","):
                rule = rule.strip()
                if rule:
                    self.rules_violated.append(rule)


class Linker:
    """Fetches and parses all agent comments from the past 7 days."""

    def __init__(self, client: GitHubClient) -> None:
        self.client = client

    def collect(self) -> list[CommentData]:
        since = _week_ago()
        raw_comments = self.client.get_issue_comments(since=since)
        results: list[CommentData] = []

        for comment in raw_comments:
            body = comment.get("body", "")
            if AGENT_COMMENT_MARKER not in body:
                continue

            # html_url contains "/pull/" for PR comments, "/issues/" for issues
            html_url = comment.get("html_url", "")
            kind = "pr" if "/pull/" in html_url else "issue"

            # Extract number from issue_url: ".../issues/7" → 7
            issue_url = comment.get("issue_url", "")
            number = int(issue_url.rstrip("/").split("/")[-1]) if issue_url else 0

            results.append(CommentData(kind, number, body))

        return results
