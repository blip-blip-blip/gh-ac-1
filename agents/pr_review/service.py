"""PR Review Service — entry point for the pr-review GitHub Actions workflow."""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, wait

from agents.core.orchestrator import parse_event
from agents.core.github_client import GitHubClient
from agents.pr_review.security import SecurityAgent
from agents.pr_review.architecture import ArchitectureAgent
from agents.pr_review.req_checker import RequirementsAgent
from agents.pr_review.test_coverage import TestCoverageAgent
from agents.pr_review.aggregator import PRAggregator


def run() -> None:
    event = parse_event()
    if event is None:
        sys.exit(0)

    if event.event_name != "pull_request" or event.pr_number is None:
        print("[pr_review] WARNING: Not a PR event, skipping")
        sys.exit(0)

    token = os.environ["GITHUB_TOKEN"]
    client = GitHubClient(token=token, repo=event.repo)

    pr = client.get_pr(event.pr_number)
    if pr is None:
        print(f"[pr_review] ERROR: Could not fetch PR #{event.pr_number}")
        sys.exit(1)

    # Fetch linked issue if referenced in PR body
    linked_issue = None
    if pr.linked_issue:
        linked_issue = client.get_issue(pr.linked_issue)

    # Try importing fix service (Unit 4) — optional, graceful if not installed
    fix_service = None
    try:
        from agents.fix.fix_service import FixService
        fix_service = FixService(client)
    except ImportError:
        print("[pr_review] INFO: fix package not installed, skipping auto-fix")

    agents_and_args = [
        (SecurityAgent(client), (pr,)),
        (ArchitectureAgent(client), (pr,)),
        (RequirementsAgent(client), (pr, linked_issue)),
        (TestCoverageAgent(client), (pr,)),
    ]

    def _staggered_submit(executor, agent, args, delay):
        time.sleep(delay)
        return executor.submit(agent.run, *args)

    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            _staggered_submit(executor, agent, args, i * 2): agent.agent_type
            for i, (agent, args) in enumerate(agents_and_args)
        }
        done, _ = wait(futures, timeout=240)
        for future in done:
            agent_type = futures[future]
            try:
                results[agent_type] = future.result()
            except Exception as e:
                print(f"[pr_review] ERROR: {agent_type} raised: {e}")

    # Fill timeouts
    for agent, _ in agents_and_args:
        if agent.agent_type not in results:
            from agents.core.base_agent import AgentResult
            results[agent.agent_type] = AgentResult(
                agent_type=agent.agent_type, success=False,
                data=None, error="timeout or unhandled error"
            )

    PRAggregator(client, fix_service).run(results, pr)
    print(f"[pr_review] Done — PR #{event.pr_number} reviewed")


if __name__ == "__main__":
    run()
