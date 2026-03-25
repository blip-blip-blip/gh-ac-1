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
_FINDINGS_COUNT_RE = re.compile(r"\*\*Findings\*\*:\s*(\d+)\s*issue", re.IGNORECASE)
_FIX_PR_RE = re.compile(r"fix PR #(\d+)", re.IGNORECASE)
_RULE_RE = re.compile(r"\|\s*(?:🔴|🟠|🟡|🟢)\s*\w+\s*\|\s*\w+\s*\|\s*[^|]+\|\s*([^|]+)\|")


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

        self.severities = [m.lower() for m in _SEVERITY_RE.findall(body)]

        if m := _FINDINGS_COUNT_RE.search(body):
            self.findings_count = int(m.group(1))

        self.fix_pr_count = len(_FIX_PR_RE.findall(body))

        for m in _RULE_RE.finditer(body):
            rule_part = m.group(1).strip()
            # Extract rule_id: "SEC-01: message" → "SEC-01"
            if ":" in rule_part:
                self.rules_violated.append(rule_part.split(":")[0].strip())


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

            # Determine kind from context (issue vs PR comment)
            kind = "issue" if comment.get("pull_request_url") is None else "pr"
            number = comment.get("issue_number", 0)
            results.append(CommentData(kind, number, body))

        return results
