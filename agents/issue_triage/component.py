"""ComponentAgent — maps an issue to affected codebase areas."""

from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.github_client import GitHubIssue

SYSTEM_PROMPT = """You identify which components of a codebase are affected by a GitHub issue.
Based on the issue description and the repository file structure provided,
identify the relevant high-level components (e.g. "api", "auth", "database") and specific files.
If the issue is unclear or could affect multiple areas, list all plausible ones.

Return ONLY valid JSON:
{"components": ["<component>", ...], "files": ["<file_path>", ...], "rationale": "<brief reason>"}"""


class ComponentAgent(BaseAgent):
    OUTPUT_SCHEMA = {"required": ["components", "files", "rationale"]}

    def __init__(self, github_client) -> None:
        super().__init__("component", github_client)

    def execute(self, issue: GitHubIssue, file_tree: list[str] | None = None, *_) -> AgentResult:
        system = self.build_system_prompt(SYSTEM_PROMPT)
        tree_str = "\n".join(file_tree or []) or "(file tree unavailable)"
        user = (
            f"Title: {issue.title}\n\n"
            f"Body:\n{issue.body or '(no body)'}\n\n"
            f"Repository structure (top-level):\n{tree_str}"
        )
        data = self.call_model(system, user)
        if data is None:
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error="model call failed")
        if not isinstance(data.get("components"), list):
            data["components"] = []
        if not isinstance(data.get("files"), list):
            data["files"] = []
        return AgentResult(agent_type=self.agent_type, success=True, data=data)
