# Week 1 - Assignment A3: Containerize Your Stack

A production-grade, containerized Task CRUD REST API built with **Python 3.11**, **FastAPI**, and **PostgreSQL 17**, completely orchestrated using **Docker** and **Docker Compose**.

Start the entire application, database server, networking, and storage volume with a single command.

---

## The One Command to Run Everything

```bash
docker compose up
```

To run in detached mode or rebuild:
```bash
docker compose up -d --build
```

To shut down while preserving your database data:
```bash
docker compose down
```

---

## Environment Variables & Configuration

Configuration and database secrets are read from `.env` (which is strictly git-ignored). A template file `.env.example` is committed to the repository for reference.

### Setting up `.env`:
```bash
cp .env.example .env
```

### Variables reference (`.env.example`):
| Variable | Description | Default Local Value | Compose Value |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://postgres:dev@localhost:5432/tasks` | `postgres://postgres:dev@db:5432/tasks` |
| `PORT` | API server port | `3000` | `3000` |

> [!IMPORTANT]
> Within the Docker Compose bridge network, containers communicate using service names as hostnames. The API container connects to `db:5432`, not `localhost:5432`.

---

## Endpoints Table

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API service metadata & documentation links | `200 OK` |
| `GET` | `/health` | Health check verifying HTTP server and database `SELECT 1` ping | `200 OK`, `503 Service Unavailable` |
| `GET` | `/tasks` | List all tasks with SQL filtering (`?done=true`), search (`?search=`), sort, and pagination | `200 OK` |
| `GET` | `/tasks/{id}` | Retrieve single task by primary key | `200 OK`, `404 Not Found` |
| `POST` | `/tasks` | Create a new task with validation (`{"title": "..."}`) | `201 Created`, `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update task title and/or completion status | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Delete task permanently from PostgreSQL | `204 No Content`, `404 Not Found` |
| `GET` | `/stats` | Return aggregate counts computed directly via `SELECT COUNT(*)` in SQL | `200 OK` |

Interactive Swagger documentation is automatically available at: [http://localhost:3000/docs](http://localhost:3000/docs).

---

## Sample Request & Response (`curl -i`)

### 1. Read Seeded Tasks (`GET /tasks`)

```http
$ curl -i http://localhost:3000/tasks

HTTP/1.1 200 OK
date: Sat, 24 Oct 2026 14:20:39 GMT
server: uvicorn
content-length: 156
content-type: application/json

[
  {"id":1,"title":"Read the assignment","done":true},
  {"id":2,"title":"Build the task API","done":false},
  {"id":3,"title":"Try the Swagger docs","done":false}
]
```

### 2. Live Health Check with Database Ping (`GET /health`)

```http
$ curl -i http://localhost:3000/health

HTTP/1.1 200 OK
date: Sat, 24 Oct 2026 14:17:01 GMT
server: uvicorn
content-length: 25
content-type: application/json

{"status":"ok","db":"ok"}
```

### 3. Create Task (`POST /tasks`)

```http
$ curl -i -X POST http://localhost:3000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Persistence test task"}'

HTTP/1.1 201 Created
date: Sat, 24 Oct 2026 14:17:33 GMT
server: uvicorn
content-length: 53
content-type: application/json

{"id":4,"title":"Persistence test task","done":false}
```

### 4. Not Found Error (`GET /tasks/999`)

```http
$ curl -i http://localhost:3000/tasks/999

HTTP/1.1 404 Not Found
date: Sat, 24 Oct 2026 14:17:10 GMT
server: uvicorn
content-length: 26
content-type: application/json

{"error":"Task not found"}
```

---

## Verification of Data in Database (`psql`)

Inside the database container `ass-3-db-1`:

```sql
tasks=# \dt
         List of relations
 Schema | Name  | Type  |  Owner   
--------+-------+-------+----------
 public | tasks | table | postgres
(1 row)

tasks=# SELECT id, title, done, created_at FROM tasks;
 id |        title         | done |          created_at          
----+----------------------+------+------------------------------
  1 | Read the assignment  | t    | 2026-10-24 14:16:30.79178+00
  2 | Build the task API   | f    | 2026-10-24 14:16:30.79178+00
  3 | Try the Swagger docs | f    | 2026-10-24 14:16:30.79178+00
(3 rows)
```

---

## Persistence Across Full-Stack Restart

The database storage is backed by a named Docker volume `taskdata` (`ass-3_taskdata`):

1. Start stack and create a task (`id: 4`).
2. Run `docker compose down` — all containers and virtual networks are stopped and removed.
3. Run `docker compose up -d` — containers are recreated and remount the existing volume.
4. Query `GET /tasks/4` -> `200 OK` with all task data intact.
5. The `init_db()` seed function checks `SELECT COUNT(*) FROM tasks;` and executes the seed query **only if the table is empty (count == 0)**, ensuring idempotent startup with no duplicated rows.

---

## Extras & Architectural Deep Dives

### 1. The Database Mortality Experiment (Why Volumes Exist)
When a container runs without a mounted volume, all changes to `/var/lib/postgresql/data` are stored in the container's ephemeral copy-on-write filesystem layer (OverlayFS). The moment the container is removed (`docker rm`), its writable layer is permanently discarded by Docker, causing all database rows to vanish. Named volumes decouple storage from the container lifecycle by mapping disk space on the host, ensuring data persists across restarts, upgrades, and rebuilds.

### 2. Production Health Check with Database Gate
The `GET /health` endpoint does not merely return a static string; it executes an active `SELECT 1;` query against the PostgreSQL database. If the database is unreachable or recovering, the endpoint raises HTTP `503 Service Unavailable`:

```bash
$ curl -i http://localhost:3000/health
HTTP/1.1 200 OK
{"status":"ok","db":"ok"}
```

**Why this matters in production:** Reverse proxies and cloud load balancers (such as AWS ALB, GCP Load Balancer, or Nginx) use health checks to gate deployments and traffic. If a container cannot communicate with its database, the load balancer automatically stops directing user traffic to that container until it recovers.

### 3. PostgreSQL Performance Indexing & EXPLAIN ANALYZE
Indexes were created on `title` and `done` columns:

```sql
CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);
CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title);
```

#### Query Execution Plan (`EXPLAIN ANALYZE`):

```sql
tasks=# EXPLAIN ANALYZE SELECT * FROM tasks WHERE title = 'Read the assignment';

                                                       QUERY PLAN                                                       
------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on tasks  (cost=4.19..12.66 rows=5 width=53) (actual time=0.035..0.036 rows=1 loops=1)
   Recheck Cond: (title = 'Read the assignment'::text)
   Heap Blocks: exact=1
   ->  Bitmap Index Scan on idx_tasks_title  (cost=0.00..4.19 rows=5 width=0) (actual time=0.025..0.025 rows=1 loops=1)
         Index Cond: (title = 'Read the assignment'::text)
 Planning Time: 0.401 ms
 Execution Time: 0.068 ms
(7 rows)
```

The database query planner utilizes a `Bitmap Index Scan on idx_tasks_title` via B-Tree index traversal rather than a sequential scan, ensuring sub-millisecond execution time even as the table grows to millions of rows.

### 4. Automated Pytest Test Suite
A complete automated test suite in `test_api.py` validates all endpoints, status codes, validations, and aggregation queries:

```bash
python -m pytest -v ass-3/test_api.py
```
```
ass-3/test_api.py::test_health_check PASSED                              [  8%]
ass-3/test_api.py::test_read_root PASSED                                 [ 16%]
ass-3/test_api.py::test_list_tasks_seeded PASSED                         [ 25%]
ass-3/test_api.py::test_get_single_task_success PASSED                   [ 33%]
ass-3/test_api.py::test_get_single_task_not_found PASSED                 [ 41%]
ass-3/test_api.py::test_create_task_success PASSED                       [ 50%]
ass-3/test_api.py::test_create_task_empty_title_validation PASSED        [ 58%]
ass-3/test_api.py::test_update_task_success PASSED                       [ 66%]
ass-3/test_api.py::test_update_task_not_found PASSED                     [ 75%]
ass-3/test_api.py::test_delete_task_success PASSED                       [ 83%]
ass-3/test_api.py::test_delete_task_not_found PASSED                     [ 91%]
ass-3/test_api.py::test_stats_endpoint PASSED                            [100%]
======================= 12 passed in 1.81s ========================
```
