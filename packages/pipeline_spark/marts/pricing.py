"""Spark mart generator for mart_pricing.parquet.

Computes price elasticity, price sensitivity classifications, and promotion overlap
around historical price change events using 28-day pre/post observation windows
at item/restaurant + price-change event grain.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession

from packages.common.logging import get_logger
from packages.core.contracts.analytical_contracts import (
    PriceElasticityContract,
    PriceSensitivityClass,
)

logger = get_logger(__name__)


def build_pricing_mart_spark(
    spark: SparkSession,
    pricing_history_df: DataFrame,
    order_items_df: DataFrame,
    orders_df: DataFrame,
    promotions_df: DataFrame,
    menu_items_df: DataFrame,
) -> DataFrame:
    """Build Pricing Analytics and Elasticity analytical mart using native PySpark."""
    logger.info("Executing Spark Pricing mart transformation")

    # 1. Clean dates and prepare events
    pricing = (
        pricing_history_df.withColumn("eff_date", F.to_date(F.col("effective_from")))
        .withColumn(
            "pre_start", F.date_sub(F.col("eff_date"), PriceElasticityContract.PRE_WINDOW_DAYS)
        )
        .withColumn("pre_end", F.date_sub(F.col("eff_date"), 1))
        .withColumn("post_start", F.col("eff_date"))
        .withColumn(
            "post_end", F.date_add(F.col("eff_date"), PriceElasticityContract.POST_WINDOW_DAYS - 1)
        )
    )
    pricing.createOrReplaceTempView("spark_temp_pricing_events")

    # 2. Daily item sales
    valid_orders = orders_df.filter(F.col("order_status") != "Voided").withColumn(
        "order_date", F.to_date(F.col("order_timestamp"))
    )

    item_sales = order_items_df.join(
        valid_orders.select("source_order_id", "source_restaurant_id", "order_date"),
        on="source_order_id",
        how="inner",
    )
    item_sales.createOrReplaceTempView("spark_temp_item_sales")

    # 3. Promotions view
    promos = promotions_df.withColumn("promo_start", F.to_date(F.col("start_date"))).withColumn(
        "promo_end", F.to_date(F.col("end_date"))
    )
    promos.createOrReplaceTempView("spark_temp_promos")

    # 4. Spark SQL: Join pricing events with sales in pre and post windows
    pricing_metrics = spark.sql("""
        SELECT
            p.source_pricing_history_id,
            p.source_menu_item_id,
            p.source_restaurant_id,
            p.base_price,
            p.eff_date AS effective_from,
            p.pre_start AS pre_window_start,
            p.post_end AS post_window_end,

            -- Pre-window aggregations
            COALESCE(SUM(CASE WHEN s.order_date BETWEEN p.pre_start AND p.pre_end THEN s.quantity ELSE 0 END), 0) AS pre_quantity,
            COALESCE(ROUND(AVG(CASE WHEN s.order_date BETWEEN p.pre_start AND p.pre_end THEN s.unit_price_at_sale END), 2), ROUND(p.base_price * 0.95, 2)) AS pre_price,

            -- Post-window aggregations
            COALESCE(SUM(CASE WHEN s.order_date BETWEEN p.post_start AND p.post_end THEN s.quantity ELSE 0 END), 0) AS post_quantity,
            COALESCE(ROUND(AVG(CASE WHEN s.order_date BETWEEN p.post_start AND p.post_end THEN s.unit_price_at_sale END), 2), p.base_price) AS post_price,

            -- Promotion overlap detection
            MAX(CASE WHEN s.order_date BETWEEN p.pre_start AND p.post_end AND s.source_promotion_id IS NOT NULL THEN 1 ELSE 0 END) AS has_promo_overlap

        FROM spark_temp_pricing_events p
        LEFT JOIN spark_temp_item_sales s
            ON p.source_menu_item_id = s.source_menu_item_id
            AND (p.source_restaurant_id IS NULL OR p.source_restaurant_id = s.source_restaurant_id)
            AND s.order_date BETWEEN p.pre_start AND p.post_end
        GROUP BY
            p.source_pricing_history_id,
            p.source_menu_item_id,
            p.source_restaurant_id,
            p.base_price,
            p.eff_date,
            p.pre_start,
            p.post_end
    """)

    # 5. Compute elasticity and sensitivity class
    # elasticity = (post_qty - pre_qty) / pre_qty / ((post_price - pre_price) / pre_price)
    pricing_metrics = pricing_metrics.withColumn(
        "promotion_overlap", F.col("has_promo_overlap") == 1
    ).drop("has_promo_overlap")

    price_diff_pct = (F.col("post_price") - F.col("pre_price")) / F.col("pre_price")
    qty_diff_pct = (F.col("post_quantity") - F.col("pre_quantity")) / F.col("pre_quantity")

    valid_elasticity = (
        (F.col("pre_quantity") > 0) & (F.col("pre_price") > 0) & (F.abs(price_diff_pct) > 1e-6)
    )

    pricing_metrics = pricing_metrics.withColumn(
        "elasticity",
        F.when(valid_elasticity, F.round(qty_diff_pct / price_diff_pct, 4)).otherwise(None),
    )

    # Sensitivity classification
    high_t = PriceElasticityContract.THRESHOLD_HIGH_SENSITIVITY
    mod_t = PriceElasticityContract.THRESHOLD_MODERATE_SENSITIVITY

    sens_expr = (
        F.when(F.col("elasticity").isNull(), PriceSensitivityClass.LOW.value)
        .when(F.abs(F.col("elasticity")) >= high_t, PriceSensitivityClass.HIGH.value)
        .when(F.abs(F.col("elasticity")) >= mod_t, PriceSensitivityClass.MODERATE.value)
        .otherwise(PriceSensitivityClass.LOW.value)
    )
    pricing_metrics = pricing_metrics.withColumn("sensitivity_class", sens_expr)

    # Attach menu item name via broadcast join
    pricing_metrics = pricing_metrics.join(
        F.broadcast(menu_items_df.select("source_menu_item_id", "item_name")),
        on="source_menu_item_id",
        how="left",
    )

    return pricing_metrics
