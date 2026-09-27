"""Spark mart generator for mart_channel_performance.parquet.

Evaluates multi-channel distribution metrics across Dine-in, Takeaway,
Delivery Direct, and Delivery Aggregator touchpoints at restaurant + channel + month grain.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Window

from packages.common.logging import get_logger

logger = get_logger(__name__)


def build_channel_performance_mart_spark(
    spark: SparkSession,
    orders_df: DataFrame,
    order_items_df: DataFrame,
) -> DataFrame:
    """Build Dining Channel Performance analytical mart using native PySpark."""
    logger.info("Executing Spark Channel Performance mart transformation")

    valid_orders = orders_df.filter(F.col("order_status") != "Voided").withColumn(
        "order_month", F.trunc(F.col("order_timestamp"), "month")
    )
    valid_orders.createOrReplaceTempView("spark_temp_chan_orders")

    # 1. Order and Revenue Aggregations per restaurant + channel + month
    channel_orders = spark.sql("""
        SELECT
            source_restaurant_id,
            order_channel,
            order_channel AS channel,
            order_month,
            COUNT(source_order_id) AS total_orders,
            ROUND(SUM(subtotal_amount), 2) AS gross_amount,
            ROUND(SUM(discount_amount), 2) AS discount_amount,
            ROUND(SUM(total_amount), 2) AS net_revenue,
            ROUND(SUM(tip_amount), 2) AS tip_amount,
            ROUND(SUM(total_amount) / COUNT(source_order_id), 2) AS avg_order_value,
            ROUND(SUM(discount_amount) / GREATEST(1.0, SUM(subtotal_amount)), 4) AS discount_rate
        FROM spark_temp_chan_orders
        GROUP BY source_restaurant_id, order_channel, order_month
    """)

    # 2. Attach Line Contribution Margin
    items_with_channel = order_items_df.join(
        valid_orders.select(
            "source_order_id", "source_restaurant_id", "order_channel", "order_month"
        ),
        on="source_order_id",
        how="inner",
    )
    items_with_channel.createOrReplaceTempView("spark_temp_chan_items")

    channel_margin = spark.sql("""
        SELECT
            source_restaurant_id,
            order_channel,
            order_channel AS channel,
            order_month,
            ROUND(SUM(line_contribution_margin), 2) AS contribution_margin
        FROM spark_temp_chan_items
        GROUP BY source_restaurant_id, order_channel, order_month
    """)

    mart = channel_orders.join(
        channel_margin,
        on=["source_restaurant_id", "order_channel", "channel", "order_month"],
        how="left",
    )
    mart = mart.withColumn(
        "contribution_margin", F.coalesce(F.col("contribution_margin"), F.lit(0.0))
    ).withColumn(
        "margin_pct",
        F.when(
            F.col("net_revenue") > 0,
            F.round(F.col("contribution_margin") / F.col("net_revenue"), 4),
        ).otherwise(0.0),
    )

    # Share of restaurant volume per month
    rest_month_window = Window.partitionBy("source_restaurant_id", "order_month")
    mart = mart.withColumn(
        "order_share_pct",
        F.round(F.col("total_orders") / F.sum("total_orders").over(rest_month_window), 4),
    )

    return mart
