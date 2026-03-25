"""Loads AI-DLC rule files and assembles agent-specific context strings."""

import os
from pathlib import Path

RULES_BASE_PATH = Path(os.environ.get("AIDLC_RULES_PATH", ".aidlc-rule-details"))

EXCERPT_MAX_CHARS = 2_000

RULE_MAP: dict[str, list[str]] = {
    "security": [
        "extensions/security/baseline/security-baseline.md",
    ],
    "classifier": [
        "common/overconfidence-prevention.md",
    ],
    "severity": [
        "common/overconfidence-prevention.md",
    ],
    "component": [
        "common/overconfidence-prevention.md",
    ],
    "reproduction": [
        "common/question-format-guide.md",
        "common/overconfidence-prevention.md",
    ],
    "duplicate": [
        "common/overconfidence-prevention.md",
    ],
    "architecture": [
        "common/depth-levels.md",
        "common/overconfidence-prevention.md",
    ],
    "requirements": [
        "common/overconfidence-prevention.md",
    ],
    "test_coverage": [
        "common/overconfidence-prevention.md",
    ],
}

# All agents receive the first excerpt of depth-levels.md
UNIVERSAL_RULES = ["common/depth-levels.md"]


class RuleLoader:
    def __init__(self, base_path: Path = RULES_BASE_PATH) -> None:
        self.base_path = base_path

    def load_for_agent(self, agent_type: str) -> str:
        """Return assembled rule context string for the given agent type."""
        sections: list[str] = []

        # Universal rules (excerpt only)
        for relative_path in UNIVERSAL_RULES:
            content = self._read_file(relative_path, excerpt=True)
            if content:
                sections.append(content)

        # Agent-specific rules
        for relative_path in RULE_MAP.get(agent_type, []):
            is_full = agent_type == "security" and "security-baseline" in relative_path
            content = self._read_file(relative_path, excerpt=not is_full)
            if content:
                sections.append(content)

        if not sections:
            return ""

        body = "\n\n---\n\n".join(sections)
        return f"# AI-DLC Rules Context\n\n{body}"

    def _read_file(self, relative_path: str, excerpt: bool = False) -> str | None:
        """Read a rule file. Returns None and logs a warning if the file is missing."""
        full_path = self.base_path / relative_path
        if not full_path.exists():
            print(f"[rule_loader] WARNING: Rule file not found: {full_path}")
            return None
        content = full_path.read_text(encoding="utf-8")
        if excerpt:
            content = content[:EXCERPT_MAX_CHARS]
        return content
