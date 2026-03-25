# Application Design — Consolidated
**Date**: 2026-03-24

---

## System Overview

A multi-agent GitHub automation system that triages issues, reviews pull requests, creates automated fix PRs, and produces weekly trend reports — all running inside GitHub Actions using `GITHUB_TOKEN` only (no external secrets).

---

## Design Decisions

| # | Decision | Choice |
|---|---|---|
| Q1 | Orchestrator routing | Fixed pipeline — all agents always run per event type |
| Q2 | AI-DLC rules passed to agents | Static mapping per agent type via RuleLoader |
| Q3 | Duplicate detection | AI model compares against last 50 open issues |
| Q4 | Fix code generation | Same agent that finds the issue also generates the fix |
| Q5 | Agent output format | Structured JSON (finding type, severity, file, line, message, fix_code) |
| Q6 | Trend report output | Both GitHub Issue (weekly) + `TREND-REPORT.md` committed to repo |
| Q7 | PR blocking | Advisory only — all findings are non-blocking |

---

## Component Summary

### Core Infrastructure
| Component | Role |
|---|---|
| Orchestrator | Entry point, event parsing, service routing |
| BaseAgent | Shared AI call, rule loading, retry, JSON validation |
| GitHubClient | All GitHub API interactions |
| RuleLoader | Loads AI-DLC rules as agent context (static mapping) |

### Issue Triage (5 parallel agents + 1 aggregator)
| Component | Role |
|---|---|
| ClassifierAgent | Classifies issue type |
| SeverityAgent | Assigns severity |
| ComponentAgent | Maps to codebase area |
| ReproductionAgent | Validates reproducibility, asks for missing info |
| DuplicateDetectorAgent | Detects duplicates via AI comparison |
| IssueAggregator | Merges results → labels + comment |

### PR Review (4 parallel agents + 1 aggregator)
| Component | Role |
|---|---|
| SecurityAgent | Enforces SECURITY-01–15, generates fix code |
| ArchitectureAgent | Checks design consistency |
| RequirementsAgent | Validates PR resolves linked issue |
| TestCoverageAgent | Checks test coverage, generates test stubs |
| PRAggregator | Merges results → GitHub review + fix PRs |

### Reporting
| Component | Role |
|---|---|
| TrendReporter | Weekly aggregation → GitHub Issue + TREND-REPORT.md |

---

## Services

| Service | Trigger | Agents |
|---|---|---|
| IssueTriage | `issues.opened/edited` | 5 parallel + IssueAggregator |
| PRReview | `pull_request.opened/synchronize` | 4 parallel + PRAggregator + optional fix PRs |
| Reporting | Weekly cron (Mon 09:00 UTC) | TrendReporter |

---

## Project Structure

```
gh-ac-1/
+-- .github/
|   +-- workflows/
|   |   +-- issue-triage.yml
|   |   +-- pr-review.yml
|   |   +-- trend-report.yml
|   +-- copilot-instructions.md
+-- agents/
|   +-- orchestrator.py
|   +-- base_agent.py
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
|   +-- reporting/
|   |   +-- trend_reporter.py
|   +-- shared/
|       +-- github_client.py
|       +-- rule_loader.py
+-- infra/
|   +-- terraform/
|   +-- cloudformation/
+-- .aidlc-rule-details/
+-- aidlc-docs/
+-- requirements.txt
+-- TREND-REPORT.md
+-- README.md
```

---

## Agents Per Event Summary

| Event | Parallel Agents | Sequential After | Total |
|---|---|---|---|
| Issue opened/edited | 5 | 1 (IssueAggregator) | 6 |
| PR opened/synchronised | 4 | 1 (PRAggregator) + N fix agents | 5–9 |
| Weekly cron | 1 (TrendReporter) | — | 1 |

---

## References
- `components.md` — full component definitions
- `component-methods.md` — method signatures
- `services.md` — service orchestration detail
- `component-dependency.md` — dependency matrix and data flow diagrams
