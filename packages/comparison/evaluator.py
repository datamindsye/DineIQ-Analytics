"""Cross-pipeline comparison engine for DineIQ Analytics Phase 4.

Reads prediction Parquet files from both Spark (data/marts/spark/ml_*.parquet)
and Python (data/marts/python/ml_*.parquet), joins them on common keys, computes
numerical differences, agreement rates, and winner decisions, then materialises
comparison results to data/marts/comparison/*.parquet.

Output contract (per task JSON shape for FastAPI):
{
  "task": "demand_forecast",
  "agreement_pct": 87.3,
  "spark_wins": true,
  "metrics_comparison": {
    "spark": {"rmse": 4.12, "mae": 2.88},
    "python": {"rmse": 4.45, "mae": 3.01}
  },
  "record_level_sample": [
    {
      "key": {"week_start_date": "2025-10-01", "menu_item_id": "MI-001", ...},
      "spark_prediction": 120.0,
      "python_prediction": 115.5,
      "numerical_difference": 4.5,
      "match": false
    }
  ]
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from packages.common.logging import get_logger
from packages.core.contracts.evaluation import (
    EvaluationMetricResult,
    PipelineComparisonResult,
)

logger = get_logger(__name__)

# Tolerance for treating two regression predictions as "agreeing"
REGRESSION_TOLERANCE = 0.10  # 10% relative tolerance
CLASSIFICATION_THRESHOLD = 0.5


class PipelineComparator:
    """Compares metrics and prediction alignment between Spark and Python pipelines."""

    def compare_metrics(
        self,
        spark_metrics: EvaluationMetricResult,
        python_metrics: EvaluationMetricResult,
        target_name: str,
        comparison_id: str,
    ) -> PipelineComparisonResult:
        """Compute absolute metric diffs between both pipeline evaluations."""
        diffs: dict[str, float] = {
            "f1_difference": abs(spark_metrics.f1_score - python_metrics.f1_score),
            "precision_difference": abs(spark_metrics.precision - python_metrics.precision),
            "recall_difference": abs(spark_metrics.recall - python_metrics.recall),
            "runtime_difference_sec": abs(
                spark_metrics.runtime_seconds - python_metrics.runtime_seconds
            ),
        }
        logger.info("Executed comparison %s for target %s", comparison_id, target_name)
        return PipelineComparisonResult(
            comparison_id=comparison_id,
            target_name=target_name,
            spark_metrics=spark_metrics,
            python_metrics=python_metrics,
            metric_differences=diffs,
            agreement_rate=1.0 - diffs["f1_difference"],
            timestamp="",
        )


def _read_parquet_dir(path: Path) -> pd.DataFrame | None:
    """Read a Parquet file or directory (handles multi-part Spark output)."""
    if not path.exists():
        logger.warning("Parquet path not found: %s", path)
        return None
    if path.is_dir():
        parts = list(path.glob("*.parquet"))
        if not parts:
            return None
        df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    else:
        df = pd.read_parquet(path)
    if "week_start_date" in df.columns:
        df["week_start_date"] = pd.to_datetime(df["week_start_date"]).dt.strftime("%Y-%m-%d")
    return df


def compare_demand_forecast(
    spark_dir: Path,
    python_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Compare demand forecast predictions from both pipelines."""
    logger.info("[Comparison] Comparing demand_forecast...")
    spark_df = _read_parquet_dir(spark_dir / "ml_demand_forecast.parquet")
    python_df = _read_parquet_dir(python_dir / "ml_demand_forecast.parquet")

    if spark_df is None or python_df is None:
        return {
            "task": "demand_forecast",
            "status": "SKIPPED",
            "reason": "Missing prediction files",
        }

    # Join on common keys
    join_keys = ["week_start_date", "menu_item_id", "restaurant_id"]
    merged = spark_df[join_keys + ["actual_quantity", "predicted_quantity", "split"]].merge(
        python_df[join_keys + ["predicted_quantity"]].rename(
            columns={"predicted_quantity": "python_predicted_quantity"}
        ),
        on=join_keys,
        how="inner",
    )

    actual = merged["actual_quantity"].values
    spark_pred = merged["predicted_quantity"].values
    python_pred = merged["python_predicted_quantity"].values

    # Numerical difference
    merged["numerical_difference"] = np.round(np.abs(spark_pred - python_pred), 4)
    # Agreement: predictions within REGRESSION_TOLERANCE of each other
    mean_pred = (np.abs(spark_pred) + np.abs(python_pred)) / 2 + 1e-9
    merged["match"] = (merged["numerical_difference"] / mean_pred) <= REGRESSION_TOLERANCE
    agreement_pct = round(float(merged["match"].mean() * 100), 2)

    # Metrics
    def rmse(a: np.ndarray, b: np.ndarray) -> float:
        return round(float(np.sqrt(np.mean((a - b) ** 2))), 6)

    def mae(a: np.ndarray, b: np.ndarray) -> float:
        return round(float(np.mean(np.abs(a - b))), 6)

    spark_rmse = rmse(actual, spark_pred)
    python_rmse = rmse(actual, python_pred)
    spark_wins = spark_rmse <= python_rmse

    result: dict[str, Any] = {
        "task": "demand_forecast",
        "agreement_pct": agreement_pct,
        "total_records_compared": len(merged),
        "spark_wins": spark_wins,
        "metrics_comparison": {
            "spark": {"rmse": spark_rmse, "mae": mae(actual, spark_pred)},
            "python": {"rmse": python_rmse, "mae": mae(actual, python_pred)},
        },
    }

    # Save record-level comparison
    out_df = merged.rename(
        columns={
            "predicted_quantity": "spark_prediction",
            "python_predicted_quantity": "python_prediction",
        }
    )
    out_df["pipeline_winner"] = np.where(
        np.abs(spark_pred - actual) <= np.abs(python_pred - actual), "spark", "python"
    )
    _save_comparison(out_df, output_dir, "comparison_demand_forecast")
    _save_summary(result, output_dir, "comparison_demand_forecast_summary.json")
    return result


def compare_classification(
    task: str,
    spark_dir: Path,
    python_dir: Path,
    output_dir: Path,
    join_keys: list[str],
    label_col: str,
    prob_col: str,
) -> dict[str, Any]:
    """Generic classification comparison for wastage_risk and churn_risk."""
    logger.info("[Comparison] Comparing %s...", task)
    spark_df = _read_parquet_dir(spark_dir / f"ml_{task}.parquet")
    python_df = _read_parquet_dir(python_dir / f"ml_{task}.parquet")

    if spark_df is None or python_df is None:
        return {"task": task, "status": "SKIPPED", "reason": "Missing prediction files"}

    rename_python = {
        "predicted_label": "python_predicted_label",
        prob_col: f"python_{prob_col}",
    }
    merged = spark_df[join_keys + ["actual_label", "predicted_label", prob_col, "split"]].merge(
        python_df[join_keys + ["predicted_label", prob_col]].rename(columns=rename_python),
        on=join_keys,
        how="inner",
    )

    merged["match"] = merged["predicted_label"] == merged["python_predicted_label"]
    merged["numerical_difference"] = np.round(
        np.abs(merged[prob_col] - merged[f"python_{prob_col}"]), 4
    )
    agreement_pct = round(float(merged["match"].mean() * 100), 2)

    # Simple majority-vote winner based on accuracy
    actual = merged["actual_label"].values
    spark_acc = float((merged["predicted_label"].values == actual).mean())
    python_acc = float((merged["python_predicted_label"].values == actual).mean())
    spark_wins = spark_acc >= python_acc

    result: dict[str, Any] = {
        "task": task,
        "agreement_pct": agreement_pct,
        "total_records_compared": len(merged),
        "spark_wins": spark_wins,
        "metrics_comparison": {
            "spark": {"accuracy": round(spark_acc, 6)},
            "python": {"accuracy": round(python_acc, 6)},
        },
    }

    out_df = merged.rename(
        columns={
            "predicted_label": "spark_predicted_label",
            prob_col: f"spark_{prob_col}",
        }
    )
    out_df["pipeline_winner"] = np.where(
        merged["predicted_label"].values == actual,
        "spark",
        np.where(merged["python_predicted_label"].values == actual, "python", "neither"),
    )
    _save_comparison(out_df, output_dir, f"comparison_{task}")
    _save_summary(result, output_dir, f"comparison_{task}_summary.json")
    return result


def compare_segmentation(
    spark_dir: Path,
    python_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Compare customer segmentation assignments between both pipelines."""
    logger.info("[Comparison] Comparing customer_segmentation...")
    spark_df = _read_parquet_dir(spark_dir / "ml_customer_segmentation.parquet")
    python_df = _read_parquet_dir(python_dir / "ml_customer_segmentation.parquet")

    if spark_df is None or python_df is None:
        return {"task": "customer_segmentation", "status": "SKIPPED", "reason": "Missing files"}

    merged = spark_df[["customer_id", "segment_label"]].merge(
        python_df[["customer_id", "segment_label"]].rename(
            columns={"segment_label": "python_segment_label"}
        ),
        on="customer_id",
        how="inner",
    )
    merged["match"] = merged["segment_label"] == merged["python_segment_label"]
    agreement_pct = round(float(merged["match"].mean() * 100), 2)

    result: dict[str, Any] = {
        "task": "customer_segmentation",
        "agreement_pct": agreement_pct,
        "total_customers_compared": len(merged),
        "spark_wins": None,  # Unsupervised — no ground truth
        "segment_agreement_breakdown": (
            merged.groupby(["segment_label", "python_segment_label"])
            .size()
            .reset_index(name="count")
            .to_dict(orient="records")
        ),
    }

    merged.rename(columns={"segment_label": "spark_segment_label"}, inplace=True)
    _save_comparison(merged, output_dir, "comparison_customer_segmentation")
    _save_summary(result, output_dir, "comparison_customer_segmentation_summary.json")
    return result


def _save_comparison(df: pd.DataFrame, output_dir: Path, name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_dir / f"{name}.parquet", index=False, compression="snappy")
    logger.info("[Comparison] Saved %s: %d rows", name, len(df))


def _save_summary(data: dict[str, Any], output_dir: Path, filename: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / filename).write_text(json.dumps(data, indent=2, default=str))
    logger.info("[Comparison] Saved summary: %s", filename)


def run_full_comparison(
    spark_dir: str | Path = "data/marts/spark",
    python_dir: str | Path = "data/marts/python",
    output_dir: str | Path = "data/marts/comparison",
) -> dict[str, Any]:
    """Execute all four cross-pipeline comparisons and return aggregated summary."""
    spark_dir = Path(spark_dir).resolve()
    python_dir = Path(python_dir).resolve()
    output_dir = Path(output_dir).resolve()

    logger.info("=" * 60)
    logger.info("DineIQ Cross-Pipeline Comparison Engine Starting")
    logger.info("=" * 60)

    results: dict[str, Any] = {}

    results["demand_forecast"] = compare_demand_forecast(spark_dir, python_dir, output_dir)

    results["wastage_risk"] = compare_classification(
        task="wastage_risk",
        spark_dir=spark_dir,
        python_dir=python_dir,
        output_dir=output_dir,
        join_keys=["week_start_date", "menu_item_id", "restaurant_id"],
        label_col="predicted_label",
        prob_col="risk_probability",
    )

    results["churn_risk"] = compare_classification(
        task="churn_risk",
        spark_dir=spark_dir,
        python_dir=python_dir,
        output_dir=output_dir,
        join_keys=["customer_id"],
        label_col="predicted_label",
        prob_col="churn_probability",
    )

    results["customer_segmentation"] = compare_segmentation(spark_dir, python_dir, output_dir)

    # Aggregate summary
    agreement_values = [
        v.get("agreement_pct", 0)
        for v in results.values()
        if isinstance(v, dict) and "agreement_pct" in v
    ]
    results["overall_agreement_pct"] = (
        round(float(np.mean(agreement_values)), 2) if agreement_values else 0.0
    )

    _save_summary(results, output_dir, "comparison_overall_summary.json")
    logger.info(
        "=" * 60 + "\nOverall Pipeline Agreement: %.1f%%\n" + "=" * 60,
        results["overall_agreement_pct"],
    )
    return results


if __name__ == "__main__":
    result = run_full_comparison()
    print("\n--- COMPARISON SUMMARY ---")
    for task, r in result.items():
        if isinstance(r, dict) and "agreement_pct" in r:
            winner = (
                "spark"
                if r.get("spark_wins")
                else "python"
                if r.get("spark_wins") is False
                else "n/a"
            )
            print(f"  {task}: {r['agreement_pct']}% agreement | winner={winner}")
    print(f"  OVERALL: {result.get('overall_agreement_pct')}% agreement")
