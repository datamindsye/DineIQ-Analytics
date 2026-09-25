"""Unit tests for the Data Quality profiler, cleaning rules, and quarantine engine."""

from pathlib import Path

import pyarrow.parquet as pq

from packages.common.generator.config import (
    GenerationProfile,
    GeneratorConfig,
)
from packages.common.generator.engine import DatasetGenerator
from packages.common.quality.cleaner import DataQualityCleaner
from packages.common.quality.profiler import DataQualityProfiler


def test_data_quality_profiler_and_cleaner_workflow(tmp_path: Path):
    """Verify end to end profiling, anomaly detection, and quarantine isolation."""
    # 1. Generate a small dataset with anomalies enabled
    raw_dir = tmp_path / "raw"
    cleaned_dir = tmp_path / "cleaned"
    quarantine_dir = tmp_path / "quarantine"

    config = GeneratorConfig(
        profile=GenerationProfile.SMALL,
        seed=123,
        output_dir=raw_dir,
        snapshot_id="v_dq_test",
        enable_anomalies=True,
    )
    generator = DatasetGenerator(config)
    generator.generate()

    # 2. Run Data Quality Profiler
    profiler = DataQualityProfiler(generator.output_path)
    profile_report = profiler.profile_all()

    assert profile_report["snapshot_id"] == "v_dq_test"
    table_profiles = profile_report["table_profiles"]

    # Verify orders profiling metrics
    orders_prof = table_profiles["orders"]
    assert orders_prof["guest_orders_count"] > 0
    assert "Cancelled" in orders_prof["status_breakdown"]
    assert orders_prof["duplicate_source_ids"] >= 0

    # Verify order items profiling metrics
    items_prof = table_profiles["order_items"]
    assert items_prof["row_count"] >= 1500
    assert items_prof["duplicate_source_ids"] >= 0

    # Verify referential integrity
    ref_integrity = profile_report["referential_integrity"]
    assert ref_integrity["orders_to_restaurants"]["is_clean"]
    assert ref_integrity["order_items_to_orders"]["is_clean"]

    # 3. Run Data Quality Cleaner
    cleaner = DataQualityCleaner(
        snapshot_dir=generator.output_path,
        cleaned_dir=cleaned_dir,
        quarantine_dir=quarantine_dir,
    )
    clean_report = cleaner.clean_and_quarantine()

    assert clean_report["overall_status"] in ("PASSED_WITH_QUARANTINE", "CLEAN")
    assert clean_report["totals"]["cleaned_records_output"] > 0

    # Check clean output files exist
    clean_snapshot_path = Path(clean_report["cleaned_output_path"])
    assert (clean_snapshot_path / "orders.parquet").exists()
    assert (clean_snapshot_path / "order_items.parquet").exists()
    assert (clean_snapshot_path / "quality_report.json").exists()
    assert (clean_snapshot_path / "split_manifest.json").exists()

    # Verify clean order items have no duplicate source IDs and no negative prices
    clean_items = pq.read_table(clean_snapshot_path / "order_items.parquet")
    clean_item_ids = clean_items.column("source_order_item_id").to_pylist()
    assert len(clean_item_ids) == len(set(clean_item_ids)), "Clean table must have no duplicate IDs"

    prices = clean_items.column("unit_price_at_sale").to_pylist()
    assert all(p >= 0.0 for p in prices), "Clean table must have no negative prices"

    quantities = clean_items.column("quantity").to_pylist()
    assert all(q > 0 for q in quantities), "Clean table must have no zero quantities"

    # Verify clean orders have no future timestamps
    clean_orders = pq.read_table(clean_snapshot_path / "orders.parquet")
    timestamps = clean_orders.column("order_timestamp").to_pylist()
    assert all(ts.year <= 2025 for ts in timestamps), "Clean orders must have no future timestamps"


def test_quarantine_metadata_and_reasons(tmp_path: Path):
    """Verify quarantined records carry quarantine_reason and quarantined_at timestamps."""
    raw_dir = tmp_path / "raw"
    cleaned_dir = tmp_path / "cleaned"
    quarantine_dir = tmp_path / "quarantine"

    config = GeneratorConfig(
        profile=GenerationProfile.SMALL,
        seed=456,
        output_dir=raw_dir,
        snapshot_id="v_q_meta",
        enable_anomalies=True,
    )
    generator = DatasetGenerator(config)
    generator.generate()

    cleaner = DataQualityCleaner(
        snapshot_dir=generator.output_path,
        cleaned_dir=cleaned_dir,
        quarantine_dir=quarantine_dir,
    )
    clean_report = cleaner.clean_and_quarantine()

    quarantine_path = Path(clean_report["quarantine_output_path"])
    if (quarantine_path / "order_items_quarantine.parquet").exists():
        q_table = pq.read_table(quarantine_path / "order_items_quarantine.parquet")
        assert "quarantine_reason" in q_table.column_names
        assert "quarantined_at" in q_table.column_names
        reasons = q_table.column("quarantine_reason").to_pylist()
        valid_reasons = {
            "DUPLICATE_ORDER_ITEM_ID",
            "INVALID_NEGATIVE_PRICE",
            "INVALID_ZERO_QUANTITY",
            "ORPHANED_ORDER_PARENT",
            "ORPHANED_MENU_ITEM",
        }
        assert all(r in valid_reasons for r in reasons)
