# Task API

A small FastAPI CRUD API built for the FlyRank Backend Track Week 2 assignment. It stores tasks in memory, so changes reset when the server stops.

## Run

Requires Python 3.10 or newer.

```bash
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) to use Swagger UI. The OpenAPI schema is available at `/openapi.json`.

## Endpoints

| Method | Path | Description | Success |
| --- | --- | --- | --- |
| GET | `/` | API name, version, and entry point | 200 |
| GET | `/health` | Server health | 200 |
| GET | `/tasks` | List tasks; optional `done`, `search`, `limit`, and `offset` filters | 200 |
| GET | `/tasks/{task_id}` | Read one task | 200 |
| POST | `/tasks` | Create a task from `{"title":"Buy milk"}` | 201 |
| PUT | `/tasks/{task_id}` | Update `title`, `done`, or both | 200 |
| DELETE | `/tasks/{task_id}` | Delete a task | 204 |
| GET | `/stats` | Count total, done, and open tasks | 200 |

POST requires a non-empty title. PUT requires at least one valid field and rejects empty titles. Unknown task IDs return 404 with a JSON error. Invalid request data returns 400 with a JSON error. The built-in docs also expose FastAPI's generated validation response schemas.

## Example 404 response

Run this after starting the server to capture the live `curl -i` response:

```bash
curl -i http://localhost:8000/tasks/99
```

Expected JSON body: `{"error":"Task 99 not found"}`.

## In-memory data

Create, update, and delete a task, then restart the server and list tasks: the original three examples return. The list is a Python variable, so it exists only while that server process is running.

## Assignment stages

The project implements the assignment checkpoints: hello server, root and health, read endpoints, create with validation, full CRUD, Swagger UI, and publication documentation. Save a Git commit after each stage as you work through them.

## AI vs me (optional assignment stage)

This repository is the hand-built version. The optional AI rematch asks you to write your own prompt, generate a separate `ai-version/`, run the same CRUD checks against both implementations, and record at least three concrete differences here. That comparison has not been performed yet.
