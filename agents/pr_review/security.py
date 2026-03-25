"""SecurityAgent — reviews PR diffs against AI-DLC security baseline rules."""

from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.github_client import GitHubPR

SYSTEM_PROMPT_SUFFIX = """
Review the pull request diff below against the security rules above.
For each violation found:
- Identify the specific rule ID (e.g. SECURITY-05)
- Specify severity: critical, high, medium, or low
- Specify the file and line number if determinable
- Write a clear message explaining the violation
- If the fix is unambiguous (e.g. parameterize a query, add a header), provide fix_code
  with the corrected code snippet. If the fix requires architectural judgement, set fix_code to null.

Return ONLY valid JSON:
{
  "findings": [
    {
      "rule_id": "<SECURITY-XX>",
      "severity": "<critical|high|medium|low>",
      "file": "<path or null>",
      "line": <number or null>,
      "message": "<explanation>",
      "fix_code": "<corrected code snippet or null>"
    }
  ]
}
If no violations are found, return {"findings": []}."""


class SecurityAgent(BaseAgent):
    OUTPUT_SCHEMA = {"required": ["findings"]}

    def __init__(self, github_client) -> None:
        super().__init__("security", github_client)

    def execute(self, pr: GitHubPR, *_) -> AgentResult:
        system = self.build_system_prompt(SYSTEM_PROMPT_SUFFIX)
        user = (
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
