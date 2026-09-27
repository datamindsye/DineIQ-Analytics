"""CleanDataLoader for ingesting immutable cleaned Parquet datasets.

Loads and validates clean Parquet snapshots into Spark DataFrames with schema conformance.
Provides columnar PyArrow fallback when running in non-Spark environments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from packages.common.logging import get_logger
from packages.pipeline_spark.schemas import CLEANED_TABLE_NAMES, get_spark_table_schemas
from packages.pipeline_spark.session import get_spark_session, is_spark_available

logger = get_logger(__name__)


class SnapshotNotFoundError(FileNotFoundError):
    """Raised when the specified clean Parquet snapshot directory does not exist."""

    pass


class CleanDataLoader:
    """Ingestion loader and schema validator for cleaned competition benchmark snapshots."""

    def __init__(
        self,
        snapshot_dir: str | Path = "data/cleaned/competition_benchmark_v1",
        spark: Any | None = None,
    ) -> None:
        self.snapshot_path = Path(snapshot_dir).resolve()
        if not self.snapshot_path.exists():
            raise SnapshotNotFoundError(f"Clean snapshot directory not found: {self.snapshot_path}")

        self.spark = spark
        if self.spark is None and is_spark_available():
            self.spark = get_spark_session()

        self._spark_schemas = get_spark_table_schemas()

    def validate_snapshot_completeness(self) -> dict[str, bool]:
        """Verify that all eleven required domain Parquet files exist in the snapshot."""
        completeness = {}
        for table_name in CLEANED_TABLE_NAMES:
            table_file = self.snapshot_path / f"{table_name}.parquet"
            completeness[table_name] = table_file.exists() and table_file.is_file()
        return completeness

    def load_table_spark(self, table_name: str) -> Any:
        """Load a single clean table as a PySpark DataFrame with strict schema enforcement.

        Raises RuntimeError if PySpark is not available.
        """
        if not is_spark_available() or self.spark is None:
            raise RuntimeError(
                f"PySpark is not available. Cannot load {table_name} as Spark DataFrame."
            )

        table_file = self.snapshot_path / f"{table_name}.parquet"
        if not table_file.exists():
            raise FileNotFoundError(f"Table file not found: {table_file}")

        schema = self._spark_schemas.get(table_name)
        reader = self.spark.read.format("parquet")
        if schema is not None:
            reader = reader.schema(schema)

        df = reader.load(str(table_file))
        logger.info("Loaded Spark DataFrame for table '%s' from %s", table_name, table_file)
        return df

    def load_table_arrow(self, table_name: str) -> Any:
        """Load a single clean table as a PyArrow Table."""
        table_file = self.snapshot_path / f"{table_name}.parquet"
        if not table_file.exists():
            raise FileNotFoundError(f"Table file not found: {table_file}")

        table = pq.read_table(table_file)
        logger.info(
            "Loaded PyArrow Table for '%s' (%d rows, %d cols)",
            table_name,
            table.num_rows,
            table.num_columns,
        )
        return table

    def load_all_spark(self) -> dict[str, Any]:
        """Load all eleven clean domain tables into a dictionary of PySpark DataFrames."""
        dfs = {}
        for table_name in CLEANED_TABLE_NAMES:
            dfs[table_name] = self.load_table_spark(table_name)
        return dfs

    def load_all_arrow(self) -> dict[str, Any]:
        """Load all eleven clean domain tables into a dictionary of PyArrow Tables."""
        tables = {}
        for table_name in CLEANED_TABLE_NAMES:
            tables[table_name] = self.load_table_arrow(table_name)
        return tables
