"""Independent Python scikit-learn model training for DineIQ Analytics Phase 6B.

Trains candidate models per task, performs validation-only champion selection,
evaluates the selected champion on test data, and materialises predictions
to data/marts/python/.

Never imports from packages.pipeline_spark.

Tasks & Candidates:
    1. Demand Forecast  → Ridge, RandomForestRegressor, GradientBoostingRegressor
                          (Validation RMSE primary, MAE tie-breaker)
    2. Wastage Risk     → LogisticRegression, RandomForestClassifier, GradientBoostingClassifier
                          (Validation ROC-AUC primary, F1 tie-breaker)
    3. Churn Risk       → LogisticRegression, RandomForestClassifier, GradientBoostingClassifier
                          (Validation ROC-AUC primary, F1 tie-breaker)
    4. Customer Segmentation → KMeans, GaussianMixture
                          (Silhouette Score)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import make_pipeline
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
    """Train candidate regression models, select champion on validation RMSE, materialise predictions."""
    t_start = time.time()
    logger.info("[Python ML] Training Demand Forecast multi-model candidate competition...")

    df_train, df_val, df_test = _split(df, "week_start_date")
    X_all = _encode_features(df, DEMAND_FEATURES)

    X_train = X_all.loc[df_train.index]
    y_train = df_train[DEMAND_TARGET]
    X_val = X_all.loc[df_val.index]
    y_val = df_val[DEMAND_TARGET]
    X_test = X_all.loc[df_test.index]
    y_test = df_test[DEMAND_TARGET]

    def _reg_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mae = float(mean_absolute_error(y_true, y_pred))
        return {"rmse": round(rmse, 6), "mae": round(mae, 6)}

    candidates_def = [
        (
            "Ridge",
            make_pipeline(StandardScaler(), Ridge(alpha=1.0, random_state=42)),
            {"alpha": 1.0, "random_state": 42},
        ),
        (
            "RandomForestRegressor",
            RandomForestRegressor(n_estimators=40, max_depth=5, random_state=42, n_jobs=-1),
            {"n_estimators": 40, "max_depth": 5, "random_state": 42},
        ),
        (
            "GradientBoostingRegressor",
            GradientBoostingRegressor(
                n_estimators=60, max_depth=4, learning_rate=0.1, random_state=42
            ),
            {"n_estimators": 60, "max_depth": 4, "learning_rate": 0.1, "random_state": 42},
        ),
    ]

    candidate_results: list[dict[str, Any]] = []
    fitted_models: dict[str, Any] = {}

    for name, estimator, params in candidates_def:
        c_start = time.time()
        estimator.fit(X_train, y_train)
        c_duration = round(time.time() - c_start, 2)

        val_pred = estimator.predict(X_val)
        val_m = _reg_metrics(y_val, val_pred)

        logger.info(
            "[Python ML] Candidate %s — Val RMSE: %.4f | Val MAE: %.4f (took %.2fs)",
            name,
            val_m["rmse"],
            val_m["mae"],
            c_duration,
        )
        candidate_results.append(
            {
                "algorithm": name,
                "hyperparameters": params,
                "validation_metrics": val_m,
                "training_duration_sec": c_duration,
            }
        )
        fitted_models[name] = estimator

    # Validation-based selection: lower RMSE primary, lower MAE tie-breaker
    sorted_candidates = sorted(
        candidate_results,
        key=lambda x: (x["validation_metrics"]["rmse"], x["validation_metrics"]["mae"]),
    )
    champion_info = sorted_candidates[0]
    champion_name = champion_info["algorithm"]
    champion_model = fitted_models[champion_name]

    val_metrics = champion_info["validation_metrics"]
    test_metrics = _reg_metrics(y_test, champion_model.predict(X_test))

    logger.info(
        "[Python ML] Selected Champion: %s | Val RMSE: %.4f | Test RMSE: %.4f",
        champion_name,
        val_metrics["rmse"],
        test_metrics["rmse"],
    )

    # Materialise predictions across full dataframe with champion model
    raw_predictions = champion_model.predict(X_all)
    predictions = np.clip(raw_predictions, 0.0, None)

    out_df = df[["week_start_date", "menu_item_id", "restaurant_id", DEMAND_TARGET, "split"]].copy()
    out_df["predicted_quantity"] = np.round(predictions, 2)
    out_df["absolute_error"] = np.round(
        np.abs(out_df[DEMAND_TARGET] - out_df["predicted_quantity"]), 2
    )
    out_df.rename(columns={DEMAND_TARGET: "actual_quantity"}, inplace=True)
    out_df["pipeline"] = "python"

    _save_parquet(out_df, output_dir, "ml_demand_forecast")
    duration = round(time.time() - t_start, 2)
    meta: dict[str, Any] = {
        "pipeline": "python",
        "task": "demand_forecast",
        "model_version": "v2.0-phase6b",
        "selected_algorithm": champion_name,
        "algorithm": champion_name,
        "selection_criteria": "validation_rmse (lower is better, validation_mae tie-breaker)",
        "selection_reason": (
            f"{champion_name} selected with validation RMSE={val_metrics['rmse']:.4f} "
            f"and MAE={val_metrics['mae']:.4f}"
        ),
        "candidates": candidate_results,
        "feature_cols": DEMAND_FEATURES,
        "target_col": DEMAND_TARGET,
        "rows_train": len(df_train),
        "rows_validation": len(df_val),
        "rows_test": len(df_test),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
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
    """Train candidate classification models, select champion on validation ROC-AUC, materialise predictions."""
    t_start = time.time()
    logger.info("[Python ML] Training Wastage Risk multi-model candidate competition...")

    df_train, df_val, df_test = _split(df, "week_start_date")
    X_all = _encode_features(df, WASTAGE_FEATURES)

    X_train = X_all.loc[df_train.index]
    y_train = df_train[WASTAGE_TARGET]
    X_val = X_all.loc[df_val.index]
    y_val = df_val[WASTAGE_TARGET]
    X_test = X_all.loc[df_test.index]
    y_test = df_test[WASTAGE_TARGET]

    def _cls_metrics(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
        return {
            "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 6),
            "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 6),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 6),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 6),
        }

    candidates_def = [
        (
            "LogisticRegression",
            make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, random_state=42)),
            {"max_iter": 500, "random_state": 42},
        ),
        (
            "RandomForestClassifier",
            RandomForestClassifier(n_estimators=40, max_depth=5, random_state=42, n_jobs=-1),
            {"n_estimators": 40, "max_depth": 5, "random_state": 42},
        ),
        (
            "GradientBoostingClassifier",
            GradientBoostingClassifier(
                n_estimators=60, max_depth=4, learning_rate=0.1, random_state=42
            ),
            {"n_estimators": 60, "max_depth": 4, "learning_rate": 0.1, "random_state": 42},
        ),
    ]

    candidate_results: list[dict[str, Any]] = []
    fitted_models: dict[str, Any] = {}

    for name, estimator, params in candidates_def:
        c_start = time.time()
        estimator.fit(X_train, y_train)
        c_duration = round(time.time() - c_start, 2)

        val_pred = estimator.predict(X_val)
        val_prob = estimator.predict_proba(X_val)[:, 1]
        val_m = _cls_metrics(y_val, val_pred, val_prob)

        logger.info(
            "[Python ML] Candidate %s — Val ROC-AUC: %.4f | Val F1: %.4f (took %.2fs)",
            name,
            val_m["roc_auc"],
            val_m["f1"],
            c_duration,
        )
        candidate_results.append(
            {
                "algorithm": name,
                "hyperparameters": params,
                "validation_metrics": val_m,
                "training_duration_sec": c_duration,
            }
        )
        fitted_models[name] = estimator

    # Validation-based selection: higher ROC-AUC primary, higher F1 tie-breaker
    sorted_candidates = sorted(
        candidate_results,
        key=lambda x: (-x["validation_metrics"]["roc_auc"], -x["validation_metrics"]["f1"]),
    )
    champion_info = sorted_candidates[0]
    champion_name = champion_info["algorithm"]
    champion_model = fitted_models[champion_name]

    val_metrics = champion_info["validation_metrics"]
    test_pred = champion_model.predict(X_test)
    test_prob = champion_model.predict_proba(X_test)[:, 1]
    test_metrics = _cls_metrics(y_test, test_pred, test_prob)

    logger.info(
        "[Python ML] Selected Champion: %s | Val ROC-AUC: %.4f | Test ROC-AUC: %.4f",
        champion_name,
        val_metrics["roc_auc"],
        test_metrics["roc_auc"],
    )

    preds = champion_model.predict(X_all)
    probs = champion_model.predict_proba(X_all)[:, 1]
    out_df = df[
        ["week_start_date", "menu_item_id", "restaurant_id", WASTAGE_TARGET, "split"]
    ].copy()
    out_df["predicted_label"] = preds
    out_df["risk_probability"] = np.round(probs, 4)
    out_df.rename(columns={WASTAGE_TARGET: "actual_label"}, inplace=True)
    out_df["pipeline"] = "python"

    _save_parquet(out_df, output_dir, "ml_wastage_risk")
    duration = round(time.time() - t_start, 2)
    meta: dict[str, Any] = {
        "pipeline": "python",
        "task": "wastage_risk",
        "model_version": "v2.0-phase6b",
        "selected_algorithm": champion_name,
        "algorithm": champion_name,
        "selection_criteria": "validation_roc_auc (higher is better, validation_f1 tie-breaker)",
        "selection_reason": (
            f"{champion_name} selected with validation ROC-AUC={val_metrics['roc_auc']:.4f} "
            f"and F1={val_metrics['f1']:.4f}"
        ),
        "candidates": candidate_results,
        "feature_cols": WASTAGE_FEATURES,
        "target_col": WASTAGE_TARGET,
        "rows_train": len(df_train),
        "rows_validation": len(df_val),
        "rows_test": len(df_test),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
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
    """Train candidate classification models, select champion on validation ROC-AUC, materialise predictions."""
    t_start = time.time()
    logger.info("[Python ML] Training Churn Risk multi-model candidate competition...")

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

    def _cls_metrics(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray) -> dict[str, float]:
        if len(y_true) == 0 or len(np.unique(y_true)) < 2:
            return {"roc_auc": 0.0, "f1": 0.0, "precision": 0.0, "recall": 0.0}
        return {
            "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 6),
            "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 6),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 6),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 6),
        }

    candidates_def = [
        (
            "LogisticRegression",
            make_pipeline(StandardScaler(), LogisticRegression(max_iter=500, random_state=42)),
            {"max_iter": 500, "random_state": 42},
        ),
        (
            "RandomForestClassifier",
            RandomForestClassifier(n_estimators=40, max_depth=5, random_state=42, n_jobs=-1),
            {"n_estimators": 40, "max_depth": 5, "random_state": 42},
        ),
        (
            "GradientBoostingClassifier",
            GradientBoostingClassifier(
                n_estimators=60, max_depth=4, learning_rate=0.1, random_state=42
            ),
            {"n_estimators": 60, "max_depth": 4, "learning_rate": 0.1, "random_state": 42},
        ),
    ]

    candidate_results: list[dict[str, Any]] = []
    fitted_models: dict[str, Any] = {}

    for name, estimator, params in candidates_def:
        c_start = time.time()
        estimator.fit(X_train, y_train)
        c_duration = round(time.time() - c_start, 2)

        val_pred = estimator.predict(X_val)
        val_prob = estimator.predict_proba(X_val)[:, 1]
        val_m = _cls_metrics(y_val, val_pred, val_prob)

        logger.info(
            "[Python ML] Candidate %s — Val ROC-AUC: %.4f | Val F1: %.4f (took %.2fs)",
            name,
            val_m["roc_auc"],
            val_m["f1"],
            c_duration,
        )
        candidate_results.append(
            {
                "algorithm": name,
                "hyperparameters": params,
                "validation_metrics": val_m,
                "training_duration_sec": c_duration,
            }
        )
        fitted_models[name] = estimator

    # Validation-based selection: higher ROC-AUC primary, higher F1 tie-breaker
    sorted_candidates = sorted(
        candidate_results,
        key=lambda x: (-x["validation_metrics"]["roc_auc"], -x["validation_metrics"]["f1"]),
    )
    champion_info = sorted_candidates[0]
    champion_name = champion_info["algorithm"]
    champion_model = fitted_models[champion_name]

    val_metrics = champion_info["validation_metrics"]
    test_pred = champion_model.predict(X_test)
    test_prob = champion_model.predict_proba(X_test)[:, 1]
    test_metrics = _cls_metrics(y_test, test_pred, test_prob)

    logger.info(
        "[Python ML] Selected Champion: %s | Val ROC-AUC: %.4f | Test ROC-AUC: %.4f",
        champion_name,
        val_metrics["roc_auc"],
        test_metrics["roc_auc"],
    )

    X_all = df[CHURN_FEATURES].fillna(0)
    preds = champion_model.predict(X_all)
    probs = champion_model.predict_proba(X_all)[:, 1]
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
    duration = round(time.time() - t_start, 2)
    meta: dict[str, Any] = {
        "pipeline": "python",
        "task": "churn_risk",
        "model_version": "v2.0-phase6b",
        "selected_algorithm": champion_name,
        "algorithm": champion_name,
        "selection_criteria": "validation_roc_auc (higher is better, validation_f1 tie-breaker)",
        "selection_reason": (
            f"{champion_name} selected with validation ROC-AUC={val_metrics['roc_auc']:.4f} "
            f"and F1={val_metrics['f1']:.4f}"
        ),
        "candidates": candidate_results,
        "feature_cols": CHURN_FEATURES,
        "target_col": CHURN_TARGET,
        "rows_train": len(df_train),
        "rows_validation": len(df_val),
        "rows_test": len(df_test),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
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
    """Run candidate clustering models (KMeans, GaussianMixture), select champion by Silhouette score."""
    t_start = time.time()
    logger.info("[Python ML] Training Customer Segmentation candidate competition...")

    X = df[SEG_FEATURES].fillna(0).values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    candidates_def = [
        (
            "KMeans",
            KMeans(n_clusters=K_CLUSTERS, random_state=42, n_init=10, max_iter=300),
            {"n_clusters": K_CLUSTERS, "random_state": 42, "n_init": 10, "max_iter": 300},
        ),
        (
            "GaussianMixture",
            GaussianMixture(n_components=K_CLUSTERS, random_state=42),
            {"n_components": K_CLUSTERS, "random_state": 42},
        ),
    ]

    candidate_results: list[dict[str, Any]] = []
    fitted_candidates: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    sample_size = min(5000, len(X_scaled))

    for name, estimator, params in candidates_def:
        c_start = time.time()
        cluster_ids = estimator.fit_predict(X_scaled)
        c_duration = round(time.time() - c_start, 2)

        sil = round(
            float(
                silhouette_score(X_scaled, cluster_ids, sample_size=sample_size, random_state=42)
            ),
            6,
        )
        logger.info(
            "[Python ML] Candidate %s — Silhouette Score: %.4f (took %.2fs)", name, sil, c_duration
        )

        if hasattr(estimator, "cluster_centers_"):
            raw_centers = estimator.cluster_centers_
        elif hasattr(estimator, "means_"):
            raw_centers = estimator.means_
        else:
            raw_centers = np.array(
                [X_scaled[cluster_ids == i].mean(axis=0) for i in range(K_CLUSTERS)]
            )

        candidate_results.append(
            {
                "algorithm": name,
                "hyperparameters": params,
                "validation_metrics": {"silhouette_score": sil},
                "training_duration_sec": c_duration,
            }
        )
        fitted_candidates[name] = (cluster_ids, raw_centers)

    # Champion selection: highest silhouette score
    sorted_candidates = sorted(
        candidate_results,
        key=lambda x: x["validation_metrics"]["silhouette_score"],
        reverse=True,
    )
    champion_info = sorted_candidates[0]
    champion_name = champion_info["algorithm"]
    best_sil = champion_info["validation_metrics"]["silhouette_score"]
    cluster_ids, centers_scaled = fitted_candidates[champion_name]

    logger.info(
        "[Python ML] Selected Champion: %s with Silhouette score %.4f",
        champion_name,
        best_sil,
    )

    # Assign segment labels by centroid RFM ordering
    centers = pd.DataFrame(
        scaler.inverse_transform(centers_scaled),
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
    duration = round(time.time() - t_start, 2)
    meta: dict[str, Any] = {
        "pipeline": "python",
        "task": "customer_segmentation",
        "model_version": "v2.0-phase6b",
        "selected_algorithm": champion_name,
        "algorithm": champion_name,
        "selection_criteria": "silhouette_score (higher is better)",
        "selection_reason": f"{champion_name} achieved highest Silhouette score ({best_sil:.4f})",
        "candidates": candidate_results,
        "k": K_CLUSTERS,
        "feature_cols": SEG_FEATURES,
        "silhouette_score": best_sil,
        "validation_metrics": {"silhouette_score": best_sil},
        "test_metrics": {"silhouette_score": best_sil},
        "segment_labels": label_map,
        "total_customers": len(out_df),
        "rows_train": len(out_df),
        "rows_validation": len(out_df),
        "rows_test": len(out_df),
        "duration_sec": duration,
    }
    (artifact_dir / "python_customer_segmentation_metadata.json").write_text(
        json.dumps(meta, indent=2)
    )
    return meta
