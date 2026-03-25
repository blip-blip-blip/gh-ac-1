# NFR Requirements — Unit 1: Core Infrastructure

---

## Performance

| Requirement | Value | Notes |
|---|---|---|
| Max job wall-clock time | 5 minutes | Set via `timeout-minutes: 5` in workflow YAML |
| Max AI call input | 8,000 tokens | Soft limit — truncate + warn, don't fail |
| GitHub API retry backoff | 2s, 4s | Exponential, max 3 attempts |
| AI API retry backoff | 2s, 4s | Exponential, max 3 attempts |
| Target agent response time | < 30s per agent | Single AI call + GitHub API overhead |

---

## Reliability

| Requirement | Value | Notes |
|---|---|---|
| Agent failure handling | Partial results posted | Never block all output because one agent fails |
| GitHub API failure handling | Partial results + warning | Same pattern as agent failures |
| Retry attempts | 3 max | For both AI calls and GitHub API calls |
| Unhandled exceptions | Must not crash silently | All exceptions logged to stdout before exit |

---

## Cost Control

| Requirement | Value | Notes |
|---|---|---|
| Max tokens per AI call | 8,000 input + 1,000 output | Configurable via env var |
| Cost config mechanism | Environment variables in workflow YAML | No hardcoding, no config file |
| Key env vars | `MAX_INPUT_TOKENS`, `MAX_OUTPUT_TOKENS` | Set in workflow YAML |

---

## Security

| Requirement | Detail |
|---|---|
| Token handling | `GITHUB_TOKEN` read from env only, never logged, never written to files |
| No secrets in code | All credentials via env vars |
| No external network calls | Only GitHub REST API and GitHub Models API |
| Principle of least privilege | Workflow permissions scoped to minimum needed per workflow |

---

## Maintainability

| Requirement | Detail |
|---|---|
| Python version | 3.12 |
| Dependency manager | `uv` |
| Code style | PEP 8, enforced via `ruff` |
| Test coverage target | 80% for core unit |
| All agents must extend BaseAgent | No standalone agent code |

---

## Observability

| Requirement | Detail |
|---|---|
| Logging | `print()` to stdout — visible in GitHub Actions run log |
| Log format | `[{agent_type}] {level}: {message}` |
| Truncation warnings | Always logged with original + truncated token counts |
| Retry warnings | Always logged with attempt number and error |
| Partial result warnings | Always logged before posting to GitHub |
