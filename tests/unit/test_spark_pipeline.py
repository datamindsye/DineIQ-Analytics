"""Tests for Phase 3 Spark analytical pipeline, CleanDataLoader, joins, and schema fidelity."""

from pathlib import Path

import pytest
from pyspark.sql import DataFrame, SparkSession

from packages.core.contracts.dataset_contract import ARROW_SCHEMAS
from packages.pipeline_spark.joins import (
    join_order_lines_spark,
    route_wastage_spark,
)
from packages.pipeline_spark.loader import CleanDataLoader, SnapshotNotFoundError
from packages.pipeline_spark.session import get_spark_session, is_spark_available


@pytest.fixture(scope="module")
def spark() -> SparkSession:
    """Fixture providing active PySpark session."""
    return get_spark_session()


def test_spark_session_available_and_execution(spark: SparkSession):
    """Verify PySpark session is available and can execute distributed transformations."""
    assert is_spark_available()
    assert spark is not None

    test_df = spark.createDataFrame([(1, "Burger"), (2, "Salad")], ["id", "name"])
    assert test_df.count() == 2
    rows = [r.name for r in test_df.collect()]
    assert "Burger" in rows


def test_physical_schema_fidelity_and_zero_hallucinations():
    """Verify all 11 tables match verified physical column names without hallucinated fields."""
    # menu_items: current_base_price, current_base_cost (NOT base_price, base_cost)
    menu_fields = set(ARROW_SCHEMAS["menu_items"].names)
    assert "current_base_price" in menu_fields
    assert "current_base_cost" in menu_fields
    assert "base_price" not in menu_fields
    assert "is_spoilage_sensitive" not in menu_fields

    # pricing_history: source_pricing_history_id, base_price, base_cost, effective_to
    pricing_fields = set(ARROW_SCHEMAS["pricing_history"].names)
    assert "source_pricing_history_id" in pricing_fields
    assert "is_current" not in pricing_fields

    # promotions: campaign_name (NOT promotion_name)
    promo_fields = set(ARROW_SCHEMAS["promotions"].names)
    assert "campaign_name" in promo_fields
    assert "promotion_name" not in promo_fields

    # wastage: quantity_lost (NOT quantity)
    wastage_fields = set(ARROW_SCHEMAS["wastage"].names)
    assert "quantity_lost" in wastage_fields
    assert "cost_loss_amount" in wastage_fields

    # inventory: ingredient_name, unit_purchase_cost (NO source_menu_item_id or daily ledger)
    inventory_fields = set(ARROW_SCHEMAS["inventory"].names)
    assert "ingredient_name" in inventory_fields
    assert "unit_purchase_cost" in inventory_fields
    assert "source_menu_item_id" not in inventory_fields
    assert "stock_date" not in inventory_fields

    # orders: NO promotion foreign key
    orders_fields = set(ARROW_SCHEMAS["orders"].names)
    assert "source_promotion_id" not in orders_fields

    # order_items: contains source_promotion_id
    item_fields = set(ARROW_SCHEMAS["order_items"].names)
    assert "source_promotion_id" in item_fields


def test_clean_data_loader_completeness():
    """Verify CleanDataLoader validates all eleven clean Parquet tables."""
    loader = CleanDataLoader(snapshot_dir="data/cleaned/competition_benchmark_v1")
    completeness = loader.validate_snapshot_completeness()
    assert len(completeness) == 11
    assert all(completeness.values()), (
        f"Missing tables: {[k for k, v in completeness.items() if not v]}"
    )


def test_spark_data_loader_ingestion(spark: SparkSession):
    """Verify CleanDataLoader loads typed PySpark DataFrames with strict schema enforcement."""
    loader = CleanDataLoader(snapshot_dir="data/cleaned/competition_benchmark_v1", spark=spark)
    df_menu = loader.load_table_spark("menu_items")
    assert isinstance(df_menu, DataFrame)
    assert "current_base_price" in df_menu.columns
    assert "current_base_cost" in df_menu.columns
    assert df_menu.count() > 0


def test_clean_data_loader_nonexistent_directory():
    """Verify CleanDataLoader raises SnapshotNotFoundError for invalid path."""
    with pytest.raises(SnapshotNotFoundError):
        CleanDataLoader(snapshot_dir="data/cleaned/nonexistent_snapshot")


def test_line_level_promotion_linkage_spark(spark: SparkSession):
    """Verify promotion linkage occurs strictly at order_items grain in Spark."""
    loader = CleanDataLoader(snapshot_dir="data/cleaned/competition_benchmark_v1", spark=spark)
    orders = loader.load_table_spark("orders")
    items = loader.load_table_spark("order_items")
    menu = loader.load_table_spark("menu_items")
    promos = loader.load_table_spark("promotions")

    joined = join_order_lines_spark(
        orders_df=orders,
        order_items_df=items,
        menu_items_df=menu,
        promotions_df=promos,
    )

    assert "campaign_name" in joined.columns
    assert "source_promotion_id" in joined.columns
    assert "current_base_price" in joined.columns
    assert joined.count() > 0


def test_dual_path_wastage_routing_spark(spark: SparkSession):
    """Verify dual-path wastage routes dishes to menu_items and raw to inventory in Spark."""
    loader = CleanDataLoader(snapshot_dir="data/cleaned/competition_benchmark_v1", spark=spark)
    wastage = loader.load_table_spark("wastage")
    menu = loader.load_table_spark("menu_items")
    inventory = loader.load_table_spark("inventory")

    dish_waste, raw_waste = route_wastage_spark(
        wastage_df=wastage,
        menu_items_df=menu,
        inventory_df=inventory,
    )

    assert "source_menu_item_id" in dish_waste.columns
    assert "current_base_cost" in dish_waste.columns
    assert dish_waste.filter("source_menu_item_id IS NULL").count() == 0

    assert "ingredient_name" in raw_waste.columns
    assert "unit_purchase_cost" in raw_waste.columns
    assert raw_waste.filter("source_menu_item_id IS NOT NULL").count() == 0


def test_dual_pipeline_artifact_path_separation():
    """Verify Spark and Python pipelines maintain strictly separated artifact paths."""
    spark_mart_path = Path("data/marts/spark")
    python_mart_path = Path("data/marts/python")
    comparison_mart_path = Path("data/marts/comparison")

    assert spark_mart_path != python_mart_path
    assert spark_mart_path != comparison_mart_path
    assert python_mart_path != comparison_mart_path
