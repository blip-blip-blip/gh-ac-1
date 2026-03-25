# Deployment Architecture — Unit 1: Core Infrastructure

---

## Runtime Architecture

```
GitHub Repo
    |
    | (webhook event)
    v
GitHub Actions Runner (ubuntu-latest)
    |
    +-- Python 3.12 process
    |       |
    |       +-- agents/core/orchestrator.py   (entry point)
    |       +-- agents/core/base_agent.py
    |       +-- agents/core/github_client.py
    |       +-- agents/core/rule_loader.py
    |       |
    |       +-- [reads] .aidlc-rule-details/  (local filesystem)
    |       |
    |       +-- [HTTPS] GitHub Models API     (AI calls)
    |       +-- [HTTPS] GitHub REST API       (comments, labels, PRs)
    |
    | (results)
    v
GitHub PR / Issue
    (comments posted, labels applied, reviews submitted)
```

---

## No Persistent Infrastructure

Unit 1 has zero persistent infrastructure:
- No database
- No queue
- No cache
- No deployed service

The GitHub Actions runner is ephemeral — spun up per event, torn down after the job completes.

---

## Deployment Process

No deployment step needed. Code changes take effect immediately on the next GitHub event:

1. Push changes to `main` (or merge a PR)
2. Next `issues.opened` or `pull_request.opened` event triggers the updated workflow automatically

---

## Secrets and Auth

| Secret | Source | How accessed |
|---|---|---|
| `GITHUB_TOKEN` | Auto-injected by GitHub Actions | `os.environ["GITHUB_TOKEN"]` |

No secrets need to be manually configured in GitHub Settings for Unit 1.
