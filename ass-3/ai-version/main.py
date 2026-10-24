"""AI-generated version of the Containerized PostgreSQL Task API (Stage 6 quarantine)."""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row

load_dotenv()

app = FastAPI(title="Task API (AI Version)")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:dev@db:5432/tasks")


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@app.on_event("startup")
def startup():
    # Note: AI uses deprecated on_event("startup") instead of modern lifespan
    # Also: Lacks connection retry logic, which can crash if Postgres container takes 2 seconds to initialize
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT,
                done BOOLEAN DEFAULT FALSE
            );
            """
        )
        cur.execute("SELECT COUNT(*) FROM tasks;")
        if cur.fetchone()["count"] == 0:
            cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s);", ("Read the assignment", True))
            cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s);", ("Build the task API", False))
            cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s);", ("Try the Swagger docs", False))
        conn.commit()
    conn.close()


class TaskSchema(BaseModel):
    title: str


class TaskUpdateSchema(BaseModel):
    title: str | None = None
    done: bool | None = None


@app.get("/tasks")
def list_tasks():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, title, done FROM tasks;")
        tasks = cur.fetchall()
    conn.close()
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
        task = cur.fetchone()
    conn.close()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskSchema):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;",
            (task.title.strip(), False),
        )
        created = cur.fetchone()
        conn.commit()
    conn.close()
    return created


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdateSchema):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, title, done FROM tasks WHERE id = %s;", (task_id,))
        existing = cur.fetchone()
        if not existing:
            conn.close()
            raise HTTPException(status_code=404, detail="Task not found")

        new_title = task.title.strip() if task.title is not None else existing["title"]
        new_done = task.done if task.done is not None else existing["done"]

        cur.execute(
            "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done;",
            (new_title, new_done, task_id),
        )
        updated = cur.fetchone()
        conn.commit()
    conn.close()
    return updated


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
        # Note: AI again forgets to check cur.rowcount! Unknown IDs return 204 instead of 404!
        conn.commit()
    conn.close()
    return None
