"""Independent Python feature engineering for DineIQ Analytics Phase 4.

Reads ONLY from data/cleaned/competition_benchmark_v1/ Parquet tables using
PyArrow + Pandas. Never imports from packages.pipeline_spark. Never reads
from data/marts/spark/. This enforces the dual-pipeline independence rule.

Produces four feature matrices:
    - demand_features.parquet       → weekly item-level demand
    - wastage_features.parquet      → weekly item-level wastage ratios
    - churn_features.parquet        → per-customer RFM from scratch
    - segmentation_features.parquet → same as churn (RFM for KMeans)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from packages.common.logging import get_logger

logger = get_logger(__name__)

TRAIN_END = pd.Timestamp("2025-08-31")
VALIDATION_END = pd.Timestamp("2025-10-31")
TEST_END = pd.Timestamp("2025-11-30")
CHURN_DAYS = 60


COLUMN_MAP = {
    "source_order_id": "order_id",
    "source_restaurant_id": "restaurant_id",
    "source_customer_id": "customer_id",
    "source_menu_item_id": "menu_item_id",
    "source_category_id": "category_id",
    "source_wastage_id": "wastage_id",
    "order_timestamp": "order_date",
    "wastage_timestamp": "waste_date",
    "quantity_lost": "waste_quantity",
    "cost_loss_amount": "waste_cost",
    "line_net_revenue": "line_total",
}


def _read_parquet(cleaned_dir: Path, table: str) -> pd.DataFrame:
    """Read a single cleaned table from Parquet, handling multi-file directories and renaming columns."""
    table_dir = cleaned_dir / f"{table}.parquet"
    if table_dir.is_dir():
        # Multi-part Spark-written Parquet
        parts = list(table_dir.glob("*.parquet"))
        if not parts:
            raise FileNotFoundError(f"No parquet parts found in {table_dir}")
        df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    elif table_dir.with_suffix("").with_suffix(".parquet").exists():
        df = pd.read_parquet(table_dir)
    else:
        # Single-file
        path = cleaned_dir / f"{table}.parquet"
        df = pd.read_parquet(path)

    rename_dict = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    if rename_dict:
        df = df.rename(columns=rename_dict)
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"]).dt.tz_localize(None)
    if "waste_date" in df.columns:
        df["waste_date"] = pd.to_datetime(df["waste_date"]).dt.tz_localize(None)
    return df


def build_demand_features(cleaned_dir: str | Path) -> pd.DataFrame:
    """Build weekly item-demand feature matrix from raw cleaned tables.

    Features derived independently — NO mart reads. Columns:
        week_start_date, menu_item_id, restaurant_id, category_id,
        weekly_quantity (target), lag_1w_quantity, lag_4w_quantity,
        rolling_4w_avg_quantity, rolling_4w_std_quantity,
        lag_1w_revenue, lag_4w_revenue, rolling_4w_avg_revenue,
        dow_avg_quantity, week_of_year, month, is_weekend, split.
    """
    cleaned_dir = Path(cleaned_dir).resolve()
    logger.info("[Python Features] Building demand features from %s...", cleaned_dir)

    orders = _read_parquet(cleaned_dir, "orders")
    order_items = _read_parquet(cleaned_dir, "order_items")
    menu_items = _read_parquet(cleaned_dir, "menu_items")

    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["week_start_date"] = orders["order_date"].dt.to_period("W").apply(lambda p: p.start_time)

    # Join
    oi = order_items.merge(
        orders[["order_id", "restaurant_id", "week_start_date", "order_date"]],
        on="order_id",
        how="inner",
    )
    oi = oi.merge(
        menu_items[["menu_item_id", "category_id"]],
        on="menu_item_id",
        how="left",
    )

    # Weekly aggregates per item per restaurant
    weekly = (
        oi.groupby(["week_start_date", "menu_item_id", "restaurant_id", "category_id"])
        .agg(
            weekly_quantity=("quantity", "sum"),
            weekly_revenue=("line_total", "sum"),
        )
        .reset_index()
        .sort_values(["menu_item_id", "restaurant_id", "week_start_date"])
    )

    # Anti-leakage lag features (shift by 1 week)
    g = weekly.groupby(["menu_item_id", "restaurant_id"])
    weekly["lag_1w_quantity"] = g["weekly_quantity"].shift(1)
    weekly["lag_4w_quantity"] = g["weekly_quantity"].shift(4)
    weekly["rolling_4w_avg_quantity"] = g["weekly_quantity"].transform(
        lambda x: x.shift(1).rolling(4).mean()
    )
    weekly["rolling_4w_std_quantity"] = g["weekly_quantity"].transform(
        lambda x: x.shift(1).rolling(4).std().fillna(0)
    )
    weekly["lag_1w_revenue"] = g["weekly_revenue"].shift(1)
    weekly["lag_4w_revenue"] = g["weekly_revenue"].shift(4)
    weekly["rolling_4w_avg_revenue"] = g["weekly_revenue"].transform(
        lambda x: x.shift(1).rolling(4).mean()
    )

    weekly["week_of_year"] = weekly["week_start_date"].dt.isocalendar().week.astype(int)
    weekly["month"] = weekly["week_start_date"].dt.month
    weekly["is_weekend"] = 0  # week-level aggregation

    # DOW avg (approximation from order-level)
    dow_avg = (
        oi.groupby(["menu_item_id", "restaurant_id", oi["order_date"].dt.dayofweek])["quantity"]
        .mean()
        .groupby(level=[0, 1])
        .mean()
        .rename("dow_avg_quantity")
        .reset_index()
    )
    weekly = weekly.merge(dow_avg, on=["menu_item_id", "restaurant_id"], how="left")

    # Fill nulls in lag columns with 0
    lag_cols = [c for c in weekly.columns if "lag" in c or "rolling" in c or "dow" in c]
    weekly[lag_cols] = weekly[lag_cols].fillna(0)

    # Temporal split label
    weekly["split"] = np.where(
        weekly["week_start_date"] <= TRAIN_END,
        "TRAIN",
        np.where(
            weekly["week_start_date"] <= VALIDATION_END,
            "VALIDATION",
            np.where(weekly["week_start_date"] <= TEST_END, "TEST", "UNSEEN_COMPARISON"),
        ),
    )

    logger.info("[Python Features] Demand features: %d rows", len(weekly))
    return weekly.reset_index(drop=True)


def build_wastage_features(cleaned_dir: str | Path) -> pd.DataFrame:
    """Build weekly wastage risk feature matrix from raw cleaned tables."""
    cleaned_dir = Path(cleaned_dir).resolve()
    logger.info("[Python Features] Building wastage features from %s...", cleaned_dir)

    wastage = _read_parquet(cleaned_dir, "wastage")
    order_items = _read_parquet(cleaned_dir, "order_items")
    orders = _read_parquet(cleaned_dir, "orders")

    wastage["waste_date"] = pd.to_datetime(wastage["waste_date"])
    wastage["week_start_date"] = (
        wastage["waste_date"].dt.to_period("W").apply(lambda p: p.start_time)
    )
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    orders["week_start_date"] = orders["order_date"].dt.to_period("W").apply(lambda p: p.start_time)

    # Weekly revenue and sold quantity from order side
    oi = order_items.merge(orders[["order_id", "restaurant_id", "week_start_date"]], on="order_id")
    sold_agg = (
        oi.groupby(["week_start_date", "menu_item_id", "restaurant_id"])
        .agg(sold_quantity=("quantity", "sum"), gross_revenue=("line_total", "sum"))
        .reset_index()
    )

    # Weekly wastage aggregation — only prepared dishes (menu_item_id IS NOT NULL)
    prepared = wastage[wastage["menu_item_id"].notna()].copy()
    waste_agg = (
        prepared.groupby(["week_start_date", "menu_item_id", "restaurant_id"])
        .agg(waste_quantity=("waste_quantity", "sum"), waste_cost=("waste_cost", "sum"))
        .reset_index()
    )

    merged = waste_agg.merge(
        sold_agg, on=["week_start_date", "menu_item_id", "restaurant_id"], how="left"
    ).fillna({"sold_quantity": 0, "gross_revenue": 0})

    merged["cost_ratio"] = np.where(
        merged["gross_revenue"] > 0, merged["waste_cost"] / merged["gross_revenue"], 0.0
    )
    merged["quantity_ratio"] = np.where(
        merged["sold_quantity"] > 0, merged["waste_quantity"] / merged["sold_quantity"], 0.0
    )
    merged["wastage_risk_label"] = (
        (merged["cost_ratio"] >= 0.05) | (merged["quantity_ratio"] >= 0.10)
    ).astype(int)

    merged = merged.sort_values(["menu_item_id", "restaurant_id", "week_start_date"])
    g = merged.groupby(["menu_item_id", "restaurant_id"])
    merged["lag_1w_cost_ratio"] = g["cost_ratio"].shift(1).fillna(0)
    merged["lag_4w_avg_cost_ratio"] = (
        g["cost_ratio"].transform(lambda x: x.shift(1).rolling(4).mean()).fillna(0)
    )
    merged["lag_1w_quantity_ratio"] = g["quantity_ratio"].shift(1).fillna(0)
    merged["lag_4w_avg_quantity_ratio"] = (
        g["quantity_ratio"].transform(lambda x: x.shift(1).rolling(4).mean()).fillna(0)
    )
    merged["rolling_4w_waste_events"] = (
        g["wastage_risk_label"].transform(lambda x: x.shift(1).rolling(4).sum()).fillna(0)
    )
    merged["week_of_year"] = merged["week_start_date"].dt.isocalendar().week.astype(int)
    merged["month"] = merged["week_start_date"].dt.month

    merged["split"] = np.where(
        merged["week_start_date"] <= TRAIN_END,
        "TRAIN",
        np.where(
            merged["week_start_date"] <= VALIDATION_END,
            "VALIDATION",
            np.where(merged["week_start_date"] <= TEST_END, "TEST", "UNSEEN_COMPARISON"),
        ),
    )

    logger.info("[Python Features] Wastage features: %d rows", len(merged))
    return merged.reset_index(drop=True)


def build_churn_features(cleaned_dir: str | Path) -> pd.DataFrame:
    """Build per-customer RFM features and churn label from raw cleaned tables."""
    cleaned_dir = Path(cleaned_dir).resolve()
    logger.info("[Python Features] Building churn/RFM features from %s...", cleaned_dir)

    customers = _read_parquet(cleaned_dir, "customers")
    orders = _read_parquet(cleaned_dir, "orders")

    # Use only completed orders in TRAIN period to avoid leakage
    completed = orders[
        (orders["order_status"] == "Completed") & (orders["order_date"] <= TRAIN_END)
    ].copy()

    snapshot_date = TRAIN_END
    rfm = (
        completed.groupby("customer_id")
        .agg(
            last_order_date=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary_total=("total_amount", "sum"),
        )
        .reset_index()
    )
    rfm["recency_days"] = (snapshot_date - rfm["last_order_date"]).dt.days
    rfm["avg_order_value"] = rfm["monetary_total"] / rfm["frequency"].clip(lower=1)

    # RFM quintile scores (5=best)
    rfm["r_score"] = pd.qcut(rfm["recency_days"], q=5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["f_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["m_score"] = pd.qcut(
        rfm["monetary_total"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["rfm_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

    # Churn label: no order in CHURN_DAYS after snapshot
    rfm["churn_label"] = (rfm["recency_days"] > CHURN_DAYS).astype(int)
    rfm["split"] = "TRAIN"

    # Include all customers (even those with no orders = churned by default)
    all_customers = customers[["customer_id"]].copy()
    rfm_full = all_customers.merge(rfm, on="customer_id", how="left")
    rfm_full["churn_label"] = rfm_full["churn_label"].fillna(1).astype(int)
    rfm_full["recency_days"] = rfm_full["recency_days"].fillna(9999.0)
    rfm_full["frequency"] = rfm_full["frequency"].fillna(0.0)
    rfm_full["monetary_total"] = rfm_full["monetary_total"].fillna(0.0)
    rfm_full["avg_order_value"] = rfm_full["avg_order_value"].fillna(0.0)
    for sc in ["r_score", "f_score", "m_score", "rfm_score"]:
        rfm_full[sc] = rfm_full[sc].fillna(0.0)
    rfm_full["split"] = rfm_full["split"].fillna("TRAIN")

    logger.info("[Python Features] Churn/RFM features: %d customers", len(rfm_full))
    return rfm_full.reset_index(drop=True)


def save_features(df: pd.DataFrame, output_dir: Path, name: str) -> Path:
    """Save a feature DataFrame as Parquet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{name}.parquet"
    df.to_parquet(path, index=False, compression="snappy")
    logger.info("[Python Features] Saved %s: %d rows → %s", name, len(df), path)
    return path
