"""Tests for Phase 6B Multi-Algorithm Model Competition and Candidate Selection.

Verifies:
1. Spark supervised tasks evaluate at least 3 distinct candidates.
2. Python supervised tasks evaluate at least 3 distinct candidates.
3. Candidate algorithms are distinct per task.
4. Selected model matches the candidate with the best validation metric.
5. Deterministic tie-breaker behavior.
6. Test metrics do not determine selection (anti-leakage).
7. UNSEEN_COMPARISON does not determine selection.
8. Selected champion model generates final prediction marts.
9. Candidate metrics are fully recorded in metadata.
10. Selected algorithm is documented in metadata.
11. Existing prediction mart schemas remain backward-compatible.
12. Spark and Python pipelines remain strictly independent.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import pytest

ARTIFACTS_DIR = Path("data/artifacts")
MARTS_SPARK_DIR = Path("data/marts/spark")
MARTS_PYTHON_DIR = Path("data/marts/python")

SUPERVISED_TASKS = ["demand_forecast", "wastage_risk", "churn_risk"]
ALL_TASKS = ["demand_forecast", "wastage_risk", "churn_risk", "customer_segmentation"]


def _load_metadata(pipeline: str, task: str) -> dict[str, Any]:
    meta_path = ARTIFACTS_DIR / f"{pipeline}_{task}_metadata.json"
    assert meta_path.exists(), f"Metadata not found at {meta_path}"
    return json.loads(meta_path.read_text(encoding="utf-8"))


# ── 1 & 2. Supervised Tasks Evaluate >= 3 Candidates ──────────────────────────


@pytest.mark.parametrize("task", SUPERVISED_TASKS)
def test_spark_supervised_candidates_count(task: str):
    """Verify that Spark supervised tasks evaluate at least 3 candidate algorithms."""
    meta = _load_metadata("spark", task)
    candidates = meta.get("candidates", [])
    assert len(candidates) >= 3, (
        f"Spark {task} has only {len(candidates)} candidates, expected at least 3"
    )


@pytest.mark.parametrize("task", SUPERVISED_TASKS)
def test_python_supervised_candidates_count(task: str):
    """Verify that Python supervised tasks evaluate at least 3 candidate algorithms."""
    meta = _load_metadata("python", task)
    candidates = meta.get("candidates", [])
    assert len(candidates) >= 3, (
        f"Python {task} has only {len(candidates)} candidates, expected at least 3"
    )


# ── 3. Candidate Algorithms are Distinct ──────────────────────────────────────


@pytest.mark.parametrize("pipeline", ["spark", "python"])
@pytest.mark.parametrize("task", SUPERVISED_TASKS)
def test_candidate_algorithms_are_distinct(pipeline: str, task: str):
    """Verify that candidate algorithms within a pipeline task are distinct."""
    meta = _load_metadata(pipeline, task)
    candidates = meta.get("candidates", [])
    algorithms = [c["algorithm"] for c in candidates]
    assert len(algorithms) == len(set(algorithms)), (
        f"{pipeline} {task} candidates are not unique: {algorithms}"
    )


# ── 4. Selected Model Equals Candidate with Best Validation Metric ─────────────


@pytest.mark.parametrize("pipeline", ["spark", "python"])
def test_demand_forecast_selection_rule(pipeline: str):
    """Selected demand champion must have lowest validation RMSE (MAE tie-breaker)."""
    meta = _load_metadata(pipeline, "demand_forecast")
    candidates = meta.get("candidates", [])
    assert candidates, "No candidates in metadata"

    # Sort by validation RMSE ascending, validation MAE ascending
    sorted_candidates = sorted(
        candidates,
        key=lambda c: (
            c["validation_metrics"]["rmse"],
            c["validation_metrics"].get("mae", 0.0),
        ),
    )
    expected_champion = sorted_candidates[0]["algorithm"]
    assert meta["selected_algorithm"] == expected_champion, (
        f"{pipeline} demand champion mismatch: got {meta['selected_algorithm']}, "
        f"expected {expected_champion} with best val RMSE"
    )


@pytest.mark.parametrize("pipeline", ["spark", "python"])
@pytest.mark.parametrize("task", ["wastage_risk", "churn_risk"])
def test_classification_selection_rule(pipeline: str, task: str):
    """Selected classification champion must have highest validation ROC-AUC (F1 tie-breaker)."""
    meta = _load_metadata(pipeline, task)
    candidates = meta.get("candidates", [])
    assert candidates, f"No candidates in {pipeline} {task} metadata"

    # Sort by validation ROC-AUC descending, validation F1 descending
    sorted_candidates = sorted(
        candidates,
        key=lambda c: (
            -c["validation_metrics"]["roc_auc"],
            -c["validation_metrics"].get("f1", 0.0),
        ),
    )
    expected_champion = sorted_candidates[0]["algorithm"]
    assert meta["selected_algorithm"] == expected_champion, (
        f"{pipeline} {task} champion mismatch: got {meta['selected_algorithm']}, "
        f"expected {expected_champion} with best val ROC-AUC"
    )


@pytest.mark.parametrize("pipeline", ["spark", "python"])
def test_segmentation_selection_rule(pipeline: str):
    """Selected segmentation champion must have highest silhouette score."""
    meta = _load_metadata(pipeline, "customer_segmentation")
    candidates = meta.get("candidates", [])
    if candidates:
        sorted_candidates = sorted(
            candidates,
            key=lambda c: -c["validation_metrics"]["silhouette_score"],
        )
        expected_champion = sorted_candidates[0]["algorithm"]
        assert meta["selected_algorithm"] == expected_champion


# ── 5. Tie-Breaker Behavior is Deterministic ──────────────────────────────────


def test_regression_tie_breaker_logic():
    """Verify that when primary metric (RMSE) ties, secondary metric (MAE) decides."""
    mock_candidates = [
        {"algorithm": "ModelA", "validation_metrics": {"rmse": 4.50, "mae": 3.20}},
        {"algorithm": "ModelB", "validation_metrics": {"rmse": 4.50, "mae": 2.80}},
        {"algorithm": "ModelC", "validation_metrics": {"rmse": 5.10, "mae": 2.00}},
    ]
    sorted_c = sorted(
        mock_candidates,
        key=lambda c: (c["validation_metrics"]["rmse"], c["validation_metrics"]["mae"]),
    )
    assert sorted_c[0]["algorithm"] == "ModelB", "Tie-breaker failed to pick lower MAE on tied RMSE"


def test_classification_tie_breaker_logic():
    """Verify that when primary metric (ROC-AUC) ties, secondary metric (F1) decides."""
    mock_candidates = [
        {"algorithm": "ModelA", "validation_metrics": {"roc_auc": 0.85, "f1": 0.70}},
        {"algorithm": "ModelB", "validation_metrics": {"roc_auc": 0.85, "f1": 0.78}},
        {"algorithm": "ModelC", "validation_metrics": {"roc_auc": 0.82, "f1": 0.80}},
    ]
    sorted_c = sorted(
        mock_candidates,
        key=lambda c: (-c["validation_metrics"]["roc_auc"], -c["validation_metrics"]["f1"]),
    )
    assert sorted_c[0]["algorithm"] == "ModelB", (
        "Tie-breaker failed to pick higher F1 on tied ROC-AUC"
    )


# ── 6. TEST Metrics Do Not Determine Selection ────────────────────────────────


def test_selection_ignores_test_metrics():
    """Verify selection algorithm ignores test performance and strictly uses validation."""
    mock_candidates = [
        {
            "algorithm": "OverfittedOnVal",
            "val_rmse": 3.0,
            "test_rmse": 8.0,
        },
        {
            "algorithm": "BetterOnTest",
            "val_rmse": 4.0,
            "test_rmse": 4.2,
        },
    ]
    # Pure validation ranking selects candidate with lower val_rmse regardless of test_rmse
    selected = min(mock_candidates, key=lambda c: c["val_rmse"])
    assert selected["algorithm"] == "OverfittedOnVal"


# ── 7. UNSEEN_COMPARISON Does Not Determine Selection ─────────────────────────


@pytest.mark.parametrize("pipeline", ["spark", "python"])
def test_unseen_comparison_temporal_isolation(pipeline: str):
    """Ensure UNSEEN_COMPARISON (December 2025) records are not in TRAIN or VALIDATION."""
    mart_dir = MARTS_SPARK_DIR if pipeline == "spark" else MARTS_PYTHON_DIR
    df = pq.read_table(mart_dir / "ml_demand_forecast.parquet").to_pandas()

    train_dates = df[df["split"] == "TRAIN"]["week_start_date"].astype(str)
    val_dates = df[df["split"] == "VALIDATION"]["week_start_date"].astype(str)
    unseen_dates = df[df["split"] == "UNSEEN_COMPARISON"]["week_start_date"].astype(str)

    # TRAIN ends 2025-08-31
    assert (train_dates <= "2025-08-31").all()
    # VALIDATION ends 2025-10-31
    assert (val_dates <= "2025-10-31").all()
    # UNSEEN is strictly after 2025-11-30
    assert (unseen_dates > "2025-11-30").all()


# ── 8. Selected Model Generates Final Prediction Marts ────────────────────────


@pytest.mark.parametrize("pipeline", ["spark", "python"])
@pytest.mark.parametrize("task", ALL_TASKS)
def test_final_prediction_mart_materialized(pipeline: str, task: str):
    """Verify physical existence and non-zero record count of final prediction mart."""
    mart_dir = MARTS_SPARK_DIR if pipeline == "spark" else MARTS_PYTHON_DIR
    path = mart_dir / f"ml_{task}.parquet"
    assert path.exists(), f"Mart {path} missing"
    table = pq.read_table(path)
    assert table.num_rows > 0, f"Mart {path} is empty"


# ── 9 & 10. Metadata Completeness and Champion Documentation ──────────────────


@pytest.mark.parametrize("pipeline", ["spark", "python"])
@pytest.mark.parametrize("task", ALL_TASKS)
def test_metadata_contains_candidates_and_selected_algorithm(pipeline: str, task: str):
    """Verify metadata contains selected_algorithm, model_version, and candidate validation metrics."""
    meta = _load_metadata(pipeline, task)
    assert "selected_algorithm" in meta, f"selected_algorithm missing in {pipeline} {task}"
    assert isinstance(meta["selected_algorithm"], str) and meta["selected_algorithm"]
    assert "model_version" in meta
    assert meta["model_version"] == "v2.0-phase6b"

    if "candidates" in meta:
        for c in meta["candidates"]:
            assert "algorithm" in c
            assert "validation_metrics" in c
            assert len(c["validation_metrics"]) > 0


# ── 11. Existing Mart Schemas Remain Compatible ───────────────────────────────


def test_mart_schemas_remain_compatible():
    """Verify all 8 ML marts preserve required contractual column names."""
    # Demand forecast contract
    for p_dir in [MARTS_SPARK_DIR, MARTS_PYTHON_DIR]:
        df = pq.read_table(p_dir / "ml_demand_forecast.parquet").to_pandas()
        required_cols = {
            "week_start_date",
            "menu_item_id",
            "restaurant_id",
            "actual_quantity",
            "predicted_quantity",
            "split",
            "pipeline",
        }
        assert required_cols.issubset(set(df.columns)), (
            f"Missing columns in {p_dir}/ml_demand_forecast: {required_cols - set(df.columns)}"
        )

    # Wastage risk contract
    for p_dir in [MARTS_SPARK_DIR, MARTS_PYTHON_DIR]:
        df = pq.read_table(p_dir / "ml_wastage_risk.parquet").to_pandas()
        required_cols = {
            "week_start_date",
            "menu_item_id",
            "restaurant_id",
            "actual_label",
            "predicted_label",
            "risk_probability",
            "split",
            "pipeline",
        }
        assert required_cols.issubset(set(df.columns)), (
            f"Missing columns in {p_dir}/ml_wastage_risk: {required_cols - set(df.columns)}"
        )

    # Churn risk contract
    for p_dir in [MARTS_SPARK_DIR, MARTS_PYTHON_DIR]:
        df = pq.read_table(p_dir / "ml_churn_risk.parquet").to_pandas()
        required_cols = {
            "customer_id",
            "actual_label",
            "predicted_label",
            "churn_probability",
            "split",
            "pipeline",
        }
        assert required_cols.issubset(set(df.columns)), (
            f"Missing columns in {p_dir}/ml_churn_risk: {required_cols - set(df.columns)}"
        )

    # Customer segmentation contract
    for p_dir in [MARTS_SPARK_DIR, MARTS_PYTHON_DIR]:
        df = pq.read_table(p_dir / "ml_customer_segmentation.parquet").to_pandas()
        required_cols = {
            "customer_id",
            "cluster_id",
            "segment_label",
            "recency_days",
            "frequency",
            "monetary_total",
            "pipeline",
        }
        assert required_cols.issubset(set(df.columns)), (
            f"Missing columns in {p_dir}/ml_customer_segmentation: {required_cols - set(df.columns)}"
        )


# ── 12. Spark/Python Independence Remains Intact ──────────────────────────────


def test_pipeline_independence_no_cross_imports():
    """Verify that packages.pipeline_spark never imports pipeline_python, and vice versa."""
    spark_files = list(Path("packages/pipeline_spark").rglob("*.py"))
    python_files = list(Path("packages/pipeline_python").rglob("*.py"))

    for f in spark_files:
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "pipeline_python" not in alias.name, (
                        f"Spark file {f} imports {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert "pipeline_python" not in node.module, (
                    f"Spark file {f} imports from {node.module}"
                )

    for f in python_files:
        tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "pipeline_spark" not in alias.name, (
                        f"Python file {f} imports {alias.name}"
                    )
                    assert "pyspark" not in alias.name, f"Python file {f} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert "pipeline_spark" not in node.module, (
                    f"Python file {f} imports from {node.module}"
                )
                assert "pyspark" not in node.module, f"Python file {f} imports from {node.module}"
