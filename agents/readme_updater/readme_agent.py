"""ReadmeAgent — updates README.md sections based on what changed in a push."""

import os
import json
import requests
import time

GITHUB_API_BASE = "https://api.github.com"
MODELS_API = "https://models.inference.ai.azure.com/chat/completions"
MAX_RETRIES = 3

SYSTEM_PROMPT = """You are a technical documentation agent. Your job is to update a README.md
to reflect recent changes in a GitHub repository.

Rules:
- Only update sections that are directly affected by the changed files.
- Preserve all Mermaid diagrams exactly — do not modify diagram syntax.
- Preserve all existing headings and overall structure.
- Keep the tone concise and technical.
- If nothing in the README needs updating, return the README unchanged.
- Return ONLY the full updated README content — no explanation, no markdown fences around it."""


class ReadmeAgent:
    def __init__(self, token: str, repo: str) -> None:
        self.token = token
        self.repo = repo
        self.model = os.environ.get("GITHUB_MODEL", "gpt-4o")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def run(self, changed_files: list[str], current_readme: str) -> str | None:
        """Return updated README content, or None if the model call failed."""
        context = self._build_context(changed_files)
        if not context:
            print("[readme_updater] No relevant context found, skipping")
            return None

        user_prompt = (
            f"The following files changed in the latest push:\n"
            f"{chr(10).join(f'  - {f}' for f in changed_files)}\n\n"
            f"Context about the changed areas:\n{context}\n\n"
            f"Current README.md:\n{current_readme}\n\n"
            f"Return the updated README.md."
        )

        return self._call_model(SYSTEM_PROMPT, user_prompt)

    def _build_context(self, changed_files: list[str]) -> str:
        """Read relevant changed files to give the model real context."""
        snippets = []
        for path in changed_files:
            if not _is_relevant(path):
                continue
            content = self._read_file(path)
            if content:
                # Cap each file at 2000 chars to stay within token budget
                snippets.append(f"### {path}\n```\n{content[:2000]}\n```")
        return "\n\n".join(snippets)

    def _read_file(self, path: str) -> str | None:
        import base64
        data = self._gh_get(f"/repos/{self.repo}/contents/{path}")
        if data and data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode(errors="replace")
        return None

    def _gh_get(self, path: str) -> dict | None:
        url = f"{GITHUB_API_BASE}{path}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = self._session.get(url, timeout=30)
                if r.status_code == 200:
                    return r.json()
                if r.status_code >= 500:
                    time.sleep(2 ** attempt)
                else:
                    break
            except requests.RequestException:
                time.sleep(2 ** attempt)
        return None

    def _call_model(self, system: str, user: str) -> str | None:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": int(os.environ.get("MAX_OUTPUT_TOKENS", "2000")),
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = requests.post(MODELS_API, json=payload,
                                  headers=headers, timeout=60)
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"].strip()
                if r.status_code == 429:
                    wait = int(r.headers.get("Retry-After", 60))
                    print(f"[readme_updater] Rate limited, waiting {wait}s")
                    time.sleep(wait)
                elif r.status_code >= 500:
                    time.sleep(2 ** attempt)
                else:
                    print(f"[readme_updater] Model API error {r.status_code}: {r.text[:200]}")
                    return None
            except requests.RequestException as e:
                print(f"[readme_updater] Request error attempt {attempt}: {e}")
                time.sleep(2 ** attempt)
        return None


def _is_relevant(path: str) -> bool:
    """Only read files that are likely to affect README content."""
    relevant_prefixes = (
        "agents/",
        ".github/workflows/",
        "infra/",
    )
    skip_suffixes = (
        "/__init__.py",
        "/tests/",
        ".pyc",
    )
    if any(path.endswith(s) or f"/{s.strip('/')}" in path
           for s in skip_suffixes):
        return False
    return any(path.startswith(p) for p in relevant_prefixes)
