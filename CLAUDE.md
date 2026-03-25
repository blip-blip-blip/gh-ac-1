# Claude Code Instructions

## AI-DLC Workflow Auto-Ingestion

At the start of every session, **automatically** read and ingest the following files before responding to any software development request — do NOT wait for the user to ask:

1. `.github/copilot-instructions.md` — main AI-DLC workflow rules
2. All files under `.aidlc-rule-details/` recursively — phase and extension rule details

This project uses the AI-DLC (AI Development Lifecycle) adaptive workflow. The instructions in `.github/copilot-instructions.md` override all default Claude Code behaviors for software development tasks.
