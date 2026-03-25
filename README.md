# gh-ac-1 — AI-DLC GitHub Agent

A multi-agent GitHub automation system built with the [AI-DLC](./aidlc-docs/) (AI Development Lifecycle) workflow. Agents automatically triage issues, review pull requests, create fix PRs, and generate weekly trend reports — all powered by the GitHub Models API using the built-in `GITHUB_TOKEN`.

## What it does

| Trigger | Agents | Output |
|---|---|---|
| Issue opened / edited | Classifier, Severity, Component, Reproduction, Duplicate Detector | Labels + triage comment |
| PR opened / synchronised | Security, Architecture, Requirements, Test Coverage | GitHub review (APPROVE / COMMENT / REQUEST_CHANGES) + optional fix PRs |
| Every Monday 09:00 UTC | Trend Reporter | `TREND-REPORT.md` committed + GitHub issue opened |

## Architecture

```mermaid
flowchart TD
    GH[GitHub Event] --> ORC[orchestrator.py]

    ORC -->|issues: opened / edited| IT[issue_triage/service.py]
    ORC -->|pull_request: opened / synchronize| PR[pr_review/service.py]
    ORC -->|schedule / workflow_dispatch| RP[reporting/service.py]

    subgraph Issue Triage ["Issue Triage  (parallel)"]
        IT --> CL[Classifier]
        IT --> SV[Severity]
        IT --> CM[Component]
        IT --> RC[Reproduction]
        IT --> DD[Duplicate Detector]
        CL & SV & CM & RC & DD --> IA[IssueAggregator]
    end

    subgraph PR Review ["PR Review  (parallel)"]
        PR --> SE[Security]
        PR --> AR[Architecture]
        PR --> RQ[Requirements]
        PR --> TC[Test Coverage]
        SE & AR & RQ & TC --> PA[PRAggregator]
        PA -->|fix_code present| FX[FixService]
    end

    subgraph Reporting
        RP --> LK[Linker]
        LK --> TR[TrendReporter]
    end

    IA -->|apply labels| GHLABEL[GitHub Labels]
    IA -->|post comment| GHCOMMENT[GitHub Comment]
    PA -->|submit review| GHREVIEW[GitHub Review]
    FX -->|open PR| GHFIXPR[Fix PR]
    TR -->|commit file| GHFILE[TREND-REPORT.md]
    TR -->|open issue| GHISSUE[GitHub Issue]
```

## PR Review & Auto-Fix flow

```mermaid
sequenceDiagram
    actor Dev
    participant GitHub
    participant PRReview as PR Review workflow
    participant Agents as Security / Arch / Req / Coverage
    participant FixAgent

    Dev->>GitHub: Open pull request
    GitHub->>PRReview: pull_request: opened
    PRReview->>Agents: run all 4 in parallel
    Agents-->>PRReview: findings[]

    alt critical or high findings
        PRReview->>GitHub: REQUEST_CHANGES review
        PRReview->>FixAgent: findings with fix_code
        FixAgent->>GitHub: create branch fix/{rule}-pr-{N}
        FixAgent->>GitHub: commit fix_code
        FixAgent->>GitHub: open fix PR → pr.head_branch
        FixAgent->>GitHub: comment on original PR linking fix PR
        GitHub-->>Dev: 🔴 Review requested + fix PR opened
    else medium / low findings
        PRReview->>GitHub: COMMENT review
        GitHub-->>Dev: 🟡 Comments posted
    else no findings
        PRReview->>GitHub: APPROVE
        GitHub-->>Dev: ✅ Approved
    end
```

## Issue Triage flow

```mermaid
sequenceDiagram
    actor User
    participant GitHub
    participant Triage as Issue Triage workflow
    participant Agents as 5 Agents (parallel)

    User->>GitHub: Open issue
    GitHub->>Triage: issues: opened
    Triage->>Agents: run all 5 in parallel
    Note over Agents: Classifier · Severity<br/>Component · Reproduction<br/>Duplicate Detector
    Agents-->>Triage: results[]
    Triage->>GitHub: apply labels (aidlc: bug, aidlc: high, …)
    Triage->>GitHub: post triage comment
    GitHub-->>User: Labels + AI triage summary
```

All agents inherit from `BaseAgent` which handles:
- GitHub Models API calls (`gpt-4o` by default, configurable via `GITHUB_MODEL`)
- Retry with exponential backoff (3 attempts)
- Soft input token budget (8 000 tokens — truncates, never rejects)
- JSON schema validation on model output

## Packages

```
agents/
  core/           Base classes, GitHub client, orchestrator, rule loader
  issue_triage/   5-agent issue triage pipeline
  pr_review/      4-agent PR review pipeline
  fix/            Auto-fix branch + PR pipeline
  reporting/      Weekly trend reporting
```

## No extra secrets needed

Everything runs on the `GITHUB_TOKEN` that GitHub Actions injects automatically. No API keys, no third-party accounts.

## Local setup

```bash
pip install requests
export GITHUB_TOKEN=<your-pat>
export GITHUB_REPOSITORY=owner/repo
export PYTHONPATH=$(pwd)

# Run tests
pip install pytest
pytest agents/*/tests/ -v
```

## Workflows

| File | Trigger | Timeout |
|---|---|---|
| `.github/workflows/issue-triage.yml` | `issues: [opened, edited]` | 5 min |
| `.github/workflows/pr-review.yml` | `pull_request: [opened, synchronize]` | 10 min |
| `.github/workflows/trend-report.yml` | Weekly cron + `workflow_dispatch` | 5 min |

## AI-DLC

This project was built using the AI-DLC adaptive workflow. Governance rules live in `.github/copilot-instructions.md` and `.aidlc-rule-details/`. The same rules are injected as system prompts into the agents via `agents/core/rule_loader.py`.

Progress is tracked in [`aidlc-docs/aidlc-state.md`](./aidlc-docs/aidlc-state.md).
