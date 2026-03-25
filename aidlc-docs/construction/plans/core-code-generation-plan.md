# Unit 1 — Core Infrastructure: Code Generation Plan
**Date**: 2026-03-24
**Status**: Approved — executing

---

## Steps

- [x] Step 1: Project structure setup — `agents/core/` package scaffold
- [x] Step 2: `pyproject.toml` + `requirements.txt` + `.python-version`
- [x] Step 3: `rule_loader.py` — AI-DLC rule file loader
- [x] Step 4: `github_client.py` — GitHub REST API wrapper
- [x] Step 5: `base_agent.py` — abstract base with retry, token budget, schema validation
- [x] Step 6: `orchestrator.py` — event parser and router
- [x] Step 7: Tests — `tests/test_rule_loader.py`
- [x] Step 8: Tests — `tests/test_github_client.py`
- [x] Step 9: Tests — `tests/test_base_agent.py`
- [x] Step 10: Tests — `tests/test_orchestrator.py`
- [x] Step 11: GitHub Actions workflows — `issue-triage.yml`, `pr-review.yml`, `trend-report.yml`
- [x] Step 12: Terraform scaffold — `infra/terraform/` placeholder files
