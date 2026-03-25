# Unit 5 — Cross-Reference & Trend Reporting: Functional Design

## Overview
Every Monday at 09:00 UTC, the reporting service scans the past 7 days of GitHub issue comments, extracts structured data from agent comments, and produces a weekly trend report committed to the repo and opened as a GitHub issue.

## Components

### Linker
- Fetches all issue comments since 7 days ago via `GET /repos/{repo}/issues/comments?since=...`
- Filters to comments containing `AGENT_COMMENT_MARKER` (`<!-- ai-dlc-agent -->`)
- Parses each comment into `CommentData` (issue type, severities, findings count, fix PR count, rules violated)

### TrendReporter
- Aggregates `CommentData` objects into a markdown report
- Sections: Issue Triage (by type, by severity), PR Reviews (counts, averages, fix PR rate), Top Rule Violations

### Service
- Calls Linker → TrendReporter
- Commits `TREND-REPORT.md` to the default branch via `commit_file`
- Opens a GitHub issue titled "AI-DLC Weekly Trend Report — YYYY-MM-DD" with the report as the body

## Output
- **File**: `TREND-REPORT.md` in repository root
- **Issue**: labelled `aidlc: report`
- **Trigger**: `schedule: cron: "0 9 * * 1"` + `workflow_dispatch`

## Business Rules
- Report is generated even if 0 comments are found (shows "No activity" placeholders).
- `create_issue` and `commit_file` failures are logged as warnings, not errors — partial output is acceptable.
- Rule violation section is omitted if there are no findings.
