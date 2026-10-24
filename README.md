# FlyRank Internship - Backend Engineering Track

Repository containing the weekly assignments and projects for the FlyRank Backend Engineering Internship.

---

## Projects Directory

### [Week 2 (Assignment 1): In-Memory CRUD API](./ass-1/)
- **Tech Stack:** Python 3.10+, FastAPI, Pydantic, Uvicorn
- **Focus:** First CRUD API endpoints (`GET`, `POST`, `PUT`, `DELETE`), request validation (400), not found handling (404), and in-memory list storage.
- [View Assignment 1 Details & Documentation](./ass-1/README.md)

### [Week 3 (Assignment 2): Connecting CRUD to SQLite](./ass-2/)
- **Tech Stack:** Python 3.10+, FastAPI, SQLite (`sqlite3`), Pydantic, Pytest
- **Focus:** Replacing in-memory storage with persistent disk storage (`tasks.db`), parameterized SQL queries, indexing, atomic transactions, SQL search/filter/sort, automated testing, and AI code review rematch.
- [View Assignment 2 Details & Documentation](./ass-2/README.md)

### [Week 4 (Assignment 3): Containerize Your Stack](./ass-3/)
- **Tech Stack:** Python 3.11, FastAPI, PostgreSQL 17, `psycopg` (v3), Docker, Docker Compose
- **Focus:** Containerizing the stack, multi-container orchestration with `compose.yaml`, `.env` secret management, PostgreSQL volume persistence, parameterized queries, health checks, database indexing, and AI code review rematch.
- [View Assignment 3 Details & Documentation](./ass-3/README.md)

---

## Quick Start (Assignment 3)

```bash
# Navigate to Assignment 3
cd ass-3

# Setup environment variables
cp .env.example .env

# Run the entire stack in one command
docker compose up -d

# Check logs
docker compose logs -f api
```

- API Base URL: [http://localhost:3000](http://localhost:3000)
- Interactive Swagger Documentation: [http://localhost:3000/docs](http://localhost:3000/docs)
- Health Check: [http://localhost:3000/health](http://localhost:3000/health)

---

## Quick Start (Assignment 2)

```bash
# Navigate to Assignment 2
cd ass-2

# Install dependencies
pip install -r requirements.txt

# Run the API with reload
uvicorn main:app --reload --port 8000

# Run automated test suite
pytest -v test_api.py
```

- Interactive Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)
