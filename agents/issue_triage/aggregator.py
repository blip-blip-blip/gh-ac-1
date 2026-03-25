"""IssueAggregator — merges triage agent results into GitHub labels and a comment."""

from agents.core.base_agent import AgentResult, AGENT_COMMENT_MARKER
from agents.core.github_client import GitHubClient

LABEL_PREFIX = "aidlc"

TYPE_LABELS = {
    "bug": f"{LABEL_PREFIX}: bug",
    "feature": f"{LABEL_PREFIX}: feature",
    "question": f"{LABEL_PREFIX}: question",
    "duplicate": f"{LABEL_PREFIX}: duplicate",
    "enhancement": f"{LABEL_PREFIX}: enhancement",
}

SEVERITY_LABELS = {
    "critical": f"{LABEL_PREFIX}: critical",
    "high": f"{LABEL_PREFIX}: high",
    "medium": f"{LABEL_PREFIX}: medium",
    "low": f"{LABEL_PREFIX}: low",
}

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}


class IssueAggregator:
    def __init__(self, github_client: GitHubClient) -> None:
        self.client = github_client

    def run(self, results: dict[str, AgentResult], issue_number: int) -> None:
        labels = self._determine_labels(results)
        comment = self._build_comment(results)

        if labels:
            self.client.apply_labels(issue_number, labels)

        self.client.post_comment(issue_number, comment)

    def _determine_labels(self, results: dict[str, AgentResult]) -> list[str]:
        labels: list[str] = []

        classifier = _data(results, "classifier")
        if classifier:
            issue_type = classifier.get("type", "")
            if label := TYPE_LABELS.get(issue_type):
                labels.append(label)
            if classifier.get("type") == "duplicate":
                labels.append(f"{LABEL_PREFIX}: duplicate")

        severity = _data(results, "severity")
        if severity:
            sev = severity.get("severity", "")
            if label := SEVERITY_LABELS.get(sev):
                labels.append(label)

        reproduction = _data(results, "reproduction")
        if reproduction and not reproduction.get("has_enough_info", True):
            labels.append(f"{LABEL_PREFIX}: needs-info")

        return labels

    def _build_comment(self, results: dict[str, AgentResult]) -> str:
        lines = [f"{AGENT_COMMENT_MARKER}", "## AI-DLC Issue Triage\n"]

        # Classifier
        classifier = _data(results, "classifier")
        if classifier:
            issue_type = classifier.get("type", "unknown").capitalize()
            confidence = int(classifier.get("confidence", 0) * 100)
            lines.append(f"**Type**: {issue_type} ({confidence}% confidence)")
            lines.append(f"> {classifier.get('rationale', '')}\n")
        else:
            lines.append("**Type**: ⚠️ Classification unavailable\n")

        # Severity
        severity = _data(results, "severity")
        if severity:
            sev = severity.get("severity", "unknown")
            emoji = SEVERITY_EMOJI.get(sev, "⚪")
            lines.append(f"**Severity**: {emoji} {sev.capitalize()}")
            lines.append(f"> {severity.get('rationale', '')}\n")
        else:
            lines.append("**Severity**: ⚠️ Assessment unavailable\n")

        # Component
        component = _data(results, "component")
        if component:
            components = ", ".join(component.get("components", [])) or "unknown"
            lines.append(f"**Affected components**: `{components}`\n")

        # Reproduction
        reproduction = _data(results, "reproduction")
        if reproduction:
            if reproduction.get("has_enough_info"):
                lines.append("**Reproduction info**: ✅ Sufficient\n")
            else:
                lines.append("**Reproduction info**: ❓ Missing information\n")
                questions = reproduction.get("questions", [])
                if questions:
                    lines.append("To help us investigate, please provide:\n")
                    for q in questions:
                        lines.append(f"- {q}")
                    lines.append("")

        # Duplicate
        duplicate = _data(results, "duplicate")
        if duplicate and duplicate.get("is_duplicate"):
            dup_of = duplicate.get("duplicate_of")
            ref = f"#{dup_of}" if dup_of else "an existing issue"
            lines.append(f"**Possible duplicate**: This may be a duplicate of {ref}.")
            lines.append(f"> {duplicate.get('rationale', '')}\n")

        # Failed agents note
        failed = [k for k, v in results.items() if not v.success]
        if failed:
            lines.append(f"\n⚠️ Note: {', '.join(failed)} agent(s) did not complete. "
                         f"See Actions log for details.")

        return "\n".join(lines)


def _data(results: dict[str, AgentResult], key: str) -> dict | None:
    r = results.get(key)
    return r.data if r and r.success and r.data else None
