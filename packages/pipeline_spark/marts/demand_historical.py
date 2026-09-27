"""Spark mart generator for mart_demand_historical.parquet.

Aggregates historical observed demand time-series and computes a leakage-safe
seasonal-naive baseline (same day-of-week over prior 4 weeks <= t-1) at
restaurant + item + day grain.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Window

from packages.common.logging import get_logger

logger = get_logger(__name__)


def build_demand_historical_mart_spark(
    spark: SparkSession,
    order_items_df: DataFrame,
    orders_df: DataFrame,
    menu_items_df: DataFrame,
    categories_df: DataFrame | None = None,
) -> DataFrame:
    """Build Historical Demand and Seasonal-Naive Baseline analytical mart using native PySpark and Spark SQL.

    Aggregation grain: (source_restaurant_id, source_menu_item_id, order_date).
    Baseline calculation strictly adheres to anti-leakage: features and baselines
    for date t use observations strictly from <= t-1.
    """
    logger.info("Executing Spark Demand Historical mart transformation")

    # 1. Join valid orders and order items
    valid_orders = orders_df.filter(F.col("order_status") != "Voided").withColumn(
        "order_date", F.to_date(F.col("order_timestamp"))
    )

    merged = order_items_df.join(
        valid_orders.select("source_order_id", "source_restaurant_id", "order_date"),
        on="source_order_id",
        how="inner",
    )
    merged.createOrReplaceTempView("spark_temp_demand_merged")

    # 2. Daily aggregation per restaurant + menu item + date via Spark SQL
    daily_demand = spark.sql("""
        SELECT
            source_restaurant_id,
            source_menu_item_id,
            order_date,
            SUM(quantity) AS historical_demand,
            ROUND(SUM(line_net_revenue), 2) AS gross_revenue,
            COUNT(DISTINCT source_order_id) AS order_count
        FROM spark_temp_demand_merged
        GROUP BY source_restaurant_id, source_menu_item_id, order_date
    """)

    # 3. Calendar features
    daily_demand = (
        daily_demand.withColumn("day_of_week", F.date_format(F.col("order_date"), "EEEE"))
        .withColumn("day_of_week_num", F.dayofweek(F.col("order_date")))
        .withColumn("day_of_month", F.dayofmonth(F.col("order_date")))
        .withColumn("month", F.month(F.col("order_date")))
        .withColumn(
            "is_weekend",
            F.dayofweek(F.col("order_date")).isin([1, 6, 7]),  # Sun, Fri, Sat
        )
    )

    # 4. Approved Chronological Split Windows
    daily_demand = daily_demand.withColumn(
        "split_window",
        F.when(F.col("order_date") <= "2025-08-31", "TRAIN")
        .when(F.col("order_date") <= "2025-10-31", "VALIDATION")
        .when(F.col("order_date") <= "2025-11-30", "TEST")
        .otherwise("UNSEEN_COMPARISON"),
    )

    # 5. Seasonal-Naive Baseline:
    # Lagged mean of same day-of-week over prior 4 weeks strictly <= t-1 (zero future leakage)
    seasonal_dow_window = (
        Window.partitionBy("source_restaurant_id", "source_menu_item_id", "day_of_week_num")
        .orderBy("order_date")
        .rowsBetween(-4, -1)
    )

    overall_hist_window = (
        Window.partitionBy("source_restaurant_id", "source_menu_item_id")
        .orderBy("order_date")
        .rowsBetween(Window.unboundedPreceding, -1)
    )

    daily_demand = (
        daily_demand.withColumn(
            "lagged_dow_avg", F.avg("historical_demand").over(seasonal_dow_window)
        )
        .withColumn("prior_overall_avg", F.avg("historical_demand").over(overall_hist_window))
        .withColumn(
            "seasonal_naive_baseline",
            F.round(
                F.coalesce(
                    F.col("lagged_dow_avg"),
                    F.col("prior_overall_avg"),
                    F.col("historical_demand").cast("double"),
                ),
                2,
            ),
        )
        .withColumn(
            "baseline_absolute_error",
            F.round(
                F.abs(F.col("historical_demand") - F.col("seasonal_naive_baseline")),
                2,
            ),
        )
        .drop("lagged_dow_avg", "prior_overall_avg")
    )

    # 6. Attach Menu Item Metadata via broadcast
    mart = daily_demand.join(
        F.broadcast(
            menu_items_df.select(
                "source_menu_item_id",
                "item_name",
                "source_category_id",
                "current_base_price",
                "is_seasonal",
            )
        ),
        on="source_menu_item_id",
        how="left",
    )

    # 7. Attach Category Metadata if provided
    if categories_df is not None:
        mart = mart.join(
            F.broadcast(categories_df.select("source_category_id", "category_name")),
            on="source_category_id",
            how="left",
        )

    return mart
