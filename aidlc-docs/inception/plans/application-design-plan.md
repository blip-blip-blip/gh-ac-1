# Application Design Plan
**Date**: 2026-03-24
**Status**: Awaiting Answers

---

## Design Artifacts to Generate
- [ ] `components.md` — component definitions and responsibilities
- [ ] `component-methods.md` — method signatures per component
- [ ] `services.md` — service definitions and orchestration
- [ ] `component-dependency.md` — dependency relationships and data flow
- [ ] `application-design.md` — consolidated design document

---

## Proposed Component Map

Based on the approved workflow plan, here are the identified components:

```
+--------------------+     +--------------------+     +--------------------+
|    Orchestrator    |---->|   Issue Triage     |     |    PR Review       |
|                    |     |   Service          |     |    Service         |
|  - parse event     |     |                    |     |                    |
|  - route pipeline  |---->|   Fix Service      |     |  Reporting Service |
|  - manage results  |     |                    |     |                    |
+--------------------+     +--------------------+     +--------------------+
         |
         v
+--------------------+     +--------------------+
|    Base Agent      |     |   GitHub Client    |
|  - call AI model   |     |  - post comments   |
|  - load rules      |     |  - apply labels    |
|  - retry logic     |     |  - create branches |
+--------------------+     |  - open PRs        |
         |                 +--------------------+
         v
+--------------------+
|    Rule Loader     |
|  - read .aidlc-    |
|    rule-details/   |
|  - chunk context   |
+--------------------+
```

---

## Clarifying Questions

### Q1. Orchestrator routing — how should it decide which agents to run?

A. Fixed pipeline — always run all agents for that event type (e.g., every PR gets all 4 review agents)
B. Dynamic routing — orchestrator asks the AI model which agents are relevant based on the event
C. Config-driven — a YAML/JSON config file per repo defines which agents to enable/disable
D. Other — describe

[Answer]:A

---

### Q2. How should AI-DLC rules be passed to agents?

A. Full file contents injected into every agent's system prompt
B. Relevant sections only — rule loader extracts the applicable rules per agent type
C. Summarized version — pre-summarize rules once, inject the summary
D. Other — describe

[Answer]:B

---

### Q3. Duplicate issue detection — how should it work?

A. Keyword/title similarity using simple string matching
B. Ask the AI model to compare the new issue against recent open issues (last 50)
C. Both — string match first, AI comparison as fallback
D. Other — describe

[Answer]: B

---

### Q4. Fix Agent — when an agent finds an issue, how should it decide what fix to apply?

A. The same agent that found the issue also generates the fix code
B. A separate dedicated Fix Agent receives the finding + original code and generates the fix
C. Other — describe

[Answer]: A

---

### Q5. Agent output format — how should agents return their findings to the aggregator?

A. Structured JSON (finding type, severity, file, line, message, suggested fix)
B. Free-form text that the aggregator summarises
C. Other — describe

[Answer]: A

---

### Q6. Trend Reporter — where should the weekly report be posted?

A. New GitHub Issue (searchable, commentable, closeable)
B. A dedicated `TREND-REPORT.md` file committed to the repo
C. Both — issue for visibility, file for history
D. Other — describe

[Answer]: C

---

### Q7. Permissions model — should any agent findings be able to block a PR merge?

A. No — all findings are advisory only, humans decide
B. Yes — CRITICAL security findings (SECURITY-01–15) block merge via required status check
C. Other — describe

[Answer]: A
