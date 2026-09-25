"""Fast columnar analytical mart scanner using PyArrow."""

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from packages.common.logging import get_logger
from packages.core.config.settings import get_settings

logger = get_logger("dineiq.core.mart_reader")
settings = get_settings()


class MartNotFoundError(FileNotFoundError):
    """Raised when a requested precomputed analytical mart does not exist on disk."""

    pass


def get_marts_directory() -> Path:
    """Return the absolute Path object pointing to the marts base directory."""
    return Path(settings.MARTS_DIR).resolve()


def check_marts_availability() -> dict[str, Any]:
    """Inspect disk storage to verify presence and readiness of analytical marts."""
    base_dir = get_marts_directory()
    spark_mart_dir = base_dir / "spark"
    python_mart_dir = base_dir / "python"
    comparison_mart_dir = base_dir / "comparison"

    has_spark = spark_mart_dir.exists() and any(spark_mart_dir.glob("*.parquet"))
    has_python = python_mart_dir.exists() and any(python_mart_dir.glob("*.parquet"))
    has_comparison = comparison_mart_dir.exists() and any(comparison_mart_dir.glob("*.parquet"))

    return {
        "marts_available": has_spark or has_python or has_comparison,
        "spark_pipeline_marts": has_spark,
        "python_pipeline_marts": has_python,
        "comparison_marts": has_comparison,
        "marts_directory": str(base_dir),
    }


def read_mart_records(
    mart_relative_path: str,
    limit: int = 100,
    columns: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Scan a precomputed Parquet analytical mart and return records as dictionaries.

    Raises MartNotFoundError if the specified mart is missing.
    Does not scan the full 1M+ order lines; queries precomputed marts only.
    """
    base_dir = get_marts_directory()
    target_path = (base_dir / mart_relative_path).resolve()

    # Security check: ensure target path is strictly within the allowed marts directory
    if not target_path.is_relative_to(base_dir):
        raise ValueError("Invalid mart path: traversal outside marts directory is prohibited")

    if not target_path.exists():
        logger.info("Mart path not found: %s", target_path)
        raise MartNotFoundError(f"Analytical mart '{mart_relative_path}' is not yet precomputed")

    try:
        table = pq.read_table(target_path, columns=columns)
        if limit is not None and limit > 0:
            table = table.slice(0, limit)
        pydict = table.to_pydict()
        # Convert column oriented dict to list of row dicts
        keys = list(pydict.keys())
        if not keys:
            return []
        num_rows = len(pydict[keys[0]])
        rows = [{col: pydict[col][i] for col in keys} for i in range(num_rows)]
        return rows
    except Exception as exc:
        if isinstance(exc, MartNotFoundError):
            raise
        logger.exception("Failed reading Parquet mart %s: %s", target_path, exc)
        raise RuntimeError(f"Error reading analytical mart '{mart_relative_path}': {exc}") from exc


def get_mart_metadata(mart_relative_path: str) -> dict[str, Any]:
    """Retrieve schema and row metadata for a precomputed Parquet analytical mart."""
    base_dir = get_marts_directory()
    target_path = (base_dir / mart_relative_path).resolve()

    # Security check: ensure target path is strictly within the allowed marts directory
    if not target_path.is_relative_to(base_dir):
        raise ValueError("Invalid mart path: traversal outside marts directory is prohibited")

    if not target_path.exists():
        raise MartNotFoundError(f"Analytical mart '{mart_relative_path}' not found")

    parquet_file = pq.ParquetFile(target_path)
    metadata = parquet_file.metadata
    schema = parquet_file.schema

    return {
        "num_rows": metadata.num_rows,
        "num_columns": metadata.num_columns,
        "num_row_groups": metadata.num_row_groups,
        "serialized_size_bytes": metadata.serialized_size,
        "column_names": schema.names,
    }
