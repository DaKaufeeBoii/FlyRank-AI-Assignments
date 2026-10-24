# Week 1 - Assignment A3: Containerize Your Stack

Run your task API against a real PostgreSQL database in Docker — then start your whole app and its database with one command.

---

## Stage 0: Postgres in Docker

Run the official PostgreSQL container with data persistence via named volume:

```bash
docker run --name taskdb -e POSTGRES_PASSWORD=dev -e POSTGRES_DB=tasks \
  -p 5432:5432 -v taskdata:/var/lib/postgresql/data -d postgres
```

Verify the container is running and test the SQL prompt:

```bash
# Check running container
docker ps

# Open psql inside container
docker exec -it taskdb psql -U postgres -d tasks
# Inside psql: \dt to view tables, \q to quit
```
