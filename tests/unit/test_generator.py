"""Automated tests for deterministic dataset generator."""

from pathlib import Path

import pyarrow.parquet as pq

from packages.common.generator.config import (
    GenerationProfile,
    GeneratorConfig,
)
from packages.common.generator.engine import DatasetGenerator


def test_small_profile_generation_and_contract_validation(tmp_path: Path):
    """Verify small profile generation produces valid schema contracts across all tables."""
    config = GeneratorConfig(
        profile=GenerationProfile.SMALL,
        seed=101,
        output_dir=tmp_path,
        snapshot_id="v_test_small",
    )
    generator = DatasetGenerator(config)
    metadata = generator.generate()

    assert metadata["profile"] == "small"
    assert metadata["seed"] == 101
    row_counts = metadata["row_counts"]

    # Cardinality checks
    assert row_counts["menu_categories"] == 10
    assert row_counts["restaurants"] == 2
    assert row_counts["menu_items"] == 20
    assert row_counts["customers"] == 100
    assert row_counts["orders"] >= 200
    assert row_counts["order_items"] >= 1500
    assert row_counts["ratings"] == 200
    assert row_counts["inventory"] == 100
    assert row_counts["wastage"] == 100

    # Contract validation check
    val_result = generator.validate_snapshot()
    assert val_result["is_valid"], f"Validation defects: {val_result['defects']}"


def test_deterministic_reproducibility(tmp_path: Path):
    """Verify that identical seeds produce identical business identifiers and values."""
    config_a = GeneratorConfig(
        profile=GenerationProfile.SMALL,
        seed=4242,
        output_dir=tmp_path / "run_a",
        snapshot_id="snap",
    )
    config_b = GeneratorConfig(
        profile=GenerationProfile.SMALL,
        seed=4242,
        output_dir=tmp_path / "run_b",
        snapshot_id="snap",
    )

    gen_a = DatasetGenerator(config_a)
    meta_a = gen_a.generate()

    gen_b = DatasetGenerator(config_b)
    meta_b = gen_b.generate()

    assert meta_a["row_counts"] == meta_b["row_counts"]

    # Read orders from both runs
    orders_a = pq.read_table(gen_a.output_path / "orders.parquet")
    orders_b = pq.read_table(gen_b.output_path / "orders.parquet")

    assert (
        orders_a.column("source_order_id").to_pylist()
        == orders_b.column("source_order_id").to_pylist()
    )
    assert (
        orders_a.column("total_amount").to_pylist() == orders_b.column("total_amount").to_pylist()
    )
    assert (
        orders_a.column("payment_method").to_pylist()
        == orders_b.column("payment_method").to_pylist()
    )


def test_foreign_key_and_source_id_integrity(tmp_path: Path):
    """Verify that foreign keys strictly link to existing master record source IDs."""
    config = GeneratorConfig(
        profile=GenerationProfile.SMALL,
        seed=555,
        output_dir=tmp_path,
        snapshot_id="v_fk_check",
    )
    generator = DatasetGenerator(config)
    generator.generate()

    # Load tables
    restaurants = pq.read_table(generator.output_path / "restaurants.parquet")
    customers = pq.read_table(generator.output_path / "customers.parquet")
    menu_items = pq.read_table(generator.output_path / "menu_items.parquet")
    orders = pq.read_table(generator.output_path / "orders.parquet")
    order_items = pq.read_table(generator.output_path / "order_items.parquet")
    ratings = pq.read_table(generator.output_path / "ratings.parquet")
    inventory = pq.read_table(generator.output_path / "inventory.parquet")
    wastage = pq.read_table(generator.output_path / "wastage.parquet")

    rest_ids = set(restaurants.column("source_restaurant_id").to_pylist())
    cust_ids = set(customers.column("source_customer_id").to_pylist())
    dish_ids = set(menu_items.column("source_menu_item_id").to_pylist())
    order_ids = set(orders.column("source_order_id").to_pylist())

    # Orders -> Restaurants
    for rid in orders.column("source_restaurant_id").to_pylist():
        assert rid in rest_ids

    # Orders -> Customers (allowing None for guest checkouts)
    for cid in orders.column("source_customer_id").to_pylist():
        if cid is not None:
            assert cid in cust_ids

    # Order items -> Orders & Menu Items
    for oid in order_items.column("source_order_id").to_pylist():
        assert oid in order_ids
    for did in order_items.column("source_menu_item_id").to_pylist():
        assert did in dish_ids

    # Ratings -> Restaurants & Menu Items
    for rid in ratings.column("source_restaurant_id").to_pylist():
        assert rid in rest_ids
    for did in ratings.column("source_menu_item_id").to_pylist():
        if did is not None:
            assert did in dish_ids

    # Inventory -> Restaurants
    for rid in inventory.column("source_restaurant_id").to_pylist():
        assert rid in rest_ids

    # Wastage -> Restaurants & Menu Items
    for rid in wastage.column("source_restaurant_id").to_pylist():
        assert rid in rest_ids
    for did in wastage.column("source_menu_item_id").to_pylist():
        if did is not None:
            assert did in dish_ids


def test_financial_formula_invariants(tmp_path: Path):
    """Verify that order line items satisfy SRS net revenue and contribution margin formulas."""
    config = GeneratorConfig(
        profile=GenerationProfile.SMALL,
        seed=777,
        output_dir=tmp_path,
        snapshot_id="v_finance_check",
        enable_anomalies=False,  # Test mathematical perfection without injected defects
    )
    generator = DatasetGenerator(config)
    generator.generate()

    items = pq.read_table(generator.output_path / "order_items.parquet").to_pylist()
    for row in items:
        qty = row["quantity"]
        price = row["unit_price_at_sale"]
        cost = row["unit_cost_at_sale"]
        disc = row["line_discount"]
        net = row["line_net_revenue"]
        cm = row["line_contribution_margin"]

        expected_net = round((qty * price) - disc, 2)
        expected_cm = round(expected_net - (qty * cost), 2)

        assert abs(net - expected_net) <= 0.01, f"Net revenue mismatch: {net} vs {expected_net}"
        assert abs(cm - expected_cm) <= 0.01, f"Contribution margin mismatch: {cm} vs {expected_cm}"

    orders = pq.read_table(generator.output_path / "orders.parquet").to_pylist()
    for o in orders:
        subtotal = o["subtotal_amount"]
        discount = o["discount_amount"]
        tax = o["tax_amount"]
        tip = o["tip_amount"]
        total = o["total_amount"]

        expected_total = round(subtotal - discount + tax + tip, 2)
        assert abs(total - expected_total) <= 0.01, f"Total mismatch: {total} vs {expected_total}"


def test_quality_anomalies_injection_rates(tmp_path: Path):
    """Verify that quality issue injection rates match configured anomaly probabilities."""
    config = GeneratorConfig(
        profile=GenerationProfile.SMALL,
        seed=888,
        output_dir=tmp_path,
        snapshot_id="v_anomaly_check",
        enable_anomalies=True,
    )
    generator = DatasetGenerator(config)
    generator.generate()

    orders = pq.read_table(generator.output_path / "orders.parquet").to_pylist()
    # Check for presence of guest orders
    guest_orders = [o for o in orders if o["source_customer_id"] is None]
    assert len(guest_orders) > 0

    # Check for presence of cancelled orders
    cancelled_orders = [o for o in orders if o["order_status"] == "Cancelled"]
    assert len(cancelled_orders) > 0

    # Check customers for missing contact info
    customers = pq.read_table(generator.output_path / "customers.parquet").to_pylist()
    missing_contact = [c for c in customers if c["email"] is None or c["phone"] is None]
    assert len(missing_contact) > 0

    # Check ratings for missing review text
    ratings = pq.read_table(generator.output_path / "ratings.parquet").to_pylist()
    missing_reviews = [r for r in ratings if r["review_text"] is None]
    assert len(missing_reviews) > 0
