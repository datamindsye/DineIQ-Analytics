"""Dataset contracts and PyArrow schema definitions for analytical source data.

This module defines formal PyArrow schemas, business source identifier regexes,
allowed enumeration values, and mathematical validation formulas for all eleven
business domain tables required by the DineIQ Analytics platform.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

import pyarrow as pa

# -----------------------------------------------------------------------------
# Business Identifier Patterns
# -----------------------------------------------------------------------------

SOURCE_ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "customers": re.compile(r"^CUST-\d{8}$"),
    "restaurants": re.compile(r"^REST-\d{4}$"),
    "menu_categories": re.compile(r"^CAT-\d{3}$"),
    "menu_items": re.compile(r"^DISH-\d{4}$"),
    "pricing_history": re.compile(r"^PRC-\d{6}$"),
    "promotions": re.compile(r"^PROMO-\d{4}$"),
    "orders": re.compile(r"^ORD-\d{8}$"),
    "order_items": re.compile(r"^ITEM-\d{8}$"),
    "ratings": re.compile(r"^RAT-\d{8}$"),
    "inventory": re.compile(r"^INV-REST\d{2}-\d{4}$"),
    "wastage": re.compile(r"^WASTE-\d{8}$"),
}

# -----------------------------------------------------------------------------
# Domain Enumerations and Allowed Values
# -----------------------------------------------------------------------------

LOYALTY_TIERS: tuple[str, ...] = ("Bronze", "Silver", "Gold", "Platinum", "None")

DINING_TYPES: tuple[str, ...] = (
    "Fast Casual",
    "Casual Dining",
    "Fine Dining",
    "Express Kiosk",
)

CHANNELS: tuple[str, ...] = (
    "Dine-in",
    "Takeaway",
    "Delivery Direct",
    "Delivery Aggregator",
)

ORDER_STATUSES: tuple[str, ...] = (
    "Completed",
    "Cancelled",
    "Refunded",
    "Voided",
)

PAYMENT_METHODS: tuple[str, ...] = (
    "Credit Card",
    "Debit Card",
    "Cash",
    "Digital Wallet",
    "Gift Card",
)

DISCOUNT_TYPES: tuple[str, ...] = (
    "Percentage",
    "Fixed Amount",
    "Buy One Get One",
    "Combo Bundle",
)

CANONICAL_CATEGORIES: tuple[str, ...] = (
    "Appetizers",
    "Entrees",
    "Seafood Specialties",
    "Pasta & Noodles",
    "Sandwiches & Burgers",
    "Side Dishes",
    "Desserts",
    "Non-Alcoholic Beverages",
    "Bar & Cocktails",
    "Chef Specials",
)

INGREDIENT_CATEGORIES: tuple[str, ...] = (
    "Produce",
    "Meat & Poultry",
    "Dairy",
    "Dry Goods",
    "Beverage Supplies",
    "Packaging",
)

UNITS_OF_MEASURE: tuple[str, ...] = (
    "kg",
    "g",
    "L",
    "ml",
    "units",
    "boxes",
)

WASTAGE_REASONS: tuple[str, ...] = (
    "Expired",
    "Over-preparation",
    "Cooking Error",
    "Equipment Failure",
    "Customer Returned",
    "Spillage",
)

# -----------------------------------------------------------------------------
# PyArrow Analytical Source Schemas (Columnar Snapshots and Marts)
# -----------------------------------------------------------------------------

CUSTOMERS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_customer_id", pa.string(), nullable=False),
        pa.field("first_name", pa.string(), nullable=True),
        pa.field("last_name", pa.string(), nullable=True),
        pa.field("email", pa.string(), nullable=True),
        pa.field("phone", pa.string(), nullable=True),
        pa.field("registration_date", pa.date32(), nullable=False),
        pa.field("loyalty_tier", pa.string(), nullable=False),
        pa.field("preferred_channel", pa.string(), nullable=True),
        pa.field("home_city", pa.string(), nullable=True),
        pa.field("is_active", pa.bool_(), nullable=False),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

RESTAURANTS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_restaurant_id", pa.string(), nullable=False),
        pa.field("location_name", pa.string(), nullable=False),
        pa.field("city", pa.string(), nullable=False),
        pa.field("state_region", pa.string(), nullable=False),
        pa.field("postal_code", pa.string(), nullable=False),
        pa.field("seating_capacity", pa.int32(), nullable=False),
        pa.field("dining_type", pa.string(), nullable=False),
        pa.field("manager_name", pa.string(), nullable=True),
        pa.field("opening_date", pa.date32(), nullable=False),
        pa.field("latitude", pa.float64(), nullable=True),
        pa.field("longitude", pa.float64(), nullable=True),
        pa.field("is_active", pa.bool_(), nullable=False),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

MENU_CATEGORIES_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_category_id", pa.string(), nullable=False),
        pa.field("category_name", pa.string(), nullable=False),
        pa.field("description", pa.string(), nullable=True),
        pa.field("display_order", pa.int32(), nullable=False),
        pa.field("is_active", pa.bool_(), nullable=False),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

MENU_ITEMS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_menu_item_id", pa.string(), nullable=False),
        pa.field("source_category_id", pa.string(), nullable=False),
        pa.field("item_name", pa.string(), nullable=False),
        pa.field("description", pa.string(), nullable=True),
        pa.field("current_base_price", pa.float64(), nullable=False),
        pa.field("current_base_cost", pa.float64(), nullable=False),
        pa.field("prep_time_minutes", pa.int32(), nullable=False),
        pa.field("is_seasonal", pa.bool_(), nullable=False),
        pa.field("is_active", pa.bool_(), nullable=False),
        pa.field("spiciness_level", pa.int32(), nullable=False),
        pa.field("allergens", pa.string(), nullable=True),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

PRICING_HISTORY_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_pricing_history_id", pa.string(), nullable=False),
        pa.field("source_menu_item_id", pa.string(), nullable=False),
        pa.field("source_restaurant_id", pa.string(), nullable=True),
        pa.field("base_price", pa.float64(), nullable=False),
        pa.field("base_cost", pa.float64(), nullable=False),
        pa.field("effective_from", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("effective_to", pa.timestamp("us", tz="UTC"), nullable=True),
        pa.field("change_reason", pa.string(), nullable=False),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

PROMOTIONS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_promotion_id", pa.string(), nullable=False),
        pa.field("campaign_name", pa.string(), nullable=False),
        pa.field("promo_code", pa.string(), nullable=True),
        pa.field("discount_type", pa.string(), nullable=False),
        pa.field("discount_value", pa.float64(), nullable=False),
        pa.field("start_date", pa.date32(), nullable=False),
        pa.field("end_date", pa.date32(), nullable=False),
        pa.field("minimum_order_amount", pa.float64(), nullable=False),
        pa.field("source_category_id", pa.string(), nullable=True),
        pa.field("source_menu_item_id", pa.string(), nullable=True),
        pa.field("applicable_channel", pa.string(), nullable=True),
        pa.field("is_active", pa.bool_(), nullable=False),
        pa.field("is_misleading", pa.bool_(), nullable=False),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

ORDERS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_order_id", pa.string(), nullable=False),
        pa.field("source_restaurant_id", pa.string(), nullable=False),
        pa.field("source_customer_id", pa.string(), nullable=True),
        pa.field("order_timestamp", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("order_channel", pa.string(), nullable=False),
        pa.field("order_status", pa.string(), nullable=False),
        pa.field("subtotal_amount", pa.float64(), nullable=False),
        pa.field("discount_amount", pa.float64(), nullable=False),
        pa.field("tax_amount", pa.float64(), nullable=False),
        pa.field("tip_amount", pa.float64(), nullable=False),
        pa.field("total_amount", pa.float64(), nullable=False),
        pa.field("payment_method", pa.string(), nullable=False),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

ORDER_ITEMS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_order_item_id", pa.string(), nullable=False),
        pa.field("source_order_id", pa.string(), nullable=False),
        pa.field("source_menu_item_id", pa.string(), nullable=False),
        pa.field("quantity", pa.int32(), nullable=False),
        pa.field("unit_price_at_sale", pa.float64(), nullable=False),
        pa.field("unit_cost_at_sale", pa.float64(), nullable=False),
        pa.field("line_discount", pa.float64(), nullable=False),
        pa.field("source_promotion_id", pa.string(), nullable=True),
        pa.field("line_net_revenue", pa.float64(), nullable=False),
        pa.field("line_contribution_margin", pa.float64(), nullable=False),
        pa.field("special_instructions", pa.string(), nullable=True),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

RATINGS_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_rating_id", pa.string(), nullable=False),
        pa.field("source_restaurant_id", pa.string(), nullable=False),
        pa.field("source_order_id", pa.string(), nullable=True),
        pa.field("source_customer_id", pa.string(), nullable=True),
        pa.field("source_menu_item_id", pa.string(), nullable=True),
        pa.field("rating_score", pa.int32(), nullable=False),
        pa.field("food_rating", pa.int32(), nullable=True),
        pa.field("service_rating", pa.int32(), nullable=True),
        pa.field("ambiance_rating", pa.int32(), nullable=True),
        pa.field("review_text", pa.string(), nullable=True),
        pa.field("rating_timestamp", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("is_verified_purchase", pa.bool_(), nullable=False),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

INVENTORY_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_inventory_id", pa.string(), nullable=False),
        pa.field("source_restaurant_id", pa.string(), nullable=False),
        pa.field("ingredient_name", pa.string(), nullable=False),
        pa.field("ingredient_category", pa.string(), nullable=False),
        pa.field("current_stock_quantity", pa.float64(), nullable=False),
        pa.field("unit_of_measure", pa.string(), nullable=False),
        pa.field("reorder_threshold", pa.float64(), nullable=False),
        pa.field("reorder_quantity", pa.float64(), nullable=False),
        pa.field("unit_purchase_cost", pa.float64(), nullable=False),
        pa.field("last_restock_date", pa.date32(), nullable=True),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("updated_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

WASTAGE_ARROW_SCHEMA = pa.schema(
    [
        pa.field("source_wastage_id", pa.string(), nullable=False),
        pa.field("source_restaurant_id", pa.string(), nullable=False),
        pa.field("source_menu_item_id", pa.string(), nullable=True),
        pa.field("ingredient_name", pa.string(), nullable=True),
        pa.field("wastage_timestamp", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("quantity_lost", pa.float64(), nullable=False),
        pa.field("unit_of_measure", pa.string(), nullable=False),
        pa.field("cost_loss_amount", pa.float64(), nullable=False),
        pa.field("wastage_reason", pa.string(), nullable=False),
        pa.field("reported_by", pa.string(), nullable=True),
        pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
    ]
)

ARROW_SCHEMAS: dict[str, pa.Schema] = {
    "customers": CUSTOMERS_ARROW_SCHEMA,
    "restaurants": RESTAURANTS_ARROW_SCHEMA,
    "menu_categories": MENU_CATEGORIES_ARROW_SCHEMA,
    "menu_items": MENU_ITEMS_ARROW_SCHEMA,
    "pricing_history": PRICING_HISTORY_ARROW_SCHEMA,
    "promotions": PROMOTIONS_ARROW_SCHEMA,
    "orders": ORDERS_ARROW_SCHEMA,
    "order_items": ORDER_ITEMS_ARROW_SCHEMA,
    "ratings": RATINGS_ARROW_SCHEMA,
    "inventory": INVENTORY_ARROW_SCHEMA,
    "wastage": WASTAGE_ARROW_SCHEMA,
}

# -----------------------------------------------------------------------------
# Financial Definition Functions and Validators
# -----------------------------------------------------------------------------


def compute_line_net_revenue(
    quantity: int,
    unit_price_at_sale: float | Decimal,
    line_discount: float | Decimal = 0.0,
) -> float:
    """Calculate net revenue for an order item line.

    Formula:
        net_revenue = quantity * unit_price_at_sale - line_discount
    """
    qty = Decimal(str(quantity))
    price = Decimal(str(unit_price_at_sale))
    discount = Decimal(str(line_discount))
    net = (qty * price) - discount
    return float(round(net, 2))


def compute_line_contribution_margin(
    net_revenue: float | Decimal,
    quantity: int,
    unit_cost_at_sale: float | Decimal,
) -> float:
    """Calculate contribution margin for an order item line.

    Formula:
        contribution_margin = net_revenue - quantity * unit_cost_at_sale
    """
    net = Decimal(str(net_revenue))
    qty = Decimal(str(quantity))
    cost = Decimal(str(unit_cost_at_sale))
    margin = net - (qty * cost)
    return float(round(margin, 2))


def compute_order_total_amount(
    subtotal_amount: float | Decimal,
    discount_amount: float | Decimal,
    tax_amount: float | Decimal,
    tip_amount: float | Decimal,
) -> float:
    """Calculate total settlement amount for an order header.

    Formula:
        total_amount = subtotal_amount - discount_amount + tax_amount + tip_amount
    """
    subtotal = Decimal(str(subtotal_amount))
    discount = Decimal(str(discount_amount))
    tax = Decimal(str(tax_amount))
    tip = Decimal(str(tip_amount))
    total = subtotal - discount + tax + tip
    return float(round(total, 2))


def validate_source_identifier(entity_name: str, source_id: str) -> bool:
    """Verify that a business source identifier adheres to the canonical naming pattern."""
    pattern = SOURCE_ID_PATTERNS.get(entity_name)
    if not pattern:
        raise ValueError(f"Unknown entity name '{entity_name}' for source identifier validation.")
    return bool(pattern.match(source_id))


# -----------------------------------------------------------------------------
# Contract Validation Results
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ContractValidationResult:
    """Validation report containing status, inspected rows, and defect list."""

    is_valid: bool
    entity_name: str
    total_records: int
    defects: list[str]


def validate_arrow_table_schema(
    entity_name: str,
    table: pa.Table,
) -> ContractValidationResult:
    """Validate that a PyArrow table conforms to the contract schema for the given entity."""
    expected_schema = ARROW_SCHEMAS.get(entity_name)
    if not expected_schema:
        return ContractValidationResult(
            is_valid=False,
            entity_name=entity_name,
            total_records=table.num_rows if table is not None else 0,
            defects=[f"Unknown entity schema for '{entity_name}'"],
        )

    defects: list[str] = []
    total_records = table.num_rows

    expected_fields = {f.name: f for f in expected_schema}
    actual_fields = {f.name: f for f in table.schema}

    # Check for missing required fields
    for field_name, expected_field in expected_fields.items():
        if field_name not in actual_fields:
            defects.append(f"Missing required field: '{field_name}'")
        else:
            actual_field = actual_fields[field_name]
            if actual_field.type != expected_field.type:
                defects.append(
                    f"Field '{field_name}' type mismatch: expected {expected_field.type}, got {actual_field.type}"
                )
            if not expected_field.nullable and actual_field.nullable:
                # Check if there are actual nulls present
                null_count = table.column(field_name).null_count
                if null_count > 0:
                    defects.append(
                        f"Field '{field_name}' is non-nullable but contains {null_count} nulls"
                    )

    # Check for extra unexpected fields
    for field_name in actual_fields:
        if field_name not in expected_fields:
            defects.append(f"Unexpected extra field: '{field_name}'")

    return ContractValidationResult(
        is_valid=len(defects) == 0,
        entity_name=entity_name,
        total_records=total_records,
        defects=defects,
    )
