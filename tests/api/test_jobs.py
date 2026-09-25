"""Integration tests for background jobs API endpoints."""

from fastapi.testclient import TestClient


def test_list_jobs(client: TestClient, admin_headers: dict[str, str]):
    """Verify listing jobs returns successful response envelope."""
    response = client.get("/api/v1/jobs", headers=admin_headers)
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"], list)


def test_trigger_pipeline_job_as_data_scientist(
    client: TestClient, scientist_headers: dict[str, str]
):
    """Verify DataScientist role can trigger an asynchronous pipeline job."""
    payload = {
        "pipeline_type": "SPARK",
        "job_type": "MENU_ENGINEERING_BATCH",
        "source_snapshot_id": "v20260924_100000",
        "parameters": {"min_support": 0.05},
    }
    response = client.post("/api/v1/jobs/trigger", json=payload, headers=scientist_headers)
    assert response.status_code == 202
    job = response.json()["data"]
    assert job["pipeline_type"] == "SPARK"
    assert job["job_type"] == "MENU_ENGINEERING_BATCH"
    assert job["status"] in ("PENDING", "RUNNING", "SUCCESS")


def test_trigger_pipeline_job_forbidden_for_cashier(
    client: TestClient, cashier_headers: dict[str, str]
):
    """Verify Cashier role cannot trigger heavy pipeline processing."""
    payload = {
        "pipeline_type": "PYTHON",
        "job_type": "WASTAGE_PREDICTION",
    }
    response = client.post("/api/v1/jobs/trigger", json=payload, headers=cashier_headers)
    assert response.status_code == 403


def test_get_job_by_id(client: TestClient, admin_headers: dict[str, str]):
    """Verify retrieving specific job by ID."""
    # First trigger a job
    trigger_resp = client.post(
        "/api/v1/jobs/trigger",
        json={"pipeline_type": "PYTHON", "job_type": "TEST_FETCH"},
        headers=admin_headers,
    )
    job_id = trigger_resp.json()["data"]["job_id"]

    # Now fetch it
    fetch_resp = client.get(f"/api/v1/jobs/{job_id}", headers=admin_headers)
    assert fetch_resp.status_code == 200
    assert fetch_resp.json()["data"]["job_id"] == job_id


def test_get_nonexistent_job_returns_404(client: TestClient, admin_headers: dict[str, str]):
    """Verify querying an unknown job ID returns 404 Not Found."""
    response = client.get("/api/v1/jobs/job_unknown_xyz", headers=admin_headers)
    assert response.status_code == 404
