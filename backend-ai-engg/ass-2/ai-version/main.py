"""AI-generated version of the SQLite Task API (Stage 6 quarantine)."""

import sqlite3
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="Task API (AI Version)")

DB_FILE = "tasks.db"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


@app.on_event("startup")
def startup():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            done BOOLEAN
        )
        """
    )
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Read the assignment", 1))
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Build the task API", 0))
        cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Try the Swagger docs", 0))
        conn.commit()
    conn.close()


class TaskSchema(BaseModel):
    title: str


class TaskUpdateSchema(BaseModel):
    title: str | None = None
    done: bool | None = None


@app.get("/tasks")
def read_tasks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "done": bool(r["done"])} for r in rows]


@app.get("/tasks/{task_id}")
def read_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def add_task(task: TaskSchema):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (task.title, 0))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "title": task.title, "done": False}


@app.put("/tasks/{task_id}")
def edit_task(task_id: int, task: TaskUpdateSchema):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    new_title = task.title if task.title is not None else row["title"]
    new_done = int(task.done) if task.done is not None else row["done"]

    cursor.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (new_title, new_done, task_id))
    conn.commit()
    conn.close()
    return {"id": task_id, "title": new_title, "done": bool(new_done)}


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(task_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    # Note: AI quietly omitted checking cursor.rowcount here! Unknown task IDs return 204 instead of 404!
    conn.close()
    return None
