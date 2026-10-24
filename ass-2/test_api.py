"""Comprehensive tests verifying the SQLite-backed Task API."""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure tests run against an isolated test SQLite database
TEST_DB_PATH = Path(__file__).resolve().parent / "test_tasks.db"
os.environ["TASKS_DB_PATH"] = str(TEST_DB_PATH)

import database
import main
from main import app


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    """Ensure a clean, freshly seeded database for each test session."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    database.init_db(TEST_DB_PATH)
    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_and_health(client):
    """Verify root endpoint and health check."""
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["name"] == "Task API"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json() == {"status": "ok"}


def test_initial_seeding_and_restart_idempotence(client):
    """Verify exactly 3 tasks are seeded on first run and restarts don't duplicate them."""
    res = client.get("/tasks")
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 3
    assert tasks[0]["title"] == "Read the assignment"
    assert tasks[0]["done"] is True
    assert tasks[1]["title"] == "Build the task API"
    assert tasks[1]["done"] is False
    assert tasks[2]["title"] == "Try the Swagger docs"
    assert tasks[2]["done"] is False

    # Simulate 3 server restarts / calls to init_db()
    for _ in range(3):
        database.init_db(TEST_DB_PATH)

    res_after = client.get("/tasks")
    assert len(res_after.json()) == 3  # Still 3, not 6 or 9!


def test_get_task_by_id_and_404(client):
    """Verify reading a task by ID and 404 behavior."""
    res = client.get("/tasks/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["title"] == "Read the assignment"

    not_found = client.get("/tasks/999")
    assert not_found.status_code == 404
    assert not_found.json() == {"error": "Task not found"}


def test_create_task_and_validation(client):
    """Verify POST /tasks inserts row into SQLite and validates empty titles."""
    # Valid create
    res = client.post("/tasks", json={"title": "Write unit tests"})
    assert res.status_code == 201
    created = res.json()
    assert created["id"] == 4
    assert created["title"] == "Write unit tests"
    assert created["done"] is False

    # Empty string validation -> 400
    bad_empty = client.post("/tasks", json={"title": ""})
    assert bad_empty.status_code == 400
    assert "error" in bad_empty.json()

    # Whitespace-only validation -> 400
    bad_space = client.post("/tasks", json={"title": "   "})
    assert bad_space.status_code == 400


def test_update_task_and_validation(client):
    """Verify PUT /tasks/{id} updates SQLite records and handles invalid payloads."""
    # Update completion
    res1 = client.put("/tasks/2", json={"done": True})
    assert res1.status_code == 200
    assert res1.json()["id"] == 2
    assert res1.json()["done"] is True

    # Update title
    res2 = client.put("/tasks/2", json={"title": "Build the SQLite task API"})
    assert res2.status_code == 200
    assert res2.json()["title"] == "Build the SQLite task API"

    # Non-existent task -> 404
    res_404 = client.put("/tasks/999", json={"done": True})
    assert res_404.status_code == 404
    assert res_404.json() == {"error": "Task not found"}

    # Empty payload -> 400
    res_400 = client.put("/tasks/2", json={})
    assert res_400.status_code == 400


def test_delete_task(client):
    """Verify DELETE /tasks/{id} returns 204 and removes row from SQLite."""
    del_res = client.delete("/tasks/3")
    assert del_res.status_code == 204
    assert del_res.content == b""

    # Confirm deleted
    get_res = client.get("/tasks/3")
    assert get_res.status_code == 404

    # Deleting non-existent task returns 404
    del_404 = client.delete("/tasks/3")
    assert del_404.status_code == 404


def test_search_and_filter_queries(client):
    """Verify SQL-backed search, status filter, and sorting."""
    # Filter by done=true
    done_res = client.get("/tasks?done=true")
    assert done_res.status_code == 200
    assert all(t["done"] is True for t in done_res.json())

    # Search with LIKE operator
    search_res = client.get("/tasks?search=assignment")
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1
    assert "assignment" in search_res.json()[0]["title"].lower()

    # Alphabetical sorting
    sort_res = client.get("/tasks?sort=title")
    assert sort_res.status_code == 200
    titles = [t["title"] for t in sort_res.json()]
    assert titles == sorted(titles)


def test_stats_computed_in_sql(client):
    """Verify GET /stats computed via SQL COUNT(*)."""
    stats_res = client.get("/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total"] == 3
    assert stats["done"] == 1
    assert stats["open"] == 2


def test_data_persistence_across_connection_resets(client):
    """Verify data outlives process/connection resets."""
    client.post("/tasks", json={"title": "Persistent task across restarts"})
    
    # Reconnect and inspect database directly
    conn = database.get_connection(TEST_DB_PATH)
    try:
        row = conn.execute("SELECT * FROM tasks WHERE title = ?;", ("Persistent task across restarts",)).fetchone()
        assert row is not None
        assert row["title"] == "Persistent task across restarts"
    finally:
        conn.close()
