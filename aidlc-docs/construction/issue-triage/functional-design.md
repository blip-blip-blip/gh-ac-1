# Unit 2 — Issue Triage Pipeline: Functional Design

## Overview
Five parallel agents classify, score, and annotate every GitHub issue within 4 minutes of creation or edit.

## Agents

| Agent | Input | Output Fields |
|---|---|---|
| ClassifierAgent | issue title + body | `type`, `confidence`, `rationale` |
| SeverityAgent | issue title + body | `severity`, `rationale` |
| ComponentAgent | issue + file tree | `components[]`, `rationale` |
| ReproductionAgent | issue title + body | `has_enough_info`, `questions[]` |
| DuplicateDetectorAgent | issue + last 50 open issues | `is_duplicate`, `duplicate_of`, `rationale` |

## Business Rules

- **ClassifierAgent** falls back to `"question"` if model returns an unrecognised type.
- **DuplicateDetectorAgent** uses a conservative similarity threshold of 0.8 — false negatives are preferred over false positives.
- **ReproductionAgent** only asks questions for `bug` and `enhancement` types; for `question` it always marks `has_enough_info: true`.
- **IssueAggregator** applies labels then posts a single comment with `AGENT_COMMENT_MARKER`.
- Failed agents are noted in the comment but do not block posting.

## Labels Applied

| Condition | Label |
|---|---|
| classifier.type | `aidlc: bug` / `aidlc: feature` / etc. |
| severity.severity | `aidlc: critical` / `aidlc: high` / etc. |
| reproduction.has_enough_info == false | `aidlc: needs-info` |
| duplicate.is_duplicate == true | `aidlc: duplicate` |

## Parallelism
All five agents run via `ThreadPoolExecutor(max_workers=5)` with a 240 s timeout per run.
