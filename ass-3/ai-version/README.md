# Stage 6 Quarantine: AI-Generated Stack

This directory contains the AI-generated implementation of the containerized Task API for Stage 6 review and comparison.

### Review Summary
1. **Startup Timing Race Condition:** The AI's code attempts an immediate database connection inside `@app.on_event("startup")` without retry/backoff. In fresh containers where PostgreSQL takes ~2 seconds to initialize its cluster, the API container can crash immediately before PostgreSQL is ready.
2. **Missing Rowcount Validation:** In `DELETE /tasks/{id}`, the AI executes `DELETE FROM tasks WHERE id = %s` but fails to check `cur.rowcount == 0`. An unknown task ID returns `204 No Content` instead of `404 Not Found`.
3. **Heavy Docker Base Image:** Uses `FROM python:3.11` instead of `python:3.11-slim`, inflating the final container image size from ~180MB to over 1GB.
4. **Older Compose Format:** Specifies obsolete `version: '3.8'` attribute which Docker Compose v2/v5 now deprecates.
