"""Spark mart generator for mart_peak_analysis.parquet.

Analyzes hourly and day-of-week traffic distributions, rush-hour spikes,
and capacity utilization metrics across restaurant locations using PySpark and Spark SQL.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Window

from packages.common.logging import get_logger

logger = get_logger(__name__)


def build_peak_analysis_mart_spark(
    spark: SparkSession,
    orders_df: DataFrame,
    restaurants_df: DataFrame,
) -> DataFrame:
    """Build Peak Hour and Rush Analysis analytical mart using native PySpark."""
    logger.info("Executing Spark Peak Analysis mart transformation")

    valid_orders = (
        orders_df.filter(F.col("order_status") != "Voided")
        .withColumn("order_ts", F.to_timestamp(F.col("order_timestamp")))
        .withColumn("day_number", F.dayofweek(F.col("order_timestamp")))
        .withColumn("day_of_week", F.date_format(F.col("order_timestamp"), "EEEE"))
        .withColumn("hour_of_day", F.hour(F.col("order_timestamp")))
    )

    valid_orders.createOrReplaceTempView("spark_temp_peak_orders")

    agg_df = spark.sql("""
        SELECT
            source_restaurant_id,
            day_number,
            day_of_week,
            hour_of_day,
            COUNT(source_order_id) AS total_orders,
            ROUND(SUM(total_amount), 2) AS gross_revenue,
            ROUND(AVG(total_amount), 2) AS avg_order_value
        FROM spark_temp_peak_orders
        GROUP BY source_restaurant_id, day_number, day_of_week, hour_of_day
    """)

    # Rush period classification
    rush_expr = (
        F.when((F.col("hour_of_day") >= 7) & (F.col("hour_of_day") <= 10), "Breakfast Rush")
        .when((F.col("hour_of_day") >= 12) & (F.col("hour_of_day") <= 14), "Lunch Rush")
        .when((F.col("hour_of_day") >= 18) & (F.col("hour_of_day") <= 21), "Dinner Rush")
        .when((F.col("hour_of_day") >= 22) | (F.col("hour_of_day") <= 4), "Late Night")
        .otherwise("Off-Peak")
    )
    agg_df = agg_df.withColumn("rush_period", rush_expr)

    # Attach restaurant capacity via broadcast join
    rest_info = F.broadcast(
        restaurants_df.select(
            "source_restaurant_id",
            "location_name",
            "city",
            "dining_type",
            "seating_capacity",
        )
    )
    agg_df = agg_df.join(rest_info, on="source_restaurant_id", how="left")

    # Capacity utilization proxy
    agg_df = agg_df.withColumn(
        "capacity_utilization_pct",
        F.when(
            F.col("seating_capacity") > 0,
            F.round(F.col("total_orders") / F.col("seating_capacity"), 4),
        ).otherwise(0.0),
    )

    # Rank peak hours per restaurant
    rest_window = Window.partitionBy("source_restaurant_id").orderBy(F.desc("total_orders"))
    agg_df = agg_df.withColumn("restaurant_hour_rank", F.dense_rank().over(rest_window)).withColumn(
        "is_peak_hour", F.col("restaurant_hour_rank") <= 5
    )

    return agg_df
