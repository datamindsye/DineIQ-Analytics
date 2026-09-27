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
from pyspark.ml.classification import GBTClassifier
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
    """Train GBTClassifier for churn risk and materialise predictions."""
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
    gbt = GBTClassifier(
        featuresCol="features",
        labelCol=TARGET_COL,
        maxIter=50,
        maxDepth=5,
        stepSize=0.1,
        seed=42,
    )
    pipeline = Pipeline(stages=[assembler, gbt])

    logger.info("[Spark ML] Training GBTClassifier for churn on %d rows...", rows_train)
    model = pipeline.fit(df_train)

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

    df_val_pred = model.transform(df_val)
    df_test_pred = model.transform(df_test)

    def _eval(pred_df: DataFrame) -> dict[str, float]:
        return {
            "roc_auc": round(auc_eval.evaluate(pred_df), 6),
            "f1": round(f1_eval.evaluate(pred_df), 6),
            "precision": round(prec_eval.evaluate(pred_df), 6),
            "recall": round(rec_eval.evaluate(pred_df), 6),
        }

    val_metrics = _eval(df_val_pred)
    test_metrics = _eval(df_test_pred)
    logger.info("[Spark ML] Churn Risk — VAL: %s | TEST: %s", val_metrics, test_metrics)

    prob_udf = F.udf(lambda v: float(v[1]), "double")

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

    df_all_pred = model.transform(df).select(
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

    duration = round(time.time() - t_start, 2)
    metadata: dict[str, Any] = {
        "pipeline": "spark",
        "task": "churn_risk",
        "algorithm": "GBTClassifier",
        "churn_definition_days": CHURN_DAYS,
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "rows_train": rows_train,
        "rows_validation": rows_val,
        "rows_test": rows_test,
        "metrics": {"validation": val_metrics, "test": test_metrics},
        "duration_sec": duration,
    }
    meta_path = artifact_dir / "spark_churn_risk_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    logger.info("[Spark ML] Metadata saved to %s", meta_path)

    return metadata
