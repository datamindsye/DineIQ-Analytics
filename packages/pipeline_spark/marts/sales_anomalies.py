"""Spark mart generator for mart_sales_anomalies.parquet.

Detects statistical sales anomalies, revenue spikes, sudden demand drops,
and operational zero-sales exceptions across restaurant locations at
restaurant + day grain.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Window

from packages.common.logging import get_logger

logger = get_logger(__name__)


def build_sales_anomalies_mart_spark(
    spark: SparkSession,
    orders_df: DataFrame,
    restaurants_df: DataFrame,
) -> DataFrame:
    """Build Sales and Revenue Anomalies analytical mart using native PySpark and Spark SQL."""
    logger.info("Executing Spark Sales Anomalies mart transformation")

    # 1. Daily aggregation per restaurant
    valid_orders = orders_df.filter(F.col("order_status") != "Voided").withColumn(
        "order_date", F.to_date(F.col("order_timestamp"))
    )
    valid_orders.createOrReplaceTempView("spark_temp_sales_orders")

    daily_sales = spark.sql("""
        SELECT
            source_restaurant_id,
            order_date,
            COUNT(source_order_id) AS daily_orders,
            ROUND(SUM(total_amount), 2) AS daily_revenue
        FROM spark_temp_sales_orders
        GROUP BY source_restaurant_id, order_date
    """)

    # 2. 14-day rolling mean and standard deviation per restaurant strictly using prior days (<= t-1)
    rolling_window = (
        Window.partitionBy("source_restaurant_id")
        .orderBy("order_date")
        .rowsBetween(-14, -1)
    )

    daily_sales = (
        daily_sales.withColumn(
            "rolling_mean_revenue",
            F.round(F.avg("daily_revenue").over(rolling_window), 2),
        )
        .withColumn(
            "rolling_std_revenue",
            F.coalesce(
                F.round(F.stddev("daily_revenue").over(rolling_window), 2),
                F.lit(1.0),
            ),
        )
    )

    # 3. Compute Z-score (strictly 0.0 when no prior baseline history exists)
    effective_std = F.when(
        F.col("rolling_std_revenue") > 0, F.col("rolling_std_revenue")
    ).otherwise(F.lit(1.0))

    daily_sales = daily_sales.withColumn(
        "z_score_revenue",
        F.when(
            F.col("rolling_mean_revenue").isNotNull(),
            F.round(
                (F.col("daily_revenue") - F.col("rolling_mean_revenue")) / effective_std,
                2,
            ),
        ).otherwise(0.0),
    )

    # 4. Detect anomalies
    daily_sales = (
        daily_sales.withColumn(
            "is_spike_anomaly",
            F.col("rolling_mean_revenue").isNotNull() & (F.col("z_score_revenue") > 2.5),
        )
        .withColumn(
            "is_drop_anomaly",
            F.col("rolling_mean_revenue").isNotNull() & (F.col("z_score_revenue") < -2.5),
        )
        .withColumn("is_zero_sales", F.col("daily_orders") == 0)
        .withColumn(
            "anomaly_type",
            F.when(F.col("daily_orders") == 0, "Zero Sales Alert")
            .when(
                F.col("rolling_mean_revenue").isNotNull() & (F.col("z_score_revenue") > 2.5),
                "Revenue Spike",
            )
            .when(
                F.col("rolling_mean_revenue").isNotNull() & (F.col("z_score_revenue") < -2.5),
                "Revenue Drop",
            )
            .otherwise("Normal"),
        )
    )

    # 5. Merge restaurant info via broadcast
    mart = daily_sales.join(
        F.broadcast(
            restaurants_df.select(
                "source_restaurant_id", "location_name", "city", "dining_type"
            )
        ),
        on="source_restaurant_id",
        how="left",
    )

    return mart
