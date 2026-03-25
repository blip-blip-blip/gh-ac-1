# Infrastructure Design — Unit 1: Core Infrastructure

---

## GitHub Actions Setup

### Workflow Permissions (all workflows)

```yaml
permissions:
  issues: write          # post comments, apply labels
  pull-requests: write   # post reviews, comments
  contents: write        # create branches, commit fixes
  models: read           # GitHub Models API (AI calls)
```

### Environment Variables (all workflows)

```yaml
env:
  MAX_INPUT_TOKENS: "8000"
  MAX_OUTPUT_TOKENS: "1000"
```

### Runner

```yaml
runs-on: ubuntu-latest
timeout-minutes: 5
```

### Python + uv Setup (shared step across all workflows)

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.12"

- name: Install uv
  run: pip install uv

- name: Install dependencies
  run: uv pip install -r agents/core/requirements.txt --system
```

---

## Workflow Files

### `issue-triage.yml`

```yaml
name: Issue Triage
on:
  issues:
    types: [opened, edited]

permissions:
  issues: write
  contents: read
  models: read

env:
  MAX_INPUT_TOKENS: "8000"
  MAX_OUTPUT_TOKENS: "1000"

jobs:
  triage:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv pip install -e agents/core -e agents/issue_triage --system
      - name: Run issue triage
        run: python -m agents.issue_triage.service
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### `pr-review.yml`

```yaml
name: PR Review
on:
  pull_request:
    types: [opened, synchronize]

permissions:
  issues: write
  pull-requests: write
  contents: write
  models: read

env:
  MAX_INPUT_TOKENS: "8000"
  MAX_OUTPUT_TOKENS: "1000"

jobs:
  review:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv pip install -e agents/core -e agents/pr_review -e agents/fix --system
      - name: Run PR review
        run: python -m agents.pr_review.service
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### `trend-report.yml`

```yaml
name: Weekly Trend Report
on:
  schedule:
    - cron: "0 9 * * 1"   # Every Monday 09:00 UTC
  workflow_dispatch:        # Manual trigger for testing

permissions:
  issues: write
  contents: write
  models: read

jobs:
  report:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: uv pip install -e agents/core -e agents/reporting --system
      - name: Run trend reporter
        run: python -m agents.reporting.service
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Terraform Scaffold (Placeholder)

`infra/terraform/main.tf` — empty, placeholder comment only:
```hcl
# Terraform Cloud configuration — to be configured later
# terraform {
#   cloud {
#     organization = "<your-org>"
#     workspaces {
#       name = "<your-workspace>"
#     }
#   }
# }
```
