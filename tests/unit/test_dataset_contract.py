"""Unit tests for analytical dataset contracts and PyArrow schemas."""

from datetime import datetime, timezone

import pyarrow as pa
import pytest

from packages.core.contracts.dataset_contract import (
    CANONICAL_CATEGORIES,
    CHANNELS,
    CUSTOMERS_ARROW_SCHEMA,
    DINING_TYPES,
    DISCOUNT_TYPES,
    INGREDIENT_CATEGORIES,
    INVENTORY_ARROW_SCHEMA,
    LOYALTY_TIERS,
    MENU_CATEGORIES_ARROW_SCHEMA,
    MENU_ITEMS_ARROW_SCHEMA,
    ORDER_ITEMS_ARROW_SCHEMA,
    ORDER_STATUSES,
    ORDERS_ARROW_SCHEMA,
    PAYMENT_METHODS,
    PRICING_HISTORY_ARROW_SCHEMA,
    PROMOTIONS_ARROW_SCHEMA,
    RATINGS_ARROW_SCHEMA,
    RESTAURANTS_ARROW_SCHEMA,
    UNITS_OF_MEASURE,
    WASTAGE_ARROW_SCHEMA,
    WASTAGE_REASONS,
    compute_line_contribution_margin,
    compute_line_net_revenue,
    compute_order_total_amount,
    validate_arrow_table_schema,
    validate_source_identifier,
)
from tests.fixtures.sample_domain_data import (
    get_sample_categories_data,
    get_sample_customers_data,
    get_sample_inventory_data,
    get_sample_menu_items_data,
    get_sample_order_items_data,
    get_sample_orders_data,
    get_sample_pricing_history_data,
    get_sample_promotions_data,
    get_sample_ratings_data,
    get_sample_restaurants_data,
    get_sample_wastage_data,
)


def test_source_id_patterns_matching():
    """Verify that source ID patterns accept canonical formats and reject malformed ones."""
    valid_ids = {
        "customers": "CUST-00042851",
        "restaurants": "REST-0012",
        "menu_categories": "CAT-005",
        "menu_items": "DISH-0142",
        "pricing_history": "PRC-000842",
        "promotions": "PROMO-0018",
        "orders": "ORD-00084920",
        "order_items": "ITEM-00948214",
        "ratings": "RAT-00078491",
        "inventory": "INV-REST01-0084",
        "wastage": "WASTE-00049182",
    }

    for entity_name, valid_id in valid_ids.items():
        assert validate_source_identifier(entity_name, valid_id), (
            f"Failed for {entity_name}: {valid_id}"
        )

    invalid_ids = {
        "customers": "CUST-42851",  # Not 8 digits
        "restaurants": "REST-1",  # Not 4 digits
        "menu_categories": "CATEGORY-01",  # Wrong prefix
        "menu_items": "DISH-ABC",  # Non digits
        "pricing_history": "PRC-1234",  # Not 6 digits
        "promotions": "PROMO-123",  # Not 4 digits
        "orders": "ORD-12345",  # Not 8 digits
        "order_items": "ITEM-123",  # Not 8 digits
        "ratings": "RATING-00000001",  # Wrong prefix
        "inventory": "INV-001",  # Missing REST branch code
        "wastage": "WASTE-999",  # Not 8 digits
    }

    for entity_name, invalid_id in invalid_ids.items():
        assert not validate_source_identifier(entity_name, invalid_id), (
            f"Should fail for {entity_name}: {invalid_id}"
        )

    with pytest.raises(ValueError):
        validate_source_identifier("non_existent_table", "FOO-123")


def test_domain_enumerations_contain_authoritative_values():
    """Verify that standard enumerations match SRS definitions."""
    assert "Bronze" in LOYALTY_TIERS
    assert "Platinum" in LOYALTY_TIERS
    assert "None" in LOYALTY_TIERS

    assert "Fast Casual" in DINING_TYPES
    assert "Fine Dining" in DINING_TYPES

    assert "Dine-in" in CHANNELS
    assert "Delivery Aggregator" in CHANNELS

    assert "Completed" in ORDER_STATUSES
    assert "Cancelled" in ORDER_STATUSES

    assert "Credit Card" in PAYMENT_METHODS
    assert "Digital Wallet" in PAYMENT_METHODS

    assert "Percentage" in DISCOUNT_TYPES
    assert "Fixed Amount" in DISCOUNT_TYPES

    assert len(CANONICAL_CATEGORIES) == 10
    assert "Appetizers" in CANONICAL_CATEGORIES
    assert "Chef Specials" in CANONICAL_CATEGORIES

    assert "Produce" in INGREDIENT_CATEGORIES
    assert "Meat & Poultry" in INGREDIENT_CATEGORIES

    assert "kg" in UNITS_OF_MEASURE
    assert "Expired" in WASTAGE_REASONS
    assert "Cooking Error" in WASTAGE_REASONS


def test_financial_formulas_calculation():
    """Verify net revenue and contribution margin calculations match exact SRS specs."""
    # Standard line: 2 burgers at $18.00, $6.50 cost, $3.00 coupon
    # net_revenue = (2 * 18.00) - 3.00 = 33.00
    # contribution_margin = 33.00 - (2 * 6.50) = 33.00 - 13.00 = 20.00
    net_rev = compute_line_net_revenue(quantity=2, unit_price_at_sale=18.00, line_discount=3.00)
    assert net_rev == 33.00

    margin = compute_line_contribution_margin(
        net_revenue=net_rev, quantity=2, unit_cost_at_sale=6.50
    )
    assert margin == 20.00

    # Promo trap scenario: 50% discount on expensive dish resulting in thin margin
    # net_revenue = (1 * 18.00) - 12.00 = 6.00
    # contribution_margin = 6.00 - (1 * 6.50) = -0.50 (negative margin trap!)
    trap_net = compute_line_net_revenue(quantity=1, unit_price_at_sale=18.00, line_discount=12.00)
    assert trap_net == 6.00
    trap_margin = compute_line_contribution_margin(
        net_revenue=trap_net, quantity=1, unit_cost_at_sale=6.50
    )
    assert trap_margin == -0.50

    # Order header settlement total formula:
    # total_amount = subtotal - discount + tax + tip
    total = compute_order_total_amount(
        subtotal_amount=50.00,
        discount_amount=5.00,
        tax_amount=4.50,
        tip_amount=8.00,
    )
    assert total == 57.50


def test_arrow_table_schema_validation_success():
    """Verify PyArrow table schema validation for customers table."""
    sample_customers = get_sample_customers_data()
    table = pa.Table.from_pylist(sample_customers, schema=CUSTOMERS_ARROW_SCHEMA)

    result = validate_arrow_table_schema("customers", table)
    assert result.is_valid
    assert result.total_records == 3
    assert len(result.defects) == 0


def test_arrow_table_schema_validation_detects_missing_field():
    """Verify that validator detects missing required fields."""
    incomplete_schema = pa.schema(
        [
            pa.field("source_customer_id", pa.string(), nullable=False),
            pa.field("first_name", pa.string(), nullable=True),
        ]
    )
    table = pa.Table.from_arrays(
        [pa.array(["CUST-00000001"]), pa.array(["Alice"])],
        schema=incomplete_schema,
    )

    result = validate_arrow_table_schema("customers", table)
    assert not result.is_valid
    assert any("Missing required field" in defect for defect in result.defects)


def test_arrow_table_schema_validation_detects_type_mismatch():
    """Verify that validator detects data type mismatches."""
    wrong_type_schema = pa.schema(
        [
            pa.field("source_customer_id", pa.string(), nullable=False),
            pa.field("first_name", pa.string(), nullable=True),
            pa.field("last_name", pa.string(), nullable=True),
            pa.field("email", pa.string(), nullable=True),
            pa.field("phone", pa.string(), nullable=True),
            pa.field("registration_date", pa.string(), nullable=False),  # String instead of date32!
            pa.field("loyalty_tier", pa.string(), nullable=False),
            pa.field("preferred_channel", pa.string(), nullable=True),
            pa.field("home_city", pa.string(), nullable=True),
            pa.field("is_active", pa.bool_(), nullable=False),
            pa.field("created_at", pa.timestamp("us", tz="UTC"), nullable=False),
        ]
    )

    table = pa.Table.from_pydict(
        {
            "source_customer_id": ["CUST-00000001"],
            "first_name": ["Alice"],
            "last_name": ["Johnson"],
            "email": ["alice@example.com"],
            "phone": ["3125550101"],
            "registration_date": ["2024-03-10"],
            "loyalty_tier": ["Gold"],
            "preferred_channel": ["Dine-in"],
            "home_city": ["Chicago"],
            "is_active": [True],
            "created_at": [datetime(2024, 3, 10, 10, 0, 0, tzinfo=timezone.utc)],
        },
        schema=wrong_type_schema,
    )

    result = validate_arrow_table_schema("customers", table)
    assert not result.is_valid
    assert any("type mismatch" in defect for defect in result.defects)


def test_arrow_all_eleven_tables_sample_schema_conformance():
    """Verify that the sample dataset conforms to all 11 PyArrow schemas."""
    sample_data_loaders = {
        "menu_categories": (MENU_CATEGORIES_ARROW_SCHEMA, get_sample_categories_data()),
        "restaurants": (RESTAURANTS_ARROW_SCHEMA, get_sample_restaurants_data()),
        "menu_items": (MENU_ITEMS_ARROW_SCHEMA, get_sample_menu_items_data()),
        "pricing_history": (PRICING_HISTORY_ARROW_SCHEMA, get_sample_pricing_history_data()),
        "promotions": (PROMOTIONS_ARROW_SCHEMA, get_sample_promotions_data()),
        "customers": (CUSTOMERS_ARROW_SCHEMA, get_sample_customers_data()),
        "orders": (ORDERS_ARROW_SCHEMA, get_sample_orders_data()),
        "order_items": (ORDER_ITEMS_ARROW_SCHEMA, get_sample_order_items_data()),
        "ratings": (RATINGS_ARROW_SCHEMA, get_sample_ratings_data()),
        "inventory": (INVENTORY_ARROW_SCHEMA, get_sample_inventory_data()),
        "wastage": (WASTAGE_ARROW_SCHEMA, get_sample_wastage_data()),
    }

    for entity_name, (arrow_schema, sample_records) in sample_data_loaders.items():
        table = pa.Table.from_pylist(sample_records, schema=arrow_schema)
        result = validate_arrow_table_schema(entity_name, table)
        assert result.is_valid, f"Validation failed for {entity_name}: {result.defects}"
        assert result.total_records == len(sample_records)
