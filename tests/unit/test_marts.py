"""Tests for the twelve Spark analytical marts, component dimensions, and tricky case flags."""

import pytest
from pyspark.sql import DataFrame, SparkSession

from packages.core.contracts.analytical_contracts import MenuPerformanceCategory
from packages.pipeline_spark.loader import CleanDataLoader
from packages.pipeline_spark.marts.basket_analysis import build_basket_analysis_mart_spark
from packages.pipeline_spark.marts.channel_performance import build_channel_performance_mart_spark
from packages.pipeline_spark.marts.customer_rfm import build_customer_rfm_mart_spark
from packages.pipeline_spark.marts.demand_historical import build_demand_historical_mart_spark
from packages.pipeline_spark.marts.location_performance import build_location_performance_mart_spark
from packages.pipeline_spark.marts.menu_performance import build_menu_performance_mart_spark
from packages.pipeline_spark.marts.peak_analysis import build_peak_analysis_mart_spark
from packages.pipeline_spark.marts.pricing import build_pricing_mart_spark
from packages.pipeline_spark.marts.promotions import build_promotions_mart_spark
from packages.pipeline_spark.marts.ratings_anomalies import build_ratings_anomalies_mart_spark
from packages.pipeline_spark.marts.sales_anomalies import build_sales_anomalies_mart_spark
from packages.pipeline_spark.marts.wastage import build_wastage_mart_spark
from packages.pipeline_spark.session import get_spark_session


@pytest.fixture(scope="module")
def spark() -> SparkSession:
    """Provide module-level active SparkSession for analytical mart verification."""
    return get_spark_session()


@pytest.fixture(scope="module")
def spark_tables(spark: SparkSession) -> dict[str, DataFrame]:
    """Load cleaned domain tables into PySpark DataFrames for mart execution testing."""
    loader = CleanDataLoader(snapshot_dir="data/cleaned/competition_benchmark_v1", spark=spark)
    return loader.load_all_spark()


def test_mart_menu_performance(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify menu performance mart generates all 9 dimensions, scores, classifications, and 10 tricky flags."""
    df = build_menu_performance_mart_spark(
        spark=spark,
        menu_items_df=spark_tables["menu_items"],
        categories_df=spark_tables["menu_categories"],
        order_items_df=spark_tables["order_items"],
        orders_df=spark_tables["orders"],
        ratings_df=spark_tables["ratings"],
        wastage_df=spark_tables["wastage"],
    )

    # 9 dimensions
    assert "total_quantity" in df.columns
    assert "gross_revenue" in df.columns
    assert "contribution_margin" in df.columns
    assert "profitability_pct" in df.columns
    assert "avg_rating" in df.columns
    assert "repeat_purchase_rate" in df.columns
    assert "wastage_pct" in df.columns
    assert "promotion_dependency" in df.columns
    assert "sales_trend_ratio" in df.columns

    # 6 sub-scores + composite
    assert "demand_score" in df.columns
    assert "profitability_score" in df.columns
    assert "customer_signal_score" in df.columns
    assert "wastage_health_score" in df.columns
    assert "sales_trend_score" in df.columns
    assert "promotion_independence_score" in df.columns
    assert "composite_score" in df.columns

    # Classification
    assert "classification" in df.columns
    distinct_classes = [r.classification for r in df.select("classification").distinct().collect()]
    valid_classes = {c.value for c in MenuPerformanceCategory}
    assert set(distinct_classes).issubset(valid_classes)

    # 10 tricky-case flags
    assert "flag_high_selling_loss_making" in df.columns
    assert "flag_profitable_rarely_purchased" in df.columns
    assert "flag_popular_high_wastage" in df.columns
    assert "flag_high_rating_low_profitability" in df.columns
    assert "flag_low_rating_high_sales" in df.columns
    assert "flag_promotion_dependent" in df.columns
    assert "flag_location_divergence" in df.columns
    assert "flag_weekend_only_pattern" in df.columns
    assert "flag_seasonal_item" in df.columns
    assert "flag_new_item_insufficient_history" in df.columns
    assert df.count() > 0


def test_mart_customer_rfm(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify customer RFM mart calculates recency, frequency, monetary, and quintile segments."""
    df = build_customer_rfm_mart_spark(
        spark=spark,
        customers_df=spark_tables["customers"],
        orders_df=spark_tables["orders"],
    )
    assert "recency_days" in df.columns
    assert "frequency" in df.columns
    assert "monetary_value" in df.columns
    assert "avg_order_value" in df.columns
    assert "rfm_segment" in df.columns
    assert "r_score" in df.columns
    assert "f_score" in df.columns
    assert "m_score" in df.columns
    assert df.count() > 0


def test_mart_basket_analysis(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify basket analysis calculates co-occurrence, support, confidence, and lift."""
    df = build_basket_analysis_mart_spark(
        spark=spark,
        order_items_df=spark_tables["order_items"],
        menu_items_df=spark_tables["menu_items"],
        min_co_occurrence=1,
    )
    assert "item_a_id" in df.columns
    assert "item_b_id" in df.columns
    assert "co_occurrence_count" in df.columns
    assert "support_ab" in df.columns
    assert "confidence_a_to_b" in df.columns
    assert "lift" in df.columns
    assert df.count() > 0


def test_mart_peak_analysis(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify peak analysis analyzes hourly and day-of-week demand and rush periods."""
    df = build_peak_analysis_mart_spark(
        spark=spark,
        orders_df=spark_tables["orders"],
        restaurants_df=spark_tables["restaurants"],
    )
    assert "day_of_week" in df.columns
    assert "hour_of_day" in df.columns
    assert "total_orders" in df.columns
    assert "rush_period" in df.columns
    assert "is_peak_hour" in df.columns
    assert df.count() > 0


def test_mart_location_performance(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify location performance mart calculates margins, check sizes, and waste ratios."""
    df = build_location_performance_mart_spark(
        spark=spark,
        restaurants_df=spark_tables["restaurants"],
        orders_df=spark_tables["orders"],
        order_items_df=spark_tables["order_items"],
        ratings_df=spark_tables["ratings"],
        wastage_df=spark_tables["wastage"],
    )
    assert "total_orders" in df.columns
    assert "total_net_revenue" in df.columns
    assert "contribution_margin" in df.columns
    assert "dish_waste_cost" in df.columns
    assert "raw_ingredient_waste_cost" in df.columns
    assert "waste_to_revenue_ratio" in df.columns
    assert df.count() > 0


def test_mart_channel_performance(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify channel performance evaluates touchpoints and discount rates."""
    df = build_channel_performance_mart_spark(
        spark=spark,
        orders_df=spark_tables["orders"],
        order_items_df=spark_tables["order_items"],
    )
    assert "order_channel" in df.columns
    assert "total_orders" in df.columns
    assert "net_revenue" in df.columns
    assert "discount_rate" in df.columns
    assert "contribution_margin" in df.columns
    assert df.count() > 0


def test_mart_wastage(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify wastage mart calculates dual-path routing and next_week_wastage_risk."""
    df = build_wastage_mart_spark(
        spark=spark,
        wastage_df=spark_tables["wastage"],
        order_items_df=spark_tables["order_items"],
        orders_df=spark_tables["orders"],
        menu_items_df=spark_tables["menu_items"],
    )
    assert "waste_cost" in df.columns
    assert "waste_cost_ratio" in df.columns
    assert "waste_quantity_ratio" in df.columns
    assert "extreme_operational_risk" in df.columns
    assert "next_week_wastage_risk" in df.columns
    risks = [
        r.next_week_wastage_risk
        for r in df.select("next_week_wastage_risk").distinct().collect()
        if r.next_week_wastage_risk is not None
    ]
    assert set(risks).issubset({0, 1})
    assert df.count() > 0


def test_mart_pricing(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify pricing mart computes 28-day windows, price elasticity, and promo overlap."""
    df = build_pricing_mart_spark(
        spark=spark,
        pricing_history_df=spark_tables["pricing_history"],
        order_items_df=spark_tables["order_items"],
        orders_df=spark_tables["orders"],
        promotions_df=spark_tables["promotions"],
        menu_items_df=spark_tables["menu_items"],
    )
    assert "source_pricing_history_id" in df.columns
    assert "pre_quantity" in df.columns
    assert "post_quantity" in df.columns
    assert "elasticity" in df.columns
    assert "sensitivity_class" in df.columns
    assert "promotion_overlap" in df.columns
    assert df.count() > 0


def test_mart_promotions(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify promotions mart links at line level and flags promotion traps."""
    df = build_promotions_mart_spark(
        spark=spark,
        promotions_df=spark_tables["promotions"],
        order_items_df=spark_tables["order_items"],
        orders_df=spark_tables["orders"],
    )
    assert "source_promotion_id" in df.columns
    assert "redemption_count" in df.columns
    assert "total_discount" in df.columns
    assert "contribution_margin" in df.columns
    assert "is_promotion_trap" in df.columns
    assert df.count() > 0


def test_mart_ratings_anomalies(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify ratings anomalies mart calculates mean, std, z-score, and anomaly flags."""
    df = build_ratings_anomalies_mart_spark(
        spark=spark,
        ratings_df=spark_tables["ratings"],
        menu_items_df=spark_tables["menu_items"],
        order_items_df=spark_tables["order_items"],
        orders_df=spark_tables["orders"],
    )
    assert "mean_rating" in df.columns
    assert "z_score" in df.columns
    assert "is_rating_anomaly" in df.columns
    assert "anomaly_reason" in df.columns
    assert df.count() > 0


def test_mart_sales_anomalies(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify sales anomalies mart detects spikes and drops."""
    df = build_sales_anomalies_mart_spark(
        spark=spark,
        orders_df=spark_tables["orders"],
        restaurants_df=spark_tables["restaurants"],
    )
    assert "daily_revenue" in df.columns
    assert "z_score_revenue" in df.columns
    assert "is_spike_anomaly" in df.columns
    assert "is_drop_anomaly" in df.columns
    assert "anomaly_type" in df.columns
    assert df.count() > 0


def test_sales_anomalies_rolling_baseline_excludes_current_day(spark: SparkSession):
    """Verify rolling baseline uses strictly prior days (t-14..t-1) and excludes day t."""
    from datetime import date

    # Construct 11 consecutive days: 10 baseline days at 100.0, and day 11 with 1000.0 spike
    orders_data = [
        (
            f"ORD_{i:02d}",
            "R_TEST",
            f"2025-01-{i:02d} 12:00:00",
            "Completed",
            100.0 if i < 11 else 1000.0,
        )
        for i in range(1, 12)
    ]
    orders_df = spark.createDataFrame(
        orders_data,
        [
            "source_order_id",
            "source_restaurant_id",
            "order_timestamp",
            "order_status",
            "total_amount",
        ],
    )
    restaurants_df = spark.createDataFrame(
        [("R_TEST", "Test Location", "Riyadh", "Dine-In")],
        ["source_restaurant_id", "location_name", "city", "dining_type"],
    )

    mart_df = build_sales_anomalies_mart_spark(spark, orders_df, restaurants_df)
    results = {r.order_date: r for r in mart_df.collect()}

    day_1 = results[date(2025, 1, 1)]
    day_11 = results[date(2025, 1, 11)]

    # 1. Day 1 has insufficient prior history: current day MUST NOT contribute to its own baseline
    assert day_1.rolling_mean_revenue is None, (
        "Day 1 rolling mean must be None (zero prior observations)"
    )
    assert day_1.z_score_revenue == 0.0
    assert day_1.anomaly_type == "Normal"

    # 2. Day 11 baseline MUST strictly reflect prior 10 days (100.0), NOT contaminated by current day (1000.0)
    # Under old rowsBetween(-13, 0), rolling_mean_revenue would be 181.82 ((10*100 + 1000) / 11)
    # Under correct rowsBetween(-14, -1), rolling_mean_revenue is strictly 100.0
    assert day_11.rolling_mean_revenue == 100.0, (
        f"Day 11 rolling mean ({day_11.rolling_mean_revenue}) contaminated by current day; expected 100.0"
    )
    assert day_11.is_spike_anomaly is True
    assert day_11.anomaly_type == "Revenue Spike"


def test_mart_demand_historical(spark: SparkSession, spark_tables: dict[str, DataFrame]):
    """Verify demand historical mart produces leakage-safe seasonal-naive baseline."""
    df = build_demand_historical_mart_spark(
        spark=spark,
        order_items_df=spark_tables["order_items"],
        orders_df=spark_tables["orders"],
        menu_items_df=spark_tables["menu_items"],
        categories_df=spark_tables["menu_categories"],
    )
    assert "historical_demand" in df.columns
    assert "seasonal_naive_baseline" in df.columns
    assert "baseline_absolute_error" in df.columns
    assert "split_window" in df.columns
    splits = [r.split_window for r in df.select("split_window").distinct().collect()]
    assert set(splits).issubset({"TRAIN", "VALIDATION", "TEST", "UNSEEN_COMPARISON"})
    assert df.count() > 0
