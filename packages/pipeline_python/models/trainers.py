"""Independent Python scikit-learn model training for DineIQ Analytics Phase 4.

Trains four models using ONLY pandas DataFrames built by feature_builder.py.
Never imports from packages.pipeline_spark. Writes outputs to data/marts/python/.

Tasks:
    1. Demand Forecast  → GradientBoostingRegressor
    2. Wastage Risk     → GradientBoostingClassifier
    3. Churn Risk       → GradientBoostingClassifier
    4. Customer Segmentation → KMeans (scikit-learn)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

from packages.common.logging import get_logger

logger = get_logger(__name__)

TRAIN_END = pd.Timestamp("2025-08-31")
VALIDATION_END = pd.Timestamp("2025-10-31")
TEST_END = pd.Timestamp("2025-11-30")

# ── Demand Forecast ────────────────────────────────────────────────────────────
DEMAND_FEATURES = [
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
    "category_id",
    "restaurant_id",
]
DEMAND_TARGET = "weekly_quantity"

# ── Wastage Risk ───────────────────────────────────────────────────────────────
WASTAGE_FEATURES = [
    "cost_ratio",
    "quantity_ratio",
    "lag_1w_cost_ratio",
    "lag_4w_avg_cost_ratio",
    "lag_1w_quantity_ratio",
    "lag_4w_avg_quantity_ratio",
    "rolling_4w_waste_events",
    "week_of_year",
    "month",
    "menu_item_id",
    "restaurant_id",
]
WASTAGE_TARGET = "wastage_risk_label"

# ── Churn Risk ─────────────────────────────────────────────────────────────────
CHURN_FEATURES = [
    "recency_days",
    "frequency",
    "monetary_total",
    "avg_order_value",
    "rfm_score",
    "r_score",
    "f_score",
    "m_score",
]
CHURN_TARGET = "churn_label"

# ── Segmentation ───────────────────────────────────────────────────────────────
SEG_FEATURES = ["recency_days", "frequency", "monetary_total"]
K_CLUSTERS = 4
SEGMENT_LABELS = {0: "Champions", 1: "Loyal", 2: "At Risk", 3: "Lost"}


def _split(df: pd.DataFrame, date_col: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df[date_col] = pd.to_datetime(df[date_col])
    train = df[df[date_col] <= TRAIN_END]
    val = df[(df[date_col] > TRAIN_END) & (df[date_col] <= VALIDATION_END)]
    test = df[(df[date_col] > VALIDATION_END) & (df[date_col] <= TEST_END)]
    return train, val, test


def _save_parquet(df: pd.DataFrame, output_dir: Path, name: str) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.parquet"
    df.to_parquet(path, index=False, compression="snappy")
    logger.info("[Python ML] Saved %s: %d rows → %s", name, len(df), path)
    return len(df)


def _encode_features(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """Ensure all feature columns are numeric, converting string columns to consistent integer codes."""
    X = df[feature_cols].copy()
    for col in feature_cols:
        if X[col].dtype == "object" or isinstance(X[col].dtype, pd.StringDtype):
            X[col] = pd.factorize(X[col])[0].astype("float64")
        else:
            X[col] = pd.to_numeric(X[col], errors="coerce").fillna(0.0).astype("float64")
    return X.fillna(0.0)


# ── 1. Demand Forecast ─────────────────────────────────────────────────────────


def train_demand_forecast_python(
    df: pd.DataFrame,
    output_dir: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    """Train GradientBoostingRegressor for demand forecasting."""
    t = time.time()
    logger.info("[Python ML] Training Demand Forecast (GBR)...")

    df_train, df_val, df_test = _split(df, "week_start_date")
    X_all = _encode_features(df, DEMAND_FEATURES)

    X_train = X_all.loc[df_train.index]
    y_train = df_train[DEMAND_TARGET]
    X_val = X_all.loc[df_val.index]
    y_val = df_val[DEMAND_TARGET]
    X_test = X_all.loc[df_test.index]
    y_test = df_test[DEMAND_TARGET]

    model = GradientBoostingRegressor(
        n_estimators=60, max_depth=4, learning_rate=0.1, random_state=42
    )
    model.fit(X_train, y_train)

    def _reg_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mae = float(mean_absolute_error(y_true, y_pred))
        return {"rmse": round(rmse, 6), "mae": round(mae, 6)}

    val_metrics = _reg_metrics(y_val, model.predict(X_val))
    test_metrics = _reg_metrics(y_test, model.predict(X_test))
    logger.info("[Python ML] Demand — VAL: %s | TEST: %s", val_metrics, test_metrics)

    # Materialise predictions across full dataframe
    predictions = model.predict(X_all)
    out_df = df[["week_start_date", "menu_item_id", "restaurant_id", DEMAND_TARGET, "split"]].copy()
    out_df["predicted_quantity"] = np.round(predictions, 2)
    out_df["absolute_error"] = np.round(
        np.abs(out_df[DEMAND_TARGET] - out_df["predicted_quantity"]), 2
    )
    out_df.rename(columns={DEMAND_TARGET: "actual_quantity"}, inplace=True)
    out_df["pipeline"] = "python"

    _save_parquet(out_df, output_dir, "ml_demand_forecast")
    duration = round(time.time() - t, 2)
    meta: dict[str, Any] = {
        "pipeline": "python",
        "task": "demand_forecast",
        "algorithm": "GradientBoostingRegressor",
        "feature_cols": DEMAND_FEATURES,
        "target_col": DEMAND_TARGET,
        "rows_train": len(df_train),
        "rows_validation": len(df_val),
        "rows_test": len(df_test),
        "metrics": {"validation": val_metrics, "test": test_metrics},
        "duration_sec": duration,
    }
    (artifact_dir / "python_demand_forecast_metadata.json").write_text(json.dumps(meta, indent=2))
    return meta


# ── 2. Wastage Risk ────────────────────────────────────────────────────────────


def train_wastage_risk_python(
    df: pd.DataFrame,
    output_dir: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    """Train GradientBoostingClassifier for wastage risk."""
    t = time.time()
    logger.info("[Python ML] Training Wastage Risk (GBC)...")

    df_train, df_val, df_test = _split(df, "week_start_date")
    X_all = _encode_features(df, WASTAGE_FEATURES)

    X_train = X_all.loc[df_train.index]
    y_train = df_train[WASTAGE_TARGET]
    X_val = X_all.loc[df_val.index]
    y_val = df_val[WASTAGE_TARGET]
    X_test = X_all.loc[df_test.index]
    y_test = df_test[WASTAGE_TARGET]

    model = GradientBoostingClassifier(
        n_estimators=60, max_depth=4, learning_rate=0.1, random_state=42
    )
    model.fit(X_train, y_train)

    def _cls_metrics(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
        return {
            "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 6),
            "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 6),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 6),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 6),
        }

    val_metrics = _cls_metrics(y_val, model.predict(X_val), model.predict_proba(X_val)[:, 1])
    test_metrics = _cls_metrics(y_test, model.predict(X_test), model.predict_proba(X_test)[:, 1])
    logger.info("[Python ML] Wastage Risk — VAL: %s | TEST: %s", val_metrics, test_metrics)

    preds = model.predict(X_all)
    probs = model.predict_proba(X_all)[:, 1]
    out_df = df[
        ["week_start_date", "menu_item_id", "restaurant_id", WASTAGE_TARGET, "split"]
    ].copy()
    out_df["predicted_label"] = preds
    out_df["risk_probability"] = np.round(probs, 4)
    out_df.rename(columns={WASTAGE_TARGET: "actual_label"}, inplace=True)
    out_df["pipeline"] = "python"

    _save_parquet(out_df, output_dir, "ml_wastage_risk")
    duration = round(time.time() - t, 2)
    meta: dict[str, Any] = {
        "pipeline": "python",
        "task": "wastage_risk",
        "algorithm": "GradientBoostingClassifier",
        "feature_cols": WASTAGE_FEATURES,
        "target_col": WASTAGE_TARGET,
        "rows_train": len(df_train),
        "rows_validation": len(df_val),
        "rows_test": len(df_test),
        "metrics": {"validation": val_metrics, "test": test_metrics},
        "duration_sec": duration,
    }
    (artifact_dir / "python_wastage_risk_metadata.json").write_text(json.dumps(meta, indent=2))
    return meta


# ── 3. Churn Risk ──────────────────────────────────────────────────────────────


def train_churn_risk_python(
    df: pd.DataFrame,
    output_dir: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    """Train GradientBoostingClassifier for churn risk on full RFM feature set."""
    t = time.time()
    logger.info("[Python ML] Training Churn Risk (GBC)...")

    # RFM is a single-snapshot mart; split by recency proxy
    df_train = df[df["split"] == "TRAIN"]
    df_val = df[df["recency_days"].between(60, 120)]  # Validation cohort
    df_test = df[df["recency_days"] > 120]  # Test cohort (longer churned)

    X_train = df_train[CHURN_FEATURES].fillna(0)
    y_train = df_train[CHURN_TARGET]
    X_val = df_val[CHURN_FEATURES].fillna(0)
    y_val = df_val[CHURN_TARGET]
    X_test = df_test[CHURN_FEATURES].fillna(0)
    y_test = df_test[CHURN_TARGET]

    model = GradientBoostingClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42
    )
    model.fit(X_train, y_train)

    def _cls_metrics(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
        if len(y_true) == 0 or len(np.unique(y_true)) < 2:
            return {"roc_auc": 0.0, "f1": 0.0, "precision": 0.0, "recall": 0.0}
        return {
            "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 6),
            "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 6),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 6),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 6),
        }

    val_metrics = _cls_metrics(y_val, model.predict(X_val), model.predict_proba(X_val)[:, 1])
    test_metrics = _cls_metrics(y_test, model.predict(X_test), model.predict_proba(X_test)[:, 1])
    logger.info("[Python ML] Churn Risk — VAL: %s | TEST: %s", val_metrics, test_metrics)

    X_all = df[CHURN_FEATURES].fillna(0)
    preds = model.predict(X_all)
    probs = model.predict_proba(X_all)[:, 1]
    out_df = df[
        [
            "customer_id",
            CHURN_TARGET,
            "recency_days",
            "frequency",
            "monetary_total",
            "rfm_score",
            "split",
        ]
    ].copy()
    out_df["predicted_label"] = preds
    out_df["churn_probability"] = np.round(probs, 4)
    out_df.rename(columns={CHURN_TARGET: "actual_label"}, inplace=True)
    out_df["pipeline"] = "python"

    _save_parquet(out_df, output_dir, "ml_churn_risk")
    duration = round(time.time() - t, 2)
    meta: dict[str, Any] = {
        "pipeline": "python",
        "task": "churn_risk",
        "algorithm": "GradientBoostingClassifier",
        "feature_cols": CHURN_FEATURES,
        "target_col": CHURN_TARGET,
        "rows_train": len(df_train),
        "rows_validation": len(df_val),
        "rows_test": len(df_test),
        "metrics": {"validation": val_metrics, "test": test_metrics},
        "duration_sec": duration,
    }
    (artifact_dir / "python_churn_risk_metadata.json").write_text(json.dumps(meta, indent=2))
    return meta


# ── 4. Customer Segmentation ───────────────────────────────────────────────────


def train_customer_segmentation_python(
    df: pd.DataFrame,
    output_dir: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    """Run scikit-learn KMeans segmentation on RFM features."""
    t = time.time()
    logger.info("[Python ML] Training Customer Segmentation (KMeans k=%d)...", K_CLUSTERS)

    X = df[SEG_FEATURES].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kmeans = KMeans(n_clusters=K_CLUSTERS, random_state=42, n_init=10, max_iter=300)
    cluster_ids = kmeans.fit_predict(X_scaled)

    sil = round(
        float(silhouette_score(X_scaled, cluster_ids, sample_size=min(5000, len(X_scaled)))), 6
    )
    logger.info("[Python ML] KMeans Silhouette: %.4f", sil)

    # Assign segment labels by centroid RFM ordering
    centers = pd.DataFrame(
        scaler.inverse_transform(kmeans.cluster_centers_),
        columns=SEG_FEATURES,
    )
    centers["cluster_id"] = range(K_CLUSTERS)
    sorted_centers = centers.sort_values(
        ["recency_days", "frequency", "monetary_total"],
        ascending=[True, False, False],
    )
    label_map = {
        int(row["cluster_id"]): SEGMENT_LABELS.get(rank, f"Segment_{rank}")
        for rank, (_, row) in enumerate(sorted_centers.iterrows())
    }

    out_df = df[["customer_id", "recency_days", "frequency", "monetary_total"]].copy()
    out_df["cluster_id"] = cluster_ids
    out_df["segment_label"] = out_df["cluster_id"].map(label_map)
    out_df["pipeline"] = "python"

    _save_parquet(out_df, output_dir, "ml_customer_segmentation")
    duration = round(time.time() - t, 2)
    meta: dict[str, Any] = {
        "pipeline": "python",
        "task": "customer_segmentation",
        "algorithm": "KMeans",
        "k": K_CLUSTERS,
        "feature_cols": SEG_FEATURES,
        "silhouette_score": sil,
        "segment_labels": label_map,
        "total_customers": len(out_df),
        "duration_sec": duration,
    }
    (artifact_dir / "python_customer_segmentation_metadata.json").write_text(
        json.dumps(meta, indent=2)
    )
    return meta
