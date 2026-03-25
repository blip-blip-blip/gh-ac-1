"""GitHub REST API wrapper. All GitHub API calls go through this class."""

import os
import time
from dataclasses import dataclass

import requests

GITHUB_API_BASE = "https://api.github.com"
MAX_RETRIES = 3


@dataclass
class GitHubIssue:
    number: int
    title: str
    body: str
    labels: list[str]
    state: str
    created_at: str
    user_login: str


@dataclass
class GitHubPR:
    number: int
    title: str
    body: str
    head_branch: str
    base_branch: str
    diff: str
    changed_files: list[str]
    linked_issue: int | None


class GitHubClient:
    def __init__(self, token: str, repo: str) -> None:
        self.repo = repo
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------

    def get_issue(self, number: int) -> GitHubIssue | None:
        data = self._get(f"/repos/{self.repo}/issues/{number}")
        if data is None:
            return None
        return GitHubIssue(
            number=data["number"],
            title=data["title"],
            body=data.get("body") or "",
            labels=[lbl["name"] for lbl in data.get("labels", [])],
            state=data["state"],
            created_at=data["created_at"],
            user_login=data["user"]["login"],
        )

    def list_issues(self, state: str = "open", limit: int = 50) -> list[GitHubIssue]:
        data = self._get(
            f"/repos/{self.repo}/issues",
            params={"state": state, "per_page": min(limit, 100)},
        )
        if data is None:
            return []
        return [
            GitHubIssue(
                number=item["number"],
                title=item["title"],
                body=item.get("body") or "",
                labels=[lbl["name"] for lbl in item.get("labels", [])],
                state=item["state"],
                created_at=item["created_at"],
                user_login=item["user"]["login"],
            )
            for item in data
            if "pull_request" not in item  # exclude PRs from issues endpoint
        ]

    def post_comment(self, issue_number: int, body: str) -> bool:
        result = self._post(
            f"/repos/{self.repo}/issues/{issue_number}/comments",
            json={"body": body},
        )
        return result is not None

    def apply_labels(self, issue_number: int, labels: list[str]) -> bool:
        result = self._post(
            f"/repos/{self.repo}/issues/{issue_number}/labels",
            json={"labels": labels},
        )
        return result is not None

    def set_assignee(self, issue_number: int, assignee: str) -> bool:
        result = self._post(
            f"/repos/{self.repo}/issues/{issue_number}/assignees",
            json={"assignees": [assignee]},
        )
        return result is not None

    # ------------------------------------------------------------------
    # Pull Requests
    # ------------------------------------------------------------------

    def get_pr(self, number: int) -> GitHubPR | None:
        data = self._get(f"/repos/{self.repo}/pulls/{number}")
        if data is None:
            return None
        diff = self._get_raw(f"/repos/{self.repo}/pulls/{number}",
                             headers={"Accept": "application/vnd.github.diff"})
        files_data = self._get(f"/repos/{self.repo}/pulls/{number}/files") or []
        changed_files = [f["filename"] for f in files_data]
        linked_issue = _parse_linked_issue(data.get("body") or "")
        return GitHubPR(
            number=data["number"],
            title=data["title"],
            body=data.get("body") or "",
            head_branch=data["head"]["ref"],
            base_branch=data["base"]["ref"],
            diff=diff or "",
            changed_files=changed_files,
            linked_issue=linked_issue,
        )

    def post_review(self, pr_number: int, body: str, event: str) -> bool:
        result = self._post(
            f"/repos/{self.repo}/pulls/{pr_number}/reviews",
            json={"body": body, "event": event},
        )
        return result is not None

    # ------------------------------------------------------------------
    # Fix pipeline
    # ------------------------------------------------------------------

    def get_repo_info(self) -> dict | None:
        return self._get(f"/repos/{self.repo}")

    def get_default_branch(self) -> str:
        return (self.get_repo_info() or {}).get("default_branch", "main")

    def create_issue(self, title: str, body: str,
                     labels: list[str] | None = None) -> int | None:
        payload: dict = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        data = self._post(f"/repos/{self.repo}/issues", json=payload)
        return data["number"] if data else None

    def create_branch(self, name: str, from_ref: str) -> bool:
        ref_data = self._get(f"/repos/{self.repo}/git/ref/heads/{from_ref}")
        if ref_data is None:
            return False
        sha = ref_data["object"]["sha"]
        result = self._post(
            f"/repos/{self.repo}/git/refs",
            json={"ref": f"refs/heads/{name}", "sha": sha},
        )
        return result is not None

    def commit_file(self, branch: str, path: str, content: str, message: str) -> bool:
        import base64
        encoded = base64.b64encode(content.encode()).decode()
        # Get current file SHA if it exists
        existing = self._get(f"/repos/{self.repo}/contents/{path}",
                             params={"ref": branch})
        payload: dict = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }
        if existing and "sha" in existing:
            payload["sha"] = existing["sha"]
        result = self._put(f"/repos/{self.repo}/contents/{path}", json=payload)
        return result is not None

    def create_pr(self, title: str, body: str, head: str, base: str) -> int | None:
        data = self._post(
            f"/repos/{self.repo}/pulls",
            json={"title": title, "body": body, "head": head, "base": base},
        )
        return data["number"] if data else None

    # ------------------------------------------------------------------
    # Internal HTTP helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: dict | None = None,
             headers: dict | None = None) -> dict | list | None:
        return self._request("GET", path, params=params, headers=headers)

    def _get_raw(self, path: str, headers: dict | None = None) -> str | None:
        url = f"{GITHUB_API_BASE}{path}"
        merged_headers = dict(self._session.headers)
        if headers:
            merged_headers.update(headers)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = requests.get(url, headers=merged_headers, timeout=30)
                if r.status_code == 200:
                    return r.text
                if r.status_code == 429:
                    time.sleep(int(r.headers.get("Retry-After", 60)))
                elif r.status_code >= 500:
                    time.sleep(2 ** attempt)
                else:
                    break
            except requests.RequestException as e:
                print(f"[github_client] WARNING: Request error on attempt {attempt}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
        return None

    def _post(self, path: str, json: dict | None = None) -> dict | None:
        return self._request("POST", path, json=json)

    def _put(self, path: str, json: dict | None = None) -> dict | None:
        return self._request("PUT", path, json=json)

    def _request(self, method: str, path: str, params: dict | None = None,
                 json: dict | None = None, headers: dict | None = None) -> dict | list | None:
        url = f"{GITHUB_API_BASE}{path}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = self._session.request(
                    method, url, params=params, json=json,
                    headers=headers, timeout=30,
                )
                if r.status_code in (200, 201, 204):
                    return r.json() if r.content else {}
                if r.status_code == 429:
                    wait = int(r.headers.get("Retry-After", 60))
                    print(f"[github_client] WARNING: Rate limited, waiting {wait}s")
                    time.sleep(wait)
                elif r.status_code >= 500:
                    wait = 2 ** attempt
                    print(f"[github_client] WARNING: Server error {r.status_code} "
                          f"on attempt {attempt}, retrying in {wait}s")
                    time.sleep(wait)
                else:
                    print(f"[github_client] WARNING: HTTP {r.status_code} for "
                          f"{method} {path}: {r.text[:200]}")
                    return None
            except requests.RequestException as e:
                print(f"[github_client] WARNING: Request error on attempt {attempt}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)

        print(f"[github_client] WARNING: {method} {path} failed after {MAX_RETRIES} attempts")
        return None


    def list_repo_contents(self, path: str = "") -> list[str]:
        """Return file paths at the given repo path (top-level by default)."""
        data = self._get(f"/repos/{self.repo}/contents/{path}")
        if not isinstance(data, list):
            return []
        return [item["path"] for item in data]

    def get_issue_comments(self, since: str | None = None) -> list[dict]:
        """Return all issue comments, optionally filtered by since (ISO 8601)."""
        params: dict = {"per_page": 100}
        if since:
            params["since"] = since
        return self._get(f"/repos/{self.repo}/issues/comments", params=params) or []


def _parse_linked_issue(body: str) -> int | None:
    """Extract issue number from PR body. Looks for 'Fixes #N', 'Closes #N', 'Resolves #N'."""
    import re
    pattern = r"(?:fixes|closes|resolves)\s+#(\d+)"
    match = re.search(pattern, body, re.IGNORECASE)
    return int(match.group(1)) if match else None
