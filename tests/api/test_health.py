"""Smoke tests for backend API health endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verify root endpoint responds with basic service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_health_liveness_endpoint(client: TestClient):
    """Verify health check liveness endpoint returns ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data


def test_health_readiness_endpoint(client: TestClient):
    """Verify health check readiness endpoint returns valid response structure."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "database" in data


def test_analytics_status_endpoint(client: TestClient):
    """Verify analytics status endpoint returns envelope structure."""
    response = client.get("/api/v1/analytics/status")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["marts_available"] is False
