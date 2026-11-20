# Assignment 2: AI Workflow Audit and Tool Setup
**Code:** FL-01 | **Track:** General AI Fluency  
**Week:** 1 | **Workload:** 4h | **Phase:** Onboarding  
**Author:** Sai Tarun Reddy (`saitarunrdy@gmail.com`)  
**Deliverable Document:** [deliverable.md](./deliverable.md)

---

## 1. Weekly AI Workflow Audit (Ethan Mollick Task Classification Framework)

The following table maps 12 recurring tasks from my real week as a backend AI engineering intern, classifying each into:
- **Just Me:** Tasks requiring human responsibility, ethical judgment, or core decision-making.
- **Delegate to AI with Review:** Well-defined boilerplate or translation tasks where AI drafts and human verifies.
- **Collaborate with AI:** Complex exploratory design where AI acts as a thinking partner or brainstorming rubber duck.
- **Fully Automate:** Deterministic, repetitive mechanical processes executed by scripts or CI.

| # | Recurring Weekly Task | Classification | One-Line Rationale |
|---|---|---|---|
| 1 | **Architecture & Trade-off Decisions** (e.g., SQLite vs PostgreSQL, sync vs async) | **Just Me** | High-stakes engineering judgment directly impacts system longevity; requires human accountability. |
| 2 | **Personal Career Vision & Ethical Principles** (e.g., scraping ethics & boundaries) | **Just Me** | Ethical boundaries and professional integrity cannot be outsourced to statistical text generators. |
| 3 | **Boilerplate CRUD Endpoints & Pydantic Schemas** | **Delegate with Review** | Highly predictable code structures; AI drafts in seconds, I audit fields, types, and HTTP status codes. |
| 4 | **Writing Unit & Integration Tests (Pytest)** | **Delegate with Review** | AI generates comprehensive edge-case test matrices, but human verification ensures assertions are meaningful. |
| 5 | **SQL Query Optimization & Indexing Strategies** | **Collaborate with AI** | Exploring composite indexes and `EXPLAIN ANALYZE` trade-offs is accelerated through iterative AI reasoning. |
| 6 | **Debugging Complex Error Traces & Race Conditions** | **Collaborate with AI** | Rubber-ducking cryptic Docker networking or async concurrency bugs with AI surfaces blind spots rapidly. |
| 7 | **System API Contract Design (Swagger / OpenAPI)** | **Collaborate with AI** | Exploring RESTful conventions and versioning strategies benefits from dynamic back-and-forth review. |
| 8 | **Code Linting, Formatting, and Import Sorting** | **Fully Automate** | Deterministic tools (`ruff`, `black`, `isort`) enforce styling rules instantly via Git pre-commit hooks. |
| 9 | **Continuous Integration Automated Testing** | **Fully Automate** | GitHub Actions runs `pytest` and Docker health checks on every push without human intervention. |
| 10 | **Daily Scraper Change Detection & Report Generation** | **Fully Automate** | Scheduled background cron executes SHA-256 diff checks and generates `run-report.json` automatically. |
| 11 | **Drafting Technical README & Markdown Docs** | **Delegate with Review** | AI organizes structured documentation from raw notes, while I verify technical accuracy and commands. |
| 12 | **Refactoring Code for Readability & Clean Code Standards** | **Collaborate with AI** | Comparing structural patterns (e.g., repository pattern vs active record) sharpens design decisions. |

---

## 2. Free Toolkit Setup & Anthropic Academy Enrollment

### Verified Tool Accounts:
* **Claude (Anthropic):** Active free tier account (`saitarunrdy@gmail.com`).
* **ChatGPT (OpenAI):** Active account utilizing GPT-4o mini for quick syntax lookups.
* **Anthropic Academy (Skilljar):** Enrolled via cohort mailbox (`saitarun.reddy@10x.ai` / `saitarunrdy@gmail.com`).
* **Course:** *AI Fluency: Framework & Foundations* — Enrolled, Module 1 ("Working with Frontier Models") completed.
* **Perplexity & Gemini:** Setup for fast documentation cross-referencing and official specification checks.

---

## 3. Configured Claude Project

**Project Name:** `FlyRank-Backend-AI-Mentor`  
**Description:** Dedicated 8-week engineering workspace and standing assistant for backend and AI fluency coursework.

### Project Custom Instructions:
```markdown
# Role & Identity
You are an expert Principal Backend & AI Systems Engineer acting as my senior mentor and thinking partner for my FlyRank Internship. My name is Sai Tarun Reddy (saitarunrdy@gmail.com).

# Core Engineering Proof Statement
"I engineer resilient, production-ready Python backend services—specializing in typed FastAPI APIs, transactional database architectures (PostgreSQL/SQLite), and fault-tolerant data pipelines that survive real-world network anomalies. My goal is to produce verifiable code artifacts that prove my engineering rigor to startup hiring managers."

# Tone & Interaction Guidelines
- Direct, pragmatic, plain, and technical. Zero corporate buzzwords or patronizing fluff.
- Never write entire systems for me; challenge my architectural assumptions and critique edge cases.
- Always demand defensive programming: typed schemas, explicit status codes (400, 404, 422, 500), atomic transactions, rate-limiting, and idempotent operations.
- When reviewing prompts or design, point out where things will fail under high load or network failure.
```

---

## 4. The Three Target Tasks (Reused in FL-02 through FL-04)

These three tasks will be carried forward for prompting fundamentals and workflow automation:

### Target Task 1: API Error Handling & Structured Response Design
* **Description:** Designing clean, standardized JSON error payloads and HTTP exception handlers for FastAPI.
* **Measurable Definition of "Done Well":**  
  All error responses return consistent `{ "detail": str, "error_code": str, "timestamp": iso8601 }` bodies; zero unhandled 500 tracebacks leak to clients; and HTTP status codes strictly match RFC 9110 specifications (400 vs 404 vs 422).

### Target Task 2: Database Migration & Schema Indexing Strategy
* **Description:** Designing relational schema migrations in PostgreSQL/SQLite with explicit indexing and foreign key constraints.
* **Measurable Definition of "Done Well":**  
  Queries filtering by search terms or foreign keys execute in under 5ms on a 50,000-row dataset via B-Tree indexes; transactions are strictly atomic (all-or-nothing rollback); and schema definitions include full Pydantic v2 validation.

### Target Task 3: Resilient Web Scraping / Data Extraction Pipeline
* **Description:** Building deterministic, polite scraping pipelines that extract structured data from external targets without getting blocked or crashing.
* **Measurable Definition of "Done Well":**  
  The scraper implements polite rate limiting (minimum 500ms delay), local disk caching to prevent duplicate network hits, handles HTTP 404/5xx errors gracefully without aborting the run, and outputs validated Pydantic JSON/CSV records alongside a verifiable audit telemetry report (`run-report.json`).

---

## 5. Pass / Revise Verification

- [x] **12 tasks listed:** Genuinely reflect Sai's real backend engineering study and internship tasks.
- [x] **Clear rationale:** Every single task contains a concise one-line explanation.
- [x] **Honestly marked "Just Me":** Architecture decision-making and ethical boundaries are reserved strictly for human judgment.
- [x] **Three specific target tasks:** Error handling, database indexing, and resilient scraping with clear, quantitative "done well" criteria.
- [x] **Tool accounts & Academy evidenced:** Documented Claude project setup and Anthropic Academy enrollment.
