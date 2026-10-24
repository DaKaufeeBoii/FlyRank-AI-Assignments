# Stage 4: SQL Exploration Notes

This document records the SQL queries executed directly against `tasks.db` (via DB Browser for SQLite / SQLite client) to understand direct interaction with the database storage layer.

## Executed Queries and Results

### 1. List every task
```sql
SELECT * FROM tasks;
```
**Output:**
```
id | title               | done
---+---------------------+-----
1  | Read the assignment | 1
2  | Build the task API  | 0
3  | Try the Swagger docs| 0
```
**Observation:** Returns all rows currently stored in the table. The `done` boolean is represented as an integer (`1` for `True`, `0` for `False`).

---

### 2. List only completed tasks
```sql
SELECT * FROM tasks WHERE done = 1;
```
**Output:**
```
id | title               | done
---+---------------------+-----
1  | Read the assignment | 1
```
**Observation:** The `WHERE` clause filters rows down to only those matching the predicate `done = 1`.

---

### 3. Count total tasks
```sql
SELECT COUNT(*) FROM tasks;
```
**Output:**
```
3
```
**Observation:** An aggregate function that computes the exact number of rows in the table directly in the database engine without loading all rows into application memory.

---

### 4. Mark every task as completed
```sql
UPDATE tasks SET done = 1;
```
**Output:**
```
Rows updated: 3
```
**Observation:** Omitting the `WHERE` clause causes the `UPDATE` to modify every single row in the table.

---

### 5. Delete all completed tasks
```sql
DELETE FROM tasks WHERE done = 1;
```
**Output:**
```
Rows deleted: 3
```
**Observation:** All tasks with `done = 1` were purged. Calling `GET /tasks` on the API immediately returns `[]` without requiring a server restart because the API and database client share the single source of truth (`tasks.db`).
