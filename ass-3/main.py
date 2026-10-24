"""FastAPI Task API connected to containerized PostgreSQL database."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import database


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Automatically ensure database tables, indexes, and seed tasks are initialized on startup."""
    database.init_db()
    yield


app = FastAPI(
    title="Containerized Task API",
    version="1.0",
    description="A PostgreSQL-backed Task CRUD API running in Docker containers with Docker Compose.",
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


@app.get("/", summary="Describe the Task API")
def read_root():
    return {
        "name": "Containerized Task API",
        "version": "1.0",
        "endpoints": ["/tasks", "/stats", "/health"],
    }


@app.get("/health", summary="Check that the server and database are healthy")
def health_check():
    db_ok = database.check_db_health()
    if not db_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        )
    return {"status": "ok", "db": "ok"}


@app.get("/tasks", response_model=list[Task], summary="List and filter tasks from PostgreSQL")
def list_tasks(
    done: bool | None = Query(default=None, description="Filter by completion status"),
    search: str | None = Query(default=None, description="Search titles using SQL ILIKE"),
    sort: str | None = Query(default=None, description="Sort order: 'title' or 'id'"),
    limit: int | None = Query(default=None, ge=1, description="Max number of tasks to return"),
    offset: int = Query(default=0, ge=0, description="Number of tasks to skip"),
):
    rows = database.get_all_tasks(
        done=done,
        search=search,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return [Task(**row) for row in rows]


@app.get("/tasks/{task_id}", response_model=Task, summary="Get one task from PostgreSQL")
def get_task(task_id: int):
    row = database.get_task_by_id(task_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return Task(**row)


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task in PostgreSQL",
)
def create_task(payload: TaskCreate):
    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title cannot be empty or whitespace only",
        )
    created = database.create_task(title)
    return Task(**created)


@app.put(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Update a task in PostgreSQL",
)
def update_task(task_id: int, payload: TaskUpdate):
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

    title = None
    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title cannot be empty or whitespace only",
            )

    updated = database.update_task(task_id, title=title, done=payload.done)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return Task(**updated)


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task from PostgreSQL",
)
def delete_task(task_id: int):
    deleted = database.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/stats", summary="Count total, completed, and open tasks using SQL COUNT(*)")
def task_stats():
    return database.get_stats()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
