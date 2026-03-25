# Units of Work
**Date**: 2026-03-24

---

## Overview

The system is decomposed into 5 units of work, each as an independent Python package under `agents/`. Units 2 and 3 are built in parallel after Unit 1 is complete.

```
Build sequence:

[Unit 1 — Core Infrastructure]          <- build first, alone
          |
    +-----+-----+
    |           |
[Unit 2]    [Unit 3]                     <- build in parallel
Issue        PR Review
Triage
    |           |
    +-----+-----+
          |
    [Unit 4 — Auto-Fix]                  <- build after 2 and 3
          |
    [Unit 5 — Reporting]                 <- build last
```

---

## Unit Definitions

### Unit 1 — Core Infrastructure
**Package**: `agents/core/`
**Built**: First, alone — all other units depend on it
**GitHub Actions workflow**: None (library only)

**Responsibilities**:
- GitHub Actions event parsing and routing (Orchestrator)
- Shared base class for all agents (BaseAgent)
- All GitHub REST API calls (GitHubClient)
- AI-DLC rule loading and agent context assembly (RuleLoader)

**Components**:
- `orchestrator.py` — entry point, event routing
- `base_agent.py` — abstract base for all agents
- `github_client.py` — GitHub API wrapper
- `rule_loader.py` — rule file loader with static agent mapping

**Package structure**:
```
agents/core/
+-- __init__.py
+-- orchestrator.py
+-- base_agent.py
+-- github_client.py
+-- rule_loader.py
+-- requirements.txt       # requests, python-dotenv
+-- pyproject.toml
```

---

### Unit 2 — Issue Triage Pipeline
**Package**: `agents/issue_triage/`
**Built**: In parallel with Unit 3, after Unit 1
**GitHub Actions workflow**: `.github/workflows/issue-triage.yml`
**Trigger**: `issues.opened`, `issues.edited`

**Responsibilities**:
- Classify issue type (bug, feature, question, duplicate, enhancement)
- Assign severity (critical, high, medium, low)
- Map issue to affected codebase component
- Validate reproduction information, ask author for missing details
- Detect duplicate issues via AI comparison against last 50 open issues
- Aggregate all findings into labels + comment on the issue

**Components**:
- `classifier.py` — ClassifierAgent
- `severity.py` — SeverityAgent
- `component.py` — ComponentAgent
- `reproduction.py` — ReproductionAgent
- `duplicate.py` — DuplicateDetectorAgent
- `aggregator.py` — IssueAggregator
- `service.py` — IssueTriage orchestration (parallel execution)

**Package structure**:
```
agents/issue_triage/
+-- __init__.py
+-- service.py
+-- classifier.py
+-- severity.py
+-- component.py
+-- reproduction.py
+-- duplicate.py
+-- aggregator.py
+-- requirements.txt       # inherits core via local dependency
+-- pyproject.toml
```

---

### Unit 3 — PR Review Pipeline
**Package**: `agents/pr_review/`
**Built**: In parallel with Unit 2, after Unit 1
**GitHub Actions workflow**: `.github/workflows/pr-review.yml`
**Trigger**: `pull_request.opened`, `pull_request.synchronize`

**Responsibilities**:
- Enforce AI-DLC security baseline rules (SECURITY-01–15) against PR diff
- Check PR consistency with existing application design
- Validate PR resolves its linked issue
- Verify test coverage for changed code
- Generate fix_code for unambiguous findings (passed to Unit 4)
- Aggregate all findings into a GitHub review (APPROVE / REQUEST_CHANGES / COMMENT)

**Components**:
- `security.py` — SecurityAgent (uses full security-baseline.md)
- `architecture.py` — ArchitectureAgent
- `requirements.py` — RequirementsAgent
- `test_coverage.py` — TestCoverageAgent
- `aggregator.py` — PRAggregator
- `service.py` — PRReview orchestration (parallel execution)

**Package structure**:
```
agents/pr_review/
+-- __init__.py
+-- service.py
+-- security.py
+-- architecture.py
+-- requirements.py
+-- test_coverage.py
+-- aggregator.py
+-- requirements.txt
+-- pyproject.toml
```

---

### Unit 4 — Auto-Fix Pipeline
**Package**: `agents/fix/`
**Built**: After Units 2 and 3 are complete
**GitHub Actions workflow**: None (called by PR review agents)

**Responsibilities**:
- Receive a finding + fix_code from any review agent
- Create a fix branch off the original PR branch
- Commit the fix to the fix branch
- Open a fix PR targeting the original PR branch
- Post a comment on the original PR linking to the fix PR
- Shared and reusable by any current or future agent that produces fix_code

**Components**:
- `fix_agent.py` — core fix logic (branch, commit, PR)
- `fix_service.py` — orchestrates fix_agent for a list of findings

**Package structure**:
```
agents/fix/
+-- __init__.py
+-- fix_agent.py
+-- fix_service.py
+-- requirements.txt
+-- pyproject.toml
```

---

### Unit 5 — Cross-Reference & Trend Reporting
**Package**: `agents/reporting/`
**Built**: Last, after all other units complete
**GitHub Actions workflow**: `.github/workflows/trend-report.yml`
**Trigger**: Weekly cron — every Monday 09:00 UTC

**Responsibilities**:
- Validate that a PR description correctly references and resolves its linked issue (Issue↔PR Linker)
- Aggregate agent findings from the past 7 days via GitHub API
- Generate weekly trend report as a new GitHub Issue
- Commit updated `TREND-REPORT.md` to the repo default branch

**Components**:
- `linker.py` — Issue↔PR cross-reference validator
- `trend_reporter.py` — weekly aggregation and report generation
- `service.py` — Reporting service orchestration

**Package structure**:
```
agents/reporting/
+-- __init__.py
+-- service.py
+-- linker.py
+-- trend_reporter.py
+-- requirements.txt
+-- pyproject.toml
```

---

## Full Project Structure

```
gh-ac-1/
+-- .github/
|   +-- workflows/
|   |   +-- issue-triage.yml        # Unit 2 trigger
|   |   +-- pr-review.yml           # Unit 3 trigger
|   |   +-- trend-report.yml        # Unit 5 trigger (weekly cron)
|   +-- copilot-instructions.md
+-- agents/
|   +-- core/                       # Unit 1
|   |   +-- __init__.py
|   |   +-- orchestrator.py
|   |   +-- base_agent.py
|   |   +-- github_client.py
|   |   +-- rule_loader.py
|   |   +-- requirements.txt
|   |   +-- pyproject.toml
|   +-- issue_triage/               # Unit 2
|   |   +-- __init__.py
|   |   +-- service.py
|   |   +-- classifier.py
|   |   +-- severity.py
|   |   +-- component.py
|   |   +-- reproduction.py
|   |   +-- duplicate.py
|   |   +-- aggregator.py
|   |   +-- requirements.txt
|   |   +-- pyproject.toml
|   +-- pr_review/                  # Unit 3
|   |   +-- __init__.py
|   |   +-- service.py
|   |   +-- security.py
|   |   +-- architecture.py
|   |   +-- requirements.py
|   |   +-- test_coverage.py
|   |   +-- aggregator.py
|   |   +-- requirements.txt
|   |   +-- pyproject.toml
|   +-- fix/                        # Unit 4
|   |   +-- __init__.py
|   |   +-- fix_agent.py
|   |   +-- fix_service.py
|   |   +-- requirements.txt
|   |   +-- pyproject.toml
|   +-- reporting/                  # Unit 5
|       +-- __init__.py
|       +-- service.py
|       +-- linker.py
|       +-- trend_reporter.py
|       +-- requirements.txt
|       +-- pyproject.toml
+-- infra/
|   +-- terraform/
|   +-- cloudformation/
+-- .aidlc-rule-details/
+-- aidlc-docs/
+-- requirements.txt                # top-level dev deps (pytest, etc.)
+-- TREND-REPORT.md
+-- README.md
```
