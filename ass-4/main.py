"""FastAPI Authentication API with Supabase Auth."""

from contextlib import asynccontextmanager
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from supabase_auth.errors import AuthApiError, AuthError

from supabase_client import PORT, get_supabase_client, init_supabase

logger = logging.getLogger("auth_api")


class AuthRequest(BaseModel):
    """Schema for authentication credentials."""
    email: Optional[str] = None
    password: Optional[str] = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan context: initialize Supabase client on startup."""
    init_supabase()
    yield


app = FastAPI(
    title="Secure Auth API",
    version="1.0.0",
    description="FastAPI service with Supabase Auth, JWT verification, and protected routes.",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError):
    """Return 400 Bad Request with a clear JSON error message for validation errors."""
    messages = [error.get("msg", "Invalid request body") for error in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "; ".join(messages)},
    )


@app.exception_handler(HTTPException)
async def http_error_handler(_request: Request, exc: HTTPException):
    """Return assignment-standard JSON errors for application HTTP exceptions."""
    message = exc.detail.get("error") if isinstance(exc.detail, dict) else exc.detail
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": message},
        headers=exc.headers,
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify server is active."""
    return {"status": "ok", "service": "Supabase Auth API"}


# ---------------------------------------------------------
# STAGE 1: Open auth - Sign Up & Log In
# ---------------------------------------------------------


@app.post("/auth/signup", status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def signup(credentials: AuthRequest):
    """Register a new user with email and password via Supabase Auth."""
    if not credentials.email or not credentials.email.strip() or not credentials.password or not credentials.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Email and password are required and cannot be empty"},
        )

    client = get_supabase_client()
    try:
        response = client.auth.sign_up({
            "email": credentials.email.strip(),
            "password": credentials.password.strip(),
        })

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Unable to create account with provided details"},
            )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(response.user.id),
                "email": response.user.email,
                "created_at": str(response.user.created_at) if response.user.created_at else None,
                "app_metadata": response.user.app_metadata or {},
                "user_metadata": response.user.user_metadata or {},
            },
        )
    except HTTPException:
        raise
    except (AuthApiError, AuthError) as e:
        logger.warning("Supabase signup rejected: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": getattr(e, "message", str(e))},
        )
    except Exception as e:
        logger.error("Unexpected error during signup: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Signup failed: {str(e)}"},
        )


@app.post("/auth/login", status_code=status.HTTP_200_OK, tags=["Auth"])
async def login(credentials: AuthRequest):
    """Authenticate an existing user and return Supabase JWT access and refresh tokens."""
    if not credentials.email or not credentials.email.strip() or not credentials.password or not credentials.password.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Email and password are required and cannot be empty"},
        )

    client = get_supabase_client()
    try:
        response = client.auth.sign_in_with_password({
            "email": credentials.email.strip(),
            "password": credentials.password.strip(),
        })

        if not response.session or not response.session.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid login credentials"},
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
            "expires_in": response.session.expires_in,
            "user": {
                "id": str(response.user.id) if response.user else None,
                "email": response.user.email if response.user else credentials.email.strip(),
            },
        }
    except HTTPException:
        raise
    except (AuthApiError, AuthError) as e:
        logger.warning("Supabase login rejected: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"},
        )
    except Exception as e:
        logger.error("Unexpected error during login: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"},
        )


# ---------------------------------------------------------
# STAGE 2: The public & protected gates (unverified guard)
# ---------------------------------------------------------


@app.get("/public/info", status_code=status.HTTP_200_OK, tags=["Public"])
async def public_info():
    """Public open endpoint reachable by anyone without authentication."""
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile", status_code=status.HTTP_200_OK, tags=["Protected"])
async def protected_profile(request: Request):
    """Protected profile endpoint - Stage 2 extracts token, returns 401 if missing."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"},
        )

    parts = auth_header.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"},
        )

    token = parts[1].strip()
    return {"message": "Token presented", "token": token}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
