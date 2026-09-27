"""Spark MLlib Phase 4 ML pipeline runner for DineIQ Analytics.

Orchestrates all four Spark ML tasks in sequence:
    1. Demand Forecast  (GBTRegressor)
    2. Wastage Risk     (GBTClassifier)
    3. Churn Risk       (GBTClassifier)
    4. Customer Segmentation (KMeans)

Each task reads from precomputed analytical marts in data/marts/spark/ and
materialises predictions to data/marts/spark/ml_*.parquet. Model metadata
is saved to data/artifacts/spark_*_metadata.json.

Usage:
    python -m packages.pipeline_spark.ml_runner
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from packages.common.logging import get_logger
from packages.pipeline_spark.ml.churn_risk import train_churn_risk
from packages.pipeline_spark.ml.customer_segmentation import train_customer_segmentation
from packages.pipeline_spark.ml.demand_forecast import train_demand_forecast
from packages.pipeline_spark.ml.wastage_risk import train_wastage_risk
from packages.pipeline_spark.session import get_spark_session

logger = get_logger(__name__)


def run_spark_ml_pipeline(
    mart_dir: str | Path = "data/marts/spark",
    output_dir: str | Path = "data/marts/spark",
    artifact_dir: str | Path = "data/artifacts",
) -> dict[str, Any]:
    """Execute all four Spark MLlib models sequentially on a single SparkSession.

    Args:
        mart_dir: Directory containing the 12 precomputed analytical mart Parquet files.
        output_dir: Destination for ML prediction Parquet files.
        artifact_dir: Destination for model metadata JSON files.

    Returns:
        Summary dictionary keyed by task name with metrics and duration.
    """
    t_total = time.time()
    summary: dict[str, Any] = {}

    logger.info("=" * 60)
    logger.info("DineIQ Spark MLlib Phase 4 Pipeline Starting")
    logger.info("=" * 60)

    spark = get_spark_session()
    if spark is None:
        raise RuntimeError(
            "SparkSession is not available. Ensure Java 17 is installed and JAVA_HOME is set."
        )

    common_kwargs = {
        "spark": spark,
        "mart_dir": mart_dir,
        "output_dir": output_dir,
        "artifact_dir": artifact_dir,
    }

    # ── 1. Demand Forecast ────────────────────────────────────────────────────
    logger.info("[1/4] Running Demand Forecast (GBTRegressor)...")
    try:
        summary["demand_forecast"] = train_demand_forecast(**common_kwargs)
        logger.info(
            "[1/4] Demand Forecast complete — VAL RMSE=%.4f",
            summary["demand_forecast"]["metrics"]["validation"]["rmse"],
        )
    except Exception as exc:
        logger.error("[1/4] Demand Forecast FAILED: %s", exc)
        summary["demand_forecast"] = {"status": "FAILED", "error": str(exc)}

    # ── 2. Wastage Risk ───────────────────────────────────────────────────────
    logger.info("[2/4] Running Wastage Risk (GBTClassifier)...")
    try:
        summary["wastage_risk"] = train_wastage_risk(**common_kwargs)
        logger.info(
            "[2/4] Wastage Risk complete — VAL ROC-AUC=%.4f",
            summary["wastage_risk"]["metrics"]["validation"]["roc_auc"],
        )
    except Exception as exc:
        logger.error("[2/4] Wastage Risk FAILED: %s", exc)
        summary["wastage_risk"] = {"status": "FAILED", "error": str(exc)}

    # ── 3. Churn Risk ─────────────────────────────────────────────────────────
    logger.info("[3/4] Running Churn Risk (GBTClassifier)...")
    try:
        summary["churn_risk"] = train_churn_risk(**common_kwargs)
        logger.info(
            "[3/4] Churn Risk complete — VAL ROC-AUC=%.4f",
            summary["churn_risk"]["metrics"]["validation"]["roc_auc"],
        )
    except Exception as exc:
        logger.error("[3/4] Churn Risk FAILED: %s", exc)
        summary["churn_risk"] = {"status": "FAILED", "error": str(exc)}

    # ── 4. Customer Segmentation ──────────────────────────────────────────────
    logger.info("[4/4] Running Customer Segmentation (KMeans k=4)...")
    try:
        summary["customer_segmentation"] = train_customer_segmentation(**common_kwargs)
        logger.info(
            "[4/4] Segmentation complete — Silhouette=%.4f",
            summary["customer_segmentation"]["silhouette_score"],
        )
    except Exception as exc:
        logger.error("[4/4] Segmentation FAILED: %s", exc)
        summary["customer_segmentation"] = {"status": "FAILED", "error": str(exc)}

    total_sec = round(time.time() - t_total, 2)
    summary["total_duration_sec"] = total_sec
    summary["status"] = (
        "SUCCESS"
        if all("error" not in v for v in summary.values() if isinstance(v, dict))
        else "PARTIAL"
    )

    logger.info("=" * 60)
    logger.info("Spark ML Pipeline %s in %.2fs", summary["status"], total_sec)
    logger.info("=" * 60)
    return summary


if __name__ == "__main__":
    result = run_spark_ml_pipeline()
    print("\n--- SPARK ML PIPELINE SUMMARY ---")
    for task, meta in result.items():
        if isinstance(meta, dict) and "metrics" in meta:
            val = meta["metrics"].get("validation", {})
            print(f"  {task}: {val} ({meta.get('duration_sec')}s)")
        elif isinstance(meta, dict) and "silhouette_score" in meta:
            print(f"  {task}: silhouette={meta['silhouette_score']} ({meta.get('duration_sec')}s)")
        elif task not in ("total_duration_sec", "status"):
            print(f"  {task}: {meta}")
    print(f"  TOTAL: {result.get('total_duration_sec')}s [{result.get('status')}]")
