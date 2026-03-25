# Unit 3 — PR Review Pipeline: Functional Design

## Overview
Four parallel agents review every PR against security, architecture, requirements, and test-coverage rules. Results are posted as a GitHub review (APPROVE / COMMENT / REQUEST_CHANGES).

## Agents

| Agent | Input | Output Fields |
|---|---|---|
| SecurityAgent | PR diff + changed files | `findings[]` (rule_id, severity, message, file, fix_code?) |
| ArchitectureAgent | PR diff + design docs | `findings[]` |
| RequirementsAgent | PR + linked issue | `resolves_issue`, `gaps[]`, `rationale` |
| TestCoverageAgent | PR changed files | `findings[]`, `fix_code` (test stubs) |

## Review Event Logic

| Highest severity | GitHub review event |
|---|---|
| critical or high | `REQUEST_CHANGES` |
| medium or low | `COMMENT` |
| no findings | `APPROVE` |

## Fix Pipeline Integration
Any finding with `fix_code` is passed to `FixService` after the review is posted. Fix PRs target `pr.head_branch` so fixes travel with the original PR.

## Business Rules
- **SecurityAgent** maps to SECURITY-01 through SECURITY-15 from `security-baseline.md`.
- **ArchitectureAgent** loads `components.md` and `component-dependency.md` from `aidlc-docs/`.
- **RequirementsAgent** only checks requirements if PR body references a linked issue; otherwise `resolves_issue: true`.
- **TestCoverageAgent** skips config files, `__init__.py`, YAML, and Markdown.
- Fix module is imported optionally — PR review works without it.

## Parallelism
All four agents run via `ThreadPoolExecutor(max_workers=4)` with a 240 s timeout.
