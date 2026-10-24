"""A small in-memory task API for the FlyRank Week 2 assignment."""

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A simple in-memory to-do list with full CRUD operations.",
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    """Use the assignment's 400 status and a concise JSON error for bad input."""
    messages = [error["msg"] for error in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "; ".join(messages)},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(_request: Request, exc: HTTPException):
    """Return assignment-style JSON errors for application errors."""
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


tasks: list[Task] = [
    Task(id=1, title="Read the assignment", done=True),
    Task(id=2, title="Build the task API", done=False),
    Task(id=3, title="Try the Swagger docs", done=False),
]
next_task_id = 4


def find_task(task_id: int) -> Task:
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {task_id} not found",
    )


@app.get("/", summary="Describe the Task API")
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Check that the server is running")
def health_check():
    return {"status": "ok"}


@app.get("/tasks", response_model=list[Task], summary="List and filter tasks")
def list_tasks(
    done: bool | None = Query(default=None, description="Filter by completion"),
    search: str | None = Query(default=None, description="Search titles (case-insensitive)"),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
):
    result = tasks
    if done is not None:
        result = [task for task in result if task.done is done]
    if search:
        result = [task for task in result if search.casefold() in task.title.casefold()]
    if limit is not None:
        result = result[offset : offset + limit]
    elif offset:
        result = result[offset:]
    return result


@app.get("/tasks/{task_id}", response_model=Task, summary="Get one task")
def get_task(task_id: int):
    return find_task(task_id)


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
def create_task(payload: TaskCreate):
    global next_task_id
    task = Task(id=next_task_id, title=payload.title, done=False)
    next_task_id += 1
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", response_model=Task, summary="Update a task")
def update_task(task_id: int, payload: TaskUpdate):
    task = find_task(task_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=400,
            detail="Provide a title or done value",
        )
    if any(changes.get(field) is None for field in ("title", "done") if field in changes):
        raise HTTPException(status_code=400, detail="Task fields cannot be null")
    updated = task.model_copy(update=changes)
    tasks[tasks.index(task)] = updated
    return updated


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(task_id: int):
    task = find_task(task_id)
    tasks.remove(task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/stats", summary="Count total, completed, and open tasks")
def task_stats():
    done_count = sum(task.done for task in tasks)
    return {"total": len(tasks), "done": done_count, "open": len(tasks) - done_count}
