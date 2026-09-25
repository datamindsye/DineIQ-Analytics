"""Unit tests for business domain SQLAlchemy models, relationships, and constraints."""

from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from packages.db.models.domain import (
    Customer,
    Inventory,
    MenuCategory,
    MenuItem,
    Order,
    Rating,
    Restaurant,
    Wastage,
)
from tests.fixtures.sample_domain_data import seed_domain_sample_into_db


def test_seed_domain_sample_and_relationships(db_session: Session):
    """Verify that all 11 tables can be seeded into the database and relationships resolve."""
    counts = seed_domain_sample_into_db(db_session)

    assert counts["menu_categories"] == 3
    assert counts["restaurants"] == 2
    assert counts["menu_items"] == 4
    assert counts["pricing_history"] == 3
    assert counts["promotions"] == 2
    assert counts["customers"] == 3
    assert counts["orders"] == 4
    assert counts["order_items"] == 5
    assert counts["ratings"] == 3
    assert counts["inventory"] == 3
    assert counts["wastage"] == 3

    # Query customer with order relationships
    alice = db_session.execute(
        select(Customer).where(Customer.source_customer_id == "CUST-00000001")
    ).scalar_one()
    assert alice.first_name == "Alice"
    assert alice.loyalty_tier == "Gold"
    assert len(alice.orders) == 2  # Order 1 and Order 4

    # Query restaurant and its orders
    chicago_rest = db_session.execute(
        select(Restaurant).where(Restaurant.source_restaurant_id == "REST-0001")
    ).scalar_one()
    assert chicago_rest.city == "Chicago"
    assert len(chicago_rest.orders) == 3  # Orders 1, 3, 4
    assert len(chicago_rest.inventory_items) == 2
    assert len(chicago_rest.wastage_records) == 2


def test_guest_checkout_order_null_customer(db_session: Session):
    """Verify that guest orders with null customer_id persist cleanly without foreign key error."""
    seed_domain_sample_into_db(db_session)

    guest_order = db_session.execute(
        select(Order).where(Order.source_order_id == "ORD-00000002")
    ).scalar_one()

    assert guest_order.customer_id is None
    assert guest_order.customer is None
    assert guest_order.order_channel == "Takeaway"
    assert guest_order.total_amount == 16.50
    assert len(guest_order.items) == 1
    assert guest_order.items[0].menu_item.item_name == "Margherita Pizza"


def test_cancelled_order_and_financial_capture(db_session: Session):
    """Verify that cancelled orders retain point-in-time financial amounts."""
    seed_domain_sample_into_db(db_session)

    cancelled_order = db_session.execute(
        select(Order).where(Order.source_order_id == "ORD-00000003")
    ).scalar_one()

    assert cancelled_order.order_status == "Cancelled"
    assert cancelled_order.subtotal_amount == 18.00
    assert len(cancelled_order.items) == 1
    item = cancelled_order.items[0]
    assert item.unit_price_at_sale == 18.00
    assert item.unit_cost_at_sale == 6.50
    assert item.line_net_revenue == 18.00
    assert item.line_contribution_margin == 11.50


def test_scd_type_2_pricing_history(db_session: Session):
    """Verify Slowly Changing Dimension Type 2 price tracking queries."""
    seed_domain_sample_into_db(db_session)

    wagyu_burger = db_session.execute(
        select(MenuItem).where(MenuItem.source_menu_item_id == "DISH-0002")
    ).scalar_one()

    assert len(wagyu_burger.pricing_history) == 2

    # Check historical record
    historical_price = [p for p in wagyu_burger.pricing_history if p.effective_to is not None][0]
    assert historical_price.base_price == 16.50
    assert historical_price.change_reason == "Initial introductory launch pricing"

    # Check active record
    active_price = [p for p in wagyu_burger.pricing_history if p.effective_to is None][0]
    assert active_price.base_price == 18.00
    assert active_price.base_cost == 6.50


def test_ratings_constraints_and_reviews(db_session: Session):
    """Verify rating scores and optional review links."""
    seed_domain_sample_into_db(db_session)

    # Verified rating with full breakdown
    r1 = db_session.execute(
        select(Rating).where(Rating.source_rating_id == "RAT-00000001")
    ).scalar_one()
    assert r1.is_verified_purchase is True
    assert r1.rating_score == 5
    assert r1.food_rating == 5
    assert r1.menu_item.item_name == "Wagyu Burger"

    # Unverified walk-in rating
    r3 = db_session.execute(
        select(Rating).where(Rating.source_rating_id == "RAT-00000003")
    ).scalar_one()
    assert r3.is_verified_purchase is False
    assert r3.order_id is None
    assert r3.rating_score == 2


def test_inventory_and_wastage_tracking(db_session: Session):
    """Verify restaurant inventory thresholds and recorded waste losses."""
    seed_domain_sample_into_db(db_session)

    wagyu_inv = db_session.execute(
        select(Inventory).where(Inventory.source_inventory_id == "INV-REST01-0001")
    ).scalar_one()
    assert wagyu_inv.current_stock_quantity == 45.50
    assert wagyu_inv.reorder_threshold == 15.00
    assert wagyu_inv.unit_purchase_cost == 12.50

    # Query equipment failure wastage
    cooler_failure = db_session.execute(
        select(Wastage).where(Wastage.source_wastage_id == "WASTE-00000002")
    ).scalar_one()
    assert cooler_failure.wastage_reason == "Equipment Failure"
    assert cooler_failure.cost_loss_amount == 50.00
    assert cooler_failure.quantity_lost == 4.00


def test_check_constraint_invalid_rating_score(db_session: Session):
    """Verify check constraint enforces rating scores between 1 and 5."""
    seed_domain_sample_into_db(db_session)

    rest = db_session.execute(select(Restaurant)).scalars().first()
    invalid_rating = Rating(
        source_rating_id="RAT-99999999",
        restaurant_id=rest.id,
        rating_score=6,  # Invalid: score > 5
        rating_timestamp=datetime.now(timezone.utc),
    )
    db_session.add(invalid_rating)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_check_constraint_negative_price(db_session: Session):
    """Verify check constraint rejects negative menu item base prices."""
    seed_domain_sample_into_db(db_session)
    cat = db_session.execute(select(MenuCategory)).scalars().first()
    invalid_item = MenuItem(
        source_menu_item_id="DISH-9999",
        category_id=cat.id,
        item_name="Negative Item",
        current_base_price=-5.00,  # Invalid: negative price
        current_base_cost=2.00,
    )
    db_session.add(invalid_item)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_check_constraint_invalid_loyalty_tier(db_session: Session):
    """Verify check constraint rejects unsupported loyalty tiers."""
    invalid_cust = Customer(
        source_customer_id="CUST-99999999",
        registration_date=date(2025, 1, 1),
        loyalty_tier="DiamondVIP",  # Invalid tier
    )
    db_session.add(invalid_cust)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
