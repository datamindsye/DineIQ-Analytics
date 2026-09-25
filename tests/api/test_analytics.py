"""Integration tests for Analytics API endpoints."""

from fastapi.testclient import TestClient


def test_analytics_status(client: TestClient):
    """Verify analytics status endpoint returns mart availability status."""
    response = client.get("/api/v1/analytics/status")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "marts_available" in data
    assert "spark_pipeline_marts" in data
    assert "python_pipeline_marts" in data


def test_query_mart_missing_file_returns_404(client: TestClient, admin_headers: dict[str, str]):
    """Verify querying an uncomputed mart returns 404 Not Found."""
    response = client.get(
        "/api/v1/analytics/mart?mart_path=spark/nonexistent.parquet",
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_query_mart_directory_traversal_blocked(client: TestClient, admin_headers: dict[str, str]):
    """Verify security protection blocks path traversal attempts."""
    response = client.get(
        "/api/v1/analytics/mart?mart_path=../../etc/passwd",
        headers=admin_headers,
    )
    assert response.status_code == 400
