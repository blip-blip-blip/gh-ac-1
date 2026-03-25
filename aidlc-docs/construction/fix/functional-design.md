# Unit 4 — Auto-Fix Pipeline: Functional Design

## Overview
For each finding with `fix_code`, FixAgent creates a branch, commits the fix, opens a PR, and posts a link on the original PR. Humans must approve the fix PR before it is merged.

## Flow

```
finding (has fix_code)
  → create_branch("fix/{rule}-pr-{N}", from=pr.head_branch)
  → commit_file(branch, file_path, fix_code, message)
  → create_pr(title, body, head=fix_branch, base=pr.head_branch)
  → post_comment(original_pr, "🔧 Opened fix PR #X")
```

## Branch Naming
`fix/{safe_rule_id}-pr-{pr_number}` — rule ID characters outside `[a-zA-Z0-9-]` are replaced with `-`.

## Business Rules
- Fix PRs target the original PR's **head branch** (not `main`).
- `FixService` logs warnings but does not raise on individual failures — the review comment is already posted.
- Humans must approve and merge fix PRs; there is no auto-merge.
- If `fix_code` or `file` is missing, the finding is skipped with an error result.

## FixPRResult Fields
| Field | Type | Description |
|---|---|---|
| `finding` | dict | Original finding |
| `fix_branch` | str | Created branch name |
| `fix_pr_number` | int or None | Opened PR number |
| `success` | bool | Overall success |
| `error` | str or None | Error message if failed |
