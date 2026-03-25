# Business Rules — Unit 1: Core Infrastructure

---

## Orchestrator Rules

| ID | Rule |
|---|---|
| ORC-01 | Only process `issues` events with action `opened` or `edited` |
| ORC-02 | Only process `pull_request` events with action `opened` or `synchronize` |
| ORC-03 | All other event types MUST be logged as warnings and skipped (exit 0) |
| ORC-04 | Event payload MUST be read from `GITHUB_EVENT_PATH` env var |
| ORC-05 | `GITHUB_TOKEN` MUST be present — fail immediately with clear error if missing |
| ORC-06 | `GITHUB_REPOSITORY` MUST be present — fail immediately if missing |

---

## BaseAgent Rules

| ID | Rule |
|---|---|
| AGT-01 | All agents MUST extend BaseAgent — no direct GitHub Models API calls outside BaseAgent |
| AGT-02 | Input MUST be truncated (not rejected) if estimated tokens exceed `MAX_INPUT_TOKENS` |
| AGT-03 | Truncation MUST be logged as a warning with original and truncated token counts |
| AGT-04 | All agent outputs MUST be valid JSON matching the agent's defined output schema |
| AGT-05 | If schema validation fails, retry the AI call (counts against the 3-attempt limit) |
| AGT-06 | A failed agent (after 3 attempts) MUST return `None` — never raise an unhandled exception |
| AGT-07 | Retry backoff MUST be: 2s after attempt 1, 4s after attempt 2 |
| AGT-08 | `MAX_INPUT_TOKENS` defaults to 8,000 — overridable via `MAX_INPUT_TOKENS` env var |

---

## GitHubClient Rules

| ID | Rule |
|---|---|
| GHC-01 | All GitHub API requests MUST include `Authorization: Bearer {GITHUB_TOKEN}` |
| GHC-02 | Rate limit responses (429) MUST respect `Retry-After` header |
| GHC-03 | Server errors (5xx) MUST be retried up to 3 times with exponential backoff |
| GHC-04 | Client errors (4xx except 429) MUST NOT be retried |
| GHC-05 | After 3 failed attempts, GitHub API calls MUST return `None` and log a warning |
| GHC-06 | Fix branches MUST follow naming: `fix/{identifier}-pr-{pr_number}` |
| GHC-07 | Fix PRs MUST target the original PR's head branch (not `main`) |
| GHC-08 | Fix PR body MUST reference the original PR number and finding details |

---

## RuleLoader Rules

| ID | Rule |
|---|---|
| RUL-01 | Rule files MUST be loaded from `.aidlc-rule-details/` relative to workspace root |
| RUL-02 | Missing rule files MUST log a warning and continue (not crash) |
| RUL-03 | Excerpt-only files MUST be capped at 2,000 characters |
| RUL-04 | All agents MUST receive `common/depth-levels.md` (first 3 paragraphs) |
| RUL-05 | Rule content MUST be separated by `\n\n---\n\n` when multiple files are concatenated |
| RUL-06 | Assembled context MUST be prepended with `# AI-DLC Rules Context\n\n` |
