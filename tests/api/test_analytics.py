"""Integration tests for Analytics API endpoints with real authentication and RBAC."""

from fastapi.testclient import TestClient


def test_analytics_status(client: TestClient, admin_headers: dict[str, str]):
    """Verify analytics status endpoint returns mart availability status for authenticated user."""
    response = client.get("/api/v1/analytics/status", headers=admin_headers)
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


def test_executive_summary_kpis(client: TestClient, admin_headers: dict[str, str]):
    """Verify executive summary returns non-empty aggregated metrics."""
    response = client.get("/api/v1/analytics/executive-summary", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total_revenue" in data
    assert "total_orders" in data
    assert "contribution_margin" in data
    assert "active_customers" in data
    assert data["total_revenue"] > 0


def test_filter_options(client: TestClient, admin_headers: dict[str, str]):
    """Verify filter options returns distinct dimension values."""
    response = client.get("/api/v1/analytics/filters", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "locations" in data
    assert "categories" in data
    assert "channels" in data
    assert len(data["locations"]) > 0


def test_menu_intelligence_endpoint(client: TestClient, admin_headers: dict[str, str]):
    """Verify menu intelligence endpoint returns items, scores, and flags."""
    response = client.get("/api/v1/analytics/menu?limit=10", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "items" in data
    assert "classification_counts" in data
    assert len(data["items"]) > 0
    item = data["items"][0]
    assert "menu_item_id" in item
    assert "classification" in item
    assert "flags" in item


def test_customer_intelligence_endpoint(client: TestClient, admin_headers: dict[str, str]):
    """Verify customer intelligence endpoint returns RFM segment distribution and ML clustering."""
    response = client.get("/api/v1/analytics/customers?limit=10", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "customers" in data
    assert "segment_distribution" in data
    assert "ml_segment_distribution" in data
    assert "spark_selected_algorithm" in data
    assert "python_selected_algorithm" in data
    assert len(data["customers"]) > 0

    c = data["customers"][0]
    assert "customer_id" in c
    assert "rfm_segment" in c
    assert "cluster_id" in c
    assert "segment_label" in c
    assert "ml_segment_label" in c


def test_sales_and_operations_endpoint(client: TestClient, admin_headers: dict[str, str]):
    """Verify sales and operations endpoint returns peak heatmap and channel share."""
    response = client.get("/api/v1/analytics/sales", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "peak_hourly_heatmap" in data
    assert "channel_breakdown" in data
    assert "locations" in data


def test_demand_pricing_endpoint(client: TestClient, admin_headers: dict[str, str]):
    """Verify demand forecast and price elasticity endpoint with dual-pipeline ML predictions."""
    response = client.get("/api/v1/analytics/demand", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "demand_forecast_curve" in data
    assert "spark_demand_forecast_curve" in data
    assert "python_demand_forecast_curve" in data
    assert "spark_selected_algorithm" in data
    assert "python_selected_algorithm" in data
    assert data["spark_selected_algorithm"] == "GBTRegressor"
    assert data["python_selected_algorithm"] == "GradientBoostingRegressor"
    assert len(data["demand_forecast_curve"]) > 0
    assert len(data["python_demand_forecast_curve"]) > 0
    assert "pricing_items" in data


def test_wastage_inventory_endpoint(client: TestClient, admin_headers: dict[str, str]):
    """Verify wastage causes, historical high-risk items, and forward-looking ML risk."""
    response = client.get("/api/v1/analytics/wastage", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "reasons" in data
    assert "high_risk_items" in data
    assert "weekly_trend" in data
    assert "ml_risk_summary" in data
    assert "ml_predicted_risks" in data
    assert data["ml_risk_summary"]["total_evaluated"] > 0
    assert data["ml_risk_summary"]["predicted_high_risk_count"] > 0
    assert data["ml_risk_summary"]["spark_selected_algorithm"] == "LogisticRegression"
    assert data["ml_risk_summary"]["python_selected_algorithm"] == "GradientBoostingClassifier"
    assert len(data["ml_predicted_risks"]) > 0
    item = data["ml_predicted_risks"][0]
    assert "menu_item_id" in item
    assert "risk_probability" in item
    assert "predicted_risk_status" in item


def test_promotions_and_basket_endpoint(client: TestClient, admin_headers: dict[str, str]):
    """Verify promotions and market basket association rules."""
    response = client.get("/api/v1/analytics/promotions", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "promotions" in data
    assert "market_basket_pairs" in data


def test_ratings_and_anomalies_endpoint(client: TestClient, admin_headers: dict[str, str]):
    """Verify ratings and sales anomalies stream."""
    response = client.get("/api/v1/analytics/anomalies", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "sales_anomalies" in data
    assert "rating_anomalies" in data


def test_comparison_arena_endpoint(client: TestClient, admin_headers: dict[str, str]):
    """Verify Data Science Arena returns summary agreement and sample records with dynamic metadata."""
    response = client.get(
        "/api/v1/analytics/comparison?task=demand_forecast&limit=5", headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "arena_overview" in data
    assert "comparison_samples" in data
    overview = data["arena_overview"]
    assert overview["overall_agreement_pct"] == 63.48
    assert overview["demand_forecast"]["spark_selected_algorithm"] == "GBTRegressor"
    assert overview["demand_forecast"]["python_selected_algorithm"] == "GradientBoostingRegressor"
    assert overview["customer_segmentation"]["agreement_pct"] == 77.63
    assert overview["customer_segmentation"]["spark_selected_algorithm"] == "BisectingKMeans"
    assert overview["customer_segmentation"]["python_selected_algorithm"] == "KMeans"


def test_recommendations_feed_endpoint(client: TestClient, admin_headers: dict[str, str]):
    """Verify evidence-based recommendations synthesis with dynamic data-driven impact."""
    response = client.get("/api/v1/analytics/recommendations", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) > 0
    rec = data[0]
    assert "observation" in rec
    assert "evidence" in rec
    assert "recommendation" in rec
    assert "priority" in rec
    assert "expected_impact" in rec


def test_what_if_scenario_calculation(client: TestClient, admin_headers: dict[str, str]):
    """Verify what-if scenario calculator computes empirical estimates."""
    payload = {
        "item_id": "DISH-0001",
        "price_change_pct": 10.0,
        "discount_change_pct": 0.0,
        "waste_reduction_pct": 15.0,
    }
    response = client.post("/api/v1/analytics/what-if", json=payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ESTIMATE"
    assert "baseline" in data
    assert "estimated_outcome" in data
    assert "volume_delta_pct" in data["estimated_outcome"]


def test_export_mart_csv(client: TestClient, admin_headers: dict[str, str]):
    """Verify CSV export functionality with Authorization header."""
    response = client.get(
        "/api/v1/analytics/export?mart_path=spark/mart_promotions.parquet&limit=10",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.text
    assert "campaign_name" in content


# =========================================================================
# Phase 7B Authentication & RBAC Granular Tests
# =========================================================================


def test_unauthenticated_requests_return_401(client: TestClient):
    """Verify all protected analytics endpoints return 401 Unauthorized when token is missing."""
    endpoints = [
        "/api/v1/analytics/status",
        "/api/v1/analytics/filters",
        "/api/v1/analytics/executive-summary",
        "/api/v1/analytics/menu",
        "/api/v1/analytics/customers",
        "/api/v1/analytics/sales",
        "/api/v1/analytics/demand",
        "/api/v1/analytics/wastage",
        "/api/v1/analytics/promotions",
        "/api/v1/analytics/anomalies",
        "/api/v1/analytics/comparison",
        "/api/v1/analytics/recommendations",
        "/api/v1/analytics/export?mart_path=spark/mart_promotions.parquet",
        "/api/v1/analytics/mart?mart_path=spark/mart_promotions.parquet",
    ]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 401, (
            f"Expected 401 for unauthenticated GET {ep}, got {resp.status_code}"
        )
        assert "WWW-Authenticate" in resp.headers

    # Also test POST endpoint
    what_if_resp = client.post("/api/v1/analytics/what-if", json={"item_id": "DISH-0001"})
    assert what_if_resp.status_code == 401


def test_invalid_token_returns_401(client: TestClient):
    """Verify invalid or corrupted token returns 401 Unauthorized."""
    bad_headers = {"Authorization": "Bearer totally.invalid.signature"}
    response = client.get("/api/v1/analytics/status", headers=bad_headers)
    assert response.status_code == 401
    assert "Authentication token is invalid or expired" in response.text


def test_cashier_rbac_allow_menu_and_status(client: TestClient, cashier_headers: dict[str, str]):
    """Verify Cashier role CAN access menu lookup, filters, and status for operational POS support."""
    status_resp = client.get("/api/v1/analytics/status", headers=cashier_headers)
    assert status_resp.status_code == 200

    filters_resp = client.get("/api/v1/analytics/filters", headers=cashier_headers)
    assert filters_resp.status_code == 200

    menu_resp = client.get("/api/v1/analytics/menu?limit=5", headers=cashier_headers)
    assert menu_resp.status_code == 200
    assert "items" in menu_resp.json()["data"]


def test_cashier_rbac_forbidden_from_restricted_analytics(
    client: TestClient, cashier_headers: dict[str, str]
):
    """Verify Cashier role is strictly blocked (403 Forbidden) from management and ML analytics."""
    restricted_endpoints = [
        "/api/v1/analytics/executive-summary",
        "/api/v1/analytics/customers",
        "/api/v1/analytics/sales",
        "/api/v1/analytics/demand",
        "/api/v1/analytics/wastage",
        "/api/v1/analytics/promotions",
        "/api/v1/analytics/anomalies",
        "/api/v1/analytics/comparison",
        "/api/v1/analytics/recommendations",
        "/api/v1/analytics/export?mart_path=spark/mart_promotions.parquet",
        "/api/v1/analytics/mart?mart_path=spark/mart_promotions.parquet",
    ]
    for ep in restricted_endpoints:
        resp = client.get(ep, headers=cashier_headers)
        assert resp.status_code == 403, f"Expected 403 for Cashier on {ep}, got {resp.status_code}"

    # Also check what-if POST
    what_if_resp = client.post(
        "/api/v1/analytics/what-if",
        json={"item_id": "DISH-0001"},
        headers=cashier_headers,
    )
    assert what_if_resp.status_code == 403


def test_store_manager_rbac_permissions(client: TestClient, manager_headers: dict[str, str]):
    """Verify StoreManager can access operational analytics and export, but NOT ML arena or raw marts."""
    allowed_endpoints = [
        "/api/v1/analytics/executive-summary",
        "/api/v1/analytics/menu?limit=5",
        "/api/v1/analytics/customers?limit=5",
        "/api/v1/analytics/sales",
        "/api/v1/analytics/demand",
        "/api/v1/analytics/wastage",
        "/api/v1/analytics/promotions",
        "/api/v1/analytics/anomalies",
        "/api/v1/analytics/recommendations",
    ]
    for ep in allowed_endpoints:
        resp = client.get(ep, headers=manager_headers)
        assert resp.status_code == 200, (
            f"Expected 200 for StoreManager on {ep}, got {resp.status_code}"
        )

    # What-If scenario is allowed for StoreManager
    what_if_resp = client.post(
        "/api/v1/analytics/what-if",
        json={"item_id": "DISH-0001", "price_change_pct": 5.0},
        headers=manager_headers,
    )
    assert what_if_resp.status_code == 200

    # Export is allowed for StoreManager
    export_resp = client.get(
        "/api/v1/analytics/export?mart_path=spark/mart_promotions.parquet&limit=5",
        headers=manager_headers,
    )
    assert export_resp.status_code == 200

    # ML Arena is forbidden for StoreManager (data scientists & admin only)
    arena_resp = client.get("/api/v1/analytics/comparison", headers=manager_headers)
    assert arena_resp.status_code == 403

    # Raw mart reading is forbidden for StoreManager (data scientists & admin only)
    mart_resp = client.get(
        "/api/v1/analytics/mart?mart_path=spark/mart_promotions.parquet",
        headers=manager_headers,
    )
    assert mart_resp.status_code == 403


def test_data_scientist_rbac_permissions(client: TestClient, scientist_headers: dict[str, str]):
    """Verify DataScientist role can access comparison arena, raw marts, and analytics."""
    arena_resp = client.get("/api/v1/analytics/comparison", headers=scientist_headers)
    assert arena_resp.status_code == 200
    assert "arena_overview" in arena_resp.json()["data"]

    mart_resp = client.get(
        "/api/v1/analytics/mart?mart_path=spark/mart_promotions.parquet&limit=5",
        headers=scientist_headers,
    )
    assert mart_resp.status_code == 200

    demand_resp = client.get("/api/v1/analytics/demand", headers=scientist_headers)
    assert demand_resp.status_code == 200


def test_export_mart_csv_token_query_param(
    client: TestClient, manager_headers: dict[str, str], cashier_headers: dict[str, str]
):
    """Verify CSV export supports ?token= query parameter for direct browser downloads."""
    # Extract token string from Bearer header
    manager_token = manager_headers["Authorization"].split(" ")[1]
    cashier_token = cashier_headers["Authorization"].split(" ")[1]

    # Authorized download via query param
    resp = client.get(
        f"/api/v1/analytics/export?mart_path=spark/mart_promotions.parquet&limit=5&token={manager_token}"
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")

    # Unauthorized role via query param
    forbidden_resp = client.get(
        f"/api/v1/analytics/export?mart_path=spark/mart_promotions.parquet&limit=5&token={cashier_token}"
    )
    assert forbidden_resp.status_code == 403
