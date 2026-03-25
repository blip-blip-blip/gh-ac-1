# Business Logic Model — Unit 1: Core Infrastructure

---

## Orchestrator Logic

### Event Parsing
1. Read `GITHUB_EVENT_NAME` and `GITHUB_EVENT_PATH` from environment
2. Load event JSON from `GITHUB_EVENT_PATH`
3. Match event name:
   - `issues` → extract `action`, `issue` object → route to IssueTriage Service
   - `pull_request` → extract `action`, `pull_request` object → route to PRReview Service
   - anything else → log warning to stdout: `"Unsupported event type: {event_name}, skipping"` → exit 0

### Routing Rules
```
event_name == "issues" AND action in ["opened", "edited"]  → IssueTriage
event_name == "pull_request" AND action in ["opened", "synchronize"]  → PRReview
otherwise  → warn + skip
```

---

## BaseAgent Logic

### AI Call Flow
1. Call `build_system_prompt()` → get rule context for this agent type
2. Assemble user prompt from input data
3. Check input token estimate:
   - If estimated tokens > `MAX_INPUT_TOKENS` (default: 8,000):
     - Log warning: `"Input truncated from {actual} to {max} tokens for {agent_type}"`
     - Truncate input to fit within budget
4. Call GitHub Models API via `requests.post()`
5. Parse JSON response
6. Validate against expected output schema
7. Return validated dict

### Retry Logic
```
attempt = 1
while attempt <= 3:
    try:
        response = call_github_models_api(...)
        return parse_and_validate(response)
    except (APIError, JSONDecodeError, SchemaError) as e:
        if attempt == 3:
            log_warning(f"Agent {agent_type} failed after 3 attempts: {e}")
            return None   ← signals partial result to aggregator
        wait = 2 ** attempt  ← 2s, 4s backoff
        sleep(wait)
        attempt += 1
```

### Partial Result Contract
- Any agent returning `None` is treated as a failed agent
- Aggregators must handle `None` entries gracefully
- Failed agents are noted in the final GitHub comment/review

---

## GitHubClient Logic

### Authentication
- Read `GITHUB_TOKEN` from environment
- Set `Authorization: Bearer {token}` on all requests
- Set `Accept: application/vnd.github+json`
- Set `X-GitHub-Api-Version: 2022-11-28`

### GitHub API Retry
```
attempt = 1
while attempt <= 3:
    response = requests.request(method, url, ...)
    if response.status_code in [200, 201, 204]:
        return response
    if response.status_code == 429:         ← rate limited
        wait = int(response.headers.get("Retry-After", 60))
        sleep(wait)
    elif response.status_code >= 500:       ← server error
        sleep(2 ** attempt)
    else:
        raise GitHubAPIError(response)      ← 4xx, don't retry
    attempt += 1

if attempt > 3:
    log_warning(f"GitHub API failed after 3 attempts: {url}")
    return None   ← caller handles partial result
```

### Fix Branch Naming Convention
```
fix/{rule-id-or-agent}-pr-{pr_number}
Examples:
  fix/SECURITY-05-pr-42
  fix/test-coverage-pr-42
```

---

## RuleLoader Logic

### Static Agent → Rule File Mapping
```python
RULE_MAP = {
    "security":      ["extensions/security/baseline/security-baseline.md"],
    "classifier":    ["common/overconfidence-prevention.md"],
    "severity":      ["common/overconfidence-prevention.md"],
    "component":     ["common/overconfidence-prevention.md"],
    "reproduction":  ["common/question-format-guide.md",
                      "common/overconfidence-prevention.md"],
    "duplicate":     ["common/overconfidence-prevention.md"],
    "architecture":  ["common/depth-levels.md",
                      "common/overconfidence-prevention.md"],
    "requirements":  ["common/overconfidence-prevention.md"],
    "test_coverage": ["common/overconfidence-prevention.md"],
}
# All agents also receive: common/depth-levels.md (first 3 paragraphs only)
```

### File Loading
1. Resolve path: `{RULES_BASE_PATH}/{relative_path}`
2. Read file contents
3. For excerpt-only files: extract up to first 2,000 characters
4. Concatenate all files for the agent type with `\n\n---\n\n` separator
5. Prepend header: `"# AI-DLC Rules Context\n\n"`
6. Return assembled string
