# AI Quarantine — Stage 7

This directory contains the AI-generated implementation of the Supabase Auth API for Stage 7 review and code comparison.

## The Generation Prompt
```
Build a FastAPI application with Supabase Auth. Implement POST /auth/signup (201),
POST /auth/login (200 returning access token), POST /auth/logout (204),
GET /public/info (200), and GET /protected/profile (200).
Protect the profile and logout routes using JWT verification middleware and
configure Swagger UI with Bearer authentication.
```

## Key Findings & Critical Flaws Identified

1. **Header Parsing Crash (IndexError):**  
   The AI attempted token extraction via `auth_header.split(" ")[1]`. If a client sends `Authorization: mytoken` (without the `Bearer` keyword) or multiple spaces, the code crashes with an unhandled `IndexError` (HTTP 500) rather than returning a clean `401 Unauthorized` with `{"error": "Access token required"}`.

2. **Security & Privacy Leak:**  
   The AI logged `print(f"Auth failed for token {token}: {e}")` to stdout. Logging bearer access tokens directly to standard output or server logs violates security standards (tokens in logs can be viewed by monitoring tools or operators and reused by malicious actors).

3. **Status Code Misalignment (422 vs 400 & 403 vs 401):**  
   - The AI relied on FastAPI's default Pydantic validation which returns HTTP `422 Unprocessable Entity` instead of the required `400 Bad Request`.
   - FastAPI's default `HTTPBearer()` (with `auto_error=True`) automatically returns `403 Forbidden` (`{"detail": "Not authenticated"}`) if the Authorization header is omitted, failing the requirement to return `401 Unauthorized` (`{"error": "Access token required"}`).

4. **Deprecated Lifespan Architecture:**  
   Used `@app.on_event("startup")` instead of modern `@asynccontextmanager` lifespan handlers.
