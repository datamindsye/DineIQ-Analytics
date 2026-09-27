"""Spark MLlib wastage risk classification model for DineIQ Analytics Phase 4.

Reads mart_wastage Parquet, builds cost-ratio and quantity-ratio features per
menu_item/restaurant/week, labels using WastageRiskContract thresholds, trains
a GBTClassifier, and materialises binary predictions + probabilities to
data/marts/spark/ml_wastage_risk.parquet.

Anti-leakage: rolling features for week t use only data recorded up to t-1.
"""

from __future__ import annotations

import datetime
import json
import time
from pathlib import Path
from typing import Any

from pyspark.ml import Pipeline
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from packages.common.logging import get_logger
from packages.core.contracts.analytical_contracts import WastageRiskContract

logger = get_logger(__name__)

TRAIN_END = "2025-08-31"
VALIDATION_END = "2025-10-31"
TEST_END = "2025-11-30"

FEATURE_COLS = [
    "cost_ratio",
    "quantity_ratio",
    "lag_1w_cost_ratio",
    "lag_4w_avg_cost_ratio",
    "lag_1w_quantity_ratio",
    "lag_4w_avg_quantity_ratio",
    "rolling_4w_waste_events",
    "week_of_year",
    "month",
    "category_idx",
    "restaurant_idx",
]

TARGET_COL = "wastage_risk_label"


def _build_wastage_features(df: DataFrame) -> DataFrame:
    """Derive cost_ratio, quantity_ratio and anti-leakage lag features."""
    if "source_menu_item_id" in df.columns:
        df = df.filter(F.col("source_menu_item_id").isNotNull()).withColumn(
            "menu_item_id", F.col("source_menu_item_id")
        )
    if "source_restaurant_id" in df.columns:
        df = df.withColumn("restaurant_id", F.col("source_restaurant_id"))
    if "source_category_id" in df.columns:
        df = df.withColumn("category_id", F.col("source_category_id"))

    if "waste_cost_ratio" in df.columns:
        df = df.withColumn("cost_ratio", F.col("waste_cost_ratio").cast("double"))
    elif "gross_revenue" in df.columns and "waste_cost" in df.columns:
        df = df.withColumn(
            "cost_ratio",
            F.when(F.col("gross_revenue") > 0, F.col("waste_cost") / F.col("gross_revenue"))
            .otherwise(F.lit(0.0))
            .cast("double"),
        )

    if "waste_quantity_ratio" in df.columns:
        df = df.withColumn("quantity_ratio", F.col("waste_quantity_ratio").cast("double"))
    elif "sold_quantity" in df.columns and "waste_quantity" in df.columns:
        df = df.withColumn(
            "quantity_ratio",
            F.when(F.col("sold_quantity") > 0, F.col("waste_quantity") / F.col("sold_quantity"))
            .otherwise(F.lit(0.0))
            .cast("double"),
        )

    iso_monday_udf = F.udf(
        lambda y, w: (
            str(datetime.date.fromisocalendar(int(y), int(w), 1))
            if y is not None and w is not None
            else None
        ),
        "string",
    )
    if (
        "week_start_date" not in df.columns
        and "calendar_year" in df.columns
        and "calendar_week" in df.columns
    ):
        df = df.withColumn(
            "week_start_date",
            iso_monday_udf(F.col("calendar_year"), F.col("calendar_week")),
        )

    # Binary label from WastageRiskContract thresholds
    df = df.withColumn(
        TARGET_COL,
        F.when(
            (F.col("cost_ratio") >= WastageRiskContract.COST_RATIO_THRESHOLD)
            | (F.col("quantity_ratio") >= WastageRiskContract.QUANTITY_RATIO_THRESHOLD),
            F.lit(1),
        )
        .otherwise(F.lit(0))
        .cast("integer"),
    )

    # Anti-leakage lag features (rowsBetween(-4,-1) == weeks before current)
    w_lag = Window.partitionBy("menu_item_id", "restaurant_id").orderBy("week_start_date")
    w_lag4 = (
        Window.partitionBy("menu_item_id", "restaurant_id")
        .orderBy("week_start_date")
        .rowsBetween(-4, -1)
    )

    df = (
        df.withColumn(
            "lag_1w_cost_ratio",
            F.coalesce(F.lag("cost_ratio", 1).over(w_lag), F.lit(0.0)),
        )
        .withColumn(
            "lag_4w_avg_cost_ratio", F.coalesce(F.avg("cost_ratio").over(w_lag4), F.lit(0.0))
        )
        .withColumn(
            "lag_1w_quantity_ratio",
            F.coalesce(F.lag("quantity_ratio", 1).over(w_lag), F.lit(0.0)),
        )
        .withColumn(
            "lag_4w_avg_quantity_ratio",
            F.coalesce(F.avg("quantity_ratio").over(w_lag4), F.lit(0.0)),
        )
        .withColumn(
            "rolling_4w_waste_events",
            F.coalesce(F.sum(TARGET_COL).over(w_lag4), F.lit(0.0)),
        )
        .withColumn("week_of_year", F.weekofyear(F.col("week_start_date")).cast("double"))
        .withColumn("month", F.month(F.col("week_start_date")).cast("double"))
    )

    return df


def _load_wastage_mart(spark: SparkSession, mart_dir: Path) -> DataFrame:
    """Load and validate mart_wastage Parquet directory."""
    mart_path = mart_dir / "mart_wastage.parquet"
    if not mart_path.exists():
        raise FileNotFoundError(
            f"mart_wastage not found at {mart_path}. Run: python -m packages.pipeline_spark.runner"
        )
    df = spark.read.parquet(str(mart_path))
    logger.info("Loaded mart_wastage: %d rows", df.count())
    return df


def train_wastage_risk(
    spark: SparkSession,
    mart_dir: str | Path = "data/marts/spark",
    output_dir: str | Path = "data/marts/spark",
    artifact_dir: str | Path = "data/artifacts",
) -> dict[str, Any]:
    """Train GBTClassifier for wastage risk and materialise predictions.

    Returns:
        Metadata dict with roc_auc, f1, precision, recall on validation and test.
    """
    t_start = time.time()
    mart_dir = Path(mart_dir).resolve()
    output_dir = Path(output_dir).resolve()
    artifact_dir = Path(artifact_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    logger.info("[Spark ML] Loading mart_wastage for risk modelling...")
    df_raw = _load_wastage_mart(spark, mart_dir)
    df = _build_wastage_features(df_raw)

    # Temporal split
    df_train = df.filter(F.col("week_start_date") <= TRAIN_END)
    df_val = df.filter(
        (F.col("week_start_date") > TRAIN_END) & (F.col("week_start_date") <= VALIDATION_END)
    )
    df_test = df.filter(
        (F.col("week_start_date") > VALIDATION_END) & (F.col("week_start_date") <= TEST_END)
    )

    rows_train = df_train.count()
    rows_val = df_val.count()
    rows_test = df_test.count()
    logger.info(
        "[Spark ML] Wastage Risk split — TRAIN=%d, VAL=%d, TEST=%d",
        rows_train,
        rows_val,
        rows_test,
    )

    indexer_cat = StringIndexer(
        inputCol="category_id", outputCol="category_idx", handleInvalid="keep"
    )
    indexer_rest = StringIndexer(
        inputCol="restaurant_id", outputCol="restaurant_idx", handleInvalid="keep"
    )
    assembler = VectorAssembler(inputCols=FEATURE_COLS, outputCol="features", handleInvalid="skip")
    gbt = GBTClassifier(
        featuresCol="features",
        labelCol=TARGET_COL,
        maxIter=25,
        maxDepth=4,
        stepSize=0.1,
        seed=42,
    )
    pipeline = Pipeline(stages=[indexer_cat, indexer_rest, assembler, gbt])

    logger.info("[Spark ML] Training GBTClassifier for wastage risk on %d rows...", rows_train)
    model = pipeline.fit(df_train)

    # Evaluation
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
    logger.info("[Spark ML] Wastage Risk — VAL: %s | TEST: %s", val_metrics, test_metrics)

    # Materialise predictions across full dataset
    # Extract probability of class 1 (high-risk)
    prob_udf = F.udf(lambda v: float(v[1]), "double")

    df_all_pred = model.transform(df).select(
        "week_start_date",
        "menu_item_id",
        "restaurant_id",
        F.col(TARGET_COL).alias("actual_label"),
        F.col("prediction").cast("integer").alias("predicted_label"),
        F.round(prob_udf(F.col("probability")), 4).alias("risk_probability"),
        F.when(F.col("week_start_date") <= TRAIN_END, "TRAIN")
        .when(F.col("week_start_date") <= VALIDATION_END, "VALIDATION")
        .when(F.col("week_start_date") <= TEST_END, "TEST")
        .otherwise("UNSEEN_COMPARISON")
        .alias("split"),
        F.lit("spark").alias("pipeline"),
    )

    out_path = output_dir / "ml_wastage_risk.parquet"
    if out_path.exists():
        import shutil

        if out_path.is_dir():
            shutil.rmtree(out_path)
        else:
            out_path.unlink()
    df_all_pred.coalesce(1).write.mode("overwrite").parquet(str(out_path))
    total_rows = df_all_pred.count()
    logger.info("[Spark ML] Materialised ml_wastage_risk.parquet: %d rows", total_rows)

    duration = round(time.time() - t_start, 2)
    metadata: dict[str, Any] = {
        "pipeline": "spark",
        "task": "wastage_risk",
        "algorithm": "GBTClassifier",
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "decision_threshold": WastageRiskContract.DECISION_THRESHOLD,
        "cost_ratio_threshold": WastageRiskContract.COST_RATIO_THRESHOLD,
        "quantity_ratio_threshold": WastageRiskContract.QUANTITY_RATIO_THRESHOLD,
        "rows_train": rows_train,
        "rows_validation": rows_val,
        "rows_test": rows_test,
        "metrics": {"validation": val_metrics, "test": test_metrics},
        "duration_sec": duration,
    }
    meta_path = artifact_dir / "spark_wastage_risk_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    logger.info("[Spark ML] Metadata saved to %s", meta_path)

    return metadata
