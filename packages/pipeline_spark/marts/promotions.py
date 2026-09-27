"""Spark mart generator for mart_promotions.parquet.

Evaluates line-level promotional redemption volume, discounts, net revenue,
contribution margins, and evidence-based promotion trap flags
at promotion + restaurant grain.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession

from packages.common.logging import get_logger

logger = get_logger(__name__)


def build_promotions_mart_spark(
    spark: SparkSession,
    promotions_df: DataFrame,
    order_items_df: DataFrame,
    orders_df: DataFrame,
) -> DataFrame:
    """Build Promotions Performance analytical mart using native PySpark."""
    logger.info("Executing Spark Promotions mart transformation")

    valid_orders = orders_df.filter(F.col("order_status") != "Voided")

    # 1. Line-level promotion linkage strictly at order_items grain
    promoted_items = order_items_df.filter(F.col("source_promotion_id").isNotNull())
    promoted_lines = promoted_items.join(
        valid_orders.select("source_order_id", "source_restaurant_id", "source_customer_id"),
        on="source_order_id",
        how="inner",
    )
    promoted_lines.createOrReplaceTempView("spark_temp_promoted_lines")

    # 2. Spark SQL: Compute redemptions, revenue, margin at promotion + restaurant grain
    promo_stats = spark.sql("""
        SELECT
            source_promotion_id,
            source_restaurant_id,
            COUNT(source_order_item_id) AS redemption_count,
            SUM(quantity) AS units_sold,
            COUNT(DISTINCT source_order_id) AS unique_orders,
            COUNT(DISTINCT source_customer_id) AS unique_customers,
            ROUND(SUM(line_discount), 2) AS total_discount,
            ROUND(SUM(line_net_revenue), 2) AS net_revenue,
            ROUND(SUM(line_contribution_margin), 2) AS contribution_margin,
            ROUND(SUM(line_contribution_margin) / GREATEST(1.0, SUM(line_net_revenue)), 4) AS margin_percentage,
            ROUND(SUM(line_discount) / GREATEST(1.0, SUM(quantity)), 2) AS avg_discount_per_item
        FROM spark_temp_promoted_lines
        GROUP BY source_promotion_id, source_restaurant_id
    """)

    # 3. Attach Promotion Metadata via broadcast join
    promos_meta = F.broadcast(promotions_df.select(
        "source_promotion_id",
        "campaign_name",
        "discount_type",
        "discount_value",
        "start_date",
        "end_date",
        "is_misleading",
    ))

    mart = promo_stats.join(promos_meta, on="source_promotion_id", how="inner")

    # 4. Evidence-based promotion trap:
    # Campaign volume was significant but contribution margin was negative or severely depressed (< 10%)
    # Or misleading promotion resulting in negative margin
    median_redemptions = 50.0  # benchmark threshold for active campaign
    mart = mart.withColumn(
        "is_promotion_trap",
        (
            (F.col("redemption_count") >= median_redemptions)
            & ((F.col("contribution_margin") <= 0) | (F.col("margin_percentage") < 0.10))
        ) | (F.col("is_misleading") & (F.col("contribution_margin") < 0)),
    )

    return mart
