"""Spark mart generator for mart_ratings_anomalies.parquet.

Detects customer satisfaction anomalies, sudden quality drops,
and items with low ratings despite high transaction volume
at item/restaurant + week grain.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Window

from packages.common.logging import get_logger

logger = get_logger(__name__)


def build_ratings_anomalies_mart_spark(
    spark: SparkSession,
    ratings_df: DataFrame,
    menu_items_df: DataFrame,
    order_items_df: DataFrame,
    orders_df: DataFrame,
) -> DataFrame:
    """Build Ratings and Customer Satisfaction Anomalies analytical mart using native PySpark."""
    logger.info("Executing Spark Ratings Anomalies mart transformation")

    # 1. Weekly sales volume per item + restaurant
    valid_orders = (
        orders_df.filter(F.col("order_status") != "Voided")
        .withColumn("calendar_year", F.year(F.col("order_timestamp")))
        .withColumn("calendar_week", F.weekofyear(F.col("order_timestamp")))
    )

    item_sales = order_items_df.join(
        valid_orders.select(
            "source_order_id", "source_restaurant_id", "calendar_year", "calendar_week"
        ),
        on="source_order_id",
        how="inner",
    )
    item_sales.createOrReplaceTempView("spark_temp_rating_item_sales")

    weekly_vol = spark.sql("""
        SELECT
            source_restaurant_id,
            source_menu_item_id,
            calendar_year,
            calendar_week,
            SUM(quantity) AS total_volume_sold
        FROM spark_temp_rating_item_sales
        GROUP BY source_restaurant_id, source_menu_item_id, calendar_year, calendar_week
    """)
    weekly_vol.createOrReplaceTempView("spark_temp_weekly_vol")

    # 2. Weekly dish ratings per item + restaurant + week
    dish_ratings = (
        ratings_df.filter(F.col("source_menu_item_id").isNotNull())
        .withColumn("calendar_year", F.year(F.col("rating_timestamp")))
        .withColumn("calendar_week", F.weekofyear(F.col("rating_timestamp")))
    )
    dish_ratings.createOrReplaceTempView("spark_temp_dish_ratings")

    weekly_ratings = spark.sql("""
        SELECT
            source_restaurant_id,
            source_menu_item_id,
            calendar_year,
            calendar_week,
            COUNT(rating_score) AS rating_count,
            ROUND(AVG(rating_score), 2) AS mean_rating,
            ROUND(COALESCE(STDDEV(rating_score), 0.0), 2) AS std_rating,
            MIN(rating_score) AS min_rating,
            MAX(rating_score) AS max_rating,
            SUM(CASE WHEN rating_score <= 2.0 THEN 1 ELSE 0 END) AS negative_ratings_count
        FROM spark_temp_dish_ratings
        GROUP BY source_restaurant_id, source_menu_item_id, calendar_year, calendar_week
    """)

    # 3. Join ratings with volume
    mart = weekly_ratings.join(
        weekly_vol,
        on=["source_restaurant_id", "source_menu_item_id", "calendar_year", "calendar_week"],
        how="left",
    )
    mart = mart.withColumn("total_volume_sold", F.coalesce(F.col("total_volume_sold"), F.lit(0)))

    # 4. Compute Z-score relative to item's historical baseline across weeks
    item_window = Window.partitionBy("source_menu_item_id")
    mart = (
        mart.withColumn("item_overall_mean", F.avg("mean_rating").over(item_window))
        .withColumn(
            "item_overall_std", F.coalesce(F.stddev("mean_rating").over(item_window), F.lit(0.5))
        )
        .withColumn(
            "z_score",
            F.round(
                (F.col("mean_rating") - F.col("item_overall_mean"))
                / F.when(F.col("item_overall_std") > 0, F.col("item_overall_std")).otherwise(1.0),
                2,
            ),
        )
        .withColumn(
            "negative_rating_rate",
            F.round(F.col("negative_ratings_count") / F.col("rating_count"), 4),
        )
    )

    # 5. Anomaly flags
    mart = mart.withColumn(
        "is_rating_anomaly",
        (F.col("z_score") < -1.5)
        | ((F.col("mean_rating") <= 3.0) & (F.col("total_volume_sold") >= 20))
        | (F.col("negative_rating_rate") > 0.30),
    ).withColumn(
        "anomaly_reason",
        F.when(F.col("z_score") < -1.5, "Statistically Low Rating")
        .when(
            (F.col("mean_rating") <= 3.0) & (F.col("total_volume_sold") >= 20),
            "High Volume Poor Quality",
        )
        .when(F.col("negative_rating_rate") > 0.30, "Excessive Negative Feedback")
        .otherwise("Normal"),
    )

    # Attach menu metadata via broadcast
    mart = mart.join(
        F.broadcast(
            menu_items_df.select(
                "source_menu_item_id", "item_name", "source_category_id", "current_base_price"
            )
        ),
        on="source_menu_item_id",
        how="left",
    ).drop("item_overall_mean", "item_overall_std")

    return mart
