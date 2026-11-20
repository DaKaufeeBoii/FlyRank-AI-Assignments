# AI Workflow Audit & Tool Setup (FL-01) — Deliverable
**Intern:** Sai Tarun Reddy  
**Track:** General AI Fluency  
**Date:** November 2026  

---

## 1. Weekly Task Classification Audit

| # | Task | Category | Rationale |
|---|---|---|---|
| 1 | Architecture & Trade-off Decisions | **Just Me** | High-stakes engineering choices require human responsibility and context. |
| 2 | Personal Career Vision & Ethics | **Just Me** | Ethical commitments cannot be outsourced to statistical language models. |
| 3 | Boilerplate CRUD Endpoints & Schemas | **Delegate with Review** | Highly structured boilerplate; AI drafts quickly, human verifies field types. |
| 4 | Unit & Integration Test Generation | **Delegate with Review** | AI generates edge-case test matrices; human validates assertion logic. |
| 5 | SQL Query & Indexing Strategies | **Collaborate with AI** | Accelerated database performance tuning through iterative query analysis. |
| 6 | Debugging Error Traces & Race Conditions | **Collaborate with AI** | Rubber-ducking complex concurrency issues exposes hidden failure points. |
| 7 | System API Contract Design | **Collaborate with AI** | Exploring REST conventions and response formats with AI pressure testing. |
| 8 | Code Linting, Formatting, Import Sorting | **Fully Automate** | Handled deterministically via `ruff` and Git pre-commit hooks. |
| 9 | CI / Automated Test Pipeline | **Fully Automate** | GitHub Actions runs `pytest` and Docker health checks on push. |
| 10 | Daily Scraping Change Detection | **Fully Automate** | Scheduled background jobs compute SHA-256 diffs and audit telemetry. |
| 11 | Drafting Technical Documentation | **Delegate with Review** | AI arranges raw technical notes into structured markdown; human checks accuracy. |
| 12 | Refactoring Code for Readability | **Collaborate with AI** | Comparing structural patterns (repository vs active record) sharpens design. |

---

## 2. Configured Claude Project

* **Project Name:** `FlyRank-Backend-AI-Mentor`
* **Standing Instructions:** Configured with Sai's Core Proof Statement, requesting a direct, pragmatic, buzzword-free technical mentor who challenges assumptions, prioritizes defensive programming (error handling, atomic transactions, idempotency), and reviews backend systems for production readiness.
* **Enrollment:** Anthropic Academy (*AI Fluency: Framework & Foundations* Module 1 completed).

---

## 3. Three Target Tasks with Success Criteria

1. **API Error Handling & Structured Response Design**
   * *Done Well:* Consistent `{ "detail": str, "error_code": str, "timestamp": str }` schema; zero leaked 500 tracebacks; strict adherence to HTTP status codes.
2. **Database Migration & Schema Indexing Strategy**
   * *Done Well:* Indexed search queries execute under 5ms on 50k rows; strict transaction rollback on failure; typed Pydantic models.
3. **Resilient Web Scraping Pipeline**
   * *Done Well:* Polite 500ms rate limiting; local disk caching; graceful 404/5xx error handling without crashes; verified `run-report.json` telemetry.
