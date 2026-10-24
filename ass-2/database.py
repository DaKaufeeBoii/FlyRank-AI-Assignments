"""Database connection and initialization module for the Task API."""

import os
from pathlib import Path
import sqlite3

# Default database file path in the project directory
DB_PATH = Path(os.getenv("TASKS_DB_PATH", Path(__file__).resolve().parent / "tasks.db"))


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open and return a connection to the SQLite database with row factory enabled."""
    target_path = Path(db_path) if db_path is not None else DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    """Create tasks table and seed initial tasks if the table is empty.
    
    Wrapped in a transaction so initialization is all-or-nothing.
    """
    target_path = Path(db_path) if db_path is not None else DB_PATH
    conn = get_connection(target_path)
    try:
        with conn:
            # 1. Create table if it doesn't exist
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0
                );
                """
            )
            # Create an index on done for efficient status filtering
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_tasks_done ON tasks(done);
                """
            )

            # 2. Check if the table is empty before seeding
            cursor = conn.execute("SELECT COUNT(*) FROM tasks;")
            count = cursor.fetchone()[0]

            # 3. Seed initial tasks only on first run (when count is 0)
            if count == 0:
                initial_tasks = [
                    ("Read the assignment", 1),
                    ("Build the task API", 0),
                    ("Try the Swagger docs", 0),
                ]
                conn.executemany(
                    "INSERT INTO tasks (title, done) VALUES (?, ?);",
                    initial_tasks,
                )
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
