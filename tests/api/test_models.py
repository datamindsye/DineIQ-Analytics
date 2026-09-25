"""Integration tests for Model Registry API endpoints."""

from fastapi.testclient import TestClient


def test_register_and_list_models(client: TestClient, scientist_headers: dict[str, str]):
    """Verify DataScientist can register a trained model and query the registry."""
    payload = {
        "model_id": "sklearn_linear_elasticity_v1",
        "pipeline_type": "PYTHON_SKLEARN",
        "algorithm_name": "RidgeRegression",
        "target_name": "price_elasticity_coefficient",
        "training_snapshot_id": "v20260924_01",
        "hyperparameters": {"alpha": 1.0},
        "metrics": {"r2_score": 0.81, "mae": 0.12},
        "artifact_path": "data/artifacts/python/ridge_v1.pkl",
        "is_active": True,
    }
    create_resp = client.post("/api/v1/models", json=payload, headers=scientist_headers)
    assert create_resp.status_code == 201
    model_data = create_resp.json()["data"]
    assert model_data["model_id"] == "sklearn_linear_elasticity_v1"

    # List models
    list_resp = client.get("/api/v1/models", headers=scientist_headers)
    assert list_resp.status_code == 200
    assert any(m["model_id"] == "sklearn_linear_elasticity_v1" for m in list_resp.json()["data"])


def test_get_model_details(client: TestClient, scientist_headers: dict[str, str]):
    """Verify fetching details of a specific registered model."""
    fetch_resp = client.get(
        "/api/v1/models/sklearn_linear_elasticity_v1",
        headers=scientist_headers,
    )
    assert fetch_resp.status_code == 200
    data = fetch_resp.json()["data"]
    assert data["algorithm_name"] == "RidgeRegression"
    assert data["metrics"]["r2_score"] == 0.81


def test_record_and_get_batch_predictions(client: TestClient, scientist_headers: dict[str, str]):
    """Verify recording and querying prediction metadata for a model."""
    # Get model ID
    model_resp = client.get(
        "/api/v1/models/sklearn_linear_elasticity_v1",
        headers=scientist_headers,
    )
    model_db_id = model_resp.json()["data"]["id"]

    pred_payload = {
        "prediction_id": "pred_test_elasticity_001",
        "model_version_id": model_db_id,
        "pipeline_type": "PYTHON_SKLEARN",
        "target_name": "price_elasticity_coefficient",
        "input_snapshot_id": "v20260924_01",
        "output_mart_path": "data/marts/python/elasticity_scored.parquet",
        "row_count": 150,
    }
    record_resp = client.post(
        "/api/v1/models/sklearn_linear_elasticity_v1/predictions",
        json=pred_payload,
        headers=scientist_headers,
    )
    assert record_resp.status_code == 201

    # Query predictions
    query_resp = client.get(
        "/api/v1/models/sklearn_linear_elasticity_v1/predictions",
        headers=scientist_headers,
    )
    assert query_resp.status_code == 200
    assert len(query_resp.json()["data"]) >= 1
