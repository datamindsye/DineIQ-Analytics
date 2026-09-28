"""Spark MLlib customer segmentation model for DineIQ Analytics Phase 4.

Reads mart_customer_rfm Parquet, scales RFM features, runs KMeans clustering
(k=4), assigns human-readable segment labels, and materialises results to
data/marts/spark/ml_customer_segmentation.parquet.

Segmentation is an unsupervised task — no train/test split by definition.
The model is deterministic (seed=42). Segment labels are assigned post-hoc
based on centroid RFM ordering: Champions, Loyal, At Risk, Lost.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from pyspark.ml import Pipeline
from pyspark.ml.clustering import BisectingKMeans, KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.ml.feature import StandardScaler, VectorAssembler
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from packages.common.logging import get_logger

logger = get_logger(__name__)

K_CLUSTERS = 4
FEATURE_COLS = ["recency_days", "frequency", "monetary_total"]

# Human-readable segment labels assigned by centroid rank analysis at runtime
# Order: [lowest_recency+highest_freq+highest_monetary = Champions, ...]
SEGMENT_LABELS = {0: "Champions", 1: "Loyal", 2: "At Risk", 3: "Lost"}


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
    logger.info("Loaded mart_customer_rfm: %d rows for segmentation", df.count())
    return df


def _assign_segment_labels(spark: SparkSession, df_pred: DataFrame) -> DataFrame:
    """Map cluster IDs to segment names based on mean RFM ranking of centroids."""
    # Compute per-cluster means
    cluster_stats = (
        df_pred.groupBy("prediction")
        .agg(
            F.avg("recency_days").alias("avg_recency"),
            F.avg("frequency").alias("avg_frequency"),
            F.avg("monetary_total").alias("avg_monetary"),
        )
        .orderBy("avg_recency")  # Low recency = more recent = better
    )
    rows = cluster_stats.collect()
    # Sort: ascending recency (recent first), descending frequency & monetary
    sorted_clusters = sorted(
        rows,
        key=lambda r: (r["avg_recency"], -r["avg_frequency"], -r["avg_monetary"]),
    )
    # Build mapping: cluster_id → segment name
    label_map_data = [
        (int(row["prediction"]), SEGMENT_LABELS.get(rank, f"Segment_{rank}"))
        for rank, row in enumerate(sorted_clusters)
    ]
    label_df = spark.createDataFrame(label_map_data, ["prediction", "segment_label"])
    return df_pred.join(label_df, on="prediction", how="left")


def train_customer_segmentation(
    spark: SparkSession,
    mart_dir: str | Path = "data/marts/spark",
    output_dir: str | Path = "data/marts/spark",
    artifact_dir: str | Path = "data/artifacts",
) -> dict[str, Any]:
    """Run candidate clustering algorithms and select the champion by Silhouette score."""
    t_start = time.time()
    mart_dir = Path(mart_dir).resolve()
    output_dir = Path(output_dir).resolve()
    artifact_dir = Path(artifact_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    logger.info("[Spark ML] Loading mart_customer_rfm for segmentation...")
    df = _load_rfm_mart(spark, mart_dir)

    # Ensure features are numeric
    for col in FEATURE_COLS:
        df = df.withColumn(col, F.col(col).cast("double"))

    assembler = VectorAssembler(
        inputCols=FEATURE_COLS, outputCol="raw_features", handleInvalid="skip"
    )
    scaler = StandardScaler(
        inputCol="raw_features", outputCol="features", withMean=True, withStd=True
    )
    prep_pipeline = Pipeline(stages=[assembler, scaler])
    prep_model = prep_pipeline.fit(df)
    df_prepped = prep_model.transform(df).persist()

    total_customers = df_prepped.count()
    logger.info("[Spark ML] Evaluating clustering candidates on %d customers...", total_customers)

    evaluator = ClusteringEvaluator(
        featuresCol="features", predictionCol="prediction", metricName="silhouette"
    )

    candidates_def = [
        (
            "KMeans",
            KMeans(
                featuresCol="features",
                predictionCol="prediction",
                k=K_CLUSTERS,
                seed=42,
                maxIter=50,
            ),
            {"k": K_CLUSTERS, "seed": 42, "maxIter": 50},
        ),
        (
            "BisectingKMeans",
            BisectingKMeans(
                featuresCol="features",
                predictionCol="prediction",
                k=K_CLUSTERS,
                seed=42,
                maxIter=50,
            ),
            {"k": K_CLUSTERS, "seed": 42, "maxIter": 50},
        ),
    ]

    candidate_results: list[dict[str, Any]] = []
    fitted_models: dict[str, Any] = {}

    for name, estimator, params in candidates_def:
        c_start = time.time()
        c_model = estimator.fit(df_prepped)
        c_duration = round(time.time() - c_start, 2)
        c_pred = c_model.transform(df_prepped)
        c_silhouette = round(float(evaluator.evaluate(c_pred)), 6)
        logger.info(
            "[Spark ML] Candidate %s Silhouette Score: %.4f (took %.2fs)",
            name,
            c_silhouette,
            c_duration,
        )
        candidate_results.append(
            {
                "algorithm": name,
                "hyperparameters": params,
                "validation_metrics": {"silhouette_score": c_silhouette},
                "training_duration_sec": c_duration,
            }
        )
        fitted_models[name] = (c_model, c_pred)

    # Champion selection: highest silhouette score
    sorted_candidates = sorted(
        candidate_results,
        key=lambda x: x["validation_metrics"]["silhouette_score"],
        reverse=True,
    )
    champion_info = sorted_candidates[0]
    champion_name = champion_info["algorithm"]
    champion_model, df_champion_pred = fitted_models[champion_name]
    best_silhouette = champion_info["validation_metrics"]["silhouette_score"]

    logger.info(
        "[Spark ML] Selected Champion: %s with Silhouette score %.4f",
        champion_name,
        best_silhouette,
    )

    # Assign human-readable segment labels
    df_labelled = _assign_segment_labels(spark, df_champion_pred)

    # Materialise
    df_out = df_labelled.select(
        "customer_id",
        F.col("prediction").alias("cluster_id"),
        "segment_label",
        "recency_days",
        "frequency",
        "monetary_total",
        F.lit("spark").alias("pipeline"),
    )

    out_path = output_dir / "ml_customer_segmentation.parquet"
    if out_path.exists():
        import shutil

        if out_path.is_dir():
            shutil.rmtree(out_path)
        else:
            out_path.unlink()
    df_out.coalesce(1).write.mode("overwrite").parquet(str(out_path))
    total_rows = df_out.count()
    logger.info("[Spark ML] Materialised ml_customer_segmentation.parquet: %d rows", total_rows)

    df_prepped.unpersist()

    duration = round(time.time() - t_start, 2)
    metadata: dict[str, Any] = {
        "pipeline": "spark",
        "task": "customer_segmentation",
        "model_version": "v2.0-phase6b",
        "selected_algorithm": champion_name,
        "algorithm": champion_name,
        "selection_criteria": "silhouette_score (higher is better)",
        "selection_reason": f"{champion_name} achieved highest Silhouette score ({best_silhouette:.4f})",
        "candidates": candidate_results,
        "k": K_CLUSTERS,
        "feature_cols": FEATURE_COLS,
        "silhouette_score": best_silhouette,
        "validation_metrics": {"silhouette_score": best_silhouette},
        "test_metrics": {"silhouette_score": best_silhouette},
        "segment_labels": SEGMENT_LABELS,
        "total_customers": total_rows,
        "rows_train": total_rows,
        "rows_validation": total_rows,
        "rows_test": total_rows,
        "duration_sec": duration,
    }
    meta_path = artifact_dir / "spark_customer_segmentation_metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))
    logger.info("[Spark ML] Metadata saved to %s", meta_path)

    return metadata
