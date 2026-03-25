# Component Methods

> Detailed business logic is defined in Functional Design (Construction phase).
> This document captures method signatures, inputs, outputs, and high-level purpose only.

---

## Orchestrator

```python
def run(event_payload: dict) -> None
    # Entry point. Parses payload, routes to service.

def parse_event(payload: dict) -> tuple[str, dict]
    # Returns (event_type, context)
    # event_type: "issue" | "pull_request"
    # context: relevant fields extracted from payload

def route_to_service(event_type: str, context: dict) -> None
    # Invokes IssueTriage or PRReview service based on event_type
```

---

## BaseAgent

```python
def __init__(agent_type: str, github_client: GitHubClient) -> None

def call_model(system_prompt: str, user_prompt: str) -> dict
    # Calls GitHub Models API, returns parsed JSON response
    # Raises on non-JSON or schema violation

def build_system_prompt() -> str
    # Calls RuleLoader, assembles final system prompt for this agent type

def validate_output(response: dict, schema: dict) -> dict
    # Validates response matches expected JSON schema
    # Raises ValueError on mismatch

def retry(fn: callable, max_attempts: int = 3) -> any
    # Retries fn with exponential backoff on failure
```

---

## GitHubClient

```python
def __init__(token: str, repo: str) -> None

# Issues
def get_issue(number: int) -> dict
def list_issues(state: str = "open", limit: int = 50) -> list[dict]
def post_comment(issue_number: int, body: str) -> None
def apply_labels(issue_number: int, labels: list[str]) -> None
def set_assignee(issue_number: int, assignee: str) -> None

# Pull Requests
def get_pr(number: int) -> dict
def get_pr_diff(number: int) -> str
def get_pr_files(number: int) -> list[dict]
def post_review(pr_number: int, body: str, event: str) -> None
    # event: "APPROVE" | "REQUEST_CHANGES" | "COMMENT"

# Fix pipeline
def get_default_branch() -> str
def create_branch(name: str, from_ref: str) -> None
def commit_file(branch: str, path: str, content: str, message: str) -> None
def create_pr(title: str, body: str, head: str, base: str) -> int
    # Returns new PR number
```

---

## RuleLoader

```python
def __init__(rules_base_path: str = ".aidlc-rule-details") -> None

def load_for_agent(agent_type: str) -> str
    # Returns assembled context string for the given agent type
    # Uses static mapping to determine which files to load

def read_file(relative_path: str) -> str
    # Reads a rule file, returns contents as string

def extract_excerpt(content: str, section: str) -> str
    # Extracts a named section from a markdown file
```

---

## Issue Triage Agents

```python
# ClassifierAgent
def run(issue: dict) -> dict
    # Returns: {type: str, confidence: float, rationale: str}

# SeverityAgent
def run(issue: dict) -> dict
    # Returns: {severity: str, rationale: str}

# ComponentAgent
def run(issue: dict, file_tree: list[str]) -> dict
    # Returns: {components: list[str], files: list[str], rationale: str}

# ReproductionAgent
def run(issue: dict, issue_type: str) -> dict
    # Returns: {has_enough_info: bool, missing: list[str], questions: list[str]}

# DuplicateDetectorAgent
def run(issue: dict, existing_issues: list[dict]) -> dict
    # Returns: {is_duplicate: bool, duplicate_of: int|None, similarity_score: float, rationale: str}

# IssueAggregator
def run(results: dict[str, dict], issue_number: int) -> None
    # Merges all agent results, posts comment + applies labels via GitHubClient
def build_comment(results: dict) -> str
def determine_labels(results: dict) -> list[str]
```

---

## PR Review Agents

```python
# SecurityAgent
def run(pr: dict, diff: str, files: list[str]) -> dict
    # Returns: {findings: [{rule_id, severity, file, line, message, fix_code}]}
def create_fix_pr(finding: dict, pr: dict) -> int | None
    # Creates fix branch + commits fix_code + opens fix PR
    # Returns fix PR number or None if fix_code is absent

# ArchitectureAgent
def run(pr: dict, diff: str, design_docs: str) -> dict
    # Returns: {findings: [{severity, file, message}]}

# RequirementsAgent
def run(pr: dict, diff_summary: str, linked_issue: dict | None) -> dict
    # Returns: {resolves_issue: bool, gaps: list[str], rationale: str}

# TestCoverageAgent
def run(pr: dict, diff: str, files: list[str]) -> dict
    # Returns: {findings: [{file, missing_test, fix_code}]}
def create_fix_pr(finding: dict, pr: dict) -> int | None
    # Same pattern as SecurityAgent

# PRAggregator
def run(results: dict[str, dict], pr_number: int) -> None
    # Merges all agent results, submits GitHub review via GitHubClient
def determine_review_event(results: dict) -> str
    # Returns "APPROVE" | "REQUEST_CHANGES" | "COMMENT"
def build_review_body(results: dict) -> str
```

---

## TrendReporter

```python
def run(lookback_days: int = 7) -> None
    # Main entry — fetches data, aggregates, posts report

def fetch_agent_comments(since: datetime) -> list[dict]
    # Queries GitHub API for all comments posted by the agent bot in the window

def fetch_agent_labels(since: datetime) -> list[dict]
    # Queries closed/labelled issues and PRs in the window

def aggregate(comments: list[dict], labels: list[dict]) -> dict
    # Returns structured summary: findings by category, severity, file, agent

def post_report(summary: dict) -> None
    # Opens GitHub Issue with report body
    # Commits TREND-REPORT.md to repo default branch
```
