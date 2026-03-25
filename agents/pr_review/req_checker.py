"""RequirementsAgent — validates that the PR resolves its linked issue."""

from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.github_client import GitHubPR, GitHubIssue

SYSTEM_PROMPT = """You validate that a pull request actually resolves the issue it claims to fix.
Analyze the PR description, the linked issue, and the diff summary.
Check:
- Does the PR address all aspects described in the issue?
- Are there requirements from the issue that are not covered by the changes?
- Does the PR do more than what was requested (scope creep)?

Return ONLY valid JSON:
{
  "resolves_issue": <true|false>,
  "gaps": ["<unaddressed requirement>", ...],
  "rationale": "<brief explanation>"
}
If no issue is linked, set resolves_issue to true and gaps to []."""


class RequirementsAgent(BaseAgent):
    OUTPUT_SCHEMA = {"required": ["resolves_issue", "gaps", "rationale"]}

    def __init__(self, github_client) -> None:
        super().__init__("requirements", github_client)

    def execute(self, pr: GitHubPR,
                linked_issue: GitHubIssue | None = None, *_) -> AgentResult:
        if linked_issue is None:
            return AgentResult(
                agent_type=self.agent_type, success=True,
                data={"resolves_issue": True, "gaps": [],
                      "rationale": "No linked issue found in PR description."}
            )

        system = self.build_system_prompt(SYSTEM_PROMPT)
        diff_summary = _summarise_diff(pr.diff)
        user = (
            f"Issue #{linked_issue.number}: {linked_issue.title}\n"
            f"Issue body:\n{linked_issue.body or '(no body)'}\n\n"
            f"PR #{pr.number}: {pr.title}\n"
            f"PR description:\n{pr.body or '(no description)'}\n\n"
            f"Changed files: {', '.join(pr.changed_files)}\n"
            f"Diff summary:\n{diff_summary}"
        )
        data = self.call_model(system, user)
        if data is None:
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error="model call failed")
        if not isinstance(data.get("gaps"), list):
            data["gaps"] = []
        return AgentResult(agent_type=self.agent_type, success=True, data=data)


def _summarise_diff(diff: str, max_chars: int = 2000) -> str:
    """Return first max_chars of the diff as a summary."""
    return diff[:max_chars] if diff else "(no diff)"
