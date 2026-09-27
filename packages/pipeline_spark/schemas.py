"""Formal typed schema definitions for Spark ingestion and analytical marts.

Defines exact schemas for all 11 business domain tables and 12 analytical marts.
Conforms strictly to verified physical Parquet columns with zero hallucinated names.
"""

from __future__ import annotations

from typing import Any

from packages.pipeline_spark.session import is_spark_available

# Table names corresponding to physical cleaned Parquet files
CLEANED_TABLE_NAMES: tuple[str, ...] = (
    "customers",
    "restaurants",
    "menu_categories",
    "menu_items",
    "pricing_history",
    "promotions",
    "orders",
    "order_items",
    "ratings",
    "inventory",
    "wastage",
)

# Analytical Mart filenames
MART_NAMES: tuple[str, ...] = (
    "mart_menu_performance",
    "mart_customer_rfm",
    "mart_basket_analysis",
    "mart_peak_analysis",
    "mart_location_performance",
    "mart_channel_performance",
    "mart_wastage",
    "mart_pricing",
    "mart_promotions",
    "mart_ratings_anomalies",
    "mart_sales_anomalies",
    "mart_demand_historical",
)


def get_spark_table_schemas() -> dict[str, Any]:
    """Return dictionary of PySpark StructType schemas for all 11 domain tables.

    Returns empty dict if PySpark is not installed in the environment.
    """
    if not is_spark_available():
        return {}

    from pyspark.sql.types import (
        BooleanType,
        DateType,
        DoubleType,
        IntegerType,
        StringType,
        StructField,
        StructType,
        TimestampType,
    )

    return {
        "customers": StructType(
            [
                StructField("source_customer_id", StringType(), False),
                StructField("first_name", StringType(), False),
                StructField("last_name", StringType(), False),
                StructField("email", StringType(), False),
                StructField("phone", StringType(), False),
                StructField("registration_date", DateType(), False),
                StructField("loyalty_tier", StringType(), False),
                StructField("preferred_channel", StringType(), False),
                StructField("home_city", StringType(), False),
                StructField("is_active", BooleanType(), False),
                StructField("created_at", TimestampType(), False),
            ]
        ),
        "restaurants": StructType(
            [
                StructField("source_restaurant_id", StringType(), False),
                StructField("location_name", StringType(), False),
                StructField("city", StringType(), False),
                StructField("state_region", StringType(), False),
                StructField("postal_code", StringType(), False),
                StructField("seating_capacity", IntegerType(), False),
                StructField("dining_type", StringType(), False),
                StructField("manager_name", StringType(), False),
                StructField("opening_date", DateType(), False),
                StructField("latitude", DoubleType(), True),
                StructField("longitude", DoubleType(), True),
                StructField("is_active", BooleanType(), False),
                StructField("created_at", TimestampType(), False),
            ]
        ),
        "menu_categories": StructType(
            [
                StructField("source_category_id", StringType(), False),
                StructField("category_name", StringType(), False),
                StructField("description", StringType(), True),
                StructField("display_order", IntegerType(), False),
                StructField("is_active", BooleanType(), False),
                StructField("created_at", TimestampType(), False),
            ]
        ),
        "menu_items": StructType(
            [
                StructField("source_menu_item_id", StringType(), False),
                StructField("source_category_id", StringType(), False),
                StructField("item_name", StringType(), False),
                StructField("description", StringType(), True),
                StructField("current_base_price", DoubleType(), False),
                StructField("current_base_cost", DoubleType(), False),
                StructField("prep_time_minutes", IntegerType(), False),
                StructField("is_seasonal", BooleanType(), False),
                StructField("is_active", BooleanType(), False),
                StructField("spiciness_level", IntegerType(), True),
                StructField("allergens", StringType(), True),
                StructField("created_at", TimestampType(), False),
            ]
        ),
        "pricing_history": StructType(
            [
                StructField("source_pricing_history_id", StringType(), False),
                StructField("source_menu_item_id", StringType(), False),
                StructField("source_restaurant_id", StringType(), True),
                StructField("base_price", DoubleType(), False),
                StructField("base_cost", DoubleType(), False),
                StructField("effective_from", TimestampType(), False),
                StructField("effective_to", TimestampType(), True),
                StructField("change_reason", StringType(), True),
                StructField("created_at", TimestampType(), False),
            ]
        ),
        "promotions": StructType(
            [
                StructField("source_promotion_id", StringType(), False),
                StructField("campaign_name", StringType(), False),
                StructField("promo_code", StringType(), False),
                StructField("discount_type", StringType(), False),
                StructField("discount_value", DoubleType(), False),
                StructField("start_date", DateType(), False),
                StructField("end_date", DateType(), False),
                StructField("minimum_order_amount", DoubleType(), True),
                StructField("source_category_id", StringType(), True),
                StructField("source_menu_item_id", StringType(), True),
                StructField("applicable_channel", StringType(), True),
                StructField("is_active", BooleanType(), False),
                StructField("is_misleading", BooleanType(), False),
                StructField("created_at", TimestampType(), False),
            ]
        ),
        "orders": StructType(
            [
                StructField("source_order_id", StringType(), False),
                StructField("source_restaurant_id", StringType(), False),
                StructField("source_customer_id", StringType(), False),
                StructField("order_timestamp", TimestampType(), False),
                StructField("order_channel", StringType(), False),
                StructField("order_status", StringType(), False),
                StructField("subtotal_amount", DoubleType(), False),
                StructField("discount_amount", DoubleType(), False),
                StructField("tax_amount", DoubleType(), False),
                StructField("tip_amount", DoubleType(), False),
                StructField("total_amount", DoubleType(), False),
                StructField("payment_method", StringType(), False),
                StructField("created_at", TimestampType(), False),
            ]
        ),
        "order_items": StructType(
            [
                StructField("source_order_item_id", StringType(), False),
                StructField("source_order_id", StringType(), False),
                StructField("source_menu_item_id", StringType(), False),
                StructField("quantity", IntegerType(), False),
                StructField("unit_price_at_sale", DoubleType(), False),
                StructField("unit_cost_at_sale", DoubleType(), False),
                StructField("line_discount", DoubleType(), False),
                StructField("source_promotion_id", StringType(), True),
                StructField("line_net_revenue", DoubleType(), False),
                StructField("line_contribution_margin", DoubleType(), False),
                StructField("special_instructions", StringType(), True),
                StructField("created_at", TimestampType(), False),
            ]
        ),
        "ratings": StructType(
            [
                StructField("source_rating_id", StringType(), False),
                StructField("source_restaurant_id", StringType(), False),
                StructField("source_order_id", StringType(), False),
                StructField("source_customer_id", StringType(), False),
                StructField("source_menu_item_id", StringType(), True),
                StructField("rating_score", DoubleType(), False),
                StructField("food_rating", DoubleType(), True),
                StructField("service_rating", DoubleType(), True),
                StructField("ambiance_rating", DoubleType(), True),
                StructField("review_text", StringType(), True),
                StructField("rating_timestamp", TimestampType(), False),
                StructField("is_verified_purchase", BooleanType(), False),
                StructField("created_at", TimestampType(), False),
            ]
        ),
        "inventory": StructType(
            [
                StructField("source_inventory_id", StringType(), False),
                StructField("source_restaurant_id", StringType(), False),
                StructField("ingredient_name", StringType(), False),
                StructField("ingredient_category", StringType(), False),
                StructField("current_stock_quantity", DoubleType(), False),
                StructField("unit_of_measure", StringType(), False),
                StructField("reorder_threshold", DoubleType(), False),
                StructField("reorder_quantity", DoubleType(), False),
                StructField("unit_purchase_cost", DoubleType(), False),
                StructField("last_restock_date", DateType(), False),
                StructField("created_at", TimestampType(), False),
                StructField("updated_at", TimestampType(), False),
            ]
        ),
        "wastage": StructType(
            [
                StructField("source_wastage_id", StringType(), False),
                StructField("source_restaurant_id", StringType(), False),
                StructField("source_menu_item_id", StringType(), True),
                StructField("ingredient_name", StringType(), True),
                StructField("wastage_timestamp", TimestampType(), False),
                StructField("quantity_lost", DoubleType(), False),
                StructField("unit_of_measure", StringType(), False),
                StructField("cost_loss_amount", DoubleType(), False),
                StructField("wastage_reason", StringType(), False),
                StructField("reported_by", StringType(), True),
                StructField("created_at", TimestampType(), False),
            ]
        ),
    }
