# NFR Design Patterns — Unit 1: Core Infrastructure

---

## Retry Pattern (Exponential Backoff)

Applied to: BaseAgent AI calls, GitHubClient API calls

```
Attempt 1 → fail → wait 2s
Attempt 2 → fail → wait 4s
Attempt 3 → fail → return None + log warning
```

**Implementation**: Shared `retry()` utility in `base_agent.py`, reused by `github_client.py`.

---

## Partial Result Pattern

Applied to: IssueTriage Service, PRReview Service

When one or more agents return `None`:
- Aggregator skips `None` results
- Aggregator includes a notice in the GitHub comment:
  ```
  ⚠️ Note: {agent_type} agent did not complete (see Actions log for details).
  Results below are based on {n}/{total} agents.
  ```
- Job exits with success (not failure) — partial results are better than no results

---

## Soft Token Budget Pattern

Applied to: BaseAgent

```
estimate_tokens(input_text) → token_count
if token_count > MAX_INPUT_TOKENS:
    log warning with counts
    input_text = truncate_to_budget(input_text, MAX_INPUT_TOKENS)
proceed with truncated input
```

Truncation strategy: keep first N characters of the diff/body (preserves file headers and early context which tend to be most relevant).

---

## Graceful Unknown Event Pattern

Applied to: Orchestrator

```
if event_name not in SUPPORTED_EVENTS:
    print(f"[orchestrator] WARNING: Unsupported event type: {event_name}, skipping")
    sys.exit(0)   ← success exit, no GitHub comment posted
```

---

## Structured Output Contract Pattern

Applied to: All agents → Aggregators

Every agent output is validated against a schema before being returned. Schema is defined per agent class as a class-level constant. Aggregators can safely destructure outputs without defensive checks beyond `None`.

```python
OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["severity", "rationale"],
    "properties": {
        "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
        "rationale": {"type": "string"}
    }
}
```
