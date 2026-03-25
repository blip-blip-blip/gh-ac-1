# Unit 1 — Core Infrastructure: All Design Stage Questions
**Date**: 2026-03-24
**Covers**: Functional Design + NFR Requirements + NFR Design + Infrastructure Design

Most Unit 1 design is already determined from inception. Only genuine gaps are asked here.

---

## Functional Design Questions

### Q1. What should the Orchestrator do with unexpected event types?
(e.g. a `push` event accidentally triggers the workflow)

A. Silently ignore — exit with success, no comment posted
B. Log a warning to stdout only — no GitHub comment
C. Post a comment on the event explaining it's not supported
D. Other — describe

[Answer]: B — log warning to stdout only

---

### Q2. Should the BaseAgent enforce a maximum token budget per AI call?

A. Yes — hard limit, raise an error if exceeded (prevents runaway costs)
B. Yes — soft limit, log a warning but still return the result
C. No — rely on GitHub Models API limits only
D. Other — describe

[Answer]: B — soft limit, truncate input + log warning, still return result

---

### Q3. When the GitHub API returns an error (rate limit, 5xx), what should the agent do?

A. Retry up to 3 times with exponential backoff, then fail the job
B. Retry up to 3 times, then post a partial result comment and exit gracefully
C. Fail immediately — no retry for GitHub API errors
D. Other — describe

[Answer]: B — retry 3x with backoff, post partial result and exit gracefully

---

## NFR Requirements Questions

### Q4. What is the maximum acceptable wall-clock time for a single triage or review job?

A. 2 minutes — fast feedback
B. 5 minutes — acceptable for most teams
C. 10 minutes — fine for async review
D. No hard limit — let GitHub Actions default timeout apply (6 hours)

[Answer]: B — 5 minutes

---

### Q5. How should cost limits be configured?

A. Hardcoded defaults in the code (simple, no config needed)
B. Environment variables set in GitHub Actions workflow YAML
C. A `config.yml` file in the repo root (teams can customise per repo)
D. Other — describe

[Answer]: B — environment variables in workflow YAML

---

## Infrastructure Design Questions

### Q6. Python dependency management — which tool?

A. `pip` + `requirements.txt` (simplest, universal)
B. `poetry` + `pyproject.toml` (modern, lockfile included)
C. `uv` (fastest, modern drop-in for pip)
D. Other — describe

[Answer]: C — uv

---

### Q7. GitHub Actions — should jobs run on GitHub-hosted runners or self-hosted?

A. GitHub-hosted (`ubuntu-latest`) — zero maintenance, free tier sufficient
B. Self-hosted runners — more control, needed for private network access
C. Other — describe

[Answer]: A — GitHub-hosted ubuntu-latest

---

### Q8. Terraform Cloud — do you have an org/workspace name yet, or placeholder for now?

A. Placeholder — configure later
B. I have an org/workspace — provide details below

[Answer]: A — placeholder, configure later
