"""Command line interface for data quality profiling and cleaning."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from packages.common.quality.cleaner import DataQualityCleaner
from packages.common.quality.profiler import DataQualityProfiler


def main() -> int:
    """CLI execution entrypoint for Data Quality profiling and cleaning."""
    parser = argparse.ArgumentParser(
        description="DineIQ Analytics Data Quality Profiler and Cleaner"
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        required=True,
        help="Path to the raw snapshot directory to profile and clean",
    )
    parser.add_argument(
        "--cleaned-dir",
        type=Path,
        default=Path("data/cleaned"),
        help="Destination directory for cleaned Parquet tables (default: data/cleaned)",
    )
    parser.add_argument(
        "--quarantine-dir",
        type=Path,
        default=Path("data/quarantine"),
        help="Destination directory for quarantined defective records (default: data/quarantine)",
    )
    parser.add_argument(
        "--profile-only",
        action="store_true",
        help="Run data profiling without executing quarantine and cleaning export",
    )

    args = parser.parse_args()

    print(f"Profiling raw snapshot at {args.snapshot_dir}...")
    profiler = DataQualityProfiler(args.snapshot_dir)
    profile_report = profiler.profile_all()

    print("\n--- Data Quality Profiling Summary ---")
    print(f"Snapshot ID: {profile_report['snapshot_id']}")
    print("Table Row Counts and Duplicates:")
    for entity, prof in profile_report["table_profiles"].items():
        dups = prof.get("duplicate_source_ids", 0)
        print(f"  - {entity:20s}: {prof['row_count']:,} rows (duplicates: {dups:,})")

    # Specific Anomaly Detections
    orders_prof = profile_report["table_profiles"].get("orders", {})
    if orders_prof:
        print("\nOrders Health:")
        print(
            f"  - Guest checkouts:    {orders_prof.get('guest_orders_count', 0):,} ({orders_prof.get('guest_orders_pct', 0)}%)"
        )
        print(f"  - Cancelled/Voided:   {orders_prof.get('status_breakdown', {})}")
        print(f"  - Future timestamps:  {orders_prof.get('future_timestamp_count', 0):,}")
        print(f"  - Formula mismatches: {orders_prof.get('financial_formula_discrepancies', 0):,}")

    items_prof = profile_report["table_profiles"].get("order_items", {})
    if items_prof:
        print("\nOrder Items Health:")
        print(f"  - Negative prices:    {items_prof.get('negative_price_count', 0):,}")
        print(f"  - Zero quantities:    {items_prof.get('zero_quantity_count', 0):,}")
        print(
            f"  - Promotion traps:    {items_prof.get('promotion_trap_negative_margin_count', 0):,} lines"
        )

    print("\nReferential Integrity Checks:")
    for fk_name, fk_info in profile_report.get("referential_integrity", {}).items():
        status = (
            "PASSED" if fk_info["is_clean"] else f"FAILED ({fk_info['orphaned_count']} orphaned)"
        )
        print(f"  - {fk_name:30s}: {status}")

    if args.profile_only:
        return 0

    print(f"\nExecuting quarantine and cleaning to {args.cleaned_dir}...")
    cleaner = DataQualityCleaner(
        snapshot_dir=args.snapshot_dir,
        cleaned_dir=args.cleaned_dir,
        quarantine_dir=args.quarantine_dir,
    )
    clean_report = cleaner.clean_and_quarantine()

    print("\n--- Cleaning and Quarantine Results ---")
    print(f"Status:             {clean_report['overall_status']}")
    print(f"Raw Processed:      {clean_report['totals']['raw_records_processed']:,}")
    print(f"Cleaned Output:     {clean_report['totals']['cleaned_records_output']:,}")
    print(f"Quarantined:        {clean_report['totals']['quarantined_records_isolated']:,}")
    print(f"Cleanliness Rate:   {clean_report['totals']['cleanliness_rate_pct']:.3f}%")
    print(f"Clean Output Path:  {clean_report['cleaned_output_path']}")
    print(f"Quarantine Path:    {clean_report['quarantine_output_path']}")

    print("\nQuarantine Reasons Breakdown:")
    for entity, reasons in clean_report.get("quarantine_reasons", {}).items():
        if reasons:
            print(f"  [{entity}]")
            for reason, cnt in reasons.items():
                print(f"    * {reason:30s}: {cnt:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
