"""README Updater Service — entry point for the readme-update workflow."""

import base64
import json
import os
import sys

from agents.readme_updater.readme_agent import ReadmeAgent

README_PATH = "README.md"


def run() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[readme_updater] ERROR: GITHUB_TOKEN not set")
        sys.exit(1)

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    changed_files_raw = os.environ.get("CHANGED_FILES", "")

    if not changed_files_raw:
        print("[readme_updater] No changed files, skipping")
        sys.exit(0)

    changed_files = [f.strip() for f in changed_files_raw.split("\n") if f.strip()]

    # Infinite loop guard — skip if only README.md changed
    non_readme = [f for f in changed_files if f != README_PATH]
    if not non_readme:
        print("[readme_updater] Only README.md changed, skipping to avoid loop")
        sys.exit(0)

    agent = ReadmeAgent(token=token, repo=repo)

    # Read current README
    current_readme = agent._read_file(README_PATH) or ""
    if not current_readme:
        print("[readme_updater] Could not read README.md, skipping")
        sys.exit(0)

    print(f"[readme_updater] Processing {len(non_readme)} changed file(s)")
    updated = agent.run(non_readme, current_readme)

    if not updated:
        print("[readme_updater] Model returned nothing, skipping commit")
        sys.exit(0)

    if updated.strip() == current_readme.strip():
        print("[readme_updater] README unchanged, skipping commit")
        sys.exit(0)

    # Commit the updated README
    committed = _commit_readme(token, repo, updated)
    if committed:
        print("[readme_updater] README.md updated and committed")
    else:
        print("[readme_updater] WARNING: Failed to commit README.md")


def _commit_readme(token: str, repo: str, content: str) -> bool:
    import requests
    import time

    GITHUB_API_BASE = "https://api.github.com"
    encoded = base64.b64encode(content.encode()).decode()

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })

    # Get current SHA
    r = session.get(f"{GITHUB_API_BASE}/repos/{repo}/contents/{README_PATH}",
                    timeout=30)
    if r.status_code != 200:
        return False
    sha = r.json().get("sha")

    payload = {
        "message": "docs(readme): auto-update to reflect recent changes [skip readme]",
        "content": encoded,
        "sha": sha,
    }
    r = session.put(f"{GITHUB_API_BASE}/repos/{repo}/contents/{README_PATH}",
                    json=payload, timeout=30)
    return r.status_code in (200, 201)


if __name__ == "__main__":
    run()
