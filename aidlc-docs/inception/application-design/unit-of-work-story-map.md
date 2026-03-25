# Unit of Work — Capability Map
**Date**: 2026-03-24

---

## Capabilities by Unit

### Unit 1 — Core Infrastructure

| Capability | Component | Notes |
|---|---|---|
| Parse GitHub Actions event payload | Orchestrator | Handles issue + PR event shapes |
| Route event to correct service | Orchestrator | issue → IssueTriage, PR → PRReview |
| Call GitHub Models AI API | BaseAgent | Shared by all agents |
| Load AI-DLC rules as agent context | RuleLoader | Static mapping per agent type |
| Post comments on issues and PRs | GitHubClient | |
| Apply labels to issues | GitHubClient | |
| Fetch issue details and list | GitHubClient | |
| Fetch PR diff and changed files | GitHubClient | |
| Create branches | GitHubClient | Used by Unit 4 |
| Commit files to a branch | GitHubClient | Used by Unit 4 |
| Open pull requests | GitHubClient | Used by Unit 4 |
| Submit PR reviews | GitHubClient | Used by Unit 3 |
| Retry failed AI calls with backoff | BaseAgent | |
| Validate structured JSON output | BaseAgent | |

---

### Unit 2 — Issue Triage Pipeline

| Capability | Component | Notes |
|---|---|---|
| Classify issue as bug/feature/question/duplicate/enhancement | ClassifierAgent | |
| Assign severity critical/high/medium/low | SeverityAgent | |
| Map issue to affected codebase component | ComponentAgent | Uses repo file tree |
| Validate reproduction info is present | ReproductionAgent | |
| Ask author for missing reproduction details | ReproductionAgent | Uses question-format-guide.md |
| Detect duplicate issues via AI comparison | DuplicateDetectorAgent | Compares against last 50 open issues |
| Link to existing duplicate issue | DuplicateDetectorAgent | Posts duplicate link in comment |
| Merge all triage findings into one comment | IssueAggregator | |
| Apply triage labels automatically | IssueAggregator | type, severity, component labels |
| Run all triage agents in parallel | IssueTriage Service | ThreadPoolExecutor |
| Handle partial failures gracefully | IssueTriage Service | Posts comment with available results |

---

### Unit 3 — PR Review Pipeline

| Capability | Component | Notes |
|---|---|---|
| Review PR diff against SECURITY-01–15 rules | SecurityAgent | Uses full security-baseline.md |
| Generate fix code for security findings | SecurityAgent | fix_code passed to Unit 4 |
| Check PR consistency with application design | ArchitectureAgent | Reads aidlc-docs/application-design/ |
| Validate PR resolves its linked issue | RequirementsAgent | Parses PR description for issue ref |
| Check test coverage for changed files | TestCoverageAgent | |
| Generate test stub fix code | TestCoverageAgent | fix_code passed to Unit 4 |
| Merge all review findings into GitHub review | PRAggregator | |
| Submit APPROVE / REQUEST_CHANGES / COMMENT | PRAggregator | Always advisory (non-blocking) |
| Run all review agents in parallel | PRReview Service | ThreadPoolExecutor |
| Handle partial agent failures gracefully | PRReview Service | Posts review with available results |

---

### Unit 4 — Auto-Fix Pipeline

| Capability | Component | Notes |
|---|---|---|
| Create fix branch off original PR branch | FixAgent | Branch name: `fix/<rule>-pr-<number>` |
| Commit fix code to fix branch | FixAgent | |
| Open fix PR targeting original PR branch | FixAgent | Title references original PR + finding |
| Post comment on original PR linking fix PR | FixAgent | |
| Handle multiple findings → multiple fix PRs | FixService | One fix PR per finding with fix_code |
| Log fix PR creation failures without blocking | FixService | Review still posts if fix fails |

---

### Unit 5 — Cross-Reference & Trend Reporting

| Capability | Component | Notes |
|---|---|---|
| Validate PR description references correct issue | Linker | Called during PR review workflow |
| Fetch all agent comments from past 7 days | TrendReporter | Via GitHub API |
| Fetch all agent-applied labels from past 7 days | TrendReporter | Via GitHub API |
| Aggregate findings by category, severity, file | TrendReporter | |
| Identify top recurring findings | TrendReporter | |
| Post weekly report as new GitHub Issue | TrendReporter | Every Monday 09:00 UTC |
| Commit updated TREND-REPORT.md to repo | TrendReporter | Appends new week's data |

---

## Coverage Summary

| Total Capabilities | 44 |
|---|---|
| Unit 1 (foundation) | 14 |
| Unit 2 (issue triage) | 11 |
| Unit 3 (PR review) | 10 |
| Unit 4 (auto-fix) | 6 |
| Unit 5 (reporting) | 7 |
