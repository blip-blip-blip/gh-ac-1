# AI-DLC GitHub Agent — Workflow Plan
**Date**: 2026-03-24
**Status**: APPROVED

---

## Requirements Summary (derived from conversation)

| # | Requirement |
|---|---|
| R1 | Multi-agent system triggered by GitHub events |
| R2 | Orchestrator coordinates all sub-agents |
| R3 | PR Review pipeline — security, architecture, requirements, test coverage |
| R4 | Issue Triage pipeline — classify, severity, component, reproduction, duplicate detection |
| R5 | Cross-reference PRs to linked issues |
| R6 | GitHub Actions as the trigger and runtime |
| R7 | GitHub Models API via GITHUB_TOKEN as the AI provider (no extra secrets) |
| R8 | Re-use existing AI-DLC rules as agent context/prompts |
| R9 | Post findings as GitHub comments, labels, and review decisions |
| R10 | Security Baseline (SECURITY-01–15) enforced in PR review agent |

---

## AI-DLC Rules Reuse Map

| Rule File | Reused In |
|---|---|
| `.github/copilot-instructions.md` | Fed as system context to all agents reviewing this repo |
| `extensions/security/baseline/security-baseline.md` | Security Review Agent system prompt |
| `common/overconfidence-prevention.md` | All agent system prompts — prevents false positives |
| `common/error-handling.md` | Orchestrator retry and escalation logic |
| `common/content-validation.md` | Aggregator response validation before posting |
| `common/question-format-guide.md` | Reproduction Agent — asking authors for more info |
| `common/depth-levels.md` | Orchestrator — scales depth based on PR/issue complexity |

---

## Proposed Stage Execution Plan

### INCEPTION PHASE
| Stage | Execute | Reason |
|---|---|---|
| Workspace Detection | DONE | Greenfield confirmed |
| Reverse Engineering | SKIP | No existing app code |
| Requirements Analysis | DONE | Derived from conversation |
| User Stories | SKIP | Internal tool, no user personas needed |
| Workflow Planning | THIS DOCUMENT | |
| Application Design | YES | Two pipelines + orchestrator need component design |
| Units Generation | YES | 4 distinct units identified |

### CONSTRUCTION PHASE (per unit)
| Stage | Execute | Reason |
|---|---|---|
| Functional Design | YES (Units 1–4) | Business logic per agent needs definition |
| NFR Requirements | YES (Unit 1 only) | Rate limits, API costs, timeouts matter |
| NFR Design | YES (Unit 1 only) | Retry patterns, cost controls |
| Infrastructure Design | YES (Unit 1) | GitHub Actions YAML, secrets, permissions |
| Code Generation | YES (all units) | Always executes |
| Build and Test | YES | GitHub Actions test workflow |

---

## Architecture Overview

```
GitHub Event (issue or PR)
        |
        v
+-----------------------------------------------+
|         GitHub Actions Trigger                |
|   issue-triage.yml  |  pr-review.yml          |
+-----------------------------------------------+
        |
        v
+-----------------------------------------------+
|            ORCHESTRATOR AGENT                 |
|  - Reads event payload                        |
|  - Loads AI-DLC rules as context              |
|  - Determines which sub-agents to spawn       |
|  - Manages parallel execution                 |
|  - Calls Aggregator when all complete         |
+-----------------------------------------------+
        |
        +------ ISSUE TRIAGE PATH ------+
        |                               |
        v                               v
[Classifier Agent]           [PR Review PATH]
[Severity Agent]             [Security Agent]
[Component Agent]            [Architecture Agent]
[Reproduction Agent]         [Requirements Agent]
[Duplicate Agent]            [Test Coverage Agent]
        |                               |
        +----------+   +----------------+
                   |   |
                   v   v
          +------------------+
          |  AGGREGATOR      |
          |  - Merge results |
          |  - Deduplicate   |
          |  - Prioritize    |
          +------------------+
                   |
                   v
     GitHub API Output:
     - Labels applied
     - Comment posted
     - Review submitted (PR)
     - Assignee set (issue)
```

---

## Units of Work

### Unit 1 — Core Infrastructure
**What**: Foundation all agents depend on
- GitHub Actions workflow files (triggers, permissions, secrets)
- Base orchestrator class (event parsing, agent dispatch, parallelism)
- GitHub API client (post comments, labels, reviews)
- Claude API client wrapper (system prompt loader, retry, cost guard)
- AI-DLC rule loader (reads `.aidlc-rule-details/` files as context)

### Unit 2 — Issue Triage Pipeline
**What**: Agents that handle `issues.opened` / `issues.edited` events
- Classifier Agent — bug / feature / question / duplicate / enhancement
- Severity Agent — critical / high / medium / low with rationale
- Component Agent — maps issue to affected codebase area
- Reproduction Agent — validates enough info exists; asks author if not
- Duplicate Detector — searches open+closed issues for similarity
- Issue Aggregator — applies labels, sets assignee, posts triage comment

### Unit 3 — PR Review Pipeline
**What**: Agents that handle `pull_request.opened` / `synchronize` events
- Security Agent — enforces SECURITY-01–15 from security-baseline.md
- Architecture Agent — checks consistency with existing design
- Requirements Agent — validates PR resolves its linked issue
- Test Coverage Agent — checks tests exist for changed code
- PR Aggregator — consolidates findings, posts GitHub review (APPROVE / REQUEST_CHANGES / COMMENT)

### Unit 4 — Auto-Fix Pipeline
**What**: Agent that creates fix branches and PRs when unambiguous issues are found
- Fix Branch Agent — creates branch off original PR branch, commits fix
- Fix PR Agent — opens PR targeting original PR branch with findings as description
- Posts comment on original PR linking to the fix PR
- Triggers on: Security Agent findings (SECURITY-01–15), missing test stubs, unsafe patterns
- Human must approve and merge fix PR — no auto-merge

### Unit 5 — Cross-Reference & Trend Reporting
**What**: Higher-level intelligence across both pipelines
- Issue↔PR Linker — validates a PR actually fixes the issue it claims
- Trend Reporter — scheduled weekly GitHub Actions job that:
  - Queries GitHub API for all agent comments/labels from past 7 days
  - Aggregates findings by category, file, severity, agent type
  - Opens a new GitHub Issue as the weekly report
  - No database needed — GitHub itself is the data store

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Trigger | GitHub Actions | Already available, Copilot enabled |
| Language | Python 3.12 | Simple, great for AI/prompt logic, no compile step |
| AI | GitHub Models API via `GITHUB_TOKEN` + `requests` | No extra secrets, just HTTP calls |
| GitHub API | `requests` + `GITHUB_TOKEN` | Same library, no extra deps |
| Parallelism | `concurrent.futures.ThreadPoolExecutor` | Simple parallel agent execution |
| Secrets | `GITHUB_TOKEN` only (built-in) | Auto-injected, covers GitHub API + GitHub Models |
| Scheduled jobs | GitHub Actions `schedule:` cron | Trend reporter runs weekly |
| IaC (primary) | Terraform + Terraform Cloud | Cloud resources if needed (DynamoDB, Lambda, API GW); workspace to be configured later |
| IaC (AWS fallback) | CloudFormation | Supported if Terraform not suitable for specific AWS resources |

---

## Project Structure (proposed)

```
gh-ac-1/
+-- .github/
|   +-- workflows/
|   |   +-- issue-triage.yml        # Trigger: issues opened/edited
|   |   +-- pr-review.yml           # Trigger: PR opened/synchronize
|   |   +-- trend-report.yml        # Trigger: weekly schedule (cron)
|   +-- copilot-instructions.md     # (existing)
+-- agents/
|   +-- orchestrator.py             # Main dispatcher
|   +-- base_agent.py               # Shared: GitHub Models client, rule loader, retry
|   +-- issue/
|   |   +-- classifier.py
|   |   +-- severity.py
|   |   +-- component.py
|   |   +-- reproduction.py
|   |   +-- duplicate.py
|   |   +-- aggregator.py
|   +-- pr/
|   |   +-- security.py
|   |   +-- architecture.py
|   |   +-- requirements.py
|   |   +-- test_coverage.py
|   |   +-- aggregator.py
|   +-- fix/
|   |   +-- fix_agent.py            # Creates fix branch + commits
|   |   +-- fix_pr.py               # Opens fix PR targeting original branch
|   +-- reporting/
|   |   +-- trend_reporter.py       # Weekly aggregation + issue creation
|   +-- shared/
|       +-- github_client.py
|       +-- rule_loader.py          # Loads .aidlc-rule-details/ files as context
+-- .aidlc-rule-details/            # (existing — reused as agent context)
+-- aidlc-docs/                     # (existing — AI-DLC docs)
+-- requirements.txt
+-- README.md
+-- infra/
    +-- terraform/                  # Primary IaC — cloud resources if needed
    |   +-- main.tf
    |   +-- variables.tf
    |   +-- outputs.tf
    +-- cloudformation/             # AWS fallback IaC
        +-- stack.yml
```

---

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Blocking vs advisory | Advisory by default, blocking for CRITICAL security findings | Avoids over-blocking on false positives |
| Agent model | Claude claude-sonnet-4-6 | Best cost/quality for review tasks |
| Parallelism | All sub-agents run concurrently per event | Reduces total wall-clock time |
| Context size | Diff chunked at 200 lines per agent call | Stays within context limits |
| Cost guard | Max $0.10 per PR review, $0.05 per issue triage | Configurable via env var |

---

## What is NOT in scope (v1)

- Cross-repo analysis
- Slack/Teams notifications
- Fine-tuning or custom model training
- Auto-merge of fix PRs (human approval always required)

---

## Approval

**Ready to proceed to Application Design?**

A. Yes — proceed as proposed
B. Request changes — describe what to adjust

[Answer]:
