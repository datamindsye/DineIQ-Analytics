"""Optimized relational join graphs for the DineIQ analytical pipeline.

Implements line-level promotion linkage and dual-path wastage routing
as mandated by the approved Architecture Decision Pack.
"""

from __future__ import annotations

from typing import Any

from packages.common.logging import get_logger

logger = get_logger(__name__)


# -----------------------------------------------------------------------------
# Spark DataFrame Join Implementations
# -----------------------------------------------------------------------------


def join_order_lines_spark(
    orders_df: Any,
    order_items_df: Any,
    menu_items_df: Any,
    categories_df: Any | None = None,
    promotions_df: Any | None = None,
) -> Any:
    """Perform core denormalized join across orders, items, menu, and promotions.

    CRITICAL ARCHITECTURAL RULES:
    1. Promotion linkage is strictly at the order_items grain:
       order_items.source_promotion_id = promotions.source_promotion_id
    2. orders table contains NO promotion foreign key.
    """
    # 1. Join order_items with menu_items
    items_with_menu = order_items_df.join(
        menu_items_df.select(
            "source_menu_item_id",
            "source_category_id",
            "item_name",
            "current_base_price",
            "current_base_cost",
            "is_seasonal",
            "prep_time_minutes",
        ),
        on="source_menu_item_id",
        how="inner",
    )

    # 2. Join with categories if provided
    if categories_df is not None:
        items_with_menu = items_with_menu.join(
            categories_df.select("source_category_id", "category_name"),
            on="source_category_id",
            how="left",
        )

    # 3. Line-level promotion linkage
    if promotions_df is not None:
        items_with_menu = items_with_menu.join(
            promotions_df.select(
                "source_promotion_id",
                "campaign_name",
                "discount_type",
                "discount_value",
                "is_misleading",
            ),
            on="source_promotion_id",
            how="left",
        )

    # 4. Join with orders to attach customer, restaurant, timestamp, channel
    full_lines = items_with_menu.join(
        orders_df.select(
            "source_order_id",
            "source_customer_id",
            "source_restaurant_id",
            "order_timestamp",
            "order_channel",
            "order_status",
            "payment_method",
        ),
        on="source_order_id",
        how="inner",
    )

    return full_lines


def route_wastage_spark(
    wastage_df: Any,
    menu_items_df: Any,
    inventory_df: Any,
) -> tuple[Any, Any]:
    """Execute dual-path wastage routing.

    Returns:
        (prepared_dish_wastage_df, raw_ingredient_wastage_df)

    Path A: source_menu_item_id IS NOT NULL -> joins to menu_items.
    Path B: source_menu_item_id IS NULL -> joins to inventory on (source_restaurant_id, ingredient_name).
    """
    import pyspark.sql.functions as F

    # Path A: Prepared dishes
    dish_wastage = wastage_df.filter(F.col("source_menu_item_id").isNotNull()).join(
        menu_items_df.select(
            "source_menu_item_id",
            "source_category_id",
            "item_name",
            "current_base_cost",
            "is_seasonal",
        ),
        on="source_menu_item_id",
        how="inner",
    )

    # Path B: Raw ingredients
    raw_wastage = wastage_df.filter(F.col("source_menu_item_id").isNull()).join(
        inventory_df.select(
            "source_restaurant_id",
            "ingredient_name",
            "ingredient_category",
            "unit_purchase_cost",
            "current_stock_quantity",
            "reorder_threshold",
        ),
        on=["source_restaurant_id", "ingredient_name"],
        how="left",
    )

    return dish_wastage, raw_wastage


# -----------------------------------------------------------------------------
# Pandas / PyArrow High-Performance Columnar Fallback Joins
# -----------------------------------------------------------------------------


def join_order_lines_pandas(
    orders_df: Any,
    order_items_df: Any,
    menu_items_df: Any,
    categories_df: Any | None = None,
    promotions_df: Any | None = None,
) -> Any:
    """Pandas/PyArrow equivalent for fast local development and testing."""
    # 1. Join order_items with menu_items
    merged = order_items_df.merge(
        menu_items_df[
            [
                "source_menu_item_id",
                "source_category_id",
                "item_name",
                "current_base_price",
                "current_base_cost",
                "is_seasonal",
                "prep_time_minutes",
            ]
        ],
        on="source_menu_item_id",
        how="inner",
    )

    # 2. Join categories
    if categories_df is not None:
        merged = merged.merge(
            categories_df[["source_category_id", "category_name"]],
            on="source_category_id",
            how="left",
        )

    # 3. Line-level promotion linkage
    if promotions_df is not None:
        merged = merged.merge(
            promotions_df[
                [
                    "source_promotion_id",
                    "campaign_name",
                    "discount_type",
                    "discount_value",
                    "is_misleading",
                ]
            ],
            on="source_promotion_id",
            how="left",
        )

    # 4. Join orders
    merged = merged.merge(
        orders_df[
            [
                "source_order_id",
                "source_customer_id",
                "source_restaurant_id",
                "order_timestamp",
                "order_channel",
                "order_status",
                "payment_method",
            ]
        ],
        on="source_order_id",
        how="inner",
    )

    return merged


def route_wastage_pandas(
    wastage_df: Any,
    menu_items_df: Any,
    inventory_df: Any,
) -> tuple[Any, Any]:
    """Pandas equivalent for dual-path wastage routing."""
    # Path A: Prepared dishes
    dish_mask = wastage_df["source_menu_item_id"].notna()
    dish_wastage = wastage_df[dish_mask].merge(
        menu_items_df[
            [
                "source_menu_item_id",
                "source_category_id",
                "item_name",
                "current_base_cost",
                "is_seasonal",
            ]
        ],
        on="source_menu_item_id",
        how="inner",
    )

    # Path B: Raw ingredients
    raw_mask = wastage_df["source_menu_item_id"].isna()
    raw_wastage = wastage_df[raw_mask].merge(
        inventory_df[
            [
                "source_restaurant_id",
                "ingredient_name",
                "ingredient_category",
                "unit_purchase_cost",
                "current_stock_quantity",
                "reorder_threshold",
            ]
        ],
        on=["source_restaurant_id", "ingredient_name"],
        how="left",
    )

    return dish_wastage, raw_wastage
