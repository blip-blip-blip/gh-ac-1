# Components

## Core Infrastructure

### Orchestrator
**Purpose**: Entry point for all GitHub events. Parses the webhook payload, determines event type, and routes to the appropriate service.

**Responsibilities**:
- Parse GitHub Actions event payload (issue or PR)
- Determine event type (issue opened/edited, PR opened/synchronised)
- Invoke the correct service (IssueTriage or PRReview)
- Handle top-level errors and log to stdout (visible in Actions logs)

---

### BaseAgent
**Purpose**: Abstract base class all agents extend. Provides shared AI call logic, rule loading, retry, and JSON output validation.

**Responsibilities**:
- Call GitHub Models API with system + user prompt
- Delegate to RuleLoader to build system context per agent type
- Validate structured JSON output from model
- Retry failed AI calls (up to 3 attempts with backoff)
- Enforce output schema compliance before returning to caller

---

### GitHubClient
**Purpose**: Single wrapper for all GitHub REST API interactions. All agents and services call this — nothing calls the GitHub API directly.

**Responsibilities**:
- Post comments on issues and PRs
- Apply and remove labels on issues
- Fetch issue details and list recent issues
- Fetch PR diff and changed file list
- Create branches from a ref
- Commit file changes to a branch
- Open pull requests
- Submit PR reviews (APPROVE / REQUEST_CHANGES / COMMENT)

---

### RuleLoader
**Purpose**: Loads AI-DLC rule files from `.aidlc-rule-details/` and builds agent-specific context strings via a static mapping.

**Responsibilities**:
- Maintain static mapping of agent type → relevant rule files
- Read rule files from disk
- Assemble and return context string for injection into agent system prompt

**Static mapping**:
| Agent Type | Rule Files Loaded |
|---|---|
| security | `extensions/security/baseline/security-baseline.md` (full) |
| classifier | `common/overconfidence-prevention.md` (excerpt) |
| severity | `common/overconfidence-prevention.md` (excerpt) |
| component | `common/overconfidence-prevention.md` (excerpt) |
| reproduction | `common/question-format-guide.md` (excerpt), `common/overconfidence-prevention.md` (excerpt) |
| duplicate | `common/overconfidence-prevention.md` (excerpt) |
| architecture | `common/depth-levels.md` (excerpt), `common/overconfidence-prevention.md` (excerpt) |
| requirements | `common/overconfidence-prevention.md` (excerpt) |
| test_coverage | `common/overconfidence-prevention.md` (excerpt) |
| all agents | `common/depth-levels.md` (3 paragraphs) |

---

## Issue Triage Agents

### ClassifierAgent
**Purpose**: Determines the type of a GitHub issue.
**Input**: Issue title, body
**Output**: `{type, confidence, rationale}` (JSON)
**Types**: `bug | feature | question | duplicate | enhancement`

---

### SeverityAgent
**Purpose**: Assigns a severity level to a GitHub issue.
**Input**: Issue title, body
**Output**: `{severity, rationale}` (JSON)
**Levels**: `critical | high | medium | low`

---

### ComponentAgent
**Purpose**: Maps an issue to the affected area(s) of the codebase.
**Input**: Issue title, body, repo file tree
**Output**: `{components, files, rationale}` (JSON)

---

### ReproductionAgent
**Purpose**: Validates whether an issue has sufficient information to be reproduced. Generates questions to ask the author if not.
**Input**: Issue title, body, issue type
**Output**: `{has_enough_info, missing, questions}` (JSON)
**Rule used**: `common/question-format-guide.md` (for question formatting)

---

### DuplicateDetectorAgent
**Purpose**: Detects whether a new issue is a duplicate of an existing one.
**Input**: Issue title, body, last 50 open issues (title + number + body excerpt)
**Output**: `{is_duplicate, duplicate_of, similarity_score, rationale}` (JSON)

---

### IssueAggregator
**Purpose**: Merges outputs from all 5 issue triage agents and produces the final GitHub output.
**Input**: Structured JSON results from all 5 agents
**Output**: Labels to apply, assignee to set, comment body to post

---

## PR Review Agents

### SecurityAgent
**Purpose**: Reviews PR diff against the 15 AI-DLC security baseline rules (SECURITY-01–15). Also generates fix code for unambiguous findings.
**Input**: PR diff, changed files
**Output**: `{findings: [{rule_id, severity, file, line, message, fix_code}]}` (JSON)
**Rule used**: `extensions/security/baseline/security-baseline.md` (full)
**Fix behaviour**: When `fix_code` is present, also creates a fix branch and fix PR via GitHubClient

---

### ArchitectureAgent
**Purpose**: Checks whether the PR changes are consistent with the existing design documented in `aidlc-docs/`.
**Input**: PR diff, `aidlc-docs/inception/application-design/components.md`
**Output**: `{findings: [{severity, file, message}]}` (JSON)

---

### RequirementsAgent
**Purpose**: Validates that the PR resolves the linked issue and does not introduce scope gaps.
**Input**: PR description, linked issue body, PR diff summary
**Output**: `{resolves_issue, gaps, rationale}` (JSON)

---

### TestCoverageAgent
**Purpose**: Checks that changed code has corresponding tests. Generates test stubs for unambiguous gaps.
**Input**: PR diff, changed files list
**Output**: `{findings: [{file, missing_test, fix_code}]}` (JSON)
**Fix behaviour**: When `fix_code` is present, also creates a fix branch and fix PR via GitHubClient

---

### PRAggregator
**Purpose**: Merges outputs from all 4 PR review agents and submits the final GitHub review.
**Input**: Structured JSON results from all 4 agents
**Output**: GitHub review submitted (APPROVE / REQUEST_CHANGES / COMMENT) + summary comment

---

## Reporting

### TrendReporter
**Purpose**: Weekly scheduled job that aggregates agent findings from the past 7 days and produces a trend report.
**Input**: GitHub API — all agent comments and labels from past 7 days
**Output**: New GitHub Issue (weekly report) + `TREND-REPORT.md` committed to repo
