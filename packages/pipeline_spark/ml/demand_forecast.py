"""Spark MLlib demand forecasting model for DineIQ Analytics Phase 4.

Reads the precomputed mart_demand_historical Parquet mart, assembles week-level
features, trains a GBTRegressor with temporal train/validation split, and
materialises predictions to data/marts/spark/ml_demand_forecast.parquet.

Anti-leakage guarantee: features are restricted to lag-based aggregates already
computed in mart_demand_historical (lag_1w, lag_4w, rolling_4w_avg, etc.).
The current week's sales figure is NEVER included as a feature.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.regression import GBTRegressor
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

from packages.common.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Temporal split boundaries (ISO dates — matches the project contract)
# ---------------------------------------------------------------------------
TRAIN_END = "2025-08-31"
VALIDATION_END = "2025-10-31"
TEST_END = "2025-11-30"

# ---------------------------------------------------------------------------
# Feature columns sourced from mart_demand_historical (already anti-leakage)
# ---------------------------------------------------------------------------
FEATURE_COLS = [
    "lag_1w_quantity",
    "lag_4w_quantity",
    "rolling_4w_avg_quantity",
    "rolling_4w_std_quantity",
    "lag_1w_revenue",
    "lag_4w_revenue",
    "rolling_4w_avg_revenue",
    "dow_avg_quantity",
    "week_of_year",
    "month",
    "is_weekend",
    "category_idx",
    "restaurant_idx",
]

TARGET_COL = "weekly_quantity"


def _load_demand_mart(spark: SparkSession, mart_dir: Path) -> DataFrame:
    """Load and validate the mart_demand_historical Parquet directory."""
    mart_path = mart_dir / "mart_demand_historical.parquet"
    if not mart_path.exists():
        raise FileNotFoundError(
            f"mart_demand_historical not found at {mart_path}. "
            "Run the Spark analytical pipeline first: "
            "python -m packages.pipeline_spark.runner"
        )
    df = spark.read.parquet(str(mart_path))
    logger.info("Loaded mart_demand_historical: %d rows, cols=%s", df.count(), df.columns)
    return df


def _build_features(df: DataFrame) -> DataFrame:
    """Aggregate daily demand mart to weekly grain and derive anti-leakage lag features."""
    if "menu_item_id" not in df.columns and "source_menu_item_id" in df.columns:
        df = df.withColumn("menu_item_id", F.col("source_menu_item_id"))
    if "restaurant_id" not in df.columns and "source_restaurant_id" in df.columns:
        df = df.withColumn("restaurant_id", F.col("source_restaurant_id"))
    if "category_id" not in df.columns and "source_category_id" in df.columns:
        df = df.withColumn("category_id", F.col("source_category_id"))

    if "weekly_quantity" not in df.columns:
        df = df.withColumn(
            "week_start_date", F.date_trunc("week", F.col("order_date")).cast("date")
        )
        df = df.groupBy("week_start_date", "menu_item_id", "restaurant_id", "category_id").agg(
            F.sum("historical_demand").alias("weekly_quantity"),
            F.sum("gross_revenue").alias("weekly_revenue"),
        )

    w_lag = Window.partitionBy("menu_item_id", "restaurant_id").orderBy("week_start_date")
    w_lag4 = (
        Window.partitionBy("menu_item_id", "restaurant_id")
        .orderBy("week_start_date")
        .rowsBetween(-4, -1)
    )

    df = (
        df.withColumn(
            "lag_1w_quantity", F.coalesce(F.lag("weekly_quantity", 1).over(w_lag), F.lit(0.0))
        )
        .withColumn(
            "lag_4w_quantity", F.coalesce(F.lag("weekly_quantity", 4).over(w_lag), F.lit(0.0))
        )
        .withColumn(
            "rolling_4w_avg_quantity", F.coalesce(F.avg("weekly_quantity").over(w_lag4), F.lit(0.0))
        )
        .withColumn(
            "rolling_4w_std_quantity",
            F.coalesce(F.stddev("weekly_quantity").over(w_lag4), F.lit(0.0)),
        )
        .withColumn(
            "lag_1w_revenue", F.coalesce(F.lag("weekly_revenue", 1).over(w_lag), F.lit(0.0))
        )
        .withColumn(
            "lag_4w_revenue", F.coalesce(F.lag("weekly_revenue", 4).over(w_lag), F.lit(0.0))
        )
        .withColumn(
            "rolling_4w_avg_revenue", F.coalesce(F.avg("weekly_revenue").over(w_lag4), F.lit(0.0))
        )
        .withColumn("dow_avg_quantity", F.lit(0.0))
        .withColumn("week_of_year", F.weekofyear(F.col("week_start_date")).cast("double"))
        .withColumn("month", F.month(F.col("week_start_date")).cast("double"))
        .withColumn("is_weekend", F.lit(0.0))
    )

    return df


def train_demand_forecast(
    spark: SparkSession,
    mart_dir: str | Path = "data/marts/spark",
    output_dir: str | Path = "data/marts/spark",
    artifact_dir: str | Path = "data/artifacts",
) -> dict[str, Any]:
    """Train GBTRegressor on mart_demand_historical and materialise predictions.

    Args:
        spark: Active SparkSession.
        mart_dir: Directory containing precomputed mart Parquet files.
        output_dir: Destination for ml_demand_forecast.parquet.
        artifact_dir: Destination for model metadata JSON.

    Returns:
        Dictionary with keys: rmse_validation, mae_validation, rmse_test,
        mae_test, rows_train, rows_val, rows_test, duration_sec.
    """
    t_start = time.time()
    mart_dir = Path(mart_dir).resolve()
    output_dir = Path(output_dir).resolve()
    artifact_dir = Path(artifact_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    logger.info("[Spark ML] Loading demand historical mart...")
    df_raw = _load_demand_mart(spark, mart_dir)
    df = _build_features(df_raw)

    # ── Temporal split (no shuffle — strictly chronological) ──────────────────
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
        "[Spark ML] Temporal split — TRAIN=%d, VAL=%d, TEST=%d", rows_train, rows_val, rows_test
    )

    # ── Pipeline ──────────────────────────────────────────────────────────────
    indexer_cat = StringIndexer(
        inputCol="category_id", outputCol="category_idx", handleInvalid="keep"
    )
    indexer_rest = StringIndexer(
        inputCol="restaurant_id", outputCol="restaurant_idx", handleInvalid="keep"
    )
    assembler = VectorAssembler(inputCols=FEATURE_COLS, outputCol="features", handleInvalid="skip")
    gbt = GBTRegressor(
        featuresCol="features",
        labelCol=TARGET_COL,
        maxIter=25,
        maxDepth=4,
        stepSize=0.1,
        seed=42,
    )
    pipeline = Pipeline(stages=[indexer_cat, indexer_rest, assembler, gbt])

    logger.info("[Spark ML] Training GBTRegressor on %d rows...", rows_train)
    model = pipeline.fit(df_train)

    # ── Evaluation ────────────────────────────────────────────────────────────
    evaluator_rmse = RegressionEvaluator(
        labelCol=TARGET_COL, predictionCol="prediction", metricName="rmse"
    )
    evaluator_mae = RegressionEvaluator(
        labelCol=TARGET_COL, predictionCol="prediction", metricName="mae"
    )

    df_val_pred = model.transform(df_val)
    df_test_pred = model.transform(df_test)

    rmse_val = evaluator_rmse.evaluate(df_val_pred)
    mae_val = evaluator_mae.evaluate(df_val_pred)
    rmse_test = evaluator_rmse.evaluate(df_test_pred)
    mae_test = evaluator_mae.evaluate(df_test_pred)

    logger.info(
        "[Spark ML] Demand Forecast — VAL: RMSE=%.4f MAE=%.4f | TEST: RMSE=%.4f MAE=%.4f",
        rmse_val,
        mae_val,
        rmse_test,
        mae_test,
    )

    # ── Materialise predictions (train + val + test combined) ─────────────────
    df_all_pred = model.transform(df).select(
        "week_start_date",
        "menu_item_id",
        "restaurant_id",
        F.col(TARGET_COL).alias("actual_quantity"),
        F.round(F.col("prediction"), 2).alias("predicted_quantity"),
        F.round(F.abs(F.col(TARGET_COL) - F.col("prediction")), 2).alias("absolute_error"),
        F.when(F.col("week_start_date") <= TRAIN_END, "TRAIN")
        .when(F.col("week_start_date") <= VALIDATION_END, "VALIDATION")
        .when(F.col("week_start_date") <= TEST_END, "TEST")
        .otherwise("UNSEEN_COMPARISON")
        .alias("split"),
        F.lit("spark").alias("pipeline"),
    )

    out_path = output_dir / "ml_demand_forecast.parquet"
    if out_path.exists():
        import shutil

        if out_path.is_dir():
            shutil.rmtree(out_path)
        else:
            out_path.unlink()
    df_all_pred.coalesce(1).write.mode("overwrite").parquet(str(out_path))
    total_rows = df_all_pred.count()
    logger.info("[Spark ML] Materialised ml_demand_forecast.parquet: %d rows", total_rows)

    # ── Model metadata JSON ───────────────────────────────────────────────────
    duration = round(time.time() - t_start, 2)
    metadata: dict[str, Any] = {
        "pipeline": "spark",
        "task": "demand_forecast",
        "algorithm": "GBTRegressor",
        "feature_cols": FEATURE_COLS,
        "target_col": TARGET_COL,
        "train_end": TRAIN_END,
        "validation_end": VALIDATION_END,
        "test_end": TEST_END,
        "rows_train": rows_train,
        "rows_validation": rows_val,
        "rows_test": rows_test,
        "metrics": {
            "validation": {"rmse": round(rmse_val, 6), "mae": round(mae_val, 6)},
            "test": {"rmse": round(rmse_test, 6), "mae": round(mae_test, 6)},
        },
        "duration_sec": duration,
    }
    meta_path = artifact_dir / "spark_demand_forecast_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    logger.info("[Spark ML] Metadata saved to %s", meta_path)

    return metadata
