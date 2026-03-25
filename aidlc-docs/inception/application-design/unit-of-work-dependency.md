# Unit of Work — Dependency Matrix
**Date**: 2026-03-24

---

## Dependency Matrix

| Unit | Depends On | Can Start After |
|---|---|---|
| Unit 1 — Core Infrastructure | Nothing | Immediately |
| Unit 2 — Issue Triage | Unit 1 | Unit 1 complete |
| Unit 3 — PR Review | Unit 1 | Unit 1 complete |
| Unit 4 — Auto-Fix | Unit 1, Unit 3 | Units 2+3 complete |
| Unit 5 — Reporting | Unit 1, Unit 2, Unit 3, Unit 4 | Unit 4 complete |

---

## Build Order Diagram

```
+---------------------------+
|  Unit 1 — Core            |   Week 1
|  Infrastructure           |
+---------------------------+
            |
     +------+------+
     |             |
+----+----+   +----+----+
| Unit 2  |   | Unit 3  |   Week 2 (parallel)
| Issue   |   | PR      |
| Triage  |   | Review  |
+----+----+   +----+----+
     |             |
     +------+------+
            |
+---------------------------+
|  Unit 4 — Auto-Fix        |   Week 3
+---------------------------+
            |
+---------------------------+
|  Unit 5 — Reporting       |   Week 4
+---------------------------+
```

---

## Package Import Dependencies

```
agents/core/          <- imported by ALL units
      |
      +-- agents/issue_triage/   (imports: core.base_agent, core.github_client, core.rule_loader)
      +-- agents/pr_review/      (imports: core.base_agent, core.github_client, core.rule_loader)
      +-- agents/fix/            (imports: core.github_client)
      +-- agents/reporting/      (imports: core.github_client)

agents/pr_review/ <- imported by agents/fix/
      (fix/ receives findings from pr_review agents)
```

---

## GitHub Actions Workflow Dependencies

| Workflow | Depends On | Runs When |
|---|---|---|
| `issue-triage.yml` | `agents/core/`, `agents/issue_triage/` | `issues.opened/edited` |
| `pr-review.yml` | `agents/core/`, `agents/pr_review/`, `agents/fix/` | `pull_request.opened/synchronize` |
| `trend-report.yml` | `agents/core/`, `agents/reporting/` | Weekly cron |

---

## Integration Points

| From | To | Data Passed |
|---|---|---|
| SecurityAgent | fix/ package | `{rule_id, file, line, fix_code, pr_branch}` |
| TestCoverageAgent | fix/ package | `{file, missing_test, fix_code, pr_branch}` |
| All Issue Triage agents | IssueAggregator | Structured JSON findings |
| All PR Review agents | PRAggregator | Structured JSON findings |
| PRAggregator | GitHub API | Review event + body |
| IssueAggregator | GitHub API | Labels + comment |
| TrendReporter | GitHub API | Issue body + TREND-REPORT.md content |
