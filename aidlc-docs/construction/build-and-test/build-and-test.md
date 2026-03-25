# Build and Test

## Package Layout

```
agents/
  core/          gh-ac-core     — base classes, GitHub client, orchestrator
  issue_triage/  gh-ac-issue-triage
  pr_review/     gh-ac-pr-review
  fix/           gh-ac-fix
  reporting/     gh-ac-reporting
```

Each package has its own `pyproject.toml` (hatchling build) and `requirements.txt` pointing to `../core`.

## Local Development Setup

```bash
# Install all packages in editable mode
uv pip install -e agents/core \
               -e agents/issue_triage \
               -e agents/pr_review \
               -e agents/fix \
               -e agents/reporting

# Run all tests
pytest agents/core/tests \
       agents/issue_triage/tests \
       agents/pr_review/tests \
       agents/fix/tests \
       agents/reporting/tests \
       -v
```

## Running a Single Unit

```bash
# Issue triage
uv pip install -e agents/core -e agents/issue_triage
python -m agents.issue_triage.service

# PR review
uv pip install -e agents/core -e agents/pr_review -e agents/fix
python -m agents.pr_review.service

# Trend report
uv pip install -e agents/core -e agents/reporting
python -m agents.reporting.service
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GITHUB_TOKEN` | yes | — | Auto-injected by GitHub Actions |
| `GITHUB_REPOSITORY` | yes | — | `owner/repo`, auto-injected |
| `GITHUB_EVENT_NAME` | yes | — | Auto-injected |
| `GITHUB_EVENT_PATH` | yes | — | Auto-injected |
| `GITHUB_MODEL` | no | `gpt-4o` | GitHub Models model ID |
| `MAX_INPUT_TOKENS` | no | `8000` | Soft input token budget |
| `MAX_OUTPUT_TOKENS` | no | `1000` | Max tokens for model response |

## Test Strategy

- **Unit tests**: Each agent has isolated tests using `unittest.mock.MagicMock` for `GitHubClient`.
- **No live API calls in tests**: All HTTP calls are mocked.
- **Partial failure coverage**: Tests verify that one agent failing does not block the aggregator.
- **Schema validation**: Tests verify that invalid model output is rejected and a failure result is returned.

## GitHub Actions Workflows

| Workflow | Trigger | Timeout |
|---|---|---|
| `issue-triage.yml` | `issues: [opened, edited]` | 5 min |
| `pr-review.yml` | `pull_request: [opened, synchronize]` | 10 min |
| `trend-report.yml` | `schedule: 0 9 * * 1` + `workflow_dispatch` | 5 min |

## Permissions Required

| Permission | Issue Triage | PR Review | Trend Report |
|---|---|---|---|
| `issues: write` | ✅ | — | ✅ |
| `pull-requests: write` | — | ✅ | — |
| `contents: write` | — | ✅ | ✅ |
| `contents: read` | ✅ | — | — |
| `models: read` | ✅ | ✅ | ✅ |
