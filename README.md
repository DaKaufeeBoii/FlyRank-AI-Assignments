# FlyRank AI Internship — Track Deliverables & Portfolios

**Author:** Sai Tarun Reddy (`saitarunrdy@gmail.com`)  
**Repository:** [FlyRank-AI-Assignments](https://github.com/DaKaufeeBoii/FlyRank-AI-Assignments)

This repository contains the weekly assignments, systems, and artifacts for the FlyRank Internship across two tracks:
1. **[Backend AI Engineering Track](./backend-ai-engg/)** (5/5 assignments complete)
2. **[General AI Fluency Track](./general-ai-fluency/)** (5/5 assignments complete)

---

## 1. General AI Fluency Track (`general-ai-fluency/`)
*Meets the 5-assignment threshold required for the General AI Fluency completion certificate.*

| Code / Assignment | Week | Description | Link |
|---|---|---|---|
| **What Are You Proving?** | Week 1 | One-paragraph proof statement, one-line why, and AI thinking-partner pressure test interview. | [Details](./general-ai-fluency/01-what-are-you-proving/) |
| **FL-01: AI Workflow Audit & Tool Setup** | Week 1 | 12-task real weekly audit table, Claude project configuration, and 3 target tasks with success criteria. | [Details](./general-ai-fluency/02-workflow-audit-and-tool-setup/) |
| **Draw the Path: Portfolio Sitemap + Toolkit** | Week 1 | Conversion-oriented portfolio sitemap, AI pressure-test critique, and single-page redesign. | [Details](./general-ai-fluency/03-portfolio-sitemap-and-toolkit/) |
| **Frame It as Cases: Work That Speaks for Itself** | Week 2 | Voice card ("direct, plain, technical, pragmatic, zero buzzwords"), before/after AI comparison, and 3 case studies. | [Details](./general-ai-fluency/04-frame-it-as-cases/) |
| **The Prompt Ladder** | Week 2 | 6 runs (baseline + 5 incremental layers), evaluation of output regression, and final reusable prompt. | [Details](./general-ai-fluency/05-the-prompt-ladder/) |

---

## 2. Backend AI Engineering Track (`backend-ai-engg/`)
*Meets the 5-assignment threshold required for the Backend AI Engineering completion certificate.*

| Assignment | Tech Stack | Core Highlights | Link |
|---|---|---|---|
| **Assignment 1: In-Memory CRUD API** | FastAPI, Pydantic, Uvicorn | Full CRUD endpoints, Pydantic data validation, 400/404 handling, Swagger UI docs. | [Details](./backend-ai-engg/ass-1/) |
| **Assignment 2: Connecting CRUD to SQLite** | SQLite3, FastAPI, Pytest | Persistent disk storage (`tasks.db`), parameterized queries, B-Tree indexing, transactions, Pytest. | [Details](./backend-ai-engg/ass-2/) |
| **Assignment 3: Containerize Your Stack** | Docker, Docker Compose, PostgreSQL 17 | Multi-container orchestration, volume persistence, `pg_isready` health checks, `.env` management. | [Details](./backend-ai-engg/ass-3/) |
| **Assignment 4: Auth · Login & Protect** | Supabase Auth, JWT, FastAPI | Signup, login, logout, protected routes, HTTPBearer verification, role-based access control (RBAC). | [Details](./backend-ai-engg/ass-4/) |
| **Assignment 5: The Polite Scraper** | Requests, BeautifulSoup4, Pydantic v2 | 500ms rate limiting, local disk cache, failure tolerance (404/5xx survival), JSON/CSV exports, dashboard. | [Details](./backend-ai-engg/ass-5/) |

---

## Running Backend Projects Locally

### Run Assignment 3 (Docker Compose)
```bash
cd backend-ai-engg/ass-3
docker compose up -d
curl http://localhost:3000/health
```

### Run Assignment 5 (The Polite Scraper)
```bash
cd backend-ai-engg/ass-5
pip install -r requirements.txt
python main.py
python -m pytest -v tests/test_scraper.py
```
