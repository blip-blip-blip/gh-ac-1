# Unit of Work Plan
**Date**: 2026-03-24
**Status**: Approved — generating artifacts

---

## Artifacts to Generate
- [x] `aidlc-docs/inception/application-design/unit-of-work.md` — unit definitions and responsibilities
- [x] `aidlc-docs/inception/application-design/unit-of-work-dependency.md` — dependency matrix and build order
- [x] `aidlc-docs/inception/application-design/unit-of-work-story-map.md` — capabilities mapped to units

---

## Proposed Units (from approved workflow plan)

| Unit | Name | Description |
|---|---|---|
| 1 | Core Infrastructure | Orchestrator, BaseAgent, GitHubClient, RuleLoader — foundation everything depends on |
| 2 | Issue Triage Pipeline | 5 parallel agents + IssueAggregator |
| 3 | PR Review Pipeline | 4 parallel agents + PRAggregator |
| 4 | Auto-Fix Pipeline | Fix branch creation, fix commits, fix PR opening |
| 5 | Cross-Reference & Trend Reporting | Issue↔PR linker + weekly TrendReporter |

---

## Clarifying Questions

### Q1. Development sequence — should units be built strictly one at a time, or can any overlap?

A. Strictly sequential — Unit 1 → 2 → 3 → 4 → 5 (safest, simpler)
B. Unit 1 first, then Units 2 and 3 in parallel (faster if working with others)
C. Other — describe

[Answer]: B — Unit 1 first, then Units 2 and 3 in parallel (multi-agent / multi-team), then 4 and 5 sequentially

---

### Q2. Code organisation — how should units be structured within the repo?

A. Flat modules — all agents live under `agents/` as Python modules (simplest)
B. Separate packages — each unit is its own Python package with its own `__init__.py` and `requirements.txt`
C. Other — describe

[Answer]: B — separate packages, multi-agent and multi-team working in parallel

---

### Q3. Should Unit 4 (Auto-Fix) be a standalone pipeline or embedded inside Units 2 and 3?

A. Embedded — fix logic lives inside SecurityAgent and TestCoverageAgent directly (fewer files)
B. Standalone — `agents/fix/` module called by agents when fix_code is present (cleaner separation)
C. Other — describe

[Answer]: B — standalone fix/ package, shared and reusable across all agents
