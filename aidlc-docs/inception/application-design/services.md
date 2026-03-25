# Services

## IssueTriage Service
**Trigger**: `issues.opened` / `issues.edited` GitHub event
**Orchestrated by**: Orchestrator

**Execution sequence**:
1. Fetch full issue details via GitHubClient
2. Fetch repo file tree via GitHubClient
3. Fetch last 50 open issues via GitHubClient (for DuplicateDetectorAgent)
4. Run 5 agents in parallel via `ThreadPoolExecutor`:
   - ClassifierAgent
   - SeverityAgent
   - ComponentAgent
   - ReproductionAgent
   - DuplicateDetectorAgent
5. Collect all JSON results
6. Pass to IssueAggregator → posts comment + applies labels

**Error handling**: If any single agent fails, aggregator runs with partial results and notes the failure in the comment.

---

## PRReview Service
**Trigger**: `pull_request.opened` / `pull_request.synchronize` GitHub event
**Orchestrated by**: Orchestrator

**Execution sequence**:
1. Fetch PR details, diff, and changed files via GitHubClient
2. Fetch linked issue (if present in PR description) via GitHubClient
3. Load `aidlc-docs/inception/application-design/components.md` for ArchitectureAgent
4. Run 4 agents in parallel via `ThreadPoolExecutor`:
   - SecurityAgent
   - ArchitectureAgent
   - RequirementsAgent
   - TestCoverageAgent
5. For each agent finding that includes `fix_code`:
   - Agent creates fix branch + commits fix + opens fix PR (sequentially, after parallel run)
   - Posts comment on original PR linking to fix PR
6. Pass all results to PRAggregator → submits GitHub review

**Error handling**: If any agent fails, aggregator notes it. Fix PR creation failures are logged but do not block the review.

---

## Reporting Service
**Trigger**: GitHub Actions `schedule:` cron — every Monday 09:00 UTC
**Orchestrated by**: Standalone workflow (`trend-report.yml`)

**Execution sequence**:
1. Calculate lookback window (past 7 days)
2. TrendReporter fetches all agent comments and labels from GitHub API
3. Aggregates findings by category, severity, file, agent type
4. Posts new GitHub Issue with weekly summary
5. Commits updated `TREND-REPORT.md` to default branch
