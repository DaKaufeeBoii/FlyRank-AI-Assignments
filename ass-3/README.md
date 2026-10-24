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
