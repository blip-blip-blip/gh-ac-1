"""TestCoverageAgent — checks that changed code has corresponding tests."""

from agents.core.base_agent import BaseAgent, AgentResult
from agents.core.github_client import GitHubPR

SYSTEM_PROMPT = """You review pull request changes for test coverage gaps.
Analyze the diff and list of changed files.
For each source file that was changed:
- Check if there is a corresponding test file change in the diff
- If a source file has new functions/methods but no corresponding test changes, flag it
- If the fix is straightforward (e.g. a new function), provide fix_code with a test stub

Only flag files where test coverage is clearly missing, not files that are inherently untestable
(config files, migrations, type stubs, __init__.py).

Return ONLY valid JSON:
{
  "findings": [
    {
      "file": "<source file path>",
      "missing_test": "<description of what test is missing>",
      "fix_code": "<test stub code or null>"
    }
  ]
}
If all changed files have adequate test coverage, return {"findings": []}."""

# File patterns that don't need test coverage
SKIP_PATTERNS = {
    "__init__.py", "pyproject.toml", "requirements.txt",
    ".yml", ".yaml", ".toml", ".cfg", ".ini", ".md",
}


class TestCoverageAgent(BaseAgent):
    OUTPUT_SCHEMA = {"required": ["findings"]}

    def __init__(self, github_client) -> None:
        super().__init__("test_coverage", github_client)

    def execute(self, pr: GitHubPR, *_) -> AgentResult:
        testable_files = [
            f for f in pr.changed_files
            if not any(f.endswith(p) or f == p for p in SKIP_PATTERNS)
            and "test" not in f.lower()
        ]

        if not testable_files:
            return AgentResult(
                agent_type=self.agent_type, success=True,
                data={"findings": []}
            )

        system = self.build_system_prompt(SYSTEM_PROMPT)
        user = (
            f"PR #{pr.number}: {pr.title}\n\n"
            f"Source files changed (excluding test files):\n"
            + "\n".join(f"- {f}" for f in testable_files)
            + f"\n\nAll changed files: {', '.join(pr.changed_files)}\n\n"
            f"Diff:\n{pr.diff}"
        )
        data = self.call_model(system, user)
        if data is None:
            return AgentResult(agent_type=self.agent_type, success=False,
                               data=None, error="model call failed")
        if not isinstance(data.get("findings"), list):
            data["findings"] = []
        return AgentResult(agent_type=self.agent_type, success=True, data=data)
