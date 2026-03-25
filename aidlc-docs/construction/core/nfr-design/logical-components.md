# Logical Components — Unit 1: Core Infrastructure

No external infrastructure services are required for Unit 1. All components are in-process within the GitHub Actions runner.

---

## In-Process Components

| Component | Type | Notes |
|---|---|---|
| Orchestrator | Python module | Entry point, runs in GitHub Actions job |
| BaseAgent | Python abstract class | Extended by all agents |
| GitHubClient | Python class | HTTP wrapper around GitHub REST API |
| RuleLoader | Python class | Filesystem reads of `.aidlc-rule-details/` |
| ThreadPoolExecutor | Python stdlib | Parallel agent execution within a job |

---

## External Services (No Infrastructure Setup Required)

| Service | Access | Auth |
|---|---|---|
| GitHub REST API | HTTPS | `GITHUB_TOKEN` (auto-injected) |
| GitHub Models API | HTTPS | `GITHUB_TOKEN` (auto-injected) |

---

## Future Infrastructure (Terraform — Placeholder)

These are not needed for Unit 1 but scaffolded for later:

| Resource | Purpose | When Needed |
|---|---|---|
| Terraform Cloud workspace | Remote state management | When AWS resources are provisioned |
| AWS OIDC Provider | Keyless GitHub → AWS auth | When Terraform needs AWS access |
| S3 bucket (optional) | Alternate Terraform state backend | Alternative to Terraform Cloud |

Scaffolded at: `infra/terraform/` (empty, commented placeholders)
