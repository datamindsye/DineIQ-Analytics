"""Spark mart generator for mart_wastage.parquet.

Implements dual-path wastage routing, exact weekly waste ratios,
and the approved next_week_wastage_risk ML target classification
at restaurant + item/ingredient + prepared/raw + week grain.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Window

from packages.common.logging import get_logger
from packages.core.contracts.analytical_contracts import (
    WastageRiskClass,
    WastageRiskContract,
)

logger = get_logger(__name__)


def build_wastage_mart_spark(
    spark: SparkSession,
    wastage_df: DataFrame,
    order_items_df: DataFrame,
    orders_df: DataFrame,
    menu_items_df: DataFrame,
) -> DataFrame:
    """Build Wastage Analytics and ML Target analytical mart using native PySpark."""
    logger.info("Executing Spark Wastage mart transformation")

    # 1. Prepared dish wastage path
    dish_waste = wastage_df.filter(F.col("source_menu_item_id").isNotNull()).withColumn(
        "calendar_year", F.year(F.col("wastage_timestamp"))
    ).withColumn(
        "calendar_week", F.weekofyear(F.col("wastage_timestamp"))
    )
    dish_waste.createOrReplaceTempView("spark_temp_dish_waste")

    dish_weekly_waste = spark.sql("""
        SELECT
            source_restaurant_id,
            source_menu_item_id,
            'PREPARED_DISH' AS item_type,
            NULL AS ingredient_name,
            calendar_year,
            calendar_week,
            ROUND(SUM(quantity_lost), 2) AS waste_quantity,
            ROUND(SUM(cost_loss_amount), 2) AS waste_cost,
            FIRST(wastage_reason) AS primary_reason
        FROM spark_temp_dish_waste
        GROUP BY source_restaurant_id, source_menu_item_id, calendar_year, calendar_week
    """)

    # 2. Raw ingredient wastage path (isolated for analytics, not given dish ML target)
    raw_waste = wastage_df.filter(F.col("source_menu_item_id").isNull()).withColumn(
        "calendar_year", F.year(F.col("wastage_timestamp"))
    ).withColumn(
        "calendar_week", F.weekofyear(F.col("wastage_timestamp"))
    )
    raw_waste.createOrReplaceTempView("spark_temp_raw_waste")

    raw_weekly_waste = spark.sql("""
        SELECT
            source_restaurant_id,
            NULL AS source_menu_item_id,
            'RAW_INGREDIENT' AS item_type,
            ingredient_name,
            calendar_year,
            calendar_week,
            ROUND(SUM(quantity_lost), 2) AS waste_quantity,
            ROUND(SUM(cost_loss_amount), 2) AS waste_cost,
            FIRST(wastage_reason) AS primary_reason,
            0 AS sold_quantity,
            0.0 AS gross_revenue,
            CAST(NULL AS DOUBLE) AS waste_cost_ratio,
            CAST(NULL AS DOUBLE) AS waste_quantity_ratio,
            false AS extreme_operational_risk,
            0 AS current_week_wastage_risk,
            0 AS next_week_wastage_risk
        FROM spark_temp_raw_waste
        GROUP BY source_restaurant_id, ingredient_name, calendar_year, calendar_week
    """)

    # 3. Weekly sales per (restaurant, menu_item, year, week)
    valid_orders = orders_df.filter(F.col("order_status") != "Voided").withColumn(
        "calendar_year", F.year(F.col("order_timestamp"))
    ).withColumn(
        "calendar_week", F.weekofyear(F.col("order_timestamp"))
    )

    merged_sales = order_items_df.join(
        valid_orders.select("source_order_id", "source_restaurant_id", "calendar_year", "calendar_week"),
        on="source_order_id",
        how="inner",
    )
    merged_sales.createOrReplaceTempView("spark_temp_dish_sales")

    weekly_sales = spark.sql("""
        SELECT
            source_restaurant_id,
            source_menu_item_id,
            calendar_year,
            calendar_week,
            SUM(quantity) AS sold_quantity,
            ROUND(SUM(line_net_revenue), 2) AS gross_revenue
        FROM spark_temp_dish_sales
        GROUP BY source_restaurant_id, source_menu_item_id, calendar_year, calendar_week
    """)

    # 4. Outer join weekly dish sales with weekly dish wastage
    dish_mart = weekly_sales.join(
        dish_weekly_waste,
        on=["source_restaurant_id", "source_menu_item_id", "calendar_year", "calendar_week"],
        how="outer",
    )

    dish_mart = dish_mart.withColumn(
        "item_type", F.lit("PREPARED_DISH")
    ).withColumn(
        "ingredient_name", F.lit(None).cast("string")
    ).withColumn(
        "sold_quantity", F.coalesce(F.col("sold_quantity"), F.lit(0))
    ).withColumn(
        "gross_revenue", F.coalesce(F.col("gross_revenue"), F.lit(0.0))
    ).withColumn(
        "waste_quantity", F.coalesce(F.col("waste_quantity"), F.lit(0.0))
    ).withColumn(
        "waste_cost", F.coalesce(F.col("waste_cost"), F.lit(0.0))
    ).withColumn(
        "primary_reason", F.coalesce(F.col("primary_reason"), F.lit("None"))
    )

    # 5. Strict Zero-Denominator and Ratio Calculations
    dish_mart = dish_mart.withColumn(
        "waste_cost_ratio",
        F.when(F.col("gross_revenue") > 0, F.round(F.col("waste_cost") / F.col("gross_revenue"), 4)).otherwise(None),
    ).withColumn(
        "waste_quantity_ratio",
        F.when(F.col("sold_quantity") > 0, F.round(F.col("waste_quantity") / F.col("sold_quantity"), 4)).otherwise(None),
    ).withColumn(
        "extreme_operational_risk",
        (F.col("waste_quantity") > 0) & (F.col("sold_quantity") == 0),
    )

    # 6. Current Week Wastage Risk Label
    cost_thresh = WastageRiskContract.COST_RATIO_THRESHOLD
    qty_thresh = WastageRiskContract.QUANTITY_RATIO_THRESHOLD

    current_risk_expr = (
        F.when(F.col("extreme_operational_risk"), WastageRiskClass.HIGH_RISK.value)
        .when(F.col("waste_cost_ratio") > cost_thresh, WastageRiskClass.HIGH_RISK.value)
        .when(F.col("waste_quantity_ratio") > qty_thresh, WastageRiskClass.HIGH_RISK.value)
        .otherwise(WastageRiskClass.LOW_RISK.value)
    )
    dish_mart = dish_mart.withColumn("current_week_wastage_risk", current_risk_expr)

    # 7. Next Week Wastage Risk Target (Anti-leakage: Spark Window lead by 1 week)
    dish_window = Window.partitionBy("source_restaurant_id", "source_menu_item_id").orderBy(
        "calendar_year", "calendar_week"
    )
    dish_mart = dish_mart.withColumn(
        "next_week_wastage_risk",
        F.coalesce(F.lead("current_week_wastage_risk", 1).over(dish_window), F.lit(WastageRiskClass.LOW_RISK.value)),
    )

    # 8. Union prepared dish mart with raw ingredient mart
    common_cols = [
        "source_restaurant_id", "source_menu_item_id", "item_type", "ingredient_name",
        "calendar_year", "calendar_week", "waste_quantity", "waste_cost", "primary_reason",
        "sold_quantity", "gross_revenue", "waste_cost_ratio", "waste_quantity_ratio",
        "extreme_operational_risk", "current_week_wastage_risk", "next_week_wastage_risk",
    ]

    final_mart = dish_mart.select(*common_cols).unionByName(raw_weekly_waste.select(*common_cols))

    # Attach menu item metadata
    final_mart = final_mart.join(
        F.broadcast(menu_items_df.select(
            "source_menu_item_id",
            "item_name",
            "source_category_id",
            "current_base_cost",
        )),
        on="source_menu_item_id",
        how="left",
    )

    return final_mart
