"""ReproductionAgent — validates whether a bug report has enough info to reproduce."""

from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.github_client import GitHubIssue

SYSTEM_PROMPT = """You validate whether a GitHub bug report contains enough information to reproduce the issue.
For reproduction, a bug report should include:
- Steps to reproduce
- Expected behavior
- Actual behavior / error message
- Environment details (OS, version, etc.)

If information is missing, generate clear, specific questions for the author.
Apply question format best practices: be specific, ask one thing per question.

Return ONLY valid JSON:
{
  "has_enough_info": <true|false>,
  "missing": ["<what is missing>", ...],
  "questions": ["<question for the author>", ...]
}
If has_enough_info is true, missing and questions should be empty arrays."""


class ReproductionAgent(BaseAgent):
    OUTPUT_SCHEMA = {"required": ["has_enough_info", "missing", "questions"]}

    def __init__(self, github_client) -> None:
        super().__init__("reproduction", github_client)

    def execute(self, issue: GitHubIssue, *_) -> AgentResult:
        system = self.build_system_prompt(SYSTEM_PROMPT)
        user = f"Title: {issue.title}\n\nBody:\n{issue.body or '(no body)'}"
        data = self.call_model(system, user)
        if data is None:
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error="model call failed")
        if not isinstance(data.get("missing"), list):
            data["missing"] = []
        if not isinstance(data.get("questions"), list):
            data["questions"] = []
        return AgentResult(agent_type=self.agent_type, success=True, data=data)
