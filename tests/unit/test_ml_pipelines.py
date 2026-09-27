"""Tests for Phase 4 Machine Learning pipelines (Python Scikit-Learn and Apache Spark MLlib).

Validates physical parquet mart creation, non-emptiness, schema conformance,
prediction ranges, and anti-leakage temporal split integrity.
"""

from pathlib import Path

import pyarrow.parquet as pq
import pytest

MARTS_PYTHON_DIR = Path("data/marts/python")
MARTS_SPARK_DIR = Path("data/marts/spark")

EXPECTED_ML_MARTS = [
    "ml_demand_forecast.parquet",
    "ml_wastage_risk.parquet",
    "ml_churn_risk.parquet",
    "ml_customer_segmentation.parquet",
]


@pytest.mark.parametrize("mart_file", EXPECTED_ML_MARTS)
def test_python_ml_marts_materialized(mart_file: str):
    """Verify that all 4 independent Python ML marts exist physically and are non-empty."""
    path = MARTS_PYTHON_DIR / mart_file
    assert path.exists(), f"Python ML mart {mart_file} does not exist at {path}"
    table = pq.read_table(path)
    assert table.num_rows > 0, f"Python ML mart {mart_file} has 0 rows"


@pytest.mark.parametrize("mart_file", EXPECTED_ML_MARTS)
def test_spark_ml_marts_materialized(mart_file: str):
    """Verify that all 4 Spark MLlib marts exist physically and are non-empty."""
    path = MARTS_SPARK_DIR / mart_file
    assert path.exists(), f"Spark ML mart {mart_file} does not exist at {path}"
    table = pq.read_table(path)
    assert table.num_rows > 0, f"Spark ML mart {mart_file} has 0 rows"


def test_python_demand_forecast_predictions():
    """Verify Python demand forecast schema, non-null predictions, and valid ranges."""
    table = pq.read_table(MARTS_PYTHON_DIR / "ml_demand_forecast.parquet")
    df = table.to_pandas()

    assert "predicted_quantity" in df.columns
    assert not df["predicted_quantity"].isna().any(), "Demand predictions contain null values"
    assert (df["predicted_quantity"] >= 0).all(), "Demand predictions should be non-negative"
    assert "split" in df.columns
    assert set(df["split"].unique()).issubset({"TRAIN", "VALIDATION", "TEST", "UNSEEN_COMPARISON"})


def test_spark_demand_forecast_predictions():
    """Verify Spark MLlib demand forecast predictions and schema."""
    table = pq.read_table(MARTS_SPARK_DIR / "ml_demand_forecast.parquet")
    df = table.to_pandas()

    assert "predicted_quantity" in df.columns
    assert not df["predicted_quantity"].isna().any(), "Spark demand predictions contain null values"
    assert "split" in df.columns
    assert set(df["split"].unique()).issubset({"TRAIN", "VALIDATION", "TEST", "UNSEEN_COMPARISON"})


def test_wastage_risk_probabilities_and_classes():
    """Verify wastage risk probabilities in [0, 1] and valid binary classes for both pipelines."""
    # Python
    py_table = pq.read_table(MARTS_PYTHON_DIR / "ml_wastage_risk.parquet")
    py_df = py_table.to_pandas()
    assert "predicted_label" in py_df.columns
    assert set(py_df["predicted_label"].dropna().unique()).issubset({0, 1})
    assert (py_df["risk_probability"] >= 0.0).all() and (py_df["risk_probability"] <= 1.0).all()

    # Spark
    spark_table = pq.read_table(MARTS_SPARK_DIR / "ml_wastage_risk.parquet")
    spark_df = spark_table.to_pandas()
    assert "predicted_label" in spark_df.columns
    assert set(spark_df["predicted_label"].dropna().unique()).issubset({0, 1})
    assert (spark_df["risk_probability"] >= 0.0).all() and (
        spark_df["risk_probability"] <= 1.0
    ).all()


def test_customer_segmentation_labels():
    """Verify customer segmentation clusters map to valid strategic business labels."""
    expected_segments = {"Champions", "Loyal", "At Risk", "Lost"}

    # Python
    py_table = pq.read_table(MARTS_PYTHON_DIR / "ml_customer_segmentation.parquet")
    py_df = py_table.to_pandas()
    assert "segment_label" in py_df.columns
    assert set(py_df["segment_label"].unique()).issubset(expected_segments)

    # Spark
    spark_table = pq.read_table(MARTS_SPARK_DIR / "ml_customer_segmentation.parquet")
    spark_df = spark_table.to_pandas()
    assert "segment_label" in spark_df.columns
    assert set(spark_df["segment_label"].unique()).issubset(expected_segments)


def test_temporal_anti_leakage_in_splits():
    """Verify strict chronological cutoff compliance (no future records in train split)."""
    table = pq.read_table(MARTS_PYTHON_DIR / "ml_demand_forecast.parquet")
    df = table.to_pandas()

    train_dates = df[df["split"] == "TRAIN"]["week_start_date"].astype(str)
    # Train should not contain dates later than 2025-08-31
    assert (train_dates <= "2025-08-31").all(), "Future leakage detected in TRAIN split!"
