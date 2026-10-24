"""Automated test suite verifying all CRUD endpoints, status codes, validations, and database persistence."""

import pytest
from fastapi.testclient import TestClient
from main import app
import database


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Ensure database schema is created and initialized before tests run."""
    database.init_db()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    """GET /health should return 200 with database status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"


def test_read_root(client):
    """GET / should return 200 with API metadata."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


def test_list_tasks_seeded(client):
    """GET /tasks should return 200 with at least 3 seeded tasks."""
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    assert len(tasks) >= 3


def test_get_single_task_success(client):
    """GET /tasks/1 should return the first task with 200 OK."""
    response = client.get("/tasks/1")
    assert response.status_code == 200
    task = response.json()
    assert task["id"] == 1
    assert "title" in task
    assert "done" in task


def test_get_single_task_not_found(client):
    """GET /tasks/99999 should return 404 with standard JSON error."""
    response = client.get("/tasks/99999")
    assert response.status_code == 404
    assert response.json() == {"error": "Task not found"}


def test_create_task_success(client):
    """POST /tasks with valid title should create task and return 201 Created."""
    payload = {"title": "Test automated postgres task"}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["id"] > 0
    assert created["title"] == "Test automated postgres task"
    assert created["done"] is False


def test_create_task_empty_title_validation(client):
    """POST /tasks with empty or whitespace title should return 400 Bad Request."""
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 400
    assert "error" in response.json()


def test_update_task_success(client):
    """PUT /tasks/{id} should update completion status and return 200 OK."""
    # Create a task to update
    create_resp = client.post("/tasks", json={"title": "Task to update"})
    task_id = create_resp.json()["id"]

    # Mark done
    update_resp = client.put(f"/tasks/{task_id}", json={"done": True})
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["id"] == task_id
    assert updated["done"] is True


def test_update_task_not_found(client):
    """PUT /tasks/99999 should return 404 with error message."""
    response = client.put("/tasks/99999", json={"done": True})
    assert response.status_code == 404
    assert response.json() == {"error": "Task not found"}


def test_delete_task_success(client):
    """DELETE /tasks/{id} should return 204 No Content with empty body."""
    # Create a task to delete
    create_resp = client.post("/tasks", json={"title": "Task to delete"})
    task_id = create_resp.json()["id"]

    # Delete it
    delete_resp = client.delete(f"/tasks/{task_id}")
    assert delete_resp.status_code == 204
    assert delete_resp.text == ""

    # Verify 404 after deletion
    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 404


def test_delete_task_not_found(client):
    """DELETE /tasks/99999 should return 404 Not Found."""
    response = client.delete("/tasks/99999")
    assert response.status_code == 404
    assert response.json() == {"error": "Task not found"}


def test_stats_endpoint(client):
    """GET /stats should return total, done, and open counts from database."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "done" in data
    assert "open" in data
    assert data["total"] == data["done"] + data["open"]
