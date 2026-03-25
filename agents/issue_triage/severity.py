"""SeverityAgent — assigns a severity level to a GitHub issue."""

from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.github_client import GitHubIssue

VALID_SEVERITIES = {"critical", "high", "medium", "low"}

SYSTEM_PROMPT = """You assess the severity of GitHub issues.
Severity levels:
- critical: system down, data loss, security breach, or blocks all users
- high: major feature broken, significant impact on many users, no workaround
- medium: feature partially broken, workaround available, moderate impact
- low: minor issue, cosmetic problem, affects few users, easy workaround

Return ONLY valid JSON:
{"severity": "<level>", "rationale": "<brief reason>"}"""


class SeverityAgent(BaseAgent):
    OUTPUT_SCHEMA = {"required": ["severity", "rationale"]}

    def __init__(self, github_client) -> None:
        super().__init__("severity", github_client)

    def execute(self, issue: GitHubIssue, *_) -> AgentResult:
        system = self.build_system_prompt(SYSTEM_PROMPT)
        user = f"Title: {issue.title}\n\nBody:\n{issue.body or '(no body)'}"
        data = self.call_model(system, user)
        if data is None:
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error="model call failed")
        if data.get("severity") not in VALID_SEVERITIES:
            data["severity"] = "medium"
        return AgentResult(agent_type=self.agent_type, success=True, data=data)
