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


def test_executive_summary_kpis(client: TestClient):
    """Verify executive summary returns non-empty aggregated metrics."""
    response = client.get("/api/v1/analytics/executive-summary")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total_revenue" in data
    assert "total_orders" in data
    assert "contribution_margin" in data
    assert "active_customers" in data
    assert data["total_revenue"] > 0


def test_filter_options(client: TestClient):
    """Verify filter options returns distinct dimension values."""
    response = client.get("/api/v1/analytics/filters")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "locations" in data
    assert "categories" in data
    assert "channels" in data
    assert len(data["locations"]) > 0


def test_menu_intelligence_endpoint(client: TestClient):
    """Verify menu intelligence endpoint returns items, scores, and flags."""
    response = client.get("/api/v1/analytics/menu?limit=10")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "items" in data
    assert "classification_counts" in data
    assert len(data["items"]) > 0
    item = data["items"][0]
    assert "menu_item_id" in item
    assert "classification" in item
    assert "flags" in item


def test_customer_intelligence_endpoint(client: TestClient):
    """Verify customer intelligence endpoint returns RFM segment distribution."""
    response = client.get("/api/v1/analytics/customers?limit=10")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "customers" in data
    assert "segment_distribution" in data
    assert len(data["customers"]) > 0


def test_sales_and_operations_endpoint(client: TestClient):
    """Verify sales and operations endpoint returns peak heatmap and channel share."""
    response = client.get("/api/v1/analytics/sales")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "peak_hourly_heatmap" in data
    assert "channel_breakdown" in data
    assert "locations" in data


def test_demand_pricing_endpoint(client: TestClient):
    """Verify demand forecast and price elasticity endpoint."""
    response = client.get("/api/v1/analytics/demand")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "demand_forecast_curve" in data
    assert "pricing_items" in data


def test_wastage_inventory_endpoint(client: TestClient):
    """Verify wastage causes and high-risk items endpoint."""
    response = client.get("/api/v1/analytics/wastage")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "reasons" in data
    assert "high_risk_items" in data


def test_promotions_and_basket_endpoint(client: TestClient):
    """Verify promotions and market basket association rules."""
    response = client.get("/api/v1/analytics/promotions")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "promotions" in data
    assert "market_basket_pairs" in data


def test_ratings_and_anomalies_endpoint(client: TestClient):
    """Verify ratings and sales anomalies stream."""
    response = client.get("/api/v1/analytics/anomalies")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "sales_anomalies" in data
    assert "rating_anomalies" in data


def test_comparison_arena_endpoint(client: TestClient):
    """Verify Data Science Arena returns summary agreement and sample records."""
    response = client.get("/api/v1/analytics/comparison?task=demand_forecast&limit=5")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "arena_overview" in data
    assert "comparison_samples" in data
    assert data["arena_overview"]["overall_agreement_pct"] > 0


def test_recommendations_feed_endpoint(client: TestClient):
    """Verify evidence-based recommendations synthesis."""
    response = client.get("/api/v1/analytics/recommendations")
    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
    assert len(data) > 0
    rec = data[0]
    assert "observation" in rec
    assert "evidence" in rec
    assert "recommendation" in rec
    assert "priority" in rec


def test_what_if_scenario_calculation(client: TestClient):
    """Verify what-if scenario calculator computes empirical estimates."""
    payload = {
        "item_id": "DISH-0001",
        "price_change_pct": 10.0,
        "discount_change_pct": 0.0,
        "waste_reduction_pct": 15.0,
    }
    response = client.post("/api/v1/analytics/what-if", json=payload)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ESTIMATE"
    assert "baseline" in data
    assert "estimated_outcome" in data
    assert "volume_delta_pct" in data["estimated_outcome"]


def test_export_mart_csv(client: TestClient):
    """Verify CSV export functionality."""
    response = client.get(
        "/api/v1/analytics/export?mart_path=spark/mart_promotions.parquet&limit=10"
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.text
    assert "campaign_name" in content
