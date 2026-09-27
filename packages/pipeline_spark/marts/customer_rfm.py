"""Spark mart generator for mart_customer_rfm.parquet.

Computes customer Recency, Frequency, Monetary (RFM) distributions,
quintile scores via Spark Window ntile, and behavioral customer segments.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Window

from packages.common.logging import get_logger

logger = get_logger(__name__)


def build_customer_rfm_mart_spark(
    spark: SparkSession,
    customers_df: DataFrame,
    orders_df: DataFrame,
) -> DataFrame:
    """Build Customer RFM analytical mart using native PySpark and Spark SQL."""
    logger.info("Executing Spark Customer RFM mart transformation")

    valid_orders = orders_df.filter(F.col("order_status") != "Voided").withColumn(
        "order_date", F.to_date(F.col("order_timestamp"))
    )
    valid_orders.createOrReplaceTempView("spark_temp_rfm_orders")

    # 1. Spark SQL: Compute recency, frequency, monetary aggregations per customer
    rfm_base = spark.sql("""
        WITH max_date_cte AS (
            SELECT MAX(order_date) AS ref_date FROM spark_temp_rfm_orders
        )
        SELECT
            o.source_customer_id,
            MAX(o.order_date) AS last_order_date,
            MIN(o.order_date) AS first_order_date,
            COUNT(DISTINCT o.source_order_id) AS frequency,
            ROUND(SUM(o.total_amount), 2) AS monetary_value,
            DATEDIFF((SELECT ref_date FROM max_date_cte), MAX(o.order_date)) AS recency_days,
            DATEDIFF((SELECT ref_date FROM max_date_cte), MIN(o.order_date)) AS customer_tenure_days,
            ROUND(SUM(o.total_amount) / COUNT(DISTINCT o.source_order_id), 2) AS avg_order_value
        FROM spark_temp_rfm_orders o
        GROUP BY o.source_customer_id
    """)

    # 2. Window quintile scoring (1-5)
    # Recency: lower days = higher score (5)
    r_window = Window.orderBy(F.desc("recency_days"))
    f_window = Window.orderBy("frequency")
    m_window = Window.orderBy("monetary_value")

    scored_rfm = (
        rfm_base.withColumn("r_score", F.ntile(5).over(r_window))
        .withColumn("f_score", F.ntile(5).over(f_window))
        .withColumn("m_score", F.ntile(5).over(m_window))
    )

    # 3. Behavioral RFM segmentation
    segment_expr = (
        F.when((F.col("r_score") >= 4) & (F.col("f_score") >= 4), "Champions")
        .when((F.col("r_score") >= 3) & (F.col("f_score") >= 3), "Loyal Customers")
        .when((F.col("r_score") >= 4) & (F.col("f_score") <= 2), "New & Promising")
        .when((F.col("r_score") <= 2) & (F.col("f_score") >= 3), "At Risk")
        .when((F.col("r_score") <= 2) & (F.col("f_score") <= 2), "Hibernating")
        .otherwise("Need Attention")
    )
    segmented_rfm = scored_rfm.withColumn("rfm_segment", segment_expr)

    # 4. Join customer metadata
    cust_full = customers_df.withColumn(
        "customer_name", F.concat_ws(" ", F.col("first_name"), F.col("last_name"))
    )

    final_df = cust_full.select(
        "source_customer_id",
        "customer_name",
        "loyalty_tier",
        "preferred_channel",
        "home_city",
    ).join(segmented_rfm, on="source_customer_id", how="left")

    final_df = (
        final_df.withColumn("frequency", F.coalesce(F.col("frequency"), F.lit(0)))
        .withColumn("monetary_value", F.coalesce(F.col("monetary_value"), F.lit(0.0)))
        .withColumn("recency_days", F.coalesce(F.col("recency_days"), F.lit(999)))
        .withColumn("rfm_segment", F.coalesce(F.col("rfm_segment"), F.lit("Inactive")))
        .withColumn("r_score", F.coalesce(F.col("r_score"), F.lit(1)))
        .withColumn("f_score", F.coalesce(F.col("f_score"), F.lit(1)))
        .withColumn("m_score", F.coalesce(F.col("m_score"), F.lit(1)))
    )

    return final_df
