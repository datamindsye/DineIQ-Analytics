"""Spark MLlib customer churn risk classification model for DineIQ Analytics Phase 4.

Reads mart_customer_rfm Parquet, derives churn label (no order in last 60 days
relative to each customer's last order date), builds RFM-based features, trains
a GBTClassifier, and materialises predictions to
data/marts/spark/ml_churn_risk.parquet.

Anti-leakage: features are derived solely from RFM aggregates already computed
in the mart (recency, frequency, monetary). No future order signals are used.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pyspark.ml import Pipeline
from pyspark.ml.classification import GBTClassifier, LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from packages.common.logging import get_logger

logger = get_logger(__name__)

TRAIN_END = "2025-08-31"
VALIDATION_END = "2025-10-31"
TEST_END = "2025-11-30"

# Churn definition: no order in CHURN_DAYS days after the reference snapshot date
CHURN_DAYS = 60

FEATURE_COLS = [
    "recency_days",
    "frequency",
    "monetary_total",
    "avg_order_value",
    "rfm_score",
    "r_score",
    "f_score",
    "m_score",
]

TARGET_COL = "churn_label"


def _load_rfm_mart(spark: SparkSession, mart_dir: Path) -> DataFrame:
    mart_path = mart_dir / "mart_customer_rfm.parquet"
    if not mart_path.exists():
        raise FileNotFoundError(
            f"mart_customer_rfm not found at {mart_path}. "
            "Run: python -m packages.pipeline_spark.runner"
        )
    df = spark.read.parquet(str(mart_path))
    if "customer_id" not in df.columns and "source_customer_id" in df.columns:
        df = df.withColumn("customer_id", F.col("source_customer_id"))
    if "monetary_total" not in df.columns and "monetary_value" in df.columns:
        df = df.withColumn("monetary_total", F.col("monetary_value").cast("double"))
    if "rfm_score" not in df.columns and "r_score" in df.columns:
        df = df.withColumn(
            "rfm_score",
            (F.col("r_score") + F.col("f_score") + F.col("m_score")).cast("double"),
        )
    logger.info("Loaded mart_customer_rfm: %d rows", df.count())
    return df


def _build_churn_features(df: DataFrame) -> DataFrame:
    """Derive churn label and ensure all feature columns are numeric."""
    # Churn label: recency > CHURN_DAYS means the customer has not returned
    df = df.withColumn(
        TARGET_COL,
        F.when(F.col("recency_days") > CHURN_DAYS, F.lit(1)).otherwise(F.lit(0)).cast("integer"),
    )
    # Ensure all feature cols are numeric
    for col in FEATURE_COLS:
        if col not in df.columns:
            df = df.withColumn(col, F.lit(0.0))
        df = df.withColumn(col, F.col(col).cast("double"))
    return df


def _temporal_split_rfm(df: DataFrame) -> tuple[DataFrame, DataFrame, DataFrame]:
    """Split RFM mart by snapshot_date column (computed at mart build time)."""
    # RFM mart is a single-snapshot mart — split by last_order_date as proxy
    date_col = "last_order_date" if "last_order_date" in df.columns else None
    if date_col:
        df_train = df.filter(F.col(date_col) <= TRAIN_END)
        df_val = df.filter((F.col(date_col) > TRAIN_END) & (F.col(date_col) <= VALIDATION_END))
        df_test = df.filter((F.col(date_col) > VALIDATION_END) & (F.col(date_col) <= TEST_END))
    else:
        # Fallback: 70/15/15 random split (only if date unavailable)
        df_train, df_val, df_test = df.randomSplit([0.70, 0.15, 0.15], seed=42)
    return df_train, df_val, df_test


def train_churn_risk(
    spark: SparkSession,
    mart_dir: str | Path = "data/marts/spark",
    output_dir: str | Path = "data/marts/spark",
    artifact_dir: str | Path = "data/artifacts",
) -> dict[str, Any]:
    """Train multiple candidate models for churn risk, select champion, and materialise.

    Candidates evaluated on validation split (ROC-AUC primary, F1 tie-breaker):
        1. LogisticRegression
        2. RandomForestClassifier
        3. GBTClassifier

    Returns:
        Metadata dict with champion metrics, candidate evaluations, and duration.
    """
    t_start = time.time()
    mart_dir = Path(mart_dir).resolve()
    output_dir = Path(output_dir).resolve()
    artifact_dir = Path(artifact_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    logger.info("[Spark ML] Loading mart_customer_rfm for churn modelling...")
    df_raw = _load_rfm_mart(spark, mart_dir)
    df = _build_churn_features(df_raw)

    df_train, df_val, df_test = _temporal_split_rfm(df)
    rows_train = df_train.count()
    rows_val = df_val.count()
    rows_test = df_test.count()
    logger.info(
        "[Spark ML] Churn split — TRAIN=%d, VAL=%d, TEST=%d", rows_train, rows_val, rows_test
    )

    assembler = VectorAssembler(inputCols=FEATURE_COLS, outputCol="features", handleInvalid="skip")
    prep_pipeline = Pipeline(stages=[assembler])
    prep_model = prep_pipeline.fit(df_train)

    train_prep = prep_model.transform(df_train).persist()
    val_prep = prep_model.transform(df_val).persist()
    test_prep = prep_model.transform(df_test).persist()

    auc_eval = BinaryClassificationEvaluator(
        labelCol=TARGET_COL, rawPredictionCol="rawPrediction", metricName="areaUnderROC"
    )
    f1_eval = MulticlassClassificationEvaluator(
        labelCol=TARGET_COL, predictionCol="prediction", metricName="f1"
    )
    prec_eval = MulticlassClassificationEvaluator(
        labelCol=TARGET_COL, predictionCol="prediction", metricName="weightedPrecision"
    )
    rec_eval = MulticlassClassificationEvaluator(
        labelCol=TARGET_COL, predictionCol="prediction", metricName="weightedRecall"
    )

    def _eval(pred_df: DataFrame) -> dict[str, float]:
        return {
            "roc_auc": round(float(auc_eval.evaluate(pred_df)), 6),
            "f1": round(float(f1_eval.evaluate(pred_df)), 6),
            "precision": round(float(prec_eval.evaluate(pred_df)), 6),
            "recall": round(float(rec_eval.evaluate(pred_df)), 6),
        }

    # ── Candidate Model Competition ───────────────────────────────────────────
    candidates_config = [
        {
            "name": "LogisticRegression",
            "model": LogisticRegression(
                featuresCol="features", labelCol=TARGET_COL, maxIter=50, regParam=0.01
            ),
            "hyperparameters": {"maxIter": 50, "regParam": 0.01},
        },
        {
            "name": "RandomForestClassifier",
            "model": RandomForestClassifier(
                featuresCol="features", labelCol=TARGET_COL, numTrees=20, maxDepth=5, seed=42
            ),
            "hyperparameters": {"numTrees": 20, "maxDepth": 5, "seed": 42},
        },
        {
            "name": "GBTClassifier",
            "model": GBTClassifier(
                featuresCol="features",
                labelCol=TARGET_COL,
                maxIter=30,
                maxDepth=4,
                stepSize=0.1,
                seed=42,
            ),
            "hyperparameters": {"maxIter": 30, "maxDepth": 4, "stepSize": 0.1, "seed": 42},
        },
    ]

    candidates_meta: list[dict[str, Any]] = []
    trained_candidates = []

    logger.info(
        "[Spark ML] Evaluating %d candidate classification algorithms for churn...",
        len(candidates_config),
    )
    for c in candidates_config:
        t_c = time.time()
        logger.info("[Spark ML] Training churn candidate: %s...", c["name"])
        fitted_model = c["model"].fit(train_prep)
        duration_c = round(time.time() - t_c, 2)

        val_pred = fitted_model.transform(val_prep)
        val_m = _eval(val_pred)
        logger.info(
            "[Spark ML] Candidate %s — Validation: ROC-AUC=%.4f, F1=%.4f (%.2fs)",
            c["name"],
            val_m["roc_auc"],
            val_m["f1"],
            duration_c,
        )

        c_meta = {
            "algorithm": c["name"],
            "hyperparameters": c["hyperparameters"],
            "validation_metrics": val_m,
            "training_duration_sec": duration_c,
        }
        candidates_meta.append(c_meta)
        trained_candidates.append(
            {
                "name": c["name"],
                "model": fitted_model,
                "meta": c_meta,
                "roc_auc_val": val_m["roc_auc"],
                "f1_val": val_m["f1"],
            }
        )

    # ── Champion Selection (VALIDATION only: highest ROC-AUC, F1 tie-breaker) ─
    ranked_candidates = sorted(trained_candidates, key=lambda x: (-x["roc_auc_val"], -x["f1_val"]))
    champion = ranked_candidates[0]
    logger.info(
        "[Spark ML] Champion selected for churn: %s (Validation ROC-AUC=%.4f, F1=%.4f)",
        champion["name"],
        champion["roc_auc_val"],
        champion["f1_val"],
    )

    # ── Out-of-sample Test Evaluation on Champion Only ─────────────────────────
    test_pred = champion["model"].transform(test_prep)
    test_metrics = _eval(test_pred)
    logger.info("[Spark ML] Champion %s Test: %s", champion["name"], test_metrics)

    prob_udf = F.udf(lambda v: float(v[1]) if v is not None and len(v) > 1 else 0.0, "double")

    # Determine available date column for split labelling
    date_col = "last_order_date" if "last_order_date" in df.columns else None

    def _split_label(col_name: str | None) -> Any:
        if col_name:
            return (
                F.when(F.col(col_name) <= TRAIN_END, "TRAIN")
                .when(F.col(col_name) <= VALIDATION_END, "VALIDATION")
                .when(F.col(col_name) <= TEST_END, "TEST")
                .otherwise("UNSEEN_COMPARISON")
            )
        return F.lit("TRAIN")

    full_prep = prep_model.transform(df)
    df_all_pred = (
        champion["model"]
        .transform(full_prep)
        .select(
            "customer_id",
            F.col(TARGET_COL).alias("actual_label"),
            F.col("prediction").cast("integer").alias("predicted_label"),
            F.round(prob_udf(F.col("probability")), 4).alias("churn_probability"),
            "recency_days",
            "frequency",
            "monetary_total",
            "rfm_score",
            _split_label(date_col).alias("split"),
            F.lit("spark").alias("pipeline"),
        )
    )

    out_path = output_dir / "ml_churn_risk.parquet"
    if out_path.exists():
        import shutil

        if out_path.is_dir():
            shutil.rmtree(out_path)
        else:
            out_path.unlink()
    df_all_pred.coalesce(1).write.mode("overwrite").parquet(str(out_path))
    total_rows = df_all_pred.count()
    logger.info("[Spark ML] Materialised ml_churn_risk.parquet: %d rows", total_rows)

    # Clean up persisted DataFrames
    train_prep.unpersist()
    val_prep.unpersist()
    test_prep.unpersist()

    duration = round(time.time() - t_start, 2)
    metadata: dict[str, Any] = {
        "pipeline": "spark",
        "task": "churn_risk",
        "selected_algorithm": champion["name"],
        "algorithm": champion["name"],
        "selection_criteria": "validation_roc_auc (higher is better, F1 tie-breaker)",
        "selection_reason": (
            f"Highest validation ROC-AUC ({champion['roc_auc_val']:.6f}) among "
            f"{len(candidates_config)} evaluated Spark MLlib candidates"
        ),
        "candidates": candidates_meta,
        "churn_definition_days": CHURN_DAYS,
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "rows_train": rows_train,
        "rows_validation": rows_val,
        "rows_test": rows_test,
        "metrics": {"validation": champion["meta"]["validation_metrics"], "test": test_metrics},
        "duration_sec": duration,
        "model_version": "v2.0-phase6b",
    }
    meta_path = artifact_dir / "spark_churn_risk_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    logger.info("[Spark ML] Metadata saved to %s", meta_path)

    return metadata
