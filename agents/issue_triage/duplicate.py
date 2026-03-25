"""DuplicateDetectorAgent — detects if a new issue duplicates an existing one."""

from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.github_client import GitHubIssue

SYSTEM_PROMPT = """You detect duplicate GitHub issues.
Compare the new issue against a list of existing open issues.
A duplicate describes the same underlying problem, even if worded differently.
Consider: similar error messages, same steps to reproduce, same expected/actual behavior.
Be conservative — only flag as duplicate if you are confident (similarity_score >= 0.8).

Return ONLY valid JSON:
{
  "is_duplicate": <true|false>,
  "duplicate_of": <issue_number or null>,
  "similarity_score": <0.0-1.0>,
  "rationale": "<brief reason>"
}"""

MAX_EXISTING_ISSUES = 30  # keep prompt manageable


class DuplicateDetectorAgent(BaseAgent):
    OUTPUT_SCHEMA = {"required": ["is_duplicate", "similarity_score", "rationale"]}

    def __init__(self, github_client) -> None:
        super().__init__("duplicate", github_client)

    def execute(self, issue: GitHubIssue,
                existing_issues: list[GitHubIssue] | None = None, *_) -> AgentResult:
        system = self.build_system_prompt(SYSTEM_PROMPT)

        existing_str = _format_existing(existing_issues or [], issue.number)
        user = (
            f"New issue #{issue.number}: {issue.title}\n"
            f"Body: {issue.body or '(no body)'}\n\n"
            f"Existing open issues:\n{existing_str}"
        )
        data = self.call_model(system, user)
        if data is None:
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error="model call failed")
        if "duplicate_of" not in data:
            data["duplicate_of"] = None
        return AgentResult(agent_type=self.agent_type, success=True, data=data)


def _format_existing(issues: list[GitHubIssue], exclude: int) -> str:
    lines = []
    for i in issues[:MAX_EXISTING_ISSUES]:
        if i.number == exclude:
            continue
        body_preview = (i.body or "")[:200].replace("\n", " ")
        lines.append(f"#{i.number}: {i.title} — {body_preview}")
    return "\n".join(lines) or "(no existing issues)"
