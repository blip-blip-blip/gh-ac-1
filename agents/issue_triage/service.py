"""Issue Triage Service — entry point for the issue-triage GitHub Actions workflow."""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

from agents.core.orchestrator import parse_event
from agents.core.github_client import GitHubClient
from agents.issue_triage.classifier import ClassifierAgent
from agents.issue_triage.severity import SeverityAgent
from agents.issue_triage.component import ComponentAgent
from agents.issue_triage.reproduction import ReproductionAgent
from agents.issue_triage.duplicate import DuplicateDetectorAgent
from agents.issue_triage.aggregator import IssueAggregator


def run() -> None:
    event = parse_event()
    if event is None:
        sys.exit(0)

    if event.event_name != "issues" or event.issue_number is None:
        print("[issue_triage] WARNING: Not an issue event, skipping")
        sys.exit(0)

    token = os.environ["GITHUB_TOKEN"]
    client = GitHubClient(token=token, repo=event.repo)

    issue = client.get_issue(event.issue_number)
    if issue is None:
        print(f"[issue_triage] ERROR: Could not fetch issue #{event.issue_number}")
        sys.exit(1)

    existing_issues = client.list_issues(state="open", limit=50)
    file_tree = client.list_repo_contents()

    agents_and_args = [
        (ClassifierAgent(client), (issue,)),
        (SeverityAgent(client), (issue,)),
        (ComponentAgent(client), (issue, file_tree)),
        (ReproductionAgent(client), (issue,)),
        (DuplicateDetectorAgent(client), (issue, existing_issues)),
    ]

    results = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(agent.run, *args): agent.agent_type
            for agent, args in agents_and_args
        }
        done, _ = wait(futures, timeout=240)
        for future in done:
            agent_type = futures[future]
            try:
                results[agent_type] = future.result()
            except Exception as e:
                print(f"[issue_triage] ERROR: {agent_type} raised: {e}")

    # Fill in any agents that timed out or errored
    for agent, _ in agents_and_args:
        if agent.agent_type not in results:
            from agents.core.base_agent import AgentResult
            results[agent.agent_type] = AgentResult(
                agent_type=agent.agent_type, success=False,
                data=None, error="timeout or unhandled error"
            )

    IssueAggregator(client).run(results, event.issue_number)
    print(f"[issue_triage] Done — issue #{event.issue_number} triaged")


if __name__ == "__main__":
    run()
