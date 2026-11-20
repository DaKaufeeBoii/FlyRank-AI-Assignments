# FlyRank AI Internship — Track Deliverables & Capstones

**Author:** Sai Tarun Reddy (`saitarunrdy@gmail.com`)  
**Repository:** [FlyRank-AI-Assignments](https://github.com/DaKaufeeBoii/FlyRank-AI-Assignments)

This repository contains the complete portfolio of weekly assignments and production capstones for the FlyRank Internship across two tracks:
1. **Backend AI Engineering Track** (5/5 assignments + Accepted Capstone)
2. **General AI Fluency Track** (5/5 assignments + Accepted Capstone)

---

## 🌟 Featured Track Capstones

### 1. Backend AI Engineering Capstone: [TokenPulse — Usage Metering & Billing Engine](./tokenpulse-billing-engine/)
* **Stack:** Python 3.10+, FastAPI, SQLite3 (WAL mode), Pydantic v2, Pytest, Stripe Test Mode
* **Focus:** Guaranteed exactly-once metering under retries, zero double charges via idempotency keys, boundary-honest quota enforcement (429 vs 402), integer-based token pricing math (cached input discounts, reasoning token output classification), and cryptographically verified Stripe webhooks.
* **Probes Verified:** 5/5 Acceptance Probes passed.
* **Explore:** [tokenpulse-billing-engine/](./tokenpulse-billing-engine/) | [EVIDENCE.md](./tokenpulse-billing-engine/EVIDENCE.md) | [BUILDLOG.md](./tokenpulse-billing-engine/BUILDLOG.md)

### 2. General AI Fluency Capstone: [CogniFlow — Intelligent Incident Triage & ROI Engine](./cogniflow-ai-impact-project/)
* **Stack:** Python 3.10+, Pydantic v2, Pytest, Standalone HTML Observability Dashboard
* **Focus:** End-to-end operational AI pipeline transforming chaotic production error logs into structured root-cause analysis, severity classifications (SEV-1 to SEV-3), and dual-audience communications (internal briefs vs plain-English external customer updates with zero buzzwords).
* **ROI Achieved:** 93.3% reduction in triage toil; 560 engineering hours reclaimed; $44,800 net annual business ROI.
* **Explore:** [cogniflow-ai-impact-project/](./cogniflow-ai-impact-project/) | [EVIDENCE.md](./cogniflow-ai-impact-project/EVIDENCE.md) | [BUILDLOG.md](./cogniflow-ai-impact-project/BUILDLOG.md)

---

## 📚 General AI Fluency Track (`general-ai-fluency/`)
*Meets the 5-assignment threshold required for the General AI Fluency completion certificate.*

| Code / Assignment | Week | Description | Link |
|---|---|---|---|
| **What Are You Proving?** | Week 1 | One-paragraph proof statement, one-line why, and AI thinking-partner pressure test interview. | [Details](./general-ai-fluency/01-what-are-you-proving/) |
| **FL-01: AI Workflow Audit & Tool Setup** | Week 1 | 12-task real weekly audit table, Claude project configuration, and 3 target tasks with success criteria. | [Details](./general-ai-fluency/02-workflow-audit-and-tool-setup/) |
| **Draw the Path: Portfolio Sitemap + Toolkit** | Week 1 | Conversion-oriented portfolio sitemap, AI pressure-test critique, and single-page redesign. | [Details](./general-ai-fluency/03-portfolio-sitemap-and-toolkit/) |
| **Frame It as Cases: Work That Speaks for Itself** | Week 2 | Voice card ("direct, plain, technical, pragmatic, zero buzzwords"), before/after AI comparison, and 3 case studies. | [Details](./general-ai-fluency/04-frame-it-as-cases/) |
| **The Prompt Ladder** | Week 2 | 6 runs (baseline + 5 incremental layers), evaluation of output regression, and final reusable prompt. | [Details](./general-ai-fluency/05-the-prompt-ladder/) |

---

## 🛠️ Backend AI Engineering Track (`backend-ai-engg/`)
*Meets the 5-assignment threshold required for the Backend AI Engineering completion certificate.*

| Assignment | Tech Stack | Core Highlights | Link |
|---|---|---|---|
| **Assignment 1: In-Memory CRUD API** | FastAPI, Pydantic, Uvicorn | Full CRUD endpoints, Pydantic data validation, 400/404 handling, Swagger UI docs. | [Details](./backend-ai-engg/ass-1/) |
| **Assignment 2: Connecting CRUD to SQLite** | SQLite3, FastAPI, Pytest | Persistent disk storage (`tasks.db`), parameterized queries, B-Tree indexing, transactions, Pytest. | [Details](./backend-ai-engg/ass-2/) |
| **Assignment 3: Containerize Your Stack** | Docker, Docker Compose, PostgreSQL 17 | Multi-container orchestration, volume persistence, `pg_isready` health checks, `.env` management. | [Details](./backend-ai-engg/ass-3/) |
| **Assignment 4: Auth · Login & Protect** | Supabase Auth, JWT, FastAPI | Signup, login, logout, protected routes, HTTPBearer verification, role-based access control (RBAC). | [Details](./backend-ai-engg/ass-4/) |
| **Assignment 5: The Polite Scraper** | Requests, BeautifulSoup4, Pydantic v2 | 500ms rate limiting, local disk cache, failure tolerance (404/5xx survival), JSON/CSV exports, dashboard. | [Details](./backend-ai-engg/ass-5/) |
