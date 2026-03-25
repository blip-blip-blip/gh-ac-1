"""Abstract base class for all AI-DLC agents."""

import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests

from .rule_loader import RuleLoader

GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"
AGENT_COMMENT_MARKER = "<!-- ai-dlc-agent -->"
MAX_RETRIES = 3
# Rough estimate: 1 token ≈ 4 characters
CHARS_PER_TOKEN = 4


@dataclass
class AgentResult:
    agent_type: str
    success: bool
    data: dict | None
    error: str | None = None
    truncated: bool = False


class BaseAgent(ABC):
    OUTPUT_SCHEMA: dict = {}  # Override in subclasses

    def __init__(self, agent_type: str, github_client) -> None:
        self.agent_type = agent_type
        self.github_client = github_client
        self.rule_loader = RuleLoader()
        self.token = os.environ["GITHUB_TOKEN"]
        self.model = os.environ.get("GITHUB_MODEL", "gpt-4o")
        self.max_input_tokens = int(os.environ.get("MAX_INPUT_TOKENS", "8000"))
        self.max_output_tokens = int(os.environ.get("MAX_OUTPUT_TOKENS", "1000"))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, *args, **kwargs) -> AgentResult:
        """Entry point for all agents. Wraps execute() with error handling."""
        try:
            return self.execute(*args, **kwargs)
        except Exception as e:
            print(f"[{self.agent_type}] ERROR: Unhandled exception: {e}")
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error=str(e))

    @abstractmethod
    def execute(self, *args, **kwargs) -> AgentResult:
        """Subclasses implement their specific logic here."""

    # ------------------------------------------------------------------
    # AI call
    # ------------------------------------------------------------------

    def call_model(self, system_prompt: str, user_prompt: str) -> dict | None:
        """Call GitHub Models API. Returns parsed JSON or None on failure."""
        user_prompt, truncated = self._apply_token_budget(user_prompt)
        if truncated:
            print(f"[{self.agent_type}] WARNING: Input truncated to "
                  f"{self.max_input_tokens} tokens")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }

        for attempt in range(1, MAX_RETRIES + 1):
            result = self._call_api(payload)
            if result is None:
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
                continue
            validated = self._validate_output(result)
            if validated is not None:
                return validated
            print(f"[{self.agent_type}] WARNING: Schema validation failed on "
                  f"attempt {attempt}, retrying")
            if attempt < MAX_RETRIES:
                time.sleep(2 ** attempt)

        print(f"[{self.agent_type}] WARNING: Failed after {MAX_RETRIES} attempts")
        return None

    def build_system_prompt(self, extra: str = "") -> str:
        """Assemble full system prompt including AI-DLC rules."""
        rules = self.rule_loader.load_for_agent(self.agent_type)
        parts = [p for p in [rules, extra] if p]
        return "\n\n".join(parts) if parts else ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_api(self, payload: dict) -> dict | None:
        try:
            r = requests.post(
                GITHUB_MODELS_URL,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
            if r.status_code == 200:
                data = r.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
            print(f"[{self.agent_type}] WARNING: Models API returned "
                  f"HTTP {r.status_code}: {r.text[:200]}")
            return None
        except (requests.RequestException, json.JSONDecodeError, KeyError) as e:
            print(f"[{self.agent_type}] WARNING: API call error: {e}")
            return None

    def _validate_output(self, data: dict) -> dict | None:
        """Validate output against OUTPUT_SCHEMA. Returns data if valid, None if not."""
        if not self.OUTPUT_SCHEMA:
            return data
        required = self.OUTPUT_SCHEMA.get("required", [])
        for field in required:
            if field not in data:
                print(f"[{self.agent_type}] WARNING: Missing required field '{field}' "
                      f"in output")
                return None
        return data

    def _apply_token_budget(self, text: str) -> tuple[str, bool]:
        """Truncate text to fit within token budget. Returns (text, was_truncated)."""
        max_chars = self.max_input_tokens * CHARS_PER_TOKEN
        if len(text) <= max_chars:
            return text, False
        original_len = len(text)
        truncated = text[:max_chars]
        print(f"[{self.agent_type}] WARNING: Input truncated from "
              f"~{original_len // CHARS_PER_TOKEN} to {self.max_input_tokens} tokens")
        return truncated, True
