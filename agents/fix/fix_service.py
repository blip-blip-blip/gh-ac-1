"""FixService — orchestrates FixAgent for multiple findings from a PR review."""

from agents.core.github_client import GitHubClient, GitHubPR
from agents.fix.fix_agent import FixAgent, FixPRResult


class FixService:
    def __init__(self, github_client: GitHubClient) -> None:
        self.client = github_client
        self.agent = FixAgent(github_client)

    def run(self, findings: list[dict], pr: GitHubPR) -> list[FixPRResult]:
        """
        Create fix PRs for all findings that have fix_code.
        Failures are logged but do not raise — the review is already posted.
        """
        results: list[FixPRResult] = []
        for finding in findings:
            if not finding.get("fix_code"):
                continue
            result = self.agent.run(finding, pr)
            results.append(result)
            if result.success:
                print(f"[fix] Opened fix PR #{result.fix_pr_number} "
                      f"on branch {result.fix_branch}")
            else:
                print(f"[fix] WARNING: Fix PR failed for finding "
                      f"'{finding.get('rule_id', '?')}': {result.error}")
        return results
