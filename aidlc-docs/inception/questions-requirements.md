# Requirements Analysis — Questions

Please fill in your answers after each `[Answer]:` line.

---

**Q1. What is the primary purpose of this multi-agent system?**

A. Automate the AI-DLC workflow itself (e.g., agents execute inception, construction, operations stages autonomously)
B. A general-purpose orchestration platform that can run arbitrary agent workflows
C. A specific domain workflow (e.g., code review pipeline, data processing, CI/CD automation)
D. A developer-facing SDK/framework others can use to build their own multi-agent systems
E. Other — please describe

[Answer]:

---

**Q2. Which AI provider / model runtime are you targeting?**

A. Anthropic Claude (via Claude API / claude-agent-sdk)
B. OpenAI
C. Provider-agnostic (abstract over multiple providers)
D. Local/self-hosted models (Ollama, vLLM, etc.)
E. Other — please describe

[Answer]:

---

**Q3. What should the orchestrator be responsible for?**

A. Routing tasks to the right agent and collecting results (simple coordinator)
B. Dynamic planning — decomposing a high-level goal into subtasks and assigning them at runtime
C. Stateful workflow management — tracking stage progress, retries, and approvals (mirrors AI-DLC phases)
D. All of the above
E. Other — please describe

[Answer]:

---

**Q4. How should agents communicate?**

A. Direct function/API calls (in-process)
B. Message queue / event bus (e.g., Redis, RabbitMQ, Kafka)
C. HTTP/REST between services
D. Shared database / state store
E. Other — please describe

[Answer]:

---

**Q5. What is the expected deployment target?**

A. Single machine / local dev tool (CLI)
B. Containerized services (Docker / Kubernetes)
C. Serverless (AWS Lambda, Cloud Functions)
D. Cloud-managed AI platform (AWS Bedrock, Azure AI, GCP Vertex)
E. Other — please describe

[Answer]:

---

**Q6. Which extensions would you like enforced throughout the workflow?**

A. Security Baseline — enforces 15 security rules (encryption, access control, input validation, OWASP Top 10 2025 mapped)
B. Property-Based Testing — enforces generative/property-based tests alongside unit tests
C. Both A and B
D. Neither — keep it minimal for now

[Answer]:
