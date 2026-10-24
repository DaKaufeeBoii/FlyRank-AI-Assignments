"""Comprehensive test suite for FastAPI Supabase Auth API (Assignment 4)."""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from supabase_auth.errors import AuthApiError

from main import FAILED_LOGIN_ATTEMPTS, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Reset rate limiter state before each test."""
    FAILED_LOGIN_ATTEMPTS.clear()
    yield
    FAILED_LOGIN_ATTEMPTS.clear()


# =========================================================
# Public Endpoints & Health Check
# =========================================================


def test_health_check():
    """Verify health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Supabase Auth API"}


def test_public_info():
    """Verify public endpoint is open and requires no authorization."""
    response = client.get("/public/info")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome stranger!" in data.get("message", "")


# =========================================================
# Stage 1: Signup & Login Validation
# =========================================================


def test_signup_missing_fields_validation():
    """Verify signup returns 400 Bad Request when fields are missing or empty."""
    r1 = client.post("/auth/signup", json={})
    assert r1.status_code == 400
    assert "error" in r1.json()

    r2 = client.post("/auth/signup", json={"email": "   ", "password": "valid_password"})
    assert r2.status_code == 400
    assert "error" in r2.json()

    r3 = client.post("/auth/signup", json={"email": "user@example.com", "password": "   "})
    assert r3.status_code == 400
    assert "error" in r3.json()


def test_login_missing_fields_validation():
    """Verify login returns 400 Bad Request when fields are missing or empty."""
    r1 = client.post("/auth/login", json={})
    assert r1.status_code == 400
    assert "error" in r1.json()

    r2 = client.post("/auth/login", json={"email": "user@example.com", "password": ""})
    assert r2.status_code == 400
    assert "error" in r2.json()


def test_login_invalid_credentials_returns_401():
    """Verify login returns 401 Unauthorized with proper error when credentials fail."""
    with patch("main.get_supabase_client") as mock_get_client:
        mock_auth = MagicMock()
        mock_auth.sign_in_with_password.side_effect = AuthApiError(
            "Invalid login credentials", 400, None
        )
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client

        response = client.post(
            "/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert response.json() == {"error": "Invalid login credentials"}


def test_signup_success_returns_201():
    """Verify signup returns 201 Created and user object on successful registration."""
    with patch("main.get_supabase_client") as mock_get_client:
        mock_user = MagicMock()
        mock_user.id = "11111111-2222-3333-4444-555555555555"
        mock_user.email = "newuser@example.com"
        mock_user.created_at = "2026-10-24T12:00:00Z"
        mock_user.app_metadata = {"provider": "email"}
        mock_user.user_metadata = {}

        mock_resp = MagicMock()
        mock_resp.user = mock_user

        mock_auth = MagicMock()
        mock_auth.sign_up.return_value = mock_resp
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client

        response = client.post(
            "/auth/signup",
            json={"email": "newuser@example.com", "password": "securepassword123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "11111111-2222-3333-4444-555555555555"
        assert data["email"] == "newuser@example.com"


def test_login_success_returns_200_and_tokens():
    """Verify login returns 200 OK with access and refresh tokens on valid credentials."""
    with patch("main.get_supabase_client") as mock_get_client:
        mock_session = MagicMock()
        mock_session.access_token = "mock_jwt_access_token_xyz"
        mock_session.refresh_token = "mock_refresh_token_xyz"
        mock_session.expires_in = 3600

        mock_user = MagicMock()
        mock_user.id = "11111111-2222-3333-4444-555555555555"
        mock_user.email = "user@example.com"

        mock_resp = MagicMock()
        mock_resp.session = mock_session
        mock_resp.user = mock_user

        mock_auth = MagicMock()
        mock_auth.sign_in_with_password.return_value = mock_resp
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client

        response = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "mock_jwt_access_token_xyz"
        assert data["refresh_token"] == "mock_refresh_token_xyz"
        assert data["token_type"] == "bearer"


# =========================================================
# Stage 2 & 3 & 4: Protected Routes & Token Verification
# =========================================================


def test_protected_routes_without_token_return_401():
    """Protected routes must return 401 with 'Access token required' when header is missing."""
    for path in ["/protected/profile", "/protected/dashboard", "/protected/admin"]:
        r = client.get(path)
        assert r.status_code == 401
        assert r.json() == {"error": "Access token required"}

    # Also test POST /auth/logout
    r_logout = client.post("/auth/logout")
    assert r_logout.status_code == 401
    assert r_logout.json() == {"error": "Access token required"}


def test_protected_route_malformed_token_returns_401():
    """Protected routes must reject malformed tokens without 'Bearer' prefix."""
    r1 = client.get("/protected/profile", headers={"Authorization": "Basic dummy123"})
    assert r1.status_code == 401
    assert r1.json() == {"error": "Access token required"}

    r2 = client.get("/protected/profile", headers={"Authorization": "Bearer "})
    assert r2.status_code == 401
    assert r2.json() == {"error": "Access token required"}


def test_protected_route_invalid_or_expired_token_returns_401():
    """Protected routes must return 401 with 'Invalid or expired token' when Supabase rejects token."""
    with patch("main.get_supabase_client") as mock_get_client:
        mock_auth = MagicMock()
        mock_auth.get_user.side_effect = AuthApiError("Invalid JWT", 401, None)
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client

        response = client.get(
            "/protected/profile",
            headers={"Authorization": "Bearer tampered_forged_token"},
        )
        assert response.status_code == 401
        assert response.json() == {"error": "Invalid or expired token"}


def test_protected_profile_and_dashboard_success():
    """Protected routes must return 200 with user information when token verifies."""
    with patch("main.get_supabase_client") as mock_get_client:
        mock_user = MagicMock()
        mock_user.id = "user-12345"
        mock_user.email = "verified@example.com"
        mock_user.created_at = "2026-10-24T10:00:00Z"
        mock_user.app_metadata = {"role": "member"}
        mock_user.user_metadata = {"full_name": "Test User"}

        mock_user_resp = MagicMock()
        mock_user_resp.user = mock_user

        mock_auth = MagicMock()
        mock_auth.get_user.return_value = mock_user_resp
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client

        # Test profile
        r_prof = client.get(
            "/protected/profile",
            headers={"Authorization": "Bearer valid_access_token"},
        )
        assert r_prof.status_code == 200
        p_data = r_prof.json()
        assert p_data["id"] == "user-12345"
        assert p_data["email"] == "verified@example.com"

        # Test dashboard (middleware reuse)
        r_dash = client.get(
            "/protected/dashboard",
            headers={"Authorization": "Bearer valid_access_token"},
        )
        assert r_dash.status_code == 200
        assert "verified@example.com" in r_dash.json()["message"]


def test_logout_endpoint_returns_204():
    """Protected logout endpoint calls sign_out and returns 204 No Content."""
    with patch("main.get_supabase_client") as mock_get_client:
        mock_user = MagicMock()
        mock_user.id = "user-12345"
        mock_user.email = "verified@example.com"
        mock_user.created_at = "2026-10-24T10:00:00Z"
        mock_user.app_metadata = {}
        mock_user.user_metadata = {}

        mock_user_resp = MagicMock()
        mock_user_resp.user = mock_user

        mock_auth = MagicMock()
        mock_auth.get_user.return_value = mock_user_resp
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client

        response = client.post(
            "/auth/logout",
            headers={"Authorization": "Bearer valid_access_token"},
        )
        assert response.status_code == 204
        assert response.content == b""
        mock_auth.sign_out.assert_called_once()


# =========================================================
# Extras: 403 Forbidden, Refresh, and Rate Limiting
# =========================================================


def test_admin_route_authorization_403_vs_200():
    """Test 403 Forbidden for non-admin user vs 200 OK for admin user."""
    with patch("main.get_supabase_client") as mock_get_client:
        # 1. Non-admin user -> 403 Forbidden
        normal_user = MagicMock()
        normal_user.id = "normal-1"
        normal_user.email = "regular@example.com"
        normal_user.created_at = "2026-10-24T10:00:00Z"
        normal_user.app_metadata = {"role": "user"}
        normal_user.user_metadata = {}

        mock_auth = MagicMock()
        mock_auth.get_user.return_value = MagicMock(user=normal_user)
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client

        r_forbidden = client.get(
            "/protected/admin",
            headers={"Authorization": "Bearer normal_token"},
        )
        assert r_forbidden.status_code == 403
        assert "Forbidden" in r_forbidden.json()["error"]

        # 2. Admin user -> 200 OK
        admin_user = MagicMock()
        admin_user.id = "admin-1"
        admin_user.email = "admin@flyrank.ai"
        admin_user.created_at = "2026-10-24T10:00:00Z"
        admin_user.app_metadata = {"role": "admin"}
        admin_user.user_metadata = {}
        mock_auth.get_user.return_value = MagicMock(user=admin_user)

        r_admin = client.get(
            "/protected/admin",
            headers={"Authorization": "Bearer admin_token"},
        )
        assert r_admin.status_code == 200
        assert r_admin.json()["role"] == "admin"


def test_refresh_token_endpoint():
    """Verify /auth/refresh exchanges refresh token for fresh access token."""
    r_bad = client.post("/auth/refresh", json={})
    assert r_bad.status_code == 400

    with patch("main.get_supabase_client") as mock_get_client:
        mock_session = MagicMock()
        mock_session.access_token = "new_refreshed_access_token"
        mock_session.refresh_token = "new_refresh_token"
        mock_session.expires_in = 3600

        mock_auth = MagicMock()
        mock_auth.refresh_session.return_value = MagicMock(session=mock_session)
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client

        r_ok = client.post("/auth/refresh", json={"refresh_token": "valid_refresh_token"})
        assert r_ok.status_code == 200
        data = r_ok.json()
        assert data["access_token"] == "new_refreshed_access_token"
        assert data["refresh_token"] == "new_refresh_token"


def test_login_rate_limiting_returns_429():
    """5 consecutive failed logins trigger 429 Too Many Requests."""
    with patch("main.get_supabase_client") as mock_get_client:
        mock_auth = MagicMock()
        mock_auth.sign_in_with_password.side_effect = AuthApiError(
            "Invalid login credentials", 400, None
        )
        mock_client = MagicMock()
        mock_client.auth = mock_auth
        mock_get_client.return_value = mock_client

        # Trigger 5 failed attempts
        for _ in range(5):
            r = client.post(
                "/auth/login",
                json={"email": "attacker@example.com", "password": "wrong"},
            )
            assert r.status_code == 401

        # 6th attempt should be blocked with 429 Too Many Requests
        r_locked = client.post(
            "/auth/login",
            json={"email": "attacker@example.com", "password": "wrong"},
        )
        assert r_locked.status_code == 429
        assert "Too many failed login attempts" in r_locked.json()["error"]


# =========================================================
# Stage 5: Swagger UI & OpenAPI Specification
# =========================================================


def test_swagger_openapi_schema_contains_http_bearer():
    """Verify OpenAPI specification has HTTPBearer scheme and locks protected routes."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    # Verify securitySchemes
    schemes = schema.get("components", {}).get("securitySchemes", {})
    assert "HTTPBearer" in schemes
    assert schemes["HTTPBearer"]["type"] == "http"
    assert schemes["HTTPBearer"]["scheme"] == "bearer"

    # Verify locked routes have security declared
    paths = schema.get("paths", {})
    assert "security" in paths.get("/protected/profile", {}).get("get", {})
    assert "security" in paths.get("/protected/dashboard", {}).get("get", {})
    assert "security" in paths.get("/protected/admin", {}).get("get", {})
    assert "security" in paths.get("/auth/logout", {}).get("post", {})
