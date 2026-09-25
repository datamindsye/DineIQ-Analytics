"""Integration tests for Authentication API endpoints."""

from fastapi.testclient import TestClient

from packages.core.config.settings import get_settings

settings = get_settings()


def test_login_success(client: TestClient):
    """Verify login with valid credentials returns JWT access token."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "password": settings.DEFAULT_ADMIN_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == settings.DEFAULT_ADMIN_USERNAME


def test_login_invalid_password(client: TestClient):
    """Verify login with incorrect password returns 401 Unauthorized."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.DEFAULT_ADMIN_USERNAME,
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401
    assert "error" in response.json()


def test_login_nonexistent_user(client: TestClient):
    """Verify login with unknown username returns 401 Unauthorized."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent_ghost",
            "password": "SomePassword123!",
        },
    )
    assert response.status_code == 401


def test_get_current_user_profile(client: TestClient, admin_headers: dict[str, str]):
    """Verify /auth/me returns authenticated user details when token is valid."""
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    user_data = response.json()["data"]
    assert user_data["username"] == settings.DEFAULT_ADMIN_USERNAME
    assert any(role["name"] == "Admin" for role in user_data["roles"])


def test_get_current_user_unauthorized(client: TestClient):
    """Verify /auth/me without token returns 401 Unauthorized."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_register_user_by_admin(client: TestClient, admin_headers: dict[str, str]):
    """Verify an administrator can register a new user."""
    payload = {
        "username": "new_chef",
        "email": "chef@dineiq.local",
        "password": "ChefPassword2026!",
        "full_name": "Executive Chef",
        "roles": ["StoreManager"],
    }
    response = client.post("/api/v1/auth/register", json=payload, headers=admin_headers)
    assert response.status_code == 201
    created = response.json()["data"]
    assert created["username"] == "new_chef"
    assert created["email"] == "chef@dineiq.local"


def test_register_user_forbidden_for_non_admin(client: TestClient, cashier_headers: dict[str, str]):
    """Verify non-admin roles cannot register new users."""
    payload = {
        "username": "forbidden_user",
        "email": "forbidden@dineiq.local",
        "password": "SomePassword123!",
        "roles": ["Cashier"],
    }
    response = client.post("/api/v1/auth/register", json=payload, headers=cashier_headers)
    assert response.status_code == 403
