"""Unit tests for Phase 7A analytics dashboard service ML artifact integration."""

from packages.core.services.analytics_dashboard_service import (
    _get_champion_algorithm,
    get_actionable_recommendations,
    get_customer_intelligence_summary,
    get_data_science_arena_summary,
    get_demand_and_pricing_summary,
    get_wastage_and_inventory_summary,
)


def test_champion_algorithm_discovery():
    """Verify dynamic discovery of champion algorithms from Phase 6B metadata."""
    assert _get_champion_algorithm("demand_forecast", "spark") == "GBTRegressor"
    assert _get_champion_algorithm("demand_forecast", "python") == "GradientBoostingRegressor"
    assert _get_champion_algorithm("wastage_risk", "spark") == "LogisticRegression"
    assert _get_champion_algorithm("wastage_risk", "python") == "GradientBoostingClassifier"
    assert _get_champion_algorithm("churn_risk", "spark") == "LogisticRegression"
    assert _get_champion_algorithm("churn_risk", "python") == "RandomForestClassifier"
    assert _get_champion_algorithm("customer_segmentation", "spark") == "BisectingKMeans"
    assert _get_champion_algorithm("customer_segmentation", "python") == "KMeans"


def test_wastage_ml_integration():
    """Verify wastage service exposes forward-looking ML risk alongside historical accounting."""
    res = get_wastage_and_inventory_summary()
    assert "reasons" in res
    assert "high_risk_items" in res
    assert "weekly_trend" in res
    assert "ml_risk_summary" in res
    assert "ml_predicted_risks" in res

    ml_summary = res["ml_risk_summary"]
    assert ml_summary["total_evaluated"] > 0
    assert ml_summary["predicted_high_risk_count"] > 0
    assert 0.0 <= ml_summary["avg_risk_probability"] <= 1.0
    assert ml_summary["spark_selected_algorithm"] == "LogisticRegression"
    assert ml_summary["python_selected_algorithm"] == "GradientBoostingClassifier"

    # ML predicted risks
    assert len(res["ml_predicted_risks"]) > 0
    top_pred = res["ml_predicted_risks"][0]
    assert "menu_item_id" in top_pred
    assert "item_name" in top_pred
    assert "risk_probability" in top_pred
    assert "predicted_risk_status" in top_pred
    assert top_pred["risk_probability"] >= 0.0


def test_customer_intelligence_ml_segmentation_integration():
    """Verify customer intelligence provides both rule-based RFM and ML clustering segments."""
    res = get_customer_intelligence_summary(limit=10)
    assert "customers" in res
    assert "segment_distribution" in res
    assert "ml_segment_distribution" in res
    assert res["spark_selected_algorithm"] == "BisectingKMeans"
    assert res["python_selected_algorithm"] == "KMeans"

    assert len(res["customers"]) > 0
    cust = res["customers"][0]
    # Distinct segmentation methods
    assert "rfm_segment" in cust
    assert cust["rfm_segment"] in ["Champions", "Loyal", "At Risk", "Lost"]
    assert "cluster_id" in cust
    assert "segment_label" in cust
    assert "ml_segment_label" in cust
    assert cust["cluster_id"] is not None
    assert cust["segment_label"] in ["Champions", "Loyal", "At Risk", "Lost"]

    # Verify distributions are separate
    assert len(res["segment_distribution"]) > 0
    assert len(res["ml_segment_distribution"]) > 0


def test_demand_dual_pipeline_view():
    """Verify demand forecasting provides independent Spark and Python prediction series."""
    res = get_demand_and_pricing_summary()
    assert "demand_forecast_curve" in res
    assert "spark_demand_forecast_curve" in res
    assert "python_demand_forecast_curve" in res
    assert res["spark_selected_algorithm"] == "GBTRegressor"
    assert res["python_selected_algorithm"] == "GradientBoostingRegressor"

    spark_curve = res["demand_forecast_curve"]
    python_curve = res["python_demand_forecast_curve"]
    assert len(spark_curve) > 0
    assert len(python_curve) > 0

    # Verify predictions are from separate pipelines and have expected keys
    assert "predicted_quantity" in spark_curve[0]
    assert "predicted_quantity" in python_curve[0]
    assert "week_start_date" in spark_curve[0]
    assert "week_start_date" in python_curve[0]


def test_data_science_arena_summary_dynamic_metadata():
    """Verify Data Science Arena exposes dynamic consensus and champion algorithms."""
    res = get_data_science_arena_summary(task="demand_forecast", limit=5)
    assert "arena_overview" in res
    overview = res["arena_overview"]
    assert overview["overall_agreement_pct"] == 63.48
    assert overview["demand_forecast"]["spark_selected_algorithm"] == "GBTRegressor"
    assert overview["demand_forecast"]["python_selected_algorithm"] == "GradientBoostingRegressor"
    assert overview["customer_segmentation"]["agreement_pct"] == 77.63
    assert overview["customer_segmentation"]["spark_selected_algorithm"] == "BisectingKMeans"
    assert overview["customer_segmentation"]["python_selected_algorithm"] == "KMeans"


def test_recommendations_dynamic_impact_calculation():
    """Verify actionable recommendations calculate impact dynamically from empirical metrics."""
    recs = get_actionable_recommendations()
    assert len(recs) > 0
    for rec in recs:
        assert "expected_impact" in rec
        impact = rec["expected_impact"]
        # Ensure impact is not a generic placeholder
        assert len(impact) > 5
        assert any(char.isdigit() for char in impact)


def test_wastage_optimization_filtering_and_equivalence():
    """Verify optimized wastage summary respects restaurant filters and handles non-existent locations."""
    # Global summary
    global_res = get_wastage_and_inventory_summary()
    assert len(global_res["reasons"]) > 0
    assert "high_risk_items" in global_res
    assert isinstance(global_res["high_risk_items"], list)
    assert len(global_res["weekly_trend"]) > 0
    assert global_res["ml_risk_summary"]["total_evaluated"] > 0

    # Filtered by location
    loc_res = get_wastage_and_inventory_summary(restaurant_id="REST-0001")
    assert "reasons" in loc_res
    assert "high_risk_items" in loc_res
    assert "weekly_trend" in loc_res
    assert loc_res["ml_risk_summary"]["total_evaluated"] > 0
    assert (
        loc_res["ml_risk_summary"]["total_evaluated"]
        <= global_res["ml_risk_summary"]["total_evaluated"]
    )

    # Filtered by non-existent location returns zero/empty results gracefully
    empty_res = get_wastage_and_inventory_summary(restaurant_id="NON_EXISTENT_LOCATION")
    assert empty_res["reasons"] == []
    assert empty_res["high_risk_items"] == []
    assert empty_res["weekly_trend"] == []
    assert empty_res["ml_risk_summary"]["total_evaluated"] == 0
    assert empty_res["ml_risk_summary"]["predicted_high_risk_count"] == 0
    assert empty_res["ml_predicted_risks"] == []


def test_customer_intelligence_pagination_and_filtering():
    """Verify optimized customer intelligence handles pagination, segmentation, search, and empty results."""
    # Page 1
    page1 = get_customer_intelligence_summary(limit=10, offset=0)
    assert len(page1["customers"]) == 10
    assert page1["total_count"] > 10
    ids_page1 = [c["customer_id"] for c in page1["customers"]]

    # Page 2
    page2 = get_customer_intelligence_summary(limit=10, offset=10)
    assert len(page2["customers"]) == 10
    ids_page2 = [c["customer_id"] for c in page2["customers"]]

    # No overlap between disjoint pages
    assert set(ids_page1).isdisjoint(set(ids_page2))

    # Segment filter
    seg_res = get_customer_intelligence_summary(segment="Champions", limit=15)
    assert len(seg_res["customers"]) > 0
    for c in seg_res["customers"]:
        assert c["rfm_segment"] == "Champions"

    # Search filter
    search_res = get_customer_intelligence_summary(search=ids_page1[0], limit=5)
    assert len(search_res["customers"]) == 1
    assert search_res["customers"][0]["customer_id"] == ids_page1[0]

    # Non-existent search returns empty list
    empty_search = get_customer_intelligence_summary(search="ZZZZ_NONEXISTENT_QUERY_9999")
    assert empty_search["total_count"] == 0
    assert empty_search["customers"] == []
    assert empty_search["segment_distribution"] == {}
