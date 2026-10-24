"""FastAPI Task API connected to SQLite database with SQL filtering, search, stats, and transactions."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import sqlite3

from database import get_connection, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Automatically ensure database, tables, and seed tasks are initialized on startup."""
    init_db()
    yield


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A SQLite-backed to-do list API with full CRUD persistence, SQL filtering, and stats.",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    """Return 400 Bad Request with a clear JSON error message for validation errors."""
    messages = [error["msg"] for error in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "; ".join(messages)},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(_request: Request, exc: HTTPException):
    """Return assignment-standard JSON errors for application HTTP exceptions."""
    message = exc.detail.get("error") if isinstance(exc.detail, dict) else exc.detail
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": message},
        headers=exc.headers,
    )


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, description="A non-empty task title")


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    done: bool | None = None


class Task(BaseModel):
    id: int
    title: str
    done: bool


def row_to_task(row: sqlite3.Row) -> Task:
    """Convert a sqlite3.Row into a Task Pydantic model with boolean done."""
    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"]),
    )


@app.get("/", summary="Describe the Task API")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks", "/stats"]}


@app.get("/health", summary="Check that the server is running")
def health_check():
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task], summary="List and filter tasks from SQLite")
def list_tasks(
    done: bool | None = Query(default=None, description="Filter by completion status"),
    search: str | None = Query(default=None, description="Search titles using SQL LIKE"),
    sort: str | None = Query(default=None, description="Sort order: 'title' or 'id'"),
    limit: int | None = Query(default=None, ge=1, description="Max number of tasks to return"),
    offset: int = Query(default=0, ge=0, description="Number of tasks to skip"),
):
    query = "SELECT id, title, done FROM tasks WHERE 1=1"
    params: list = []

    # Filter by completion status using parameterized query
    if done is not None:
        query += " AND done = ?"
        params.append(1 if done else 0)

    # Search by title using SQL LIKE operator
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    # Sort alphabetically or by id
    if sort == "title":
        query += " ORDER BY title ASC"
    else:
        query += " ORDER BY id ASC"

    # Pagination via SQL LIMIT and OFFSET
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    elif offset > 0:
        query += " LIMIT -1 OFFSET ?"
        params.append(offset)

    conn = get_connection()
    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [row_to_task(row) for row in rows]
    finally:
        conn.close()


@app.get("/tasks/{task_id}", response_model=Task, summary="Get one task from SQLite")
def get_task(task_id: int):
    conn = get_connection()
    try:
        # Parameterized query placeholder to prevent SQL injection
        cursor = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?;",
            (task_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return row_to_task(row)
    finally:
        conn.close()


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task in SQLite",
)
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty or whitespace only",
        )
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO tasks (title, done) VALUES (?, ?);",
                (title, 0),
            )
            new_id = cursor.lastrowid
        return Task(id=new_id, title=title, done=False)
    finally:
        conn.close()


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update a task's title or completion status in SQLite",
)
def update_task(task_id: int, payload: TaskUpdate):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?;",
            (task_id,),
        )
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide a title or done value",
            )
        if any(changes.get(field) is None for field in ("title", "done") if field in changes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task fields cannot be null",
            )

        new_title = existing["title"]
        if payload.title is not None:
            stripped = payload.title.strip()
            if not stripped:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Title cannot be empty or whitespace only",
                )
            new_title = stripped

        new_done = existing["done"]
        if payload.done is not None:
            new_done = 1 if payload.done else 0

        with conn:
            conn.execute(
                """
                UPDATE tasks
                SET title = ?, done = ?, updated_at = DATETIME('now')
                WHERE id = ?;
                """,
                (new_title, new_done, task_id),
            )

        return Task(id=task_id, title=new_title, done=bool(new_done))
    finally:
        conn.close()


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task from SQLite",
)
def delete_task(task_id: int):
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                "DELETE FROM tasks WHERE id = ?;",
                (task_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Task not found",
                )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    finally:
        conn.close()


@app.get("/stats", summary="Count total, completed, and open tasks using SQL COUNT(*)")
def task_stats():
    """Real statistics computed with SELECT COUNT(*) in SQL instead of counting in memory."""
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM tasks;").fetchone()[0]
        done_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1;").fetchone()[0]
        return {
            "total": total,
            "done": done_count,
            "open": total - done_count,
        }
    finally:
        conn.close()
