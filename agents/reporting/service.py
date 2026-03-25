"""Reporting Service — entry point for the trend-report GitHub Actions workflow."""

import os
import sys
from datetime import datetime, timezone

from agents.core.github_client import GitHubClient
from agents.reporting.linker import Linker
from agents.reporting.trend_reporter import TrendReporter

REPORT_FILE = "TREND-REPORT.md"


def run() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[reporting] ERROR: GITHUB_TOKEN not set")
        sys.exit(1)

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        print("[reporting] ERROR: GITHUB_REPOSITORY not set")
        sys.exit(1)

    client = GitHubClient(token=token, repo=repo)

    # Collect agent comments from the past 7 days
    linker = Linker(client)
    comments = linker.collect()
    print(f"[reporting] Collected {len(comments)} agent comment(s)")

    # Build the report
    reporter = TrendReporter()
    report_md = reporter.build(comments, repo)

    # Commit TREND-REPORT.md to the default branch
    now_label = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    commit_msg = f"docs(report): weekly trend report {now_label}"
    committed = client.commit_file(
        branch=_default_branch(client),
        path=REPORT_FILE,
        content=report_md,
        message=commit_msg,
    )
    if committed:
        print(f"[reporting] Committed {REPORT_FILE}")
    else:
        print(f"[reporting] WARNING: Could not commit {REPORT_FILE}")

    # Open a GitHub Issue with the report
    issue_title = f"AI-DLC Weekly Trend Report — {now_label}"
    issue_number = client.create_issue(
        title=issue_title,
        body=report_md,
        labels=["aidlc: report"],
    )
    if issue_number:
        print(f"[reporting] Opened trend report issue #{issue_number}")
    else:
        print("[reporting] WARNING: Could not open trend report issue")


def _default_branch(client: GitHubClient) -> str:
    """Return the repository's default branch name."""
    repo_info = client.get_repo_info()
    if repo_info:
        return repo_info.get("default_branch", "main")
    return "main"


if __name__ == "__main__":
    run()
