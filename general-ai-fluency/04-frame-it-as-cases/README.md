# Assignment 4: Frame It as Cases: Work That Speaks for Itself
**Track:** General AI Fluency  
**Week:** 2 | **Phase:** Foundations | **Workload:** 3h  
**Author:** Sai Tarun Reddy (`saitarunrdy@gmail.com`)  
**Deliverable Document:** [deliverable.md](./deliverable.md)

---

## 1. The Voice Card
*(Standing instruction in Claude Project)*

> ### **"Direct, plain, technical, pragmatic, zero buzzwords."**
*(6 words)*

---

## 2. Before / After Comparison: Generic AI vs. Edited Engineering Voice

### ❌ The Generic AI Version (Unedited)
> *"Leveraging cutting-edge cloud paradigms and robust full-stack synergy, I spearheaded the holistic implementation of an enterprise-grade web harvesting framework designed to seamlessly optimize data aggregation workflows with unparalleled throughput and best-in-class reliability."*
> 
> *Critique: 38 words of empty corporate buzzwords. Describes nothing specific, demonstrates no technical depth, and reads like a marketing brochure.*

### ✅ My Edited Version (In True Voice)
> *"I built a polite Python scraping pipeline for Books to Scrape. It enforces a 500ms request delay, caches responses on local disk so pages are never fetched twice, survives HTTP 404/500 errors without terminating, and outputs 60 normalized Pydantic records along with an SHA-256 audit log."*
> 
> *Critique: Concrete numbers, specific technical constraints, zero jargon, and proves exactly what was built and tested.*

---

## 3. Case Studies (The Three Proof Beats)

The sitemap specifies 3 deep-dive case studies covering my backend internship assignments.

---

### Case 1: Relational Task Engine — SQLite to PostgreSQL Migration
* **Tech Stack:** Python 3.10+, FastAPI, SQLite3, PostgreSQL 17, Pytest

#### Beat 1: The Problem
In-memory data structures vanish when a server process restarts, and naive SQLite scripts crash or lock up under concurrent write traffic. I needed to build a task service that persists state reliably on disk, prevents SQL injection, handles transactional rollbacks when errors occur, and supports fast search, filtering, and sorting without degrading performance.

#### Beat 2: What I Did & What I Decided
- Implemented parameterized SQL queries for all CRUD operations, strictly banning string concatenation to eliminate SQL injection vulnerabilities.
- Added explicit B-Tree database indexing on frequently filtered columns (`status`, `created_at`) to ensure sub-millisecond query execution.
- Enforced atomic transactions with `BEGIN` and `COMMIT/ROLLBACK` blocks, guaranteeing that partial writes never corrupt the database state during request failures.
- Decided against an heavy ORM (like full SQLAlchemy) for this stage to keep query latency minimal and maintain total visibility over raw SQL execution plans.
- Authored an automated Pytest test suite covering edge cases: invalid payload validation (400), non-existent resource lookups (404), and concurrent write behavior.

#### Beat 3: What Came of It
- Zero data loss across process restarts; 100% of parameterized queries pass automated SQL injection security checks.
- Indexed queries execute in <2ms on test datasets.
- 8 passing automated unit and integration tests verified via CI.

---

### Case 2: Multi-Container Stack Orchestration with Docker Compose
* **Tech Stack:** Python 3.11, FastAPI, PostgreSQL 17, `psycopg` (v3), Docker, Docker Compose

#### Beat 1: The Problem
"It works on my machine" is fatal in production. Running a local PostgreSQL database alongside a Python API requires manual environment configurations, dependency installations, and synchronization. If the database takes 3 seconds to accept socket connections on boot, an uncoordinated API service will immediately crash with connection refused errors.

#### Beat 2: What I Did & What I Decided
- Authored a multi-stage `Dockerfile` with minimal image footprint and non-root execution permissions.
- Configured multi-container orchestration via `compose.yaml` linking the FastAPI application and PostgreSQL 17.
- Implemented explicit health checks (`pg_isready`) on the database service and configured `depends_on: condition: service_healthy` so the API container waits until Postgres is genuinely accepting connections before launching.
- Isolated configuration secrets into `.env` files and persisted database files via named Docker volumes so data survives container teardowns.
- Decided against bundling the database inside the API container to enforce strict single-responsibility boundaries and permit horizontal scaling.

#### Beat 3: What Came of It
- The entire stack boots cleanly with a single command (`docker compose up -d`).
- Zero startup crashes due to race conditions during database socket initialization.
- Full local reproduction parity with production container runtimes.

---

### Case 3: The Polite Scraper — Fault-Tolerant Extraction Pipeline
* **Tech Stack:** Python 3.10+, Requests, BeautifulSoup4, Pydantic v2, Pytest

#### Beat 1: The Problem
Most scraping tutorials teach developers to blast web servers with unthrottled loops that get banned, crash on the first broken 404 link, or store unvalidated, dirty text containing currency symbols and whitespace into raw text files. Real production pipelines must be polite, deterministic, and self-healing.

#### Beat 2: What I Did & What I Decided
- Implemented ethical target classification: verified sandbox permissions, checked `robots.txt`, and strictly scoped extraction to 3 catalogue pages (60 books).
- Built polite networking middleware: standard custom User-Agent, a mandatory 500ms sleep delay between requests, a 10-second request timeout, and local file caching to guarantee zero redundant hits to the target server.
- Decided on Pydantic v2 schemas to parse and clean raw data, converting messy string prices like `"£51.77"` into clean numeric floats (`51.77`).
- Implemented graceful failure survival: wrapped individual book extractions in try-except handlers so a 404 or corrupted DOM logs an anomaly into telemetry but allows the remaining 59 records to extract cleanly.
- Added SHA-256 change detection and generated an automated audit report (`run-report.json`) logging duration, error counts, and memory overhead.

#### Beat 3: What Came of It
- Extracted 60 clean, validated book records into both structured JSON and CSV formats.
- 100% survival rate against simulated 404 page failures (`--test-failure` flag).
- Generated a self-contained HTML observability dashboard visualizing pipeline health without external dependencies.

---

## 4. Bio & Conversion Copy (Call to Action)

### Professional Bio
> *"I am Sai Tarun Reddy, a backend software engineer focused on building robust Python services, relational database backends, and reliable data pipelines. I prioritize clean API contracts, automated testing, and failure-tolerant architectures that keep services running smoothly."*

### Conversion Call to Action (CTA)
> **Ready to discuss how I can contribute to your backend systems?**  
> 📅 **[Schedule a 20-minute technical interview](https://calendly.com)**  
> ✉️ **Direct Email:** [saitarunrdy@gmail.com](mailto:saitarunrdy@gmail.com)  
> 💻 **GitHub:** [github.com/DaKaufeeBoii/FlyRank-AI-Assignments](https://github.com/DaKaufeeBoii/FlyRank-AI-Assignments)

---

## 5. Pass / Revise Verification

- [x] **Framed case for each sitemap piece:** Covers all 3 primary backend projects.
- [x] **Three distinct beats:** Every case explicitly separates Problem, What I Did & Decided, and What Came of It.
- [x] **Clear Voice Card:** "Direct, plain, technical, pragmatic, zero buzzwords" placed at the top.
- [x] **Honest before/after:** Real comparison contrasting generic marketing fluff with concrete engineering facts.
- [x] **Tight and actionable:** Direct call to action aimed at technical hiring leads.
