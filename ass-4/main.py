"""FastAPI Authentication API with Supabase Auth."""

from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional
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
# In-Memory Rate Limiting for Login (Brute-Force Protection)
# ---------------------------------------------------------

FAILED_LOGIN_ATTEMPTS: Dict[str, List[datetime]] = defaultdict(list)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 5


def check_login_rate_limit(client_ip: str) -> None:
    """Check if the client IP has exceeded the allowed failed login threshold."""
    now = datetime.now()
    cutoff = now - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    # Filter attempts within recent window
    FAILED_LOGIN_ATTEMPTS[client_ip] = [
        ts for ts in FAILED_LOGIN_ATTEMPTS[client_ip] if ts > cutoff
    ]
    if len(FAILED_LOGIN_ATTEMPTS[client_ip]) >= MAX_FAILED_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "Too many failed login attempts. Please try again later."},
        )


def record_failed_login(client_ip: str) -> None:
    """Record a failed login attempt for the client IP."""
    FAILED_LOGIN_ATTEMPTS[client_ip].append(datetime.now())


def clear_failed_logins(client_ip: str) -> None:
    """Reset failed attempts after a successful login."""
    FAILED_LOGIN_ATTEMPTS.pop(client_ip, None)


# ---------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------


class AuthRequest(BaseModel):
    """Schema for authentication credentials."""
    email: Optional[str] = Field(default=None, examples=["user@example.com"], description="User email address")
    password: Optional[str] = Field(default=None, examples=["StrongPassword123"], description="User password")


class RefreshRequest(BaseModel):
    """Schema for token refresh request."""
    refresh_token: Optional[str] = Field(default=None, examples=["eyJhbGciOi..."], description="Supabase refresh token")


class AuthResponse(BaseModel):
    """Schema returned upon successful login."""
    access_token: str = Field(description="Supabase signed JWT access token")
    refresh_token: str = Field(description="Supabase refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(default=3600, description="Token lifetime in seconds")
    user: Dict[str, Any] = Field(description="Basic user metadata")


class RefreshResponse(BaseModel):
    """Schema returned upon successful token refresh."""
    access_token: str = Field(description="Fresh Supabase signed JWT access token")
    refresh_token: str = Field(description="Fresh Supabase refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(default=3600, description="Token lifetime in seconds")


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
    app_metadata: dict = Field(default_factory=dict)
    user_metadata: dict = Field(default_factory=dict)
    token: str

    @property
    def is_admin(self) -> bool:
        """Determine if user has administrator authorization."""
        return bool(
            self.app_metadata.get("role") == "admin"
            or self.user_metadata.get("role") == "admin"
            or self.user_metadata.get("is_admin") is True
            or self.email.endswith("@flyrank.admin")
        )


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
        "- **Protected Endpoints**: `/protected/profile`, `/protected/dashboard`, `/protected/admin`, `/auth/logout`.\n"
        "- **Token Refresh**: Exchange long-lived refresh tokens for new access tokens at `/auth/refresh`.\n"
        "- **Role-Based Authorization (403)**: Admin-only access guard at `/protected/admin`.\n"
        "- **Brute-Force Rate Limiting (429)**: Lockout after excessive failed logins.\n"
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
        app_meta = user.app_metadata if isinstance(user.app_metadata, dict) else {}
        user_meta = user.user_metadata if isinstance(user.user_metadata, dict) else {}

        return AuthenticatedUser(
            id=str(user.id),
            email=user.email or "",
            created_at=str(user.created_at) if user.created_at else None,
            app_metadata=app_meta,
            user_metadata=user_meta,
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

        app_meta = response.user.app_metadata if isinstance(response.user.app_metadata, dict) else {}
        user_meta = response.user.user_metadata if isinstance(response.user.user_metadata, dict) else {}

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "id": str(response.user.id),
                "email": response.user.email,
                "created_at": str(response.user.created_at) if response.user.created_at else None,
                "app_metadata": app_meta,
                "user_metadata": user_meta,
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
        429: {"model": ErrorResponse, "description": "Too many failed attempts (rate limited)"},
    },
)
async def login(credentials: AuthRequest, request: Request):
    """Authenticate an existing user and return Supabase JWT access and refresh tokens."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    # Enforce brute-force rate limiting
    check_login_rate_limit(client_ip)

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
            record_failed_login(client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid login credentials"},
            )

        # Clear failed attempts on successful login
        clear_failed_logins(client_ip)

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
        record_failed_login(client_ip)
        logger.warning("Supabase login rejected: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"},
        )
    except Exception as e:
        record_failed_login(client_ip)
        logger.error("Unexpected error during login: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid login credentials"},
        )


@app.post(
    "/auth/refresh",
    status_code=status.HTTP_200_OK,
    tags=["Auth"],
    response_model=RefreshResponse,
    summary="Refresh an expired access token using a refresh token",
    responses={
        200: {"model": RefreshResponse, "description": "Successfully refreshed access token"},
        400: {"model": ErrorResponse, "description": "Missing refresh token"},
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
    },
)
async def refresh_token_endpoint(body: RefreshRequest):
    """Exchange a valid Supabase refresh token for a fresh access token."""
    if not body.refresh_token or not body.refresh_token.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "refresh_token is required"},
        )

    client = get_supabase_client()
    try:
        response = client.auth.refresh_session(body.refresh_token.strip())
        if not response.session or not response.session.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Invalid or expired refresh token"},
            )
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
            "expires_in": response.session.expires_in,
        }
    except HTTPException:
        raise
    except (AuthApiError, AuthError) as e:
        logger.warning("Refresh token rejected: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired refresh token"},
        )
    except Exception as e:
        logger.error("Unexpected error during refresh: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired refresh token"},
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


# ---------------------------------------------------------
# STRETCH GOAL: 403 Forbidden Admin Authorization
# ---------------------------------------------------------


@app.get(
    "/protected/admin",
    status_code=status.HTTP_200_OK,
    tags=["Protected"],
    summary="Admin-only private area (demonstrates 403 Forbidden)",
    responses={
        200: {"description": "Access granted to administrator panel"},
        401: {"model": ErrorResponse, "description": "Unauthenticated (who are you?)"},
        403: {"model": ErrorResponse, "description": "Forbidden (I know who you are, but no)"},
    },
)
async def protected_admin(user: AuthenticatedUser = Depends(get_current_user)):
    """Admin-only endpoint demonstrating the distinction between 401 and 403."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Forbidden: Administrator privileges required to access this resource"},
        )

    return {
        "message": f"Welcome Administrator {user.email}",
        "user_id": user.id,
        "role": "admin",
        "system_stats": {"active_sessions": 42, "auth_mode": "Supabase JWT"},
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
