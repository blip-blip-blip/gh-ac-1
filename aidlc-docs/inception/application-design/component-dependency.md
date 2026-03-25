# Component Dependencies

## Dependency Matrix

| Component | Depends On |
|---|---|
| Orchestrator | IssueTriage Service, PRReview Service |
| IssueTriage Service | ClassifierAgent, SeverityAgent, ComponentAgent, ReproductionAgent, DuplicateDetectorAgent, IssueAggregator, GitHubClient |
| PRReview Service | SecurityAgent, ArchitectureAgent, RequirementsAgent, TestCoverageAgent, PRAggregator, GitHubClient |
| Reporting Service | TrendReporter, GitHubClient |
| All Agents | BaseAgent, RuleLoader, GitHubClient |
| BaseAgent | RuleLoader, GitHubClient (GitHub Models API) |
| RuleLoader | `.aidlc-rule-details/` files (filesystem) |
| GitHubClient | `GITHUB_TOKEN` (env var), GitHub REST API |

---

## Data Flow — Issue Triage

```
GitHub Event Payload
        |
        v
   Orchestrator
   parse_event()
        |
        v
IssueTriage Service
        |
        +--[parallel]--+------------------+------------------+------------------+
        |              |                  |                  |                  |
        v              v                  v                  v                  v
 Classifier      Severity           Component          Reproduction        Duplicate
  Agent           Agent              Agent               Agent             Detector
        |              |                  |                  |                  |
        +------+-------+------------------+------------------+------------------+
               |
               v (all results as dict)
        IssueAggregator
               |
        +------+------+
        |             |
        v             v
  post_comment   apply_labels
  (GitHubClient) (GitHubClient)
```

---

## Data Flow — PR Review

```
GitHub Event Payload
        |
        v
   Orchestrator
   parse_event()
        |
        v
 PRReview Service
        |
        +--[parallel]--+------------------+------------------+
        |              |                  |                  |
        v              v                  v                  v
  Security        Architecture       Requirements      TestCoverage
   Agent            Agent              Agent             Agent
        |              |                  |                  |
        +------+--------+------------------+------------------+
               |
               v (all results as dict)
         PRAggregator
               |
        +------+------+
        |             |
        v             v
  post_review    [for each fix_code finding]
  (GitHubClient)       |
                       v
                 create_branch()
                 commit_file()
                 create_pr()       <- fix PR targeting original PR branch
                 post_comment()    <- links fix PR on original PR
```

---

## Data Flow — Trend Report

```
GitHub Actions cron schedule
        |
        v
Reporting Service
        |
        v
  TrendReporter
        |
        +---> fetch_agent_comments() --> GitHubClient --> GitHub API
        +---> fetch_agent_labels()   --> GitHubClient --> GitHub API
        |
        v
    aggregate()
        |
        +---> post_report() --> GitHubClient --> create GitHub Issue
        +---> post_report() --> GitHubClient --> commit TREND-REPORT.md
```

---

## External Dependencies

| Dependency | Used By | Auth |
|---|---|---|
| GitHub REST API | GitHubClient | `GITHUB_TOKEN` (built-in) |
| GitHub Models API (AI) | BaseAgent | `GITHUB_TOKEN` (built-in) |
| `.aidlc-rule-details/` (filesystem) | RuleLoader | None — local files |
| `aidlc-docs/` (filesystem) | ArchitectureAgent | None — local files |
