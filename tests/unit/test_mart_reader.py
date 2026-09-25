"""Unit tests for PyArrow based analytical mart scanner."""

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from packages.core.services.mart_reader import (
    MartNotFoundError,
    check_marts_availability,
    get_mart_metadata,
    read_mart_records,
)


def test_check_marts_availability_empty(monkeypatch, tmp_path):
    """Verify availability check correctly reports missing marts on empty disk."""
    monkeypatch.setattr("packages.core.services.mart_reader.get_marts_directory", lambda: tmp_path)
    status = check_marts_availability()
    assert status["marts_available"] is False
    assert status["spark_pipeline_marts"] is False
    assert status["python_pipeline_marts"] is False


def test_read_mart_records_and_metadata(monkeypatch, tmp_path):
    """Verify scanning precomputed Parquet files and extracting records."""
    monkeypatch.setattr("packages.core.services.mart_reader.get_marts_directory", lambda: tmp_path)

    spark_marts_dir = tmp_path / "spark"
    spark_marts_dir.mkdir(parents=True)
    sample_file = spark_marts_dir / "menu_profitability.parquet"

    # Create small test parquet file
    data = {
        "dish_name": ["Truffle Burger", "Margherita Pizza"],
        "net_revenue": [1250.00, 890.50],
        "contribution_margin": [650.00, 480.00],
    }
    table = pa.Table.from_pydict(data)
    pq.write_table(table, sample_file)

    # Check availability now detects the mart
    status = check_marts_availability()
    assert status["marts_available"] is True
    assert status["spark_pipeline_marts"] is True

    # Read records
    records = read_mart_records("spark/menu_profitability.parquet")
    assert len(records) == 2
    assert records[0]["dish_name"] == "Truffle Burger"
    assert records[0]["net_revenue"] == 1250.00

    # Read metadata
    metadata = get_mart_metadata("spark/menu_profitability.parquet")
    assert metadata["num_rows"] == 2
    assert metadata["num_columns"] == 3
    assert "dish_name" in metadata["column_names"]


def test_read_mart_missing_file_raises_error(monkeypatch, tmp_path):
    """Verify reading a nonexistent mart raises MartNotFoundError."""
    monkeypatch.setattr("packages.core.services.mart_reader.get_marts_directory", lambda: tmp_path)
    with pytest.raises(MartNotFoundError):
        read_mart_records("spark/nonexistent_mart.parquet")


def test_read_mart_path_traversal_prevention(monkeypatch, tmp_path):
    """Verify security guard prevents path traversal outside the marts directory."""
    monkeypatch.setattr("packages.core.services.mart_reader.get_marts_directory", lambda: tmp_path)
    with pytest.raises(ValueError) as exc_info:
        read_mart_records("../../etc/passwd")
    assert "traversal outside marts directory is prohibited" in str(exc_info.value)


def test_read_mart_sibling_directory_prefix_blocked(monkeypatch, tmp_path):
    """Verify sibling directory sharing prefix (e.g. marts_fake) is strictly rejected."""
    marts_dir = tmp_path / "marts"
    marts_dir.mkdir()
    sibling_fake = tmp_path / "marts_fake"
    sibling_fake.mkdir()
    sample_file = sibling_fake / "leak.parquet"
    table = pa.Table.from_pydict({"secret": [1, 2]})
    pq.write_table(table, sample_file)

    monkeypatch.setattr("packages.core.services.mart_reader.get_marts_directory", lambda: marts_dir)
    with pytest.raises(ValueError) as exc_info:
        read_mart_records("../marts_fake/leak.parquet")
    assert "traversal outside marts directory is prohibited" in str(exc_info.value)


def test_get_mart_metadata_path_traversal_blocked(monkeypatch, tmp_path):
    """Verify get_mart_metadata prevents path traversal and sibling prefix access."""
    marts_dir = tmp_path / "marts"
    marts_dir.mkdir()
    monkeypatch.setattr("packages.core.services.mart_reader.get_marts_directory", lambda: marts_dir)

    with pytest.raises(ValueError) as exc_info:
        get_mart_metadata("../../etc/shadow")
    assert "traversal outside marts directory is prohibited" in str(exc_info.value)

    with pytest.raises(ValueError) as exc_info:
        get_mart_metadata("../marts_fake/leak.parquet")
    assert "traversal outside marts directory is prohibited" in str(exc_info.value)
