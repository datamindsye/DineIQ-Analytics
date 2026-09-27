"""Spark mart generator for mart_location_performance.parquet.

Evaluates comparative restaurant location performance across sales volume,
profit margins, average check sizes, customer satisfaction, and waste ratios
at restaurant + month grain.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Window

from packages.common.logging import get_logger

logger = get_logger(__name__)


def build_location_performance_mart_spark(
    spark: SparkSession,
    restaurants_df: DataFrame,
    orders_df: DataFrame,
    order_items_df: DataFrame,
    ratings_df: DataFrame,
    wastage_df: DataFrame,
) -> DataFrame:
    """Build Restaurant Location Performance analytical mart using native PySpark."""
    logger.info("Executing Spark Location Performance mart transformation")

    valid_orders = orders_df.filter(F.col("order_status") != "Voided").withColumn(
        "order_month", F.trunc(F.col("order_timestamp"), "month")
    )
    valid_orders.createOrReplaceTempView("spark_temp_loc_orders")

    # 1. Orders and Revenue aggregations
    order_stats = spark.sql("""
        SELECT
            source_restaurant_id,
            order_month,
            COUNT(DISTINCT source_order_id) AS total_orders,
            COUNT(DISTINCT source_customer_id) AS unique_customers,
            ROUND(SUM(subtotal_amount), 2) AS gross_revenue,
            ROUND(SUM(discount_amount), 2) AS total_discount,
            ROUND(SUM(total_amount), 2) AS total_net_revenue,
            ROUND(SUM(tip_amount), 2) AS total_tips,
            ROUND(SUM(total_amount) / COUNT(DISTINCT source_order_id), 2) AS avg_order_value
        FROM spark_temp_loc_orders
        GROUP BY source_restaurant_id, order_month
    """)
    order_stats.createOrReplaceTempView("spark_temp_loc_order_stats")

    # 2. Margin aggregations from order_items
    items_with_month = order_items_df.join(
        valid_orders.select("source_order_id", "source_restaurant_id", "order_month"),
        on="source_order_id",
        how="inner",
    )
    items_with_month.createOrReplaceTempView("spark_temp_loc_items")

    item_stats = spark.sql("""
        SELECT
            source_restaurant_id,
            order_month,
            SUM(quantity) AS total_items_sold,
            ROUND(SUM(line_contribution_margin), 2) AS contribution_margin
        FROM spark_temp_loc_items
        GROUP BY source_restaurant_id, order_month
    """)

    loc_mart = order_stats.join(item_stats, on=["source_restaurant_id", "order_month"], how="left")
    loc_mart = loc_mart.withColumn(
        "margin_percentage",
        F.when(
            F.col("total_net_revenue") > 0,
            F.round(F.col("contribution_margin") / F.col("total_net_revenue"), 4),
        ).otherwise(0.0),
    )

    # 3. Customer Satisfaction / Ratings
    ratings_with_month = ratings_df.withColumn(
        "order_month", F.trunc(F.col("rating_timestamp"), "month")
    )
    rating_stats = ratings_with_month.groupBy("source_restaurant_id", "order_month").agg(
        F.count("rating_score").alias("total_ratings"),
        F.round(F.avg("rating_score"), 2).alias("avg_rating"),
    )
    loc_mart = loc_mart.join(rating_stats, on=["source_restaurant_id", "order_month"], how="left")
    loc_mart = loc_mart.withColumn(
        "total_ratings", F.coalesce(F.col("total_ratings"), F.lit(0))
    ).withColumn("avg_rating", F.coalesce(F.col("avg_rating"), F.lit(4.0)))

    # 4. Wastage Costs (Dual path: dish + raw)
    wastage_with_month = wastage_df.withColumn(
        "order_month", F.trunc(F.col("wastage_timestamp"), "month")
    )
    dish_waste = (
        wastage_with_month.filter(F.col("source_menu_item_id").isNotNull())
        .groupBy("source_restaurant_id", "order_month")
        .agg(F.round(F.sum("cost_loss_amount"), 2).alias("dish_waste_cost"))
    )
    raw_waste = (
        wastage_with_month.filter(F.col("source_menu_item_id").isNull())
        .groupBy("source_restaurant_id", "order_month")
        .agg(F.round(F.sum("cost_loss_amount"), 2).alias("raw_ingredient_waste_cost"))
    )
    loc_mart = loc_mart.join(dish_waste, on=["source_restaurant_id", "order_month"], how="left")
    loc_mart = loc_mart.join(raw_waste, on=["source_restaurant_id", "order_month"], how="left")
    loc_mart = loc_mart.withColumn(
        "dish_waste_cost", F.coalesce(F.col("dish_waste_cost"), F.lit(0.0))
    ).withColumn(
        "raw_ingredient_waste_cost", F.coalesce(F.col("raw_ingredient_waste_cost"), F.lit(0.0))
    )
    loc_mart = loc_mart.withColumn(
        "total_waste_cost",
        F.round(F.col("dish_waste_cost") + F.col("raw_ingredient_waste_cost"), 2),
    ).withColumn(
        "waste_to_revenue_ratio",
        F.when(
            F.col("total_net_revenue") > 0,
            F.round(F.col("total_waste_cost") / F.col("total_net_revenue"), 4),
        ).otherwise(0.0),
    )

    # 5. Attach Restaurant Metadata via broadcast
    rest_meta = F.broadcast(
        restaurants_df.select(
            "source_restaurant_id",
            "location_name",
            "city",
            "state_region",
            "dining_type",
            "seating_capacity",
            "opening_date",
        )
    )
    loc_mart = loc_mart.join(rest_meta, on="source_restaurant_id", how="left")

    # Rankings per month
    month_rev_window = Window.partitionBy("order_month").orderBy(F.desc("total_net_revenue"))
    month_margin_window = Window.partitionBy("order_month").orderBy(F.desc("contribution_margin"))
    loc_mart = loc_mart.withColumn(
        "revenue_rank", F.dense_rank().over(month_rev_window)
    ).withColumn("margin_rank", F.dense_rank().over(month_margin_window))

    return loc_mart
