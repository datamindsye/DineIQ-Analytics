"""Integration tests for Audit API endpoints."""

from fastapi.testclient import TestClient


def test_get_audit_events_as_admin(client: TestClient, admin_headers: dict[str, str]):
    """Verify administrator can inspect the audit event trail."""
    response = client.get("/api/v1/audit", headers=admin_headers)
    assert response.status_code == 200
    events = response.json()["data"]
    assert isinstance(events, list)


def test_get_audit_events_forbidden_for_non_admin(
    client: TestClient, manager_headers: dict[str, str]
):
    """Verify non-admin roles (StoreManager) cannot access audit logs."""
    response = client.get("/api/v1/audit", headers=manager_headers)
    assert response.status_code == 403
