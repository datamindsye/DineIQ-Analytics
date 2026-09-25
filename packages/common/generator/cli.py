"""Command Line Interface for the DineIQ deterministic dataset generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from packages.common.generator.config import GenerationProfile, GeneratorConfig
from packages.common.generator.engine import DatasetGenerator


def main() -> int:
    """CLI execution entrypoint."""
    parser = argparse.ArgumentParser(
        description="DineIQ Analytics Deterministic Synthetic Dataset Generator"
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="small",
        choices=["small", "medium", "competition"],
        help="Scale profile to generate (small, medium, competition)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation (default: 42)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/snapshots"),
        help="Destination directory for snapshot files (default: data/snapshots)",
    )
    parser.add_argument(
        "--snapshot-id",
        type=str,
        default=None,
        help="Explicit version/snapshot identifier directory name",
    )
    parser.add_argument(
        "--no-anomalies",
        action="store_true",
        help="Disable injection of realistic data quality defects and anomalies",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Perform automated contract validation on the generated snapshot",
    )

    args = parser.parse_args()

    profile = GenerationProfile(args.profile.lower())
    config = GeneratorConfig(
        profile=profile,
        seed=args.seed,
        output_dir=args.output_dir,
        snapshot_id=args.snapshot_id,
        enable_anomalies=not args.no_anomalies,
    )

    import tracemalloc

    tracemalloc.start()
    generator = DatasetGenerator(config)
    print(f"Generating DineIQ analytical dataset [{profile.value}] to {generator.output_path}...")
    metadata = generator.generate()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Calculate total size on disk
    total_bytes = sum(f.stat().st_size for f in generator.output_path.glob("*") if f.is_file())
    total_mb = total_bytes / (1024 * 1024)
    peak_mb = peak_mem / (1024 * 1024)

    print("\n--- Generation Summary ---")
    print(f"Snapshot ID: {metadata['snapshot_id']}")
    print(f"Duration:    {metadata['generation_duration_seconds']:.2f}s")
    print(f"Peak Memory: {peak_mb:.2f} MB")
    print(f"Output Size: {total_mb:.2f} MB ({total_bytes:,} bytes)")
    print("Row Counts:")
    for entity, count in metadata["row_counts"].items():
        print(f"  - {entity:20s}: {count:,}")

    if args.validate:
        print("\nValidating generated snapshot contracts...")
        val_result = generator.validate_snapshot()
        if val_result["is_valid"]:
            print("Validation PASSED: All 11 tables conform to PyArrow schema contracts.")
        else:
            print(f"Validation FAILED with {len(val_result['defects'])} defects:")
            for defect in val_result["defects"]:
                print(f"  * {defect}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
