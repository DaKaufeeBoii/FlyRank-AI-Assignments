"""FastAPI Authentication API with Supabase Auth."""

from contextlib import asynccontextmanager
import logging
from typing import Any, Dict, Optional
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
import uvicorn
from supabase_auth.errors import AuthApiError, AuthError

from supabase_client import PORT, get_supabase_client, init_supabase

logger = logging.getLogger("auth_api")

# HTTPBearer security scheme: enables the Swagger UI "Authorize" padlock
security = HTTPBearer(
    auto_error=False,
    description="Enter the Supabase access token (JWT) obtained from /auth/login. Example: Bearer eyJhbGciOi...",
)


# ---------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------


class AuthRequest(BaseModel):
    """Schema for authentication credentials."""
    email: Optional[str] = Field(default=None, example="user@example.com", description="User email address")
    password: Optional[str] = Field(default=None, example="StrongPassword123", description="User password")


class AuthResponse(BaseModel):
    """Schema returned upon successful login."""
    access_token: str = Field(description="Supabase signed JWT access token")
    refresh_token: str = Field(description="Supabase refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(default=3600, description="Token lifetime in seconds")
    user: Dict[str, Any] = Field(description="Basic user metadata")


class UserProfileResponse(BaseModel):
    """Schema representing user profile metadata."""
    id: str = Field(description="Supabase user UUID")
    email: str = Field(description="User email address")
    created_at: Optional[str] = Field(default=None, description="Account creation timestamp")
    app_metadata: Dict[str, Any] = Field(default_factory=dict, description="Application metadata")
    user_metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom user metadata")


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str


class AuthenticatedUser(BaseModel):
    """Internal model representing an authenticated user from Supabase."""
    id: str
    email: str
    created_at: Optional[str] = None
    app_metadata: dict = {}
    user_metadata: dict = {}
    token: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan context: initialize Supabase client on startup."""
    init_supabase()
    yield


app = FastAPI(
    title="Secure Auth API (Supabase & FastAPI)",
    version="1.0.0",
    description=(
        "Production-ready authentication and authorization API built with FastAPI and Supabase Auth.\n\n"
        "### Features:\n"
        "- **Sign Up & Log In**: Public auth endpoints issuing signed JWTs.\n"
        "- **JWT Verification**: Token signature and claims verified securely via Supabase Auth.\n"
        "- **Reusable Auth Guard**: FastAPI `Depends(get_current_user)` protecting private endpoints.\n"
        "- **Protected Endpoints**: `/protected/profile`, `/protected/dashboard`, `/auth/logout`.\n"
        "- **Swagger Bearer Auth**: Click the **Authorize** padlock above, paste your JWT, and test routes."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
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


# ---------------------------------------------------------
# STAGE 4: Reusable Auth Middleware / Dependency Guard
# ---------------------------------------------------------


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> AuthenticatedUser:
    """Reusable authentication guard dependency.

    Extracts the Bearer token from the Authorization header,
    verifies it with Supabase Auth, and returns the authenticated user.
    """
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
    client = get_supabase_client()

    try:
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid or expired token"},
            )

        user = user_response.user
        return AuthenticatedUser(
            id=str(user.id),
            email=user.email or "",
            created_at=str(user.created_at) if user.created_at else None,
            app_metadata=user.app_metadata or {},
            user_metadata=user.user_metadata or {},
            token=token,
        )
    except HTTPException:
        raise
    except (AuthApiError, AuthError) as e:
        logger.warning("Supabase rejected token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
        )
    except Exception as e:
        logger.error("Token verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
        )


@app.get("/health", tags=["Health"], response_model=Dict[str, str], summary="Health Check")
async def health_check():
    """Health check endpoint to verify server is active."""
    return {"status": "ok", "service": "Supabase Auth API"}


# ---------------------------------------------------------
# STAGE 1: Open auth - Sign Up & Log In
# ---------------------------------------------------------


@app.post(
    "/auth/signup",
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
    summary="Register a new account",
    responses={
        201: {"model": UserProfileResponse, "description": "Account created successfully"},
        400: {"model": ErrorResponse, "description": "Missing credentials or invalid request"},
    },
)
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


@app.post(
    "/auth/login",
    status_code=status.HTTP_200_OK,
    tags=["Auth"],
    response_model=AuthResponse,
    summary="Log in and retrieve JWT",
    responses={
        200: {"model": AuthResponse, "description": "Successfully authenticated with access and refresh tokens"},
        400: {"model": ErrorResponse, "description": "Missing credentials"},
        401: {"model": ErrorResponse, "description": "Invalid login credentials"},
    },
)
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


@app.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Auth"],
    summary="Log out (terminate session)",
    responses={
        204: {"description": "Successfully logged out, session terminated"},
        401: {"model": ErrorResponse, "description": "Missing, malformed, or invalid bearer token"},
    },
)
async def logout(user: AuthenticatedUser = Depends(get_current_user)):
    """End the user's session in Supabase Auth (protected by auth guard)."""
    client = get_supabase_client()
    try:
        client.auth.sign_out()
    except Exception as e:
        logger.warning("Sign out error ignored: %s", e)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------
# STAGE 2: Public gate
# ---------------------------------------------------------


@app.get(
    "/public/info",
    status_code=status.HTTP_200_OK,
    tags=["Public"],
    response_model=MessageResponse,
    summary="Read public information (open to everyone)",
)
async def public_info():
    """Public open endpoint reachable by anyone without authentication."""
    return {"message": "Welcome stranger! This info is public."}


# ---------------------------------------------------------
# STAGE 3 & 4: Protected routes using reusable guard
# ---------------------------------------------------------


@app.get(
    "/protected/profile",
    status_code=status.HTTP_200_OK,
    tags=["Protected"],
    response_model=UserProfileResponse,
    summary="Read private profile data",
    responses={
        200: {"model": UserProfileResponse, "description": "Verified profile metadata"},
        401: {"model": ErrorResponse, "description": "Access token required, or invalid/expired token"},
    },
)
async def protected_profile(user: AuthenticatedUser = Depends(get_current_user)):
    """Protected profile endpoint - verified via reusable auth dependency."""
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
        "app_metadata": user.app_metadata,
        "user_metadata": user.user_metadata,
    }


@app.get(
    "/protected/dashboard",
    status_code=status.HTTP_200_OK,
    tags=["Protected"],
    summary="Read private dashboard",
    responses={
        200: {"description": "Access granted to user dashboard"},
        401: {"model": ErrorResponse, "description": "Access token required, or invalid/expired token"},
    },
)
async def protected_dashboard(user: AuthenticatedUser = Depends(get_current_user)):
    """Second protected endpoint demonstrating middleware reuse without extra code."""
    return {
        "message": f"Welcome to your dashboard, {user.email}!",
        "user_id": user.id,
        "status": "active",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
