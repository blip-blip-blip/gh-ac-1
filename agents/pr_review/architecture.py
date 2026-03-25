"""ArchitectureAgent — checks PR consistency with existing application design."""

import os
from pathlib import Path

from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.github_client import GitHubPR

SYSTEM_PROMPT = """You review pull request changes for architectural consistency.
You are given the application design documentation and the PR diff.
Check for:
- Changes that violate component boundaries (e.g. business logic in the API layer)
- Wrong dependencies between components
- Patterns that conflict with the documented design
- Code placed in the wrong module or package

Be conservative — only flag clear violations, not style preferences.

Return ONLY valid JSON:
{
  "findings": [
    {
      "severity": "<high|medium|low>",
      "file": "<path or null>",
      "message": "<explanation of the violation>"
    }
  ]
}
If no violations are found, return {"findings": []}."""

DESIGN_DOCS_PATH = Path("aidlc-docs/inception/application-design")


class ArchitectureAgent(BaseAgent):
    OUTPUT_SCHEMA = {"required": ["findings"]}

    def __init__(self, github_client) -> None:
        super().__init__("architecture", github_client)

    def execute(self, pr: GitHubPR, *_) -> AgentResult:
        design_context = _load_design_docs()
        system = self.build_system_prompt(SYSTEM_PROMPT)
        user = (
            f"Application Design Documentation:\n{design_context}\n\n"
            f"---\n\n"
            f"PR #{pr.number}: {pr.title}\n\n"
            f"Changed files: {', '.join(pr.changed_files)}\n\n"
            f"Diff:\n{pr.diff}"
        )
        data = self.call_model(system, user)
        if data is None:
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error="model call failed")
        if not isinstance(data.get("findings"), list):
            data["findings"] = []
        return AgentResult(agent_type=self.agent_type, success=True, data=data)


def _load_design_docs() -> str:
    """Load relevant application design docs as context."""
    files = [
        DESIGN_DOCS_PATH / "components.md",
        DESIGN_DOCS_PATH / "component-dependency.md",
    ]
    parts = []
    for f in files:
        if f.exists():
            parts.append(f.read_text(encoding="utf-8")[:3000])
    return "\n\n---\n\n".join(parts) or "(design docs not found)"
