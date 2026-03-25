# Tech Stack Decisions — Unit 1: Core Infrastructure

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.12 | AI/prompt logic is natural in Python |
| Dependency manager | `uv` | Fastest Python package manager, drop-in for pip, lockfile included |
| HTTP client | `requests` | Simple, universal, no async complexity needed |
| AI provider | GitHub Models API | Uses `GITHUB_TOKEN` — no extra secrets |
| GitHub API | GitHub REST API v3 via `requests` | Same library, same token |
| Code style | `ruff` | Fast linter + formatter, replaces flake8 + black |
| Testing | `pytest` | Standard, widely supported in GitHub Actions |
| Runner | `ubuntu-latest` (GitHub-hosted) | Zero maintenance, free tier sufficient |
| IaC | Terraform + Terraform Cloud | Placeholder — configure later |
| Python version pin | `.python-version` file per package | Ensures consistent version across local + CI |

---

## Key Environment Variables

| Variable | Set In | Purpose |
|---|---|---|
| `GITHUB_TOKEN` | Auto-injected by Actions | GitHub API + GitHub Models API auth |
| `GITHUB_EVENT_NAME` | Auto-injected by Actions | Event type routing |
| `GITHUB_EVENT_PATH` | Auto-injected by Actions | Path to event JSON payload |
| `GITHUB_REPOSITORY` | Auto-injected by Actions | `owner/repo` string |
| `MAX_INPUT_TOKENS` | Workflow YAML `env:` | Soft token budget per AI call (default: 8000) |
| `MAX_OUTPUT_TOKENS` | Workflow YAML `env:` | Max output tokens per AI call (default: 1000) |
| `JOB_TIMEOUT_MINUTES` | Workflow YAML `timeout-minutes:` | 5 minutes |
