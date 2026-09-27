"""Tests for Phase 4 Cross-Pipeline Comparison Engine and Evaluation contracts."""

import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

COMPARISON_DIR = Path("data/marts/comparison")

EXPECTED_COMPARISON_PARQUET = [
    "comparison_demand_forecast.parquet",
    "comparison_wastage_risk.parquet",
    "comparison_churn_risk.parquet",
    "comparison_customer_segmentation.parquet",
]


def test_comparison_overall_summary_exists_and_valid():
    """Verify that comparison_overall_summary.json exists and contains all required task sections."""
    summary_path = COMPARISON_DIR / "comparison_overall_summary.json"
    assert summary_path.exists(), "comparison_overall_summary.json was not generated"

    with open(summary_path, encoding="utf-8") as f:
        data = json.load(f)

    assert "overall_agreement_pct" in data
    assert 0.0 <= data["overall_agreement_pct"] <= 100.0

    tasks = ["demand_forecast", "wastage_risk", "churn_risk", "customer_segmentation"]
    for task in tasks:
        assert task in data, f"Task {task} missing from comparison summary"
        task_data = data[task]
        assert "agreement_pct" in task_data
        assert 0.0 <= task_data["agreement_pct"] <= 100.0


@pytest.mark.parametrize("parquet_name", EXPECTED_COMPARISON_PARQUET)
def test_comparison_parquet_marts_materialized(parquet_name: str):
    """Verify that all cross-pipeline comparison Parquet marts exist and have non-zero records."""
    file_path = COMPARISON_DIR / parquet_name
    assert file_path.exists(), f"Comparison Parquet {parquet_name} not found at {file_path}"
    table = pq.read_table(file_path)
    assert table.num_rows > 0, f"Comparison Parquet {parquet_name} is empty"


def test_comparison_segmentation_breakdown():
    """Verify customer segmentation agreement matrix is populated."""
    summary_path = COMPARISON_DIR / "comparison_customer_segmentation_summary.json"
    assert summary_path.exists(), "Customer segmentation summary missing"

    with open(summary_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_customers_compared"] == 50000
    assert "agreement_pct" in data
    assert "segment_agreement_breakdown" in data
    assert len(data["segment_agreement_breakdown"]) > 0
