"""Entry point for all GitHub Actions workflows. Parses events and routes to services."""

import json
import os
import sys
from dataclasses import dataclass

SUPPORTED_ISSUE_ACTIONS = {"opened", "edited"}
SUPPORTED_PR_ACTIONS = {"opened", "synchronize"}


@dataclass
class GitHubEvent:
    event_name: str
    action: str
    repo: str
    issue_number: int | None
    pr_number: int | None
    payload: dict


def parse_event() -> GitHubEvent | None:
    """
    Read and parse the GitHub Actions event from environment variables.
    Returns None if the event is unsupported (already logged).
    """
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    if not event_path:
        print("[orchestrator] ERROR: GITHUB_EVENT_PATH not set")
        sys.exit(1)

    if not repo:
        print("[orchestrator] ERROR: GITHUB_REPOSITORY not set")
        sys.exit(1)

    if not os.environ.get("GITHUB_TOKEN"):
        print("[orchestrator] ERROR: GITHUB_TOKEN not set")
        sys.exit(1)

    with open(event_path, encoding="utf-8") as f:
        payload = json.load(f)

    action = payload.get("action", "")

    if event_name == "issues":
        if action not in SUPPORTED_ISSUE_ACTIONS:
            print(f"[orchestrator] WARNING: Unsupported issue action '{action}', skipping")
            return None
        return GitHubEvent(
            event_name=event_name,
            action=action,
            repo=repo,
            issue_number=payload["issue"]["number"],
            pr_number=None,
            payload=payload,
        )

    if event_name == "pull_request":
        if action not in SUPPORTED_PR_ACTIONS:
            print(f"[orchestrator] WARNING: Unsupported PR action '{action}', skipping")
            return None
        return GitHubEvent(
            event_name=event_name,
            action=action,
            repo=repo,
            issue_number=None,
            pr_number=payload["pull_request"]["number"],
            payload=payload,
        )

    print(f"[orchestrator] WARNING: Unsupported event type '{event_name}', skipping")
    return None
