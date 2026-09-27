"""Master analytical mart orchestrator for the DineIQ Spark Pipeline.

Loads cleaned Parquet snapshots into typed PySpark DataFrames, executes real
distributed Spark SQL and DataFrame analytical transformations, and materializes
all twelve analytical marts into data/marts/spark/ in Parquet format.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame, SparkSession

from packages.common.logging import get_logger
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

logger = get_logger(__name__)


class MartGenerationSummary:
    """Encapsulates execution statistics for all materialized analytical marts."""

    def __init__(self) -> None:
        self.mart_counts: dict[str, int] = {}
        self.durations: dict[str, float] = {}
        self.schemas: dict[str, list[str]] = {}
        self.total_duration_sec: float = 0.0
        self.status: str = "PENDING"


def _save_mart_spark(df: DataFrame, target_path: Path) -> int:
    """Save a PySpark DataFrame directly to Parquet storage with snappy compression."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.is_file():
        target_path.unlink()

    df.coalesce(1).write.mode("overwrite").format("parquet").option("compression", "snappy").save(
        str(target_path)
    )
    count = df.count()
    logger.info(
        "Materialized Spark mart to %s (%d rows, %d cols)",
        target_path.name,
        count,
        len(df.columns),
    )
    return count


def run_all_marts(
    snapshot_dir: str | Path = "data/cleaned/competition_benchmark_v1",
    output_dir: str | Path = "data/marts/spark",
    spark: SparkSession | None = None,
) -> MartGenerationSummary:
    """Execute end-to-end analytical mart generation using native Apache Spark."""
    start_total = time.time()
    summary = MartGenerationSummary()

    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    if spark is None:
        logger.info("Initializing active SparkSession for mart execution...")
        spark = get_spark_session()

    logger.info("Initializing CleanDataLoader for snapshot at %s", snapshot_dir)
    loader = CleanDataLoader(snapshot_dir=snapshot_dir, spark=spark)

    # Load cleaned tables directly as typed PySpark DataFrames with strict schema conformance
    logger.info("Ingesting all 11 cleaned domain tables into PySpark DataFrames...")
    tables: dict[str, Any] = loader.load_all_spark()

    # 1. mart_menu_performance
    t0 = time.time()
    logger.info("Running mart 1/12: mart_menu_performance via Spark SQL & Window functions...")
    df_menu = build_menu_performance_mart_spark(
        spark=spark,
        menu_items_df=tables["menu_items"],
        categories_df=tables["menu_categories"],
        order_items_df=tables["order_items"],
        orders_df=tables["orders"],
        ratings_df=tables["ratings"],
        wastage_df=tables["wastage"],
    )
    target_file = out_path / "mart_menu_performance.parquet"
    count = _save_mart_spark(df_menu, target_file)
    summary.mart_counts["mart_menu_performance"] = count
    summary.durations["mart_menu_performance"] = round(time.time() - t0, 2)
    summary.schemas["mart_menu_performance"] = df_menu.columns

    # 2. mart_customer_rfm
    t0 = time.time()
    logger.info("Running mart 2/12: mart_customer_rfm via Spark SQL & Quintile Windows...")
    df_rfm = build_customer_rfm_mart_spark(
        spark=spark,
        customers_df=tables["customers"],
        orders_df=tables["orders"],
    )
    target_file = out_path / "mart_customer_rfm.parquet"
    count = _save_mart_spark(df_rfm, target_file)
    summary.mart_counts["mart_customer_rfm"] = count
    summary.durations["mart_customer_rfm"] = round(time.time() - t0, 2)
    summary.schemas["mart_customer_rfm"] = df_rfm.columns

    # 3. mart_basket_analysis
    t0 = time.time()
    logger.info("Running mart 3/12: mart_basket_analysis via distributed Spark SQL self-joins...")
    df_basket = build_basket_analysis_mart_spark(
        spark=spark,
        order_items_df=tables["order_items"],
        menu_items_df=tables["menu_items"],
    )
    target_file = out_path / "mart_basket_analysis.parquet"
    count = _save_mart_spark(df_basket, target_file)
    summary.mart_counts["mart_basket_analysis"] = count
    summary.durations["mart_basket_analysis"] = round(time.time() - t0, 2)
    summary.schemas["mart_basket_analysis"] = df_basket.columns

    # 4. mart_peak_analysis
    t0 = time.time()
    logger.info("Running mart 4/12: mart_peak_analysis via Spark SQL & Window rank...")
    df_peak = build_peak_analysis_mart_spark(
        spark=spark,
        orders_df=tables["orders"],
        restaurants_df=tables["restaurants"],
    )
    target_file = out_path / "mart_peak_analysis.parquet"
    count = _save_mart_spark(df_peak, target_file)
    summary.mart_counts["mart_peak_analysis"] = count
    summary.durations["mart_peak_analysis"] = round(time.time() - t0, 2)
    summary.schemas["mart_peak_analysis"] = df_peak.columns

    # 5. mart_location_performance
    t0 = time.time()
    logger.info(
        "Running mart 5/12: mart_location_performance via Spark SQL multi-way aggregations..."
    )
    df_loc = build_location_performance_mart_spark(
        spark=spark,
        restaurants_df=tables["restaurants"],
        orders_df=tables["orders"],
        order_items_df=tables["order_items"],
        ratings_df=tables["ratings"],
        wastage_df=tables["wastage"],
    )
    target_file = out_path / "mart_location_performance.parquet"
    count = _save_mart_spark(df_loc, target_file)
    summary.mart_counts["mart_location_performance"] = count
    summary.durations["mart_location_performance"] = round(time.time() - t0, 2)
    summary.schemas["mart_location_performance"] = df_loc.columns

    # 6. mart_channel_performance
    t0 = time.time()
    logger.info("Running mart 6/12: mart_channel_performance via Spark SQL channel grouping...")
    df_chan = build_channel_performance_mart_spark(
        spark=spark,
        orders_df=tables["orders"],
        order_items_df=tables["order_items"],
    )
    target_file = out_path / "mart_channel_performance.parquet"
    count = _save_mart_spark(df_chan, target_file)
    summary.mart_counts["mart_channel_performance"] = count
    summary.durations["mart_channel_performance"] = round(time.time() - t0, 2)
    summary.schemas["mart_channel_performance"] = df_chan.columns

    # 7. mart_wastage
    t0 = time.time()
    logger.info("Running mart 7/12: mart_wastage via Spark SQL dual-path routing & Lead Window...")
    df_waste = build_wastage_mart_spark(
        spark=spark,
        wastage_df=tables["wastage"],
        order_items_df=tables["order_items"],
        orders_df=tables["orders"],
        menu_items_df=tables["menu_items"],
    )
    target_file = out_path / "mart_wastage.parquet"
    count = _save_mart_spark(df_waste, target_file)
    summary.mart_counts["mart_wastage"] = count
    summary.durations["mart_wastage"] = round(time.time() - t0, 2)
    summary.schemas["mart_wastage"] = df_waste.columns

    # 8. mart_pricing
    t0 = time.time()
    logger.info("Running mart 8/12: mart_pricing via Spark SQL 28-day pre/post intervals...")
    df_price = build_pricing_mart_spark(
        spark=spark,
        pricing_history_df=tables["pricing_history"],
        order_items_df=tables["order_items"],
        orders_df=tables["orders"],
        promotions_df=tables["promotions"],
        menu_items_df=tables["menu_items"],
    )
    target_file = out_path / "mart_pricing.parquet"
    count = _save_mart_spark(df_price, target_file)
    summary.mart_counts["mart_pricing"] = count
    summary.durations["mart_pricing"] = round(time.time() - t0, 2)
    summary.schemas["mart_pricing"] = df_price.columns

    # 9. mart_promotions
    t0 = time.time()
    logger.info("Running mart 9/12: mart_promotions via line-level Spark SQL linkage...")
    df_promo = build_promotions_mart_spark(
        spark=spark,
        promotions_df=tables["promotions"],
        order_items_df=tables["order_items"],
        orders_df=tables["orders"],
    )
    target_file = out_path / "mart_promotions.parquet"
    count = _save_mart_spark(df_promo, target_file)
    summary.mart_counts["mart_promotions"] = count
    summary.durations["mart_promotions"] = round(time.time() - t0, 2)
    summary.schemas["mart_promotions"] = df_promo.columns

    # 10. mart_ratings_anomalies
    t0 = time.time()
    logger.info("Running mart 10/12: mart_ratings_anomalies via Spark SQL & Z-Score Windows...")
    df_rat = build_ratings_anomalies_mart_spark(
        spark=spark,
        ratings_df=tables["ratings"],
        menu_items_df=tables["menu_items"],
        order_items_df=tables["order_items"],
        orders_df=tables["orders"],
    )
    target_file = out_path / "mart_ratings_anomalies.parquet"
    count = _save_mart_spark(df_rat, target_file)
    summary.mart_counts["mart_ratings_anomalies"] = count
    summary.durations["mart_ratings_anomalies"] = round(time.time() - t0, 2)
    summary.schemas["mart_ratings_anomalies"] = df_rat.columns

    # 11. mart_sales_anomalies
    t0 = time.time()
    logger.info(
        "Running mart 11/12: mart_sales_anomalies via Spark SQL & 14-day rolling Windows..."
    )
    df_sales = build_sales_anomalies_mart_spark(
        spark=spark,
        orders_df=tables["orders"],
        restaurants_df=tables["restaurants"],
    )
    target_file = out_path / "mart_sales_anomalies.parquet"
    count = _save_mart_spark(df_sales, target_file)
    summary.mart_counts["mart_sales_anomalies"] = count
    summary.durations["mart_sales_anomalies"] = round(time.time() - t0, 2)
    summary.schemas["mart_sales_anomalies"] = df_sales.columns

    # 12. mart_demand_historical
    t0 = time.time()
    logger.info(
        "Running mart 12/12: mart_demand_historical via Spark SQL & anti-leakage lag Windows..."
    )
    df_demand = build_demand_historical_mart_spark(
        spark=spark,
        order_items_df=tables["order_items"],
        orders_df=tables["orders"],
        menu_items_df=tables["menu_items"],
        categories_df=tables["menu_categories"],
    )
    target_file = out_path / "mart_demand_historical.parquet"
    count = _save_mart_spark(df_demand, target_file)
    summary.mart_counts["mart_demand_historical"] = count
    summary.durations["mart_demand_historical"] = round(time.time() - t0, 2)
    summary.schemas["mart_demand_historical"] = df_demand.columns

    summary.total_duration_sec = round(time.time() - start_total, 2)
    summary.status = "SUCCESS"
    logger.info(
        "Successfully materialized all 12 analytical marts into %s using native Spark in %.2fs",
        out_path,
        summary.total_duration_sec,
    )
    return summary


if __name__ == "__main__":
    summary = run_all_marts()
    print("--- MART EXECUTION SUMMARY ---")
    print(f"Total Duration: {summary.total_duration_sec}s")
    for mart_name, row_count in summary.mart_counts.items():
        print(f"  {mart_name}: {row_count} rows ({summary.durations.get(mart_name)}s)")
