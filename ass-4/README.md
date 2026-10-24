# Auth · Login & Protect — FastAPI + Supabase Auth API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-Auth%20IdP-3ECF8E?logo=supabase&logoColor=white)](https://supabase.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Security](https://img.shields.io/badge/Auth-Bearer%20JWT-red)](https://jwt.io)
[![Swagger](https://img.shields.io/badge/Docs-Swagger%20UI%20%2Fdocs-85EA2D?logo=swagger&logoColor=black)](http://localhost:8000/docs)

A production-grade, secure REST API built with **FastAPI** and **Supabase Auth**. This service handles the complete authentication lifecycle — user registration, login, session termination, token verification, route protection via dependency injection, token refresh, and role-based access control.

---

## The Big Idea: The Trust Triangle

Modern backends never store plaintext passwords or roll their own cryptographic hashing algorithms. Instead, authentication operates as a **trust triangle** between the client, your backend, and a dedicated Identity Provider (IdP):

```
                       +-----------------------+
                       |   Identity Provider   |
                       |    (Supabase Auth)    |
                       +-----------------------+
                         ^                   ^
          1. Credentials |                   | 4. Verify Token
         (email/password)|                   |   (getUser)
                         v                   |
               +-------------+         +-------------+
               |   Client    |-------->| Backend API |
               | (Browser /  | 3. JWT  |  (FastAPI)  |
               |  Postman)   |  Bearer +-------------+
               +-------------+
```

1. **Sign Up / Log In**: The client sends credentials (`email` + `password`) directly through our API to Supabase Auth.
2. **The Token**: Supabase verifies the credentials, generates a cryptographically signed **JSON Web Token (JWT)** access token along with a refresh token, and returns it.
3. **The Request**: The client calls protected backend endpoints, presenting the JWT in the `Authorization: Bearer <access_token>` HTTP header.
4. **Verification**: The backend guard verifies the token with Supabase (`supabase.auth.get_user(token)`). If the signature is genuine and unexpired, access is granted; if forged or expired, the door is closed immediately with `401 Unauthorized`.

---

## Features

- **Public Endpoints**: Open lobby endpoints (`/public/info`, `/health`) accessible without credentials.
- **Supabase Authentication**: Registration (`POST /auth/signup`) and Login (`POST /auth/login`) with strict server-side validation.
- **Reusable Auth Dependency**: FastAPI `Depends(get_current_user)` enforcing Bearer token validation across any protected route without code duplication.
- **Token Verification**: Live network verification of JWT tokens via Supabase Auth.
- **Session Termination**: Protected Logout (`POST /auth/logout`) returning `204 No Content`.
- **Interactive Swagger UI**: Automatic OpenAPI documentation at `/docs` configured with the `HTTPBearer` security scheme and Authorize padlock.
- **Stretch Goals & Extras**:
  - **403 Forbidden Route**: `GET /protected/admin` enforcing role-based authorization.
  - **Token Refresh**: `POST /auth/refresh` exchanging refresh tokens for fresh access tokens.
  - **Brute-Force Rate Limiting**: In-memory sliding window returning `429 Too Many Requests` after consecutive failed attempts.
- **Comprehensive Test Suite**: 16 unit and integration tests passing with 100% test coverage.

---

## Project Structure

```
ass-4/
├── .env.example              # Committed template for environment variables
├── .gitignore                # Ensures .env and secrets are never committed
├── requirements.txt          # Python dependencies
├── supabase_client.py        # Supabase client initialization & config loader
├── main.py                   # FastAPI app, auth middleware, routes, rate limiter
├── test_api.py               # Complete test suite (pytest)
├── README.md                 # Project documentation and AI comparison
└── W4 - Auth - Login & protect.pdf
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10 or higher
- A free Supabase account ([supabase.com](https://supabase.com))

### 2. Configure Supabase

1. Create a free project in Supabase (e.g. `Auth-Practice`).
2. Navigate to **Project Settings** → **API**.
3. Copy your **Project URL** and **anon public key**.
4. In **Authentication** → **Sign In / Providers** → **Email**, disable **"Confirm email"** for local development so accounts can log in immediately upon registration.

### 3. Environment Setup

Create your local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your Supabase credentials:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here
PORT=8000
```

> **Security Note**: `.env` is listed in `.gitignore` and must **never** be committed to version control. Only `.env.example` with dummy values is committed.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Server (One Command)

```bash
uvicorn main:app --reload --port 8000
```

The server will initialize and log:
```
[INFO] Server running and connected to Supabase
[INFO] Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## API Reference

| Endpoint | Method | Auth Required | Expected Status | Description |
|:---|:---|:---:|:---:|:---|
| `/health` | `GET` | No | `200 OK` | Service health status |
| `/public/info` | `GET` | No | `200 OK` | Public announcement / open data |
| `/auth/signup` | `POST` | No | `201 Created` / `400` | Registers a new user via Supabase Auth |
| `/auth/login` | `POST` | No | `200 OK` / `400` / `401` / `429` | Authenticates user and returns JWT + refresh token |
| `/auth/refresh` | `POST` | No | `200 OK` / `400` / `401` | Exchanges refresh token for new access token |
| `/auth/logout` | `POST` | **Bearer JWT** | `204 No Content` / `401` | Terminates user session |
| `/protected/profile` | `GET` | **Bearer JWT** | `200 OK` / `401` | Returns user safe metadata (id, email, created_at) |
| `/protected/dashboard`| `GET` | **Bearer JWT** | `200 OK` / `401` | Second protected route confirming middleware reuse |
| `/protected/admin` | `GET` | **Bearer JWT** | `200 OK` / `401` / `403` | Admin-only route demonstrating 403 Forbidden |

---

## End-to-End Walkthrough via `curl`

### 1. Register a New Account (`POST /auth/signup`)

```bash
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "alex@example.com", "password": "SuperSecretPassword123"}'
```

**Response (`201 Created`):**
```json
{
  "id": "e93f6c8d-781e-458f-b98a-442cf8982a51",
  "email": "alex@example.com",
  "created_at": "2026-10-24T14:30:00Z",
  "app_metadata": {"provider": "email"},
  "user_metadata": {}
}
```

### 2. Log In to Receive JWT (`POST /auth/login`)

```bash
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alex@example.com", "password": "SuperSecretPassword123"}'
```

**Response (`200 OK`):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "u43g0...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "e93f6c8d-781e-458f-b98a-442cf8982a51",
    "email": "alex@example.com"
  }
}
```

### 3. Access Protected Profile (`GET /protected/profile`)

```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN_HERE>"
```

**Response (`200 OK`):**
```json
{
  "id": "e93f6c8d-781e-458f-b98a-442cf8982a51",
  "email": "alex@example.com",
  "created_at": "2026-10-24T14:30:00Z",
  "app_metadata": {"provider": "email"},
  "user_metadata": {}
}
```

### 4. Forgery Test (Tampered Token)

Modifying a single character of the JWT and re-sending:

```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.TAMPERED.SIGNATURE"
```

**Response (`401 Unauthorized`):**
```json
{
  "error": "Invalid or expired token"
}
```

### 5. Access Protected Dashboard (`GET /protected/dashboard`)

```bash
curl -i http://localhost:8000/protected/dashboard \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN_HERE>"
```

**Response (`200 OK`):**
```json
{
  "message": "Welcome to your dashboard, alex@example.com!",
  "user_id": "e93f6c8d-781e-458f-b98a-442cf8982a51",
  "status": "active"
}
```

### 6. Terminate Session (`POST /auth/logout`)

```bash
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <PASTE_ACCESS_TOKEN_HERE>"
```

**Response (`204 No Content`):**
```
HTTP/1.1 204 No Content
```

---

## Testing in Swagger UI (`/docs`)

1. Open your browser and navigate to `http://localhost:8000/docs`.
2. Notice the lock icons next to `/protected/profile`, `/protected/dashboard`, `/protected/admin`, and `/auth/logout`.
3. First execute `POST /auth/login` using **Try it out** to obtain an `access_token`.
4. Click the green **Authorize** padlock button at the top right of the page.
5. In the modal, paste your JWT `access_token` and click **Authorize**.
6. Now execute `GET /protected/profile` with **Try it out** — Swagger automatically attaches the `Authorization: Bearer <token>` header to the request and returns status `200 OK`.

---

## Security Concepts & Architecture Notes

### 1. 401 Unauthorized vs 403 Forbidden

| Status Code | Meaning | Analogy | Triggered When |
|:---|:---|:---|:---|
| **`401 Unauthorized`** | *"I do not know who you are."* | Showing up to the club door with no ID or a forged pass. | Missing `Authorization` header, missing `Bearer` prefix, invalid signature, expired token. |
| **`403 Forbidden`** | *"I know exactly who you are, and you still cannot enter."* | Presenting valid ID, but you're not on the VIP guest list. | Valid authenticated user attempting to access `/protected/admin` without administrator privileges. |

### 2. Why Access Tokens are Short-Lived & The Role of Refresh Tokens

- **Access Tokens are Stateless**: When our API verifies a JWT, it trusts the cryptographically signed claims without having to query a centralized session database on every micro-second.
- **Revocation Challenge**: Because stateless tokens cannot be easily "un-issued", giving them long lifetimes (e.g. 30 days) is a severe vulnerability — if stolen, the attacker has free access for a month.
- **The Solution**: Access tokens are deliberately short-lived (typically 15 to 60 minutes). When they expire, the client sends their long-lived, securely stored **refresh token** to `/auth/refresh` to obtain a new access token. If the user's account is compromised, the Identity Provider can revoke the refresh token, instantly halting access once the short-lived access token expires.

### 3. Why Brute-Force Rate Limiting Lives at the Login Endpoint

The login endpoint is the primary target for credential stuffing, dictionary attacks, and password-spraying scripts. Because passwords must be checked against Supabase (which involves network round-trips and cryptographic verification), unmetered login requests can exhaust server threads and compromise user accounts. Our server enforces sliding-window IP rate limiting returning `429 Too Many Requests` after 5 consecutive failed attempts, shutting down automated attacks before they reach downstream services.

---

## Automated Test Suite

Run the automated test suite with pytest:

```bash
pytest -v
```

All 16 tests pass:
```
test_api.py::test_health_check PASSED
test_api.py::test_public_info PASSED
test_api.py::test_signup_missing_fields_validation PASSED
test_api.py::test_login_missing_fields_validation PASSED
test_api.py::test_login_invalid_credentials_returns_401 PASSED
test_api.py::test_signup_success_returns_201 PASSED
test_api.py::test_login_success_returns_200_and_tokens PASSED
test_api.py::test_protected_routes_without_token_return_401 PASSED
test_api.py::test_protected_route_malformed_token_returns_401 PASSED
test_api.py::test_protected_route_invalid_or_expired_token_returns_401 PASSED
test_api.py::test_protected_profile_and_dashboard_success PASSED
test_api.py::test_logout_endpoint_returns_204 PASSED
test_api.py::test_admin_route_authorization_403_vs_200 PASSED
test_api.py::test_refresh_token_endpoint PASSED
test_api.py::test_login_rate_limiting_returns_429 PASSED
test_api.py::test_swagger_openapi_schema_contains_http_bearer PASSED

======================= 16 passed in 1.36s =======================
```

---

## Stage 7: AI vs Me (Bonus Stage)

### 1. The Specification Prompt

Without copying from the assignment guide, the following prompt was formulated from memory to challenge the AI:

```text
Build a production-style REST API in Python using FastAPI and Supabase Auth as the Identity Provider.
The service must expose:
1. POST /auth/signup (returns 201 Created with user object, 400 on missing or invalid inputs)
2. POST /auth/login (returns 200 OK with access_token and refresh_token, 400 on empty fields, 401 on bad credentials)
3. POST /auth/logout (protected endpoint, ends session, returns 204 No Content)
4. GET /public/info (open endpoint, returns 200 OK with public greeting)
5. GET /protected/profile (protected endpoint, verifies JWT via Supabase, returns 200 with user id and email)

Protected endpoints must use a reusable FastAPI dependency to extract and verify the Bearer token from the Authorization header.
Configure Swagger UI bearer authentication so the Authorize padlock works at /docs.
All errors must return JSON in the format {"error": "..."}.
```

The AI-generated code was saved in quarantine inside [`ass-4/ai-version/`](file:///d:/Kaufee/padhai/Internships/FlyRank.ai/ass-4/ai-version/main.py).

### 2. Code Comparison & Review (`git diff --no-index`)

Running `git diff --no-index main.py ai-version/main.py` highlighted three critical differences answering the core review questions:

#### Question A: How did it handle token extraction?
- **AI Implementation:**
  ```python
  auth_header = request.headers.get("Authorization", "")
  token = auth_header.split(" ")[1]
  ```
  The AI naively performed string splitting without validating header structure. If an incoming request sent `Authorization: secret_token_xyz` without the `Bearer` prefix, or sent empty whitespace, this line crashed with an unhandled `IndexError` (triggering an HTTP 500 Internal Server Error) instead of returning HTTP 401.
- **Our Implementation:**
  ```python
  parts = auth_header.strip().split()
  if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail={"error": "Access token required"},
      )
  ```
  Strictly validates that exactly two tokens exist, case-insensitively checks the `Bearer` keyword, rejects empty tokens, and guarantees a standard `401 Unauthorized` with `{"error": "Access token required"}`.

#### Question B: What security flaws did it introduce?
- **Sensitive Token Logging**: The AI included:
  ```python
  print(f"Auth failed for token {token}: {e}")
  ```
  Dumping raw bearer tokens into standard output and application logs creates a serious security risk (tokens could be intercepted by observability pipelines, log sinks, or unauthorized staff).
- **Default 403 vs 401 Conflict**: The AI used `security = HTTPBearer()` without `auto_error=False`. When an Authorization header was missing, FastAPI intercepted the request and automatically returned `403 Forbidden` (`{"detail": "Not authenticated"}`) instead of the assignment-mandated `401 Unauthorized` (`{"error": "Access token required"}`).
- **Input Validation Mismatch (422 vs 400)**: The AI relied on raw Pydantic models without a custom `RequestValidationError` handler, causing missing fields to return HTTP `422 Unprocessable Entity` instead of HTTP `400 Bad Request`.

#### Question C: What did the prompt forget to specify, and what did the AI silently decide?
- **Omitted**: The prompt didn't specify whether to use `auto_error=False` on `HTTPBearer`, leading the AI to pick the default which hijacks 401 handling into 403.
- **Omitted**: The prompt omitted how session sign-out should behave; the AI blindly called `supabase.auth.sign_out()` globally without handling exceptions or tying to the active user context.
- **Silent Decision**: The AI silently chose the deprecated `@app.on_event("startup")` syntax instead of the modern `@asynccontextmanager` lifespan standard recommended in modern FastAPI.

### 3. The Rematch: Improved Prompt & Outcome

**Improved Prompt:**
> "Build a FastAPI REST API using Supabase Auth as the IdP. Use the modern @asynccontextmanager lifespan. Configure HTTPBearer(auto_error=False) so missing headers do not trigger default 403s. Implement custom exception handlers mapping validation errors to HTTP 400 with a JSON {'error': '...'} schema. Safely parse the 'Authorization: Bearer <token>' header ensuring length and case checks without crashing or logging tokens. Implement endpoints: POST /auth/signup (201), POST /auth/login (200), POST /auth/logout (204), GET /public/info (200), and GET /protected/profile (200)."

**Rematch Result:**
By explicitly constraining the lifespan pattern, `auto_error=False`, and token parsing safety in the improved prompt, the regenerated code eliminated the `IndexError` crash and properly adhered to all HTTP 400/401 contract requirements on the first run.
