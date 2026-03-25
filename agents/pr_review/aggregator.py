"""PRAggregator — merges review agent results into a GitHub review."""

from agents.core.base_agent import AgentResult, AGENT_COMMENT_MARKER
from agents.core.github_client import GitHubClient, GitHubPR

SEVERITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class PRAggregator:
    def __init__(self, github_client: GitHubClient, fix_service=None) -> None:
        self.client = github_client
        self.fix_service = fix_service  # injected from service.py (Unit 4)

    def run(self, results: dict[str, AgentResult], pr: GitHubPR) -> None:
        all_findings = self._collect_findings(results)
        event = self._determine_event(all_findings)
        body = self._build_review_body(results, all_findings)

        self.client.post_review(pr.number, body, event)
        print(f"[pr_review] Review submitted: {event} with "
              f"{len(all_findings)} finding(s)")

        # Trigger fix pipeline for findings that have fix_code
        if self.fix_service:
            fixable = [f for f in all_findings if f.get("fix_code")]
            if fixable:
                self.fix_service.run(fixable, pr)

    def _collect_findings(self, results: dict[str, AgentResult]) -> list[dict]:
        findings = []
        for agent_type in ("security", "architecture", "test_coverage"):
            data = _data(results, agent_type)
            if data:
                for f in data.get("findings", []):
                    f["_agent"] = agent_type
                    findings.append(f)
        return sorted(findings,
                      key=lambda f: SEVERITY_ORDER.get(f.get("severity", "low"), 3))

    def _determine_event(self, findings: list[dict]) -> str:
        if not findings:
            return "APPROVE"
        severities = {f.get("severity") for f in findings}
        if severities & {"critical", "high"}:
            return "REQUEST_CHANGES"
        return "COMMENT"

    def _build_review_body(self, results: dict[str, AgentResult],
                           findings: list[dict]) -> str:
        lines = [AGENT_COMMENT_MARKER, "## AI-DLC PR Review\n"]

        # Requirements check
        req = _data(results, "requirements")
        if req:
            if req.get("resolves_issue"):
                lines.append("**Requirements**: ✅ PR resolves linked issue")
            else:
                lines.append("**Requirements**: ❌ PR does not fully resolve linked issue")
                for gap in req.get("gaps", []):
                    lines.append(f"  - {gap}")
            lines.append(f"> {req.get('rationale', '')}\n")

        # Findings table
        if findings:
            lines.append(f"**Findings**: {len(findings)} issue(s) found\n")
            lines.append("| Severity | Agent | File | Message |")
            lines.append("|---|---|---|---|")
            for f in findings:
                emoji = SEVERITY_EMOJI.get(f.get("severity", "low"), "⚪")
                sev = f.get("severity", "low")
                agent = f.get("_agent", "unknown")
                file_ = f"`{f['file']}`" if f.get("file") else "—"
                msg = f.get("message", "").replace("|", "\\|")
                rule = f.get("rule_id", "")
                label = f"{rule}: {msg}" if rule else msg
                lines.append(f"| {emoji} {sev} | {agent} | {file_} | {label} |")
            lines.append("")

            # Fix PRs note
            fixable = [f for f in findings if f.get("fix_code")]
            if fixable:
                lines.append(f"🔧 {len(fixable)} automated fix PR(s) will be opened "
                             f"for unambiguous findings.\n")
        else:
            lines.append("**Findings**: ✅ No issues found\n")

        # Failed agents
        failed = [k for k, v in results.items() if not v.success]
        if failed:
            lines.append(f"\n⚠️ Note: {', '.join(failed)} agent(s) did not complete. "
                         f"See Actions log for details.")

        return "\n".join(lines)


def _data(results: dict[str, AgentResult], key: str) -> dict | None:
    r = results.get(key)
    return r.data if r and r.success and r.data else None
