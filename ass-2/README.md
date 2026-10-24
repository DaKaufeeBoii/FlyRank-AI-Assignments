# FlyRank Backend Track - Week 3: Connecting CRUD to SQLite

A production-ready FastAPI Task API connecting CRUD operations to a local **SQLite** database (`tasks.db`), ensuring tasks persist across server restarts, crashes, and redeployments.

---

## 1. Why SQLite?

1. **Zero Configuration & Serverless:** Unlike PostgreSQL or MySQL, SQLite requires no external server process, background daemon, network port, or credential configuration. It runs embedded directly inside the Python process.
2. **Single-File Portability:** The entire database—tables, indexes, metadata, and records—lives in a single portable file (`tasks.db`). Backups, cloning, and testing are as straightforward as copying the file.
3. **Full Persistence & ACID Reliability:** Every write query is synchronized to disk using atomic transactions. Even when the server restarts or crashes, your data remains fully preserved.
4. **Blazing Fast Local Execution:** Queries execute with negligible latency directly against local disk and OS cache, eliminating network latency and socket serialization overhead.

---

## 2. Where the Database Lives

- **Location:** The database file lives at `tasks.db` within the project root directory.
- **Automatic Initialization:** On application startup, the database file and `tasks` table are automatically created and seeded with 3 starter tasks if missing.
- **Git-Ignored:** `tasks.db` is included in `.gitignore` so every collaborator or test runner starts with a clean database instance.

---

## 3. One Command to Run

Install dependencies and start the API with live reload:

```bash
uvicorn main:app --reload --port 8000
```

- **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **OpenAPI Schema:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 4. Database Inspection (DB Browser for SQLite)

Below is `tasks.db` inspected in **DB Browser for SQLite**, showing the schema and initial seeded rows:

![DB Browser for SQLite Screenshot](db_browser_screenshot.png)

---

## 5. Stage 4: Example SQL Query Run by Hand

During Stage 4 exploration, direct queries were run against `tasks.db`:

```sql
SELECT * FROM tasks WHERE done = 1;
```

**Output Returned:**
```
id | title               | done | created_at          | updated_at
---+---------------------+------+---------------------+--------------------
1  | Read the assignment | 1    | 2026-10-24 12:45:00 | 2026-10-24 12:45:00
```

**Observation:** Modifying records directly in DB Browser immediately reflects in `GET /tasks` on the running API because both read the exact same SQLite file on disk. There is no cache or synchronization delay—the database file is the single source of truth.

---

## 6. API Endpoints

| Method | Path | Description | Success Status | Error Status |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | API description & root endpoints | `200 OK` | — |
| **GET** | `/health` | Server health check (`{"status": "ok"}`) | `200 OK` | — |
| **GET** | `/tasks` | List tasks; supports `done`, `search`, `sort`, `limit`, `offset` | `200 OK` | `400 Bad Request` |
| **GET** | `/tasks/{id}` | Fetch a single task by ID | `200 OK` | `404 Not Found` |
| **POST** | `/tasks` | Create a task (persisted to SQLite) | `201 Created` | `400 Bad Request` |
| **PUT** | `/tasks/{id}` | Update title, done status, or both | `200 OK` | `400 Bad Request`, `404 Not Found` |
| **DELETE**| `/tasks/{id}` | Permanently delete a task from SQLite | `204 No Content` | `404 Not Found` |
| **GET** | `/stats` | Task metrics calculated via SQL `COUNT(*)` | `200 OK` | — |

---

## 7. Stretch Features & Implementation Deep Dives

### A. Proof that Storage is an "Implementation Detail"
We maintained the exact same request/response contracts, HTTP status codes (`200`, `201`, `204`, `400`, `404`), and error schemas as Assignment 1. The full test suite (`pytest -v test_api.py`) passes against the SQLite implementation without any modifications to client expectations. This demonstrates that external consumers care only about the API contract; whether the backing store is an in-memory array, a SQLite file, or a distributed PostgreSQL cluster is purely an internal implementation detail.

### B. What an Index is For
We added `CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);`.  
**Why it matters:** An index creates a dedicated B-tree lookup structure. Without an index, filtering tasks with `WHERE done = ?` requires scanning every single row in the table ($O(N)$ full table scan). With an index, lookups and filtered queries run in $O(\log N)$ time, keeping queries instant even as the database scales to millions of rows.

### C. Wrapping Multi-Step Changes in Transactions
The initial 3-task seed is executed inside a transaction block (`with conn:`).  
**Why it matters:** If an error occurs midway through seeding (e.g., duplicate key, disk write interruption, or process abort), the transaction rolls back completely. The database is never left in a corrupt or partially-initialized state.

### D. Table Schema Evolutions & Migrations
We added `created_at` and `updated_at` timestamps to the tasks schema.  
**What changing the table's shape felt like:** When adding columns to an existing SQLite table, existing database files either need manual `ALTER TABLE` statements or recreation from scratch to conform. That friction of synchronizing structural changes across distributed development and production databases is precisely why schema migration tools (like Alembic) exist.

---

## 8. Bonus Stage: AI vs Me (The AI Rematch)

### The Specification Prompt Used
> *"Convert our in-memory FastAPI task CRUD API to use SQLite with the standard `sqlite3` library. The database must live in `tasks.db` and create the `tasks` table with columns (`id` integer primary key autoincrement, `title` text not null, `done` integer/boolean default 0) if missing. If the table is empty, seed three starter tasks in a transaction, ensuring restarts never duplicate rows. Preserve the exact five endpoints (`GET /tasks`, `GET /tasks/{id}`, `POST /tasks`, `PUT /tasks/{id}`, `DELETE /tasks/{id}`) with parameterized SQL queries (`?`), returning 400 for bad input, 404 for unknown IDs with `{'error': 'Task not found'}`, 201 for create, and 204 for delete. Quarantined in `ai-version/`."*

### Differences Found (Code Review)

1. **What did it do better?**  
   The AI wrote very compact single-file handlers by directly opening and closing connections inline. However, inline connections lacked context-managed error resilience and connection reuse abstraction.

2. **What did it get wrong or quietly ignore?**  
   - **The DELETE bug:** The AI executed `DELETE FROM tasks WHERE id = ?` and immediately committed and returned `204`, completely ignoring `cursor.rowcount`. Calling `DELETE /tasks/999` returned `204 No Content` instead of the required `404 Not Found`!
   - **Deprecated lifecycle:** It used `@app.on_event("startup")` instead of modern FastAPI `@asynccontextmanager` lifespans.
   - **Missing indexes:** It did not create indexes on filtered columns (`idx_tasks_done`).
   - **Non-transactional seeding:** It executed three separate `INSERT` commands without a wrapping `with conn:` transaction block.

3. **What did the prompt forget to specify vs what the AI silently decided?**  
   The prompt didn't specify whether `done` should be returned as a strict JSON boolean or SQLite integer. The AI chose to manually cast `bool(row['done'])` in dictionary comprehensions rather than utilizing Pydantic's type-coercion response models.

### One Rematch Improvement
In the rematch iteration, adding the clause *"Validate `cursor.rowcount > 0` on DELETE and PUT, raising 404 if 0"* fixed the silent 204 delete defect on the first attempt.

---

## 9. Running Automated Tests

Run the full pytest suite verifying CRUD operations, parameterized SQL, 400/404 error codes, and persistence:

```bash
pytest -v test_api.py
```
