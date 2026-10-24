"""Database repository module for PostgreSQL with parameterized queries, schema init, and seeding."""

import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

# Load environment variables from .env file
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:dev@localhost:5432/tasks")


def get_connection():
    """Return a new connection to the PostgreSQL database with dict_row factory."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db() -> None:
    """Initialize PostgreSQL database schema and seed initial tasks if table is empty.
    
    Creates:
      - tasks table: id SERIAL PRIMARY KEY, title TEXT NOT NULL, done BOOLEAN NOT NULL DEFAULT FALSE
      - indexes on done and title for query performance
      - initial tasks only on first run (seed-once rule)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Create tasks table if it does not exist
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # 2. Add performance indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks(title);")

            # 3. Seed-once check
            cur.execute("SELECT COUNT(*) AS count FROM tasks;")
            result = cur.fetchone()
            count = result["count"] if result else 0

            if count == 0:
                initial_tasks = [
                    ("Read the assignment", True),
                    ("Build the task API", False),
                    ("Try the Swagger docs", False),
                ]
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                    initial_tasks,
                )
        conn.commit()


def get_all_tasks(
    done: bool | None = None,
    search: str | None = None,
    sort: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict]:
    """Fetch tasks from PostgreSQL with optional filtering, search, sort, and pagination."""
    query = "SELECT id, title, done FROM tasks WHERE 1=1"
    params: list = []

    if done is not None:
        query += " AND done = %s"
        params.append(done)

    if search:
        query += " AND title ILIKE %s"
        params.append(f"%{search}%")

    if sort == "title":
        query += " ORDER BY title ASC"
    else:
        query += " ORDER BY id ASC"

    if limit is not None:
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
    elif offset > 0:
        query += " OFFSET %s"
        params.append(offset)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def get_task_by_id(task_id: int) -> dict | None:
    """Fetch a single task by ID using parameterized query."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s;",
                (task_id,),
            )
            return cur.fetchone()


def create_task(title: str) -> dict:
    """Insert a new task into PostgreSQL and return created record using RETURNING clause."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (title, done)
                VALUES (%s, %s)
                RETURNING id, title, done;
                """,
                (title, False),
            )
            created = cur.fetchone()
        conn.commit()
        return created


def update_task(task_id: int, title: str | None = None, done: bool | None = None) -> dict | None:
    """Update title and/or done status of a task and return updated row."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s;",
                (task_id,),
            )
            existing = cur.fetchone()
            if not existing:
                return None

            new_title = title if title is not None else existing["title"]
            new_done = done if done is not None else existing["done"]

            cur.execute(
                """
                UPDATE tasks
                SET title = %s, done = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, title, done;
                """,
                (new_title, new_done, task_id),
            )
            updated = cur.fetchone()
        conn.commit()
        return updated


def delete_task(task_id: int) -> bool:
    """Delete a task by ID. Return True if deleted, False if task does not exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM tasks WHERE id = %s;",
                (task_id,),
            )
            deleted = cur.rowcount > 0
        conn.commit()
        return deleted


def get_stats() -> dict:
    """Calculate aggregate statistics directly in PostgreSQL using SQL COUNT(*)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM tasks;")
            total = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) AS done FROM tasks WHERE done = TRUE;")
            done_count = cur.fetchone()["done"]

            return {
                "total": total,
                "done": done_count,
                "open": total - done_count,
            }


def check_db_health() -> bool:
    """Ping PostgreSQL server using SELECT 1 to verify database health."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                return True
    except Exception:
        return False


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
