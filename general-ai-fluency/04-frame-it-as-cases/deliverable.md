# Framed Case Studies: Work That Speaks for Itself — Deliverable
**Intern:** Sai Tarun Reddy  
**Track:** General AI Fluency  
**Assignment Code:** FL-Cases  
**Date:** November 2026  

---

## Voice Card
> **"Direct, plain, technical, pragmatic, zero buzzwords."**

---

## Before & After: Voice Differentiation

* **Generic AI Copy (Before):**  
  *"Leveraging cutting-edge cloud paradigms and robust full-stack synergy, I spearheaded the holistic implementation of an enterprise-grade web harvesting framework designed to seamlessly optimize data aggregation workflows with unparalleled throughput and best-in-class reliability."*
* **Edited Engineering Voice (After):**  
  *"I built a polite Python scraping pipeline for Books to Scrape. It enforces a 500ms request delay, caches responses on local disk so pages are never fetched twice, survives HTTP 404/500 errors without terminating, and outputs 60 normalized Pydantic records along with an SHA-256 audit log."*

---

## Case Study 1: Persistent Relational Task API (SQLite/Postgres)
* **The Problem:** In-memory lists disappear on server restarts, while naive database scripts cause SQL injection and write-lock crashes during concurrent requests.
* **What I Did & Decided:** Used parameterized queries for 100% of operations, implemented atomic transaction rollbacks (`BEGIN/COMMIT/ROLLBACK`), added B-Tree indexing on status fields, and built a Pytest test suite covering 400 and 404 edge cases. Kept code close to native SQL to avoid ORM abstraction overhead.
* **What Came of It:** Zero data loss across process reboots; verified sub-2ms query execution; 8 passing automated test suites in CI.

---

## Case Study 2: Containerized Backend Stack (Docker Compose & PostgreSQL 17)
* **The Problem:** Local environment drift causes service crashes when connecting APIs to unready database containers during startup.
* **What I Did & Decided:** Engineered a multi-container Docker Compose architecture with explicit `pg_isready` health checks and `condition: service_healthy` dependencies. Persisted database tables via named volumes and managed configuration via `.env` isolation.
* **What Came of It:** Entire stack launches via one command (`docker compose up -d`) with zero initialization race conditions.

---

## Case Study 3: The Polite Scraper (Deterministic Web Pipeline)
* **The Problem:** Naive web scrapers spam target servers, crash on broken links, and output unstructured, dirty text.
* **What I Did & Decided:** Added 500ms polite rate-limiting, local disk response caching, Pydantic v2 data cleaning (string to float conversions), try-except error isolation for broken links, and SHA-256 change detection with structured JSON telemetry.
* **What Came of It:** Successfully collected 60 normalized book records; achieved 100% pipeline survival during 404 failure injection; rendered a zero-dependency HTML dashboard.

---

## Bio & Call to Action
* **Bio:** Sai Tarun Reddy is a backend engineer specializing in tested Python APIs, relational database design, and resilient data processing systems.
* **Call to Action:** [Schedule a 20-minute technical interview](https://calendly.com) | [saitarunrdy@gmail.com](mailto:saitarunrdy@gmail.com)
