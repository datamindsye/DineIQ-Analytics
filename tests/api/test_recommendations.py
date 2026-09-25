"""Integration tests for business recommendations API endpoints."""

from fastapi.testclient import TestClient


def test_create_and_list_recommendations(client: TestClient, admin_headers: dict[str, str]):
    """Verify creating an actionable recommendation and listing recommendations."""
    payload = {
        "recommendation_id": "rec_wastage_salad_01",
        "category": "WASTAGE_REDUCTION",
        "title": "Reduce daily prep of Caesar Salad by 20%",
        "description": "Consistent evening spoilage observed across Downtown branch",
        "impact_estimate": "Estimated 850 USD weekly savings",
        "priority": "HIGH",
        "status": "PROPOSED",
        "source_pipeline": "SPARK",
        "metadata_payload": {"item": "Caesar Salad", "suggested_portions": 40},
    }
    create_resp = client.post("/api/v1/recommendations", json=payload, headers=admin_headers)
    assert create_resp.status_code == 201
    rec_data = create_resp.json()["data"]
    assert rec_data["recommendation_id"] == "rec_wastage_salad_01"

    # List recommendations
    list_resp = client.get("/api/v1/recommendations", headers=admin_headers)
    assert list_resp.status_code == 200
    assert any(r["recommendation_id"] == "rec_wastage_salad_01" for r in list_resp.json()["data"])


def test_update_recommendation_status_by_store_manager(
    client: TestClient, manager_headers: dict[str, str]
):
    """Verify StoreManager can accept or reject proposed recommendations."""
    update_payload = {"status": "ACCEPTED"}
    patch_resp = client.patch(
        "/api/v1/recommendations/rec_wastage_salad_01/status",
        json=update_payload,
        headers=manager_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["status"] == "ACCEPTED"


def test_update_recommendation_status_forbidden_for_cashier(
    client: TestClient, cashier_headers: dict[str, str]
):
    """Verify Cashier role cannot mutate recommendation states."""
    update_payload = {"status": "REJECTED"}
    patch_resp = client.patch(
        "/api/v1/recommendations/rec_wastage_salad_01/status",
        json=update_payload,
        headers=cashier_headers,
    )
    assert patch_resp.status_code == 403
