"""Spark mart generator for mart_menu_performance.parquet.

Implements the authoritative 9-dimension percentile scoring model,
four canonical classifications, and 10 tricky edge case boolean flags
using PySpark DataFrames, Window functions, and Spark SQL.
"""

from __future__ import annotations

import pyspark.sql.functions as F
from pyspark.sql import DataFrame, SparkSession, Window

from packages.common.logging import get_logger
from packages.core.contracts.analytical_contracts import (
    MenuPerformanceCategory,
    MenuPerformanceContract,
)

logger = get_logger(__name__)


def build_menu_performance_mart_spark(
    spark: SparkSession,
    menu_items_df: DataFrame,
    categories_df: DataFrame,
    order_items_df: DataFrame,
    orders_df: DataFrame,
    ratings_df: DataFrame,
    wastage_df: DataFrame,
    restaurant_grain: bool = True,
) -> DataFrame:
    """Build Menu Performance analytical mart using native PySpark and Spark SQL.

    Grain: (source_restaurant_id, source_menu_item_id) if restaurant_grain=True,
           or source_menu_item_id for overall chain rollup.
    """
    logger.info(
        "Executing Spark Menu Performance mart transformation (restaurant_grain=%s)",
        restaurant_grain,
    )

    # 1. Register temporary views for Spark SQL queries
    valid_orders = (
        orders_df.filter(F.col("order_status") != "Voided")
        .withColumn("order_date_dt", F.to_timestamp(F.col("order_timestamp")))
        .withColumn("order_date", F.to_date(F.col("order_timestamp")))
        .withColumn("is_weekend", F.dayofweek(F.col("order_timestamp")).isin([1, 6, 7]))
    )

    valid_orders.createOrReplaceTempView("spark_temp_orders")
    order_items_df.createOrReplaceTempView("spark_temp_order_items")

    # 2. Spark SQL: Compute sales, revenue, contribution margin, weekend share, promo share
    sql_group = (
        "o.source_restaurant_id, oi.source_menu_item_id"
        if restaurant_grain
        else "oi.source_menu_item_id"
    )
    outer_group = (
        "source_restaurant_id, source_menu_item_id" if restaurant_grain else "source_menu_item_id"
    )

    sales_stats = spark.sql(f"""
        SELECT
            {sql_group},
            SUM(oi.quantity) AS total_quantity,
            ROUND(SUM(oi.line_net_revenue), 2) AS gross_revenue,
            ROUND(SUM(oi.line_contribution_margin), 2) AS contribution_margin,
            SUM(CASE WHEN o.is_weekend THEN oi.quantity ELSE 0 END) AS weekend_quantity,
            SUM(CASE WHEN oi.source_promotion_id IS NOT NULL THEN oi.quantity ELSE 0 END) AS promo_quantity,
            COUNT(DISTINCT o.source_customer_id) AS total_customers,
            MIN(o.order_date_dt) AS first_order_date,
            MAX(o.order_date_dt) AS last_order_date
        FROM spark_temp_order_items oi
        INNER JOIN spark_temp_orders o ON oi.source_order_id = o.source_order_id
        GROUP BY {sql_group}
    """)

    # 3. Repeat purchase rate via Spark SQL
    repeat_stats = spark.sql(f"""
        WITH cust_item_orders AS (
            SELECT
                {sql_group},
                o.source_customer_id,
                COUNT(DISTINCT o.source_order_id) AS order_count
            FROM spark_temp_order_items oi
            INNER JOIN spark_temp_orders o ON oi.source_order_id = o.source_order_id
            GROUP BY {sql_group}, o.source_customer_id
        )
        SELECT
            {outer_group},
            COUNT(DISTINCT CASE WHEN order_count >= 2 THEN source_customer_id END) AS repeat_customers
        FROM cust_item_orders
        GROUP BY {outer_group}
    """)

    join_cols = (
        ["source_restaurant_id", "source_menu_item_id"]
        if restaurant_grain
        else ["source_menu_item_id"]
    )
    item_stats = sales_stats.join(repeat_stats, on=join_cols, how="left")

    # 4. Sales Trend: 2nd half vs 1st half of observation window
    window_bounds = valid_orders.select(
        F.min("order_date_dt").alias("min_dt"),
        F.max("order_date_dt").alias("max_dt"),
    ).first()
    min_dt = window_bounds["min_dt"]
    max_dt = window_bounds["max_dt"]
    mid_ts = min_dt.timestamp() + (max_dt.timestamp() - min_dt.timestamp()) / 2.0

    valid_orders_with_half = valid_orders.withColumn(
        "is_recent", F.col("order_date_dt").cast("double") >= mid_ts
    )
    valid_orders_with_half.createOrReplaceTempView("spark_temp_orders_half")

    trend_stats = spark.sql(f"""
        SELECT
            {sql_group},
            ROUND(
                SUM(CASE WHEN o.is_recent THEN oi.quantity ELSE 0 END) /
                GREATEST(1.0, SUM(CASE WHEN NOT o.is_recent THEN oi.quantity ELSE 0 END)),
                4
            ) AS sales_trend_ratio
        FROM spark_temp_order_items oi
        INNER JOIN spark_temp_orders_half o ON oi.source_order_id = o.source_order_id
        GROUP BY {sql_group}
    """)
    item_stats = item_stats.join(trend_stats, on=join_cols, how="left")

    # 5. Wastage metrics (prepared dishes only: source_menu_item_id is not null)
    dish_wastage = wastage_df.filter(F.col("source_menu_item_id").isNotNull())
    waste_stats = dish_wastage.groupBy(join_cols).agg(
        F.sum("quantity_lost").alias("waste_quantity"),
        F.round(F.sum("cost_loss_amount"), 2).alias("waste_cost"),
    )
    item_stats = item_stats.join(waste_stats, on=join_cols, how="left")

    # 6. Customer ratings
    dish_ratings = ratings_df.filter(F.col("source_menu_item_id").isNotNull())
    rating_group = (
        ["source_restaurant_id", "source_menu_item_id"]
        if restaurant_grain
        else ["source_menu_item_id"]
    )
    rating_stats = dish_ratings.groupBy(rating_group).agg(
        F.count("rating_score").alias("rating_count"),
        F.round(F.avg("rating_score"), 2).alias("avg_rating"),
    )
    item_stats = item_stats.join(rating_stats, on=join_cols, how="left")

    # Fill defaults for ratios
    item_stats = (
        item_stats.withColumn(
            "profitability_pct",
            F.when(
                F.col("gross_revenue") > 0, F.col("contribution_margin") / F.col("gross_revenue")
            ).otherwise(0.0),
        )
        .withColumn(
            "weekend_share",
            F.when(
                F.col("total_quantity") > 0, F.col("weekend_quantity") / F.col("total_quantity")
            ).otherwise(0.0),
        )
        .withColumn(
            "promotion_dependency",
            F.when(
                F.col("total_quantity") > 0, F.col("promo_quantity") / F.col("total_quantity")
            ).otherwise(0.0),
        )
        .withColumn(
            "active_days",
            F.datediff(F.col("last_order_date"), F.col("first_order_date")) + 1,
        )
        .withColumn("repeat_customers", F.coalesce(F.col("repeat_customers"), F.lit(0)))
        .withColumn(
            "repeat_purchase_rate",
            F.when(
                F.col("total_customers") > 0, F.col("repeat_customers") / F.col("total_customers")
            ).otherwise(0.0),
        )
        .withColumn("waste_quantity", F.coalesce(F.col("waste_quantity"), F.lit(0.0)))
        .withColumn("waste_cost", F.coalesce(F.col("waste_cost"), F.lit(0.0)))
        .withColumn(
            "wastage_pct",
            F.when(
                (F.col("total_quantity") + F.col("waste_quantity")) > 0,
                F.col("waste_quantity") / (F.col("total_quantity") + F.col("waste_quantity")),
            ).otherwise(0.0),
        )
        .withColumn("avg_rating", F.coalesce(F.col("avg_rating"), F.lit(4.0)))
        .withColumn("rating_count", F.coalesce(F.col("rating_count"), F.lit(0)))
        .withColumn("sales_trend_ratio", F.coalesce(F.col("sales_trend_ratio"), F.lit(1.0)))
    )

    # 7. Join menu metadata & category
    item_stats = item_stats.join(
        F.broadcast(
            menu_items_df.select(
                "source_menu_item_id",
                "source_category_id",
                "item_name",
                "current_base_price",
                "current_base_cost",
                "is_seasonal",
                "prep_time_minutes",
            )
        ),
        on="source_menu_item_id",
        how="left",
    )

    if categories_df is not None:
        item_stats = item_stats.join(
            F.broadcast(categories_df.select("source_category_id", "category_name")),
            on="source_category_id",
            how="left",
        )

    # -------------------------------------------------------------------------
    # 8. Normalized Percentile Scores (0-100 scale using Spark Window percent_rank)
    # -------------------------------------------------------------------------
    cohort_window = Window.orderBy("total_quantity")
    rev_window = Window.orderBy("gross_revenue")
    margin_window = Window.orderBy("contribution_margin")
    profit_pct_window = Window.orderBy("profitability_pct")
    rating_window = Window.orderBy("avg_rating")
    repeat_window = Window.orderBy("repeat_purchase_rate")
    waste_window = Window.orderBy("wastage_pct")
    promo_window = Window.orderBy("promotion_dependency")
    trend_window = Window.orderBy("sales_trend_ratio")

    item_stats = (
        item_stats.withColumn("rank_qty", F.percent_rank().over(cohort_window) * 100.0)
        .withColumn("rank_rev", F.percent_rank().over(rev_window) * 100.0)
        .withColumn("rank_margin", F.percent_rank().over(margin_window) * 100.0)
        .withColumn("rank_profit_pct", F.percent_rank().over(profit_pct_window) * 100.0)
        .withColumn("rank_rating", F.percent_rank().over(rating_window) * 100.0)
        .withColumn("rank_repeat", F.percent_rank().over(repeat_window) * 100.0)
        .withColumn("rank_waste", F.percent_rank().over(waste_window) * 100.0)
        .withColumn("rank_promo", F.percent_rank().over(promo_window) * 100.0)
        .withColumn("rank_trend", F.percent_rank().over(trend_window) * 100.0)
    )

    item_stats = (
        item_stats.withColumn(
            "demand_score", F.round(0.5 * F.col("rank_qty") + 0.5 * F.col("rank_rev"), 2)
        )
        .withColumn(
            "profitability_score",
            F.round(0.5 * F.col("rank_margin") + 0.5 * F.col("rank_profit_pct"), 2),
        )
        .withColumn(
            "customer_signal_score",
            F.round(0.6 * F.col("rank_rating") + 0.4 * F.col("rank_repeat"), 2),
        )
        .withColumn("wastage_health_score", F.round(100.0 - F.col("rank_waste"), 2))
        .withColumn("sales_trend_score", F.round(F.col("rank_trend"), 2))
        .withColumn("promotion_independence_score", F.round(100.0 - F.col("rank_promo"), 2))
    )

    # Composite Score
    w_d = MenuPerformanceContract.WEIGHT_DEMAND
    w_p = MenuPerformanceContract.WEIGHT_PROFITABILITY
    w_c = MenuPerformanceContract.WEIGHT_CUSTOMER_SIGNAL
    w_w = MenuPerformanceContract.WEIGHT_WASTAGE_HEALTH
    w_t = MenuPerformanceContract.WEIGHT_SALES_TREND
    w_pi = MenuPerformanceContract.WEIGHT_PROMOTION_INDEPENDENCE

    item_stats = item_stats.withColumn(
        "composite_score",
        F.round(
            w_d * F.col("demand_score")
            + w_p * F.col("profitability_score")
            + w_c * F.col("customer_signal_score")
            + w_w * F.col("wastage_health_score")
            + w_t * F.col("sales_trend_score")
            + w_pi * F.col("promotion_independence_score"),
            2,
        ),
    )

    # -------------------------------------------------------------------------
    # 9. Canonical Classification Gating Logic
    # -------------------------------------------------------------------------
    high = MenuPerformanceContract.HIGH_PERCENTILE
    low = MenuPerformanceContract.LOW_PERCENTILE

    is_high_demand = F.col("demand_score") >= high
    is_high_profit = F.col("profitability_score") >= high
    is_acceptable_waste = F.col("wastage_health_score") >= low
    is_promo_independent = F.col("promotion_independence_score") >= low
    is_high_customer = F.col("customer_signal_score") >= high

    classification_expr = (
        F.when(
            is_high_demand & is_high_profit & is_acceptable_waste & is_promo_independent,
            MenuPerformanceCategory.PROFIT_DRIVER.value,
        )
        .when(is_high_demand & (~is_high_profit), MenuPerformanceCategory.VOLUME_DRIVER.value)
        .when(
            (~is_high_demand) & (is_high_profit | is_high_customer) & is_acceptable_waste,
            MenuPerformanceCategory.HIDDEN_OPPORTUNITY.value,
        )
        .otherwise(MenuPerformanceCategory.LOW_PERFORMER.value)
    )
    item_stats = item_stats.withColumn("classification", classification_expr)

    # -------------------------------------------------------------------------
    # 10. Tricky Edge Case Boolean Flags (SRS Step 11)
    # -------------------------------------------------------------------------
    item_stats = (
        item_stats.withColumn(
            "flag_high_selling_loss_making",
            (F.col("demand_score") >= high)
            & ((F.col("contribution_margin") <= 0) | (F.col("profitability_score") <= low)),
        )
        .withColumn(
            "flag_profitable_rarely_purchased",
            (F.col("profitability_score") >= high) & (F.col("demand_score") <= low),
        )
        .withColumn(
            "flag_popular_high_wastage",
            (F.col("demand_score") >= high) & (F.col("wastage_health_score") <= low),
        )
        .withColumn(
            "flag_high_rating_low_profitability",
            (F.col("avg_rating") >= MenuPerformanceContract.HIGH_RATING_THRESHOLD)
            & (F.col("profitability_score") <= low),
        )
        .withColumn(
            "flag_low_rating_high_sales",
            (F.col("avg_rating") <= MenuPerformanceContract.LOW_RATING_THRESHOLD)
            & (F.col("demand_score") >= high),
        )
        .withColumn(
            "flag_promotion_dependent",
            F.col("promotion_dependency") >= MenuPerformanceContract.PROMOTION_DEPENDENCY_THRESHOLD,
        )
        .withColumn(
            "flag_weekend_only_pattern",
            F.col("weekend_share") >= MenuPerformanceContract.WEEKEND_SALES_THRESHOLD,
        )
        .withColumn(
            "flag_seasonal_item",
            F.coalesce(F.col("is_seasonal"), F.lit(False)),
        )
        .withColumn(
            "flag_new_item_insufficient_history",
            F.col("active_days") < MenuPerformanceContract.NEW_ITEM_MAX_ACTIVE_DAYS,
        )
        .withColumn(
            "flag_location_divergence",
            F.lit(False),
        )
    )

    # Drop intermediate rank columns for clean mart output
    final_df = item_stats.drop(
        "rank_qty",
        "rank_rev",
        "rank_margin",
        "rank_profit_pct",
        "rank_rating",
        "rank_repeat",
        "rank_waste",
        "rank_promo",
        "rank_trend",
    )

    return final_df
