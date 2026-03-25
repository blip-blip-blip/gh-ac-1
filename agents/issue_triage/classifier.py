"""ClassifierAgent — determines the type of a GitHub issue."""

from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.github_client import GitHubIssue

VALID_TYPES = {"bug", "feature", "question", "duplicate", "enhancement"}

SYSTEM_PROMPT = """You are a GitHub issue classifier for a software project.
Analyze the issue title and body and classify it into exactly one type:
- bug: unexpected behavior, crash, error, or something broken
- feature: request for new functionality that does not exist
- question: support request, how-to, or clarification needed
- duplicate: same problem as an existing issue (you may not know for certain — use when obvious)
- enhancement: improvement to existing functionality

Return ONLY valid JSON matching this schema:
{"type": "<type>", "confidence": <0.0-1.0>, "rationale": "<brief reason>"}"""


class ClassifierAgent(BaseAgent):
    OUTPUT_SCHEMA = {
        "required": ["type", "confidence", "rationale"],
    }

    def __init__(self, github_client) -> None:
        super().__init__("classifier", github_client)

    def execute(self, issue: GitHubIssue, *_) -> AgentResult:
        system = self.build_system_prompt(SYSTEM_PROMPT)
        user = f"Title: {issue.title}\n\nBody:\n{issue.body or '(no body)'}"
        data = self.call_model(system, user)
        if data is None:
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error="model call failed")
        if data.get("type") not in VALID_TYPES:
            data["type"] = "question"  # safe fallback
        return AgentResult(agent_type=self.agent_type, success=True, data=data)
