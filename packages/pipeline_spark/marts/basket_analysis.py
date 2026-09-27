"""Spark mart generator for mart_basket_analysis.parquet.

Performs market basket association analysis across multi-item orders
using distributed Spark SQL self-joins to calculate item co-occurrence frequency,
support, confidence, and association lift.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession

from packages.common.logging import get_logger

logger = get_logger(__name__)


def build_basket_analysis_mart_spark(
    spark: SparkSession,
    order_items_df: DataFrame,
    menu_items_df: DataFrame,
    min_co_occurrence: int = 5,
) -> DataFrame:
    """Build market basket analysis mart using distributed Spark SQL."""
    logger.info("Executing Spark Basket Analysis mart transformation")

    # 1. Distinct items per order
    distinct_orders = order_items_df.select(
        "source_order_id", "source_menu_item_id"
    ).dropDuplicates()
    distinct_orders.createOrReplaceTempView("spark_temp_distinct_baskets")

    # 2. Multi-item orders filter
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW spark_temp_multi_item_baskets AS
        SELECT source_order_id
        FROM spark_temp_distinct_baskets
        GROUP BY source_order_id
        HAVING COUNT(source_menu_item_id) >= 2
    """)

    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW spark_temp_basket_items AS
        SELECT b.source_order_id, b.source_menu_item_id
        FROM spark_temp_distinct_baskets b
        INNER JOIN spark_temp_multi_item_baskets m ON b.source_order_id = m.source_order_id
    """)

    # 3. Item counts across multi-item orders
    spark.sql("""
        CREATE OR REPLACE TEMPORARY VIEW spark_temp_item_counts AS
        SELECT source_menu_item_id, COUNT(DISTINCT source_order_id) AS item_order_count
        FROM spark_temp_basket_items
        GROUP BY source_menu_item_id
    """)

    # 4. Total basket count
    total_baskets = spark.table("spark_temp_multi_item_baskets").count()
    if total_baskets == 0:
        total_baskets = 1

    # 5. Distributed Self-Join for pairs (a < b to prevent duplicate symmetric pairs)
    pair_stats = spark.sql(f"""
        SELECT
            a.source_menu_item_id AS item_a_id,
            b.source_menu_item_id AS item_b_id,
            COUNT(DISTINCT a.source_order_id) AS co_occurrence_count
        FROM spark_temp_basket_items a
        INNER JOIN spark_temp_basket_items b
            ON a.source_order_id = b.source_order_id
            AND a.source_menu_item_id < b.source_menu_item_id
        GROUP BY a.source_menu_item_id, b.source_menu_item_id
        HAVING COUNT(DISTINCT a.source_order_id) >= {min_co_occurrence}
    """)
    pair_stats.createOrReplaceTempView("spark_temp_pairs")

    # 6. Compute metrics via Spark SQL
    metrics_df = spark.sql(f"""
        SELECT
            p.item_a_id,
            p.item_b_id,
            p.co_occurrence_count,
            ROUND(ca.item_order_count / {float(total_baskets)}, 4) AS support_a,
            ROUND(cb.item_order_count / {float(total_baskets)}, 4) AS support_b,
            ROUND(p.co_occurrence_count / {float(total_baskets)}, 4) AS support_ab,
            ROUND(p.co_occurrence_count / ca.item_order_count, 4) AS confidence_a_to_b,
            ROUND(p.co_occurrence_count / cb.item_order_count, 4) AS confidence_b_to_a,
            ROUND((p.co_occurrence_count * {float(total_baskets)}) / (ca.item_order_count * cb.item_order_count), 4) AS lift
        FROM spark_temp_pairs p
        INNER JOIN spark_temp_item_counts ca ON p.item_a_id = ca.source_menu_item_id
        INNER JOIN spark_temp_item_counts cb ON p.item_b_id = cb.source_menu_item_id
    """)

    # 7. Attach item names
    menu_lookup = menu_items_df.select("source_menu_item_id", "item_name")
    final_df = (
        metrics_df.join(
            F.broadcast(menu_lookup.withColumnRenamed("item_name", "item_a_name")),
            metrics_df["item_a_id"] == menu_lookup["source_menu_item_id"],
            "left",
        )
        .drop("source_menu_item_id")
        .join(
            F.broadcast(menu_lookup.withColumnRenamed("item_name", "item_b_name")),
            metrics_df["item_b_id"] == menu_lookup["source_menu_item_id"],
            "left",
        )
        .drop("source_menu_item_id")
        .orderBy(F.desc("lift"))
    )

    return final_df
