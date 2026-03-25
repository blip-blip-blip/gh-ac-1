# Domain Entities — Unit 1: Core Infrastructure

---

## AgentResult
Standardised output from any agent. Aggregators consume this.

```python
@dataclass
class AgentResult:
    agent_type: str           # "security" | "classifier" | "severity" | etc.
    success: bool             # False if agent returned None after retries
    data: dict | None         # Structured JSON output, None on failure
    error: str | None         # Error message if success=False
    truncated: bool           # True if input was truncated before AI call
```

---

## GitHubEvent
Parsed representation of an incoming GitHub Actions event.

```python
@dataclass
class GitHubEvent:
    event_name: str           # "issues" | "pull_request"
    action: str               # "opened" | "edited" | "synchronize"
    repo: str                 # "owner/repo"
    issue_number: int | None  # Set for issue events
    pr_number: int | None     # Set for PR events
    payload: dict             # Full raw event JSON
```

---

## GitHubIssue
Relevant fields extracted from GitHub issue API response.

```python
@dataclass
class GitHubIssue:
    number: int
    title: str
    body: str
    labels: list[str]
    state: str                # "open" | "closed"
    created_at: str
    user_login: str
```

---

## GitHubPR
Relevant fields extracted from GitHub pull request API response.

```python
@dataclass
class GitHubPR:
    number: int
    title: str
    body: str
    head_branch: str          # Source branch (where fix branches target)
    base_branch: str          # Target branch (usually main)
    diff: str                 # Full unified diff text
    changed_files: list[str]  # List of changed file paths
    linked_issue: int | None  # Parsed from body ("Fixes #123", "Closes #123")
```

---

## FindingWithFix
A single agent finding that includes an optional code fix.

```python
@dataclass
class FindingWithFix:
    agent_type: str
    rule_id: str | None       # e.g. "SECURITY-05", None for non-rule findings
    severity: str             # "critical" | "high" | "medium" | "low"
    file: str | None
    line: int | None
    message: str
    fix_code: str | None      # If present, fix pipeline creates a fix PR
```

---

## FixPRResult
Result of the fix pipeline creating a branch and PR.

```python
@dataclass
class FixPRResult:
    finding: FindingWithFix
    fix_branch: str           # e.g. "fix/SECURITY-05-pr-42"
    fix_pr_number: int | None # None if PR creation failed
    success: bool
    error: str | None
```
