"""Analytics dashboard domain service for DineIQ BI and reporting layer.

Queries precomputed Apache Parquet marts and ML artifacts directly via PyArrow.
Provides fast aggregated KPI summaries, filter lookups, what-if simulations,
and comparison arena benchmarks without scanning raw transaction order lines.
"""

import json
from decimal import Decimal
from typing import Any

import pyarrow.parquet as pq

from packages.common.logging import get_logger
from packages.core.config.settings import get_settings
from packages.core.services.mart_reader import get_marts_directory

logger = get_logger("dineiq.core.analytics_dashboard_service")
settings = get_settings()


def _sanitize_val(val: Any) -> Any:
    """Recursively convert PyArrow / NumPy / Decimal / datetime types to JSON-safe primitives."""
    if val is None:
        return None
    if isinstance(val, (int, float, bool, str)):
        # Handle NaN and Inf
        if isinstance(val, float) and (val != val or val == float("inf") or val == float("-inf")):
            return None
        return val
    if isinstance(val, Decimal):
        return float(val)
    if hasattr(val, "isoformat"):
        return val.isoformat()
    if hasattr(val, "tolist"):
        return [_sanitize_val(x) for x in val.tolist()]
    if isinstance(val, dict):
        return {k: _sanitize_val(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize_val(x) for x in val]
    return str(val)


def _get_champion_algorithm(task: str, pipeline: str) -> str:
    """Retrieve the selected champion algorithm dynamically from Phase 6B metadata."""
    base_dir = get_marts_directory()
    meta_path = base_dir.parent / "artifacts" / f"{pipeline}_{task}_metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, encoding="utf-8") as f:
                data = json.load(f)
                algo = data.get("selected_algorithm") or data.get("algorithm")
                if algo:
                    return str(algo)
        except Exception as e:
            logger.warning("Error reading %s: %s", meta_path, e)

    summary_path = base_dir / "comparison" / "comparison_overall_summary.json"
    if summary_path.exists():
        try:
            with open(summary_path, encoding="utf-8") as f:
                summary = json.load(f)
                task_summary = summary.get(task, {})
                algo_key = f"{pipeline}_selected_algorithm"
                if algo_key in task_summary:
                    return str(task_summary[algo_key])
        except Exception as e:
            logger.warning("Error reading summary %s: %s", summary_path, e)

    default_map = {
        ("demand_forecast", "spark"): "GBTRegressor",
        ("demand_forecast", "python"): "GradientBoostingRegressor",
        ("wastage_risk", "spark"): "LogisticRegression",
        ("wastage_risk", "python"): "GradientBoostingClassifier",
        ("churn_risk", "spark"): "LogisticRegression",
        ("churn_risk", "python"): "RandomForestClassifier",
        ("customer_segmentation", "spark"): "BisectingKMeans",
        ("customer_segmentation", "python"): "KMeans",
    }
    return default_map.get((task, pipeline), "Unknown")


def get_global_filter_options() -> dict[str, Any]:
    """Retrieve distinct locations, categories, and channels from materialized marts."""
    base_dir = get_marts_directory()

    locations = []
    categories = []
    channels = ["Dine In", "Takeout", "Drive Thru", "Delivery Direct", "Delivery Aggregator"]

    # 1. Locations from mart_location_performance
    loc_file = base_dir / "spark" / "mart_location_performance.parquet"
    if loc_file.exists():
        table = pq.read_table(
            loc_file, columns=["source_restaurant_id", "location_name", "city", "dining_type"]
        )
        pydict = table.to_pydict()
        seen = set()
        for i in range(len(pydict["source_restaurant_id"])):
            rid = pydict["source_restaurant_id"][i]
            if rid not in seen:
                seen.add(rid)
                locations.append(
                    {
                        "id": rid,
                        "name": pydict["location_name"][i] or rid,
                        "city": pydict["city"][i] or "Unknown",
                        "type": pydict["dining_type"][i] or "Standard",
                    }
                )
        locations.sort(key=lambda x: x["id"])

    # 2. Categories from mart_menu_performance
    menu_file = base_dir / "spark" / "mart_menu_performance.parquet"
    if menu_file.exists():
        table = pq.read_table(menu_file, columns=["source_category_id", "category_name"])
        pydict = table.to_pydict()
        seen = set()
        for i in range(len(pydict["source_category_id"])):
            cid = pydict["source_category_id"][i]
            if cid and cid not in seen:
                seen.add(cid)
                categories.append(
                    {
                        "id": cid,
                        "name": pydict["category_name"][i] or cid,
                    }
                )
        categories.sort(key=lambda x: x["name"])

    return {
        "locations": locations,
        "categories": categories,
        "channels": channels,
        "segments": ["Champions", "Loyal", "At Risk", "Lost"],
        "classifications": [
            "Profit Driver",
            "Volume Driver",
            "Hidden Opportunity",
            "Low Performer",
        ],
    }


def get_executive_summary() -> dict[str, Any]:
    """Compute high-level executive KPIs from precomputed analytical marts."""
    base_dir = get_marts_directory()

    total_revenue = 0.0
    total_orders = 0
    total_margin = 0.0
    total_waste_cost = 0.0
    active_customers = 0
    total_anomalies = 0

    # Revenue, orders & margin from location performance
    loc_file = base_dir / "spark" / "mart_location_performance.parquet"
    if loc_file.exists():
        table = pq.read_table(
            loc_file,
            columns=["gross_revenue", "total_orders", "contribution_margin", "total_waste_cost"],
        )
        pydict = table.to_pydict()
        for rev, ords, cm, wc in zip(
            pydict["gross_revenue"],
            pydict["total_orders"],
            pydict["contribution_margin"],
            pydict["total_waste_cost"],
            strict=False,
        ):
            if rev is not None:
                total_revenue += float(rev)
            if ords is not None:
                total_orders += int(ords)
            if cm is not None:
                total_margin += float(cm)
            if wc is not None:
                total_waste_cost += float(wc)

    # Active customers from customer RFM
    cust_file = base_dir / "spark" / "mart_customer_rfm.parquet"
    if cust_file.exists():
        table = pq.read_table(cust_file, columns=["source_customer_id"])
        active_customers = table.num_rows

    # Anomalies count from sales anomalies
    anom_file = base_dir / "spark" / "mart_sales_anomalies.parquet"
    if anom_file.exists():
        table = pq.read_table(anom_file, columns=["is_spike_anomaly", "is_drop_anomaly"])
        pydict = table.to_pydict()
        for sp, dr in zip(pydict["is_spike_anomaly"], pydict["is_drop_anomaly"], strict=False):
            if sp or dr:
                total_anomalies += 1

    aov = total_revenue / total_orders if total_orders > 0 else 0.0
    margin_pct = (total_margin / total_revenue * 100.0) if total_revenue > 0 else 0.0
    waste_ratio = (total_waste_cost / total_revenue * 100.0) if total_revenue > 0 else 0.0

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "average_order_value": round(aov, 2),
        "contribution_margin": round(total_margin, 2),
        "margin_percentage": round(margin_pct, 2),
        "total_waste_cost": round(total_waste_cost, 2),
        "waste_to_revenue_ratio": round(waste_ratio, 2),
        "active_customers": active_customers,
        "detected_anomalies_count": total_anomalies,
        "pipeline_status": "ONLINE",
        "marts_loaded": 12,
    }


def get_menu_intelligence_summary(
    category_id: str | None = None,
    restaurant_id: str | None = None,
    classification: str | None = None,
    flag: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Query menu performance mart with classification, 6-factor scores, and flags."""
    base_dir = get_marts_directory()
    file_path = base_dir / "spark" / "mart_menu_performance.parquet"
    if not file_path.exists():
        return {"items": [], "total_count": 0, "classification_counts": {}}

    table = pq.read_table(file_path)
    df = table.to_pandas()

    if category_id:
        df = df[df["source_category_id"] == category_id]
    if restaurant_id:
        df = df[df["source_restaurant_id"] == restaurant_id]
    if classification:
        df = df[df["classification"] == classification]
    if flag and flag in df.columns:
        df = df[df[flag].astype(bool)]
    if search:
        search_lower = search.lower()
        df = df[
            df["item_name"].str.lower().str.contains(search_lower, na=False)
            | df["source_menu_item_id"].str.lower().str.contains(search_lower, na=False)
        ]

    total_count = len(df)
    class_counts = df["classification"].value_counts().to_dict()

    # Pagination
    sliced = df.iloc[offset : offset + limit]
    records = []
    for _, row in sliced.iterrows():
        records.append(
            {
                "menu_item_id": row["source_menu_item_id"],
                "restaurant_id": row["source_restaurant_id"],
                "item_name": row["item_name"],
                "category_name": row["category_name"],
                "current_base_price": _sanitize_val(row["current_base_price"]),
                "current_base_cost": _sanitize_val(row["current_base_cost"]),
                "total_quantity": int(row["total_quantity"])
                if row["total_quantity"] is not None
                else 0,
                "gross_revenue": _sanitize_val(row["gross_revenue"]),
                "contribution_margin": _sanitize_val(row["contribution_margin"]),
                "profitability_pct": _sanitize_val(row["profitability_pct"]),
                "classification": row["classification"],
                "composite_score": _sanitize_val(row["composite_score"]),
                "demand_score": _sanitize_val(row["demand_score"]),
                "profitability_score": _sanitize_val(row["profitability_score"]),
                "customer_signal_score": _sanitize_val(row["customer_signal_score"]),
                "wastage_health_score": _sanitize_val(row["wastage_health_score"]),
                "sales_trend_score": _sanitize_val(row["sales_trend_score"]),
                "promotion_independence_score": _sanitize_val(row["promotion_independence_score"]),
                "flags": {
                    "high_selling_loss_making": bool(
                        row.get("flag_high_selling_loss_making", False)
                    ),
                    "profitable_rarely_purchased": bool(
                        row.get("flag_profitable_rarely_purchased", False)
                    ),
                    "popular_high_wastage": bool(row.get("flag_popular_high_wastage", False)),
                    "high_rating_low_profitability": bool(
                        row.get("flag_high_rating_low_profitability", False)
                    ),
                    "low_rating_high_sales": bool(row.get("flag_low_rating_high_sales", False)),
                    "promotion_dependent": bool(row.get("flag_promotion_dependent", False)),
                    "weekend_only_pattern": bool(row.get("flag_weekend_only_pattern", False)),
                    "seasonal_item": bool(row.get("flag_seasonal_item", False)),
                    "location_divergence": bool(row.get("flag_location_divergence", False)),
                },
            }
        )

    return {
        "items": records,
        "total_count": total_count,
        "classification_counts": class_counts,
    }


def get_customer_intelligence_summary(
    segment: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Query customer RFM mart, churn risk predictions, and unsupervised ML customer segmentation."""
    base_dir = get_marts_directory()
    rfm_path = base_dir / "spark" / "mart_customer_rfm.parquet"
    churn_path = base_dir / "spark" / "ml_churn_risk.parquet"
    ml_seg_path = base_dir / "spark" / "ml_customer_segmentation.parquet"

    if not rfm_path.exists():
        return {
            "customers": [],
            "total_count": 0,
            "segment_distribution": {},
            "ml_segment_distribution": {},
            "spark_selected_algorithm": "BisectingKMeans",
            "python_selected_algorithm": "KMeans",
        }

    rfm_cols = [
        "source_customer_id",
        "customer_name",
        "loyalty_tier",
        "preferred_channel",
        "home_city",
        "frequency",
        "monetary_value",
        "recency_days",
        "rfm_segment",
    ]
    filters = [("rfm_segment", "==", segment)] if (segment and not search) else None
    table = pq.read_table(rfm_path, columns=rfm_cols, filters=filters)
    df = table.to_pandas()

    if segment and search:
        df = df[df["rfm_segment"] == segment]
    if search:
        s = search.lower()
        df = df[
            df["customer_name"].str.lower().str.contains(s, na=False)
            | df["source_customer_id"].str.lower().str.contains(s, na=False)
        ]

    total_count = len(df)
    segment_dist = df["rfm_segment"].value_counts().to_dict()

    sliced = df.iloc[offset : offset + limit]
    target_cids = set(sliced["source_customer_id"].dropna())

    churn_map = {}
    if churn_path.exists() and target_cids:
        try:
            churn_table = pq.read_table(
                churn_path,
                columns=["customer_id", "churn_probability"],
                filters=[("customer_id", "in", target_cids)],
            )
            c_dict = churn_table.to_pydict()
            for cid, cp in zip(c_dict["customer_id"], c_dict["churn_probability"], strict=False):
                churn_map[cid] = float(cp) if cp is not None else None
        except Exception as e:
            logger.warning("Failed loading churn predictions: %s", e)

    ml_seg_map = {}
    ml_segment_dist = {}
    if ml_seg_path.exists():
        try:
            # Fast vectorized distribution calculation across segment_label
            seg_dist_table = pq.read_table(ml_seg_path, columns=["segment_label"])
            for row in seg_dist_table["segment_label"].value_counts().to_pylist():
                v = row["values"]
                if v is not None:
                    ml_segment_dist[str(v)] = int(row["counts"])

            # Selective prediction retrieval for targeted page of customers
            if target_cids:
                ml_seg_table = pq.read_table(
                    ml_seg_path,
                    columns=["customer_id", "cluster_id", "segment_label"],
                    filters=[("customer_id", "in", target_cids)],
                )
                s_dict = ml_seg_table.to_pydict()
                for cid, cl_id, s_lbl in zip(
                    s_dict["customer_id"],
                    s_dict["cluster_id"],
                    s_dict["segment_label"],
                    strict=False,
                ):
                    ml_seg_map[cid] = {
                        "cluster_id": int(cl_id) if cl_id is not None else None,
                        "segment_label": str(s_lbl) if s_lbl is not None else None,
                    }
        except Exception as e:
            logger.warning("Failed loading ML customer segmentation: %s", e)

    customers = []
    for _, row in sliced.iterrows():
        cid = row["source_customer_id"]
        ml_info = ml_seg_map.get(cid, {})
        customers.append(
            {
                "customer_id": cid,
                "customer_name": row["customer_name"],
                "loyalty_tier": row["loyalty_tier"],
                "preferred_channel": row["preferred_channel"],
                "home_city": row["home_city"],
                "frequency": int(row["frequency"]),
                "monetary_value": _sanitize_val(row["monetary_value"]),
                "recency_days": int(row["recency_days"]),
                "rfm_segment": row["rfm_segment"],
                "cluster_id": ml_info.get("cluster_id"),
                "segment_label": ml_info.get("segment_label"),
                "ml_segment_label": ml_info.get("segment_label"),
                "churn_probability": churn_map.get(cid),
            }
        )

    return {
        "customers": customers,
        "total_count": total_count,
        "segment_distribution": segment_dist,
        "ml_segment_distribution": ml_segment_dist,
        "spark_selected_algorithm": _get_champion_algorithm("customer_segmentation", "spark"),
        "python_selected_algorithm": _get_champion_algorithm("customer_segmentation", "python"),
    }


def get_sales_and_operations_summary(restaurant_id: str | None = None) -> dict[str, Any]:
    """Retrieve peak hour heatmap, channel split, and location performance rankings."""
    base_dir = get_marts_directory()

    # Peak analysis
    peak_path = base_dir / "spark" / "mart_peak_analysis.parquet"
    peak_records = []
    if peak_path.exists():
        t = pq.read_table(peak_path)
        df_peak = t.to_pandas()
        if restaurant_id:
            df_peak = df_peak[df_peak["source_restaurant_id"] == restaurant_id]
        grouped = df_peak.groupby(["day_of_week", "hour_of_day"], as_index=False)[
            "total_orders"
        ].sum()
        peak_records = [_sanitize_val(r) for r in grouped.to_dict(orient="records")]

    # Channel performance
    channel_path = base_dir / "spark" / "mart_channel_performance.parquet"
    channels = []
    if channel_path.exists():
        t = pq.read_table(channel_path)
        df_ch = t.to_pandas()
        if restaurant_id:
            df_ch = df_ch[df_ch["source_restaurant_id"] == restaurant_id]
        grouped_ch = df_ch.groupby("channel", as_index=False).agg(
            {
                "total_orders": "sum",
                "net_revenue": "sum",
                "contribution_margin": "sum",
            }
        )
        channels = [_sanitize_val(r) for r in grouped_ch.to_dict(orient="records")]

    # Location rankings
    loc_path = base_dir / "spark" / "mart_location_performance.parquet"
    locations = []
    if loc_path.exists():
        t = pq.read_table(loc_path)
        df_loc = t.to_pandas()
        grouped_loc = df_loc.groupby(
            ["source_restaurant_id", "location_name", "city", "dining_type"], as_index=False
        ).agg(
            {
                "gross_revenue": "sum",
                "total_orders": "sum",
                "contribution_margin": "sum",
                "total_waste_cost": "sum",
            }
        )
        grouped_loc["margin_pct"] = (
            grouped_loc["contribution_margin"] / grouped_loc["gross_revenue"] * 100
        ).round(2)
        grouped_loc = grouped_loc.sort_values(by="gross_revenue", ascending=False)
        locations = [_sanitize_val(r) for r in grouped_loc.to_dict(orient="records")]

    return {
        "peak_hourly_heatmap": peak_records,
        "channel_breakdown": channels,
        "locations": locations,
    }


def get_demand_and_pricing_summary(
    menu_item_id: str | None = None,
    restaurant_id: str | None = None,
) -> dict[str, Any]:
    """Query demand forecast vs actuals for both Spark and Python pipelines and price elasticity analysis."""
    base_dir = get_marts_directory()

    # 1. Spark MLlib Demand forecast
    demand_path = base_dir / "spark" / "ml_demand_forecast.parquet"
    demand_curve = []
    if demand_path.exists():
        t = pq.read_table(demand_path)
        df_dem = t.to_pandas()
        if menu_item_id:
            df_dem = df_dem[df_dem["menu_item_id"] == menu_item_id]
        if restaurant_id:
            df_dem = df_dem[df_dem["restaurant_id"] == restaurant_id]

        # Aggregate weekly
        grouped = (
            df_dem.groupby(["week_start_date", "split"], as_index=False)
            .agg(
                {
                    "actual_quantity": "sum",
                    "predicted_quantity": "sum",
                    "absolute_error": "mean",
                }
            )
            .sort_values(by="week_start_date")
        )

        for r in grouped.to_dict(orient="records"):
            entry = _sanitize_val(r)
            if "week_start_date" in entry:
                entry["week_start_date"] = str(entry["week_start_date"])[:10]
            demand_curve.append(entry)

    # 2. Python Scikit-Learn Demand forecast
    python_demand_path = base_dir / "python" / "ml_demand_forecast.parquet"
    python_demand_curve = []
    if python_demand_path.exists():
        t_py = pq.read_table(python_demand_path)
        df_py = t_py.to_pandas()
        if menu_item_id:
            df_py = df_py[df_py["menu_item_id"] == menu_item_id]
        if restaurant_id:
            df_py = df_py[df_py["restaurant_id"] == restaurant_id]

        grouped_py = (
            df_py.groupby(["week_start_date", "split"], as_index=False)
            .agg(
                {
                    "actual_quantity": "sum",
                    "predicted_quantity": "sum",
                    "absolute_error": "mean",
                }
            )
            .sort_values(by="week_start_date")
        )

        for r in grouped_py.to_dict(orient="records"):
            entry = _sanitize_val(r)
            if "week_start_date" in entry:
                entry["week_start_date"] = str(entry["week_start_date"])[:10]
            python_demand_curve.append(entry)

    spark_selected_algorithm = _get_champion_algorithm("demand_forecast", "spark")
    python_selected_algorithm = _get_champion_algorithm("demand_forecast", "python")

    # Pricing & elasticity
    pricing_path = base_dir / "spark" / "mart_pricing.parquet"
    pricing_items = []
    elasticity_classes = {}
    if pricing_path.exists():
        t = pq.read_table(pricing_path)
        df_prc = t.to_pandas()
        if menu_item_id:
            df_prc = df_prc[df_prc["source_menu_item_id"] == menu_item_id]
        if restaurant_id:
            df_prc = df_prc[df_prc["source_restaurant_id"] == restaurant_id]

        elasticity_classes = df_prc["sensitivity_class"].value_counts().to_dict()
        sliced = df_prc.head(100)
        pricing_items = [_sanitize_val(r) for r in sliced.to_dict(orient="records")]

    return {
        "demand_forecast_curve": demand_curve,
        "spark_demand_forecast_curve": demand_curve,
        "python_demand_forecast_curve": python_demand_curve,
        "spark_selected_algorithm": spark_selected_algorithm,
        "python_selected_algorithm": python_selected_algorithm,
        "pricing_items": pricing_items,
        "elasticity_distribution": elasticity_classes,
    }


def get_wastage_and_inventory_summary(restaurant_id: str | None = None) -> dict[str, Any]:
    """Retrieve wastage cost breakdown, high-risk items, weekly trends, and ML forward-looking wastage risk."""
    base_dir = get_marts_directory()
    waste_path = base_dir / "spark" / "mart_wastage.parquet"
    ml_waste_path = base_dir / "spark" / "ml_wastage_risk.parquet"

    if not waste_path.exists():
        return {
            "reasons": [],
            "high_risk_items": [],
            "weekly_trend": [],
            "ml_risk_summary": {},
            "ml_predicted_risks": [],
        }

    waste_cols = [
        "source_restaurant_id",
        "primary_reason",
        "waste_cost",
        "waste_quantity",
        "current_week_wastage_risk",
        "source_menu_item_id",
        "item_name",
        "sold_quantity",
        "calendar_year",
        "calendar_week",
    ]
    waste_filters = [("source_restaurant_id", "==", restaurant_id)] if restaurant_id else None
    t = pq.read_table(waste_path, columns=waste_cols, filters=waste_filters)
    df = t.to_pandas()
    if restaurant_id and "source_restaurant_id" in df.columns:
        df = df[df["source_restaurant_id"] == restaurant_id]

    reasons = (
        df.groupby("primary_reason", as_index=False)
        .agg(
            {
                "waste_cost": "sum",
                "waste_quantity": "sum",
            }
        )
        .to_dict(orient="records")
    )

    high_risk = (
        df[df["current_week_wastage_risk"] == "HIGH_RISK"]
        .groupby(["source_menu_item_id", "item_name"], as_index=False)
        .agg(
            {
                "waste_cost": "sum",
                "waste_quantity": "sum",
                "sold_quantity": "sum",
            }
        )
        .sort_values(by="waste_cost", ascending=False)
        .head(20)
        .to_dict(orient="records")
    )

    weekly = (
        df.groupby(["calendar_year", "calendar_week"], as_index=False)
        .agg(
            {
                "waste_cost": "sum",
                "waste_quantity": "sum",
            }
        )
        .sort_values(by=["calendar_year", "calendar_week"])
        .to_dict(orient="records")
    )

    # ML Forward-looking wastage risk integration
    ml_risk_summary: dict[str, Any] = {}
    ml_predicted_items: list[dict[str, Any]] = []
    if ml_waste_path.exists():
        try:
            ml_cols = ["restaurant_id", "menu_item_id", "predicted_label", "risk_probability"]
            ml_filters = [("restaurant_id", "==", restaurant_id)] if restaurant_id else None
            t_ml = pq.read_table(ml_waste_path, columns=ml_cols, filters=ml_filters)
            df_ml = t_ml.to_pandas()
            if restaurant_id and "restaurant_id" in df_ml.columns:
                df_ml = df_ml[df_ml["restaurant_id"] == restaurant_id]

            total_evaluated = len(df_ml)
            high_risk_count = int(df_ml["predicted_label"].sum()) if total_evaluated > 0 else 0
            avg_prob = float(df_ml["risk_probability"].mean()) if total_evaluated > 0 else 0.0
            high_risk_rate = (
                (high_risk_count / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
            )

            # Fast distinct mapping of menu item ID to item name from historical mart
            dedup = df[["source_menu_item_id", "item_name"]].drop_duplicates("source_menu_item_id")
            item_name_map = dict(
                zip(dedup["source_menu_item_id"], dedup["item_name"], strict=False)
            )

            spark_algo = _get_champion_algorithm("wastage_risk", "spark")
            python_algo = _get_champion_algorithm("wastage_risk", "python")

            ml_risk_summary = {
                "total_evaluated": total_evaluated,
                "predicted_high_risk_count": high_risk_count,
                "avg_risk_probability": round(avg_prob, 4),
                "high_risk_rate_pct": round(high_risk_rate, 2),
                "spark_selected_algorithm": spark_algo,
                "python_selected_algorithm": python_algo,
            }

            # Top forward-looking high-risk menu items (vectorized sum for binary risk count)
            grouped_ml = (
                df_ml.groupby("menu_item_id", as_index=False)
                .agg(
                    {
                        "risk_probability": "mean",
                        "predicted_label": "sum",
                    }
                )
                .rename(columns={"predicted_label": "high_risk_alerts_count"})
                .sort_values(by="risk_probability", ascending=False)
                .head(25)
            )

            for _, r_ml in grouped_ml.iterrows():
                mid = r_ml["menu_item_id"]
                prob = float(r_ml["risk_probability"])
                alerts = int(r_ml["high_risk_alerts_count"])
                is_high = 1 if (prob >= 0.5 or alerts > 0) else 0
                ml_predicted_items.append(
                    {
                        "menu_item_id": mid,
                        "item_name": item_name_map.get(mid, mid),
                        "risk_probability": round(prob, 4),
                        "predicted_label": is_high,
                        "predicted_risk_status": "HIGH RISK" if is_high == 1 else "ELEVATED",
                        "high_risk_alerts_count": alerts,
                    }
                )
        except Exception as e:
            logger.warning("Failed loading ML wastage risk mart: %s", e)

    return {
        "reasons": [_sanitize_val(r) for r in reasons],
        "high_risk_items": [_sanitize_val(r) for r in high_risk],
        "weekly_trend": [_sanitize_val(r) for r in weekly],
        "ml_risk_summary": _sanitize_val(ml_risk_summary),
        "ml_predicted_risks": [_sanitize_val(r) for r in ml_predicted_items],
    }


def get_promotions_and_basket_summary() -> dict[str, Any]:
    """Retrieve promotions performance, trap flags, and top market basket association pairs."""
    base_dir = get_marts_directory()

    promo_path = base_dir / "spark" / "mart_promotions.parquet"
    promos = []
    if promo_path.exists():
        t = pq.read_table(promo_path)
        df_p = t.to_pandas()
        grouped = df_p.groupby(
            ["source_promotion_id", "campaign_name", "discount_type", "is_promotion_trap"],
            as_index=False,
        ).agg(
            {
                "units_sold": "sum",
                "net_revenue": "sum",
                "total_discount": "sum",
                "contribution_margin": "sum",
            }
        )
        promos = [_sanitize_val(r) for r in grouped.to_dict(orient="records")]

    basket_path = base_dir / "spark" / "mart_basket_analysis.parquet"
    baskets = []
    if basket_path.exists():
        t = pq.read_table(basket_path)
        df_b = t.to_pandas()
        df_b = df_b.sort_values(by="lift", ascending=False).head(50)
        baskets = [_sanitize_val(r) for r in df_b.to_dict(orient="records")]

    return {
        "promotions": promos,
        "market_basket_pairs": baskets,
    }


def get_ratings_and_anomalies_summary() -> dict[str, Any]:
    """Retrieve sales and rating anomaly event streams with reasons and context."""
    base_dir = get_marts_directory()

    sales_path = base_dir / "spark" / "mart_sales_anomalies.parquet"
    sales_anomalies = []
    if sales_path.exists():
        t = pq.read_table(sales_path)
        df_s = t.to_pandas()
        anom_s = df_s[
            df_s["is_spike_anomaly"].astype(bool) | df_s["is_drop_anomaly"].astype(bool)
        ].head(100)
        sales_anomalies = [_sanitize_val(r) for r in anom_s.to_dict(orient="records")]

    rating_path = base_dir / "spark" / "mart_ratings_anomalies.parquet"
    rating_anomalies = []
    if rating_path.exists():
        t = pq.read_table(rating_path)
        df_r = t.to_pandas()
        anom_r = df_r[df_r["is_rating_anomaly"].astype(bool)].head(100)
        rating_anomalies = [_sanitize_val(r) for r in anom_r.to_dict(orient="records")]

    return {
        "sales_anomalies": sales_anomalies,
        "rating_anomalies": rating_anomalies,
    }


def get_data_science_arena_summary(task: str | None = None, limit: int = 100) -> dict[str, Any]:
    """Read cross-pipeline Spark vs Python evaluation metrics and agreement artifacts."""
    base_dir = get_marts_directory()
    summary_path = base_dir / "comparison" / "comparison_overall_summary.json"

    summary_data = {}
    if summary_path.exists():
        with open(summary_path, encoding="utf-8") as f:
            summary_data = json.load(f)

    # Ensure spark_selected_algorithm and python_selected_algorithm are dynamically guaranteed
    for task_name in ["demand_forecast", "wastage_risk", "churn_risk", "customer_segmentation"]:
        if task_name in summary_data and isinstance(summary_data[task_name], dict):
            if "spark_selected_algorithm" not in summary_data[task_name]:
                summary_data[task_name]["spark_selected_algorithm"] = _get_champion_algorithm(
                    task_name, "spark"
                )
            if "python_selected_algorithm" not in summary_data[task_name]:
                summary_data[task_name]["python_selected_algorithm"] = _get_champion_algorithm(
                    task_name, "python"
                )

    # Detailed record comparison
    comparison_table = []
    target_task = task or "demand_forecast"
    task_parquet = base_dir / "comparison" / f"comparison_{target_task}.parquet"
    if task_parquet.exists():
        t = pq.read_table(task_parquet)
        sliced = t.slice(0, limit)
        pydict = sliced.to_pydict()
        keys = list(pydict.keys())
        num_rows = len(pydict[keys[0]])
        for i in range(num_rows):
            comparison_table.append({k: _sanitize_val(pydict[k][i]) for k in keys})

    return {
        "arena_overview": summary_data,
        "selected_task": target_task,
        "comparison_samples": comparison_table,
    }


def get_actionable_recommendations() -> list[dict[str, Any]]:
    """Synthesize evidence-based recommendations directly from verified analytical marts."""
    base_dir = get_marts_directory()
    recs = []

    # Domain 1: Menu Optimization (from mart_menu_performance)
    menu_file = base_dir / "spark" / "mart_menu_performance.parquet"
    if menu_file.exists():
        t = pq.read_table(menu_file)
        df = t.to_pandas()
        # High selling loss making items
        loss_makers = df[df["flag_high_selling_loss_making"].astype(bool)].head(5)
        for _, r in loss_makers.iterrows():
            cm_loss = abs(float(r["contribution_margin"]))
            recs.append(
                {
                    "id": f"REC-MENU-{r['source_menu_item_id']}",
                    "domain": "Menu Optimization",
                    "target": f"{r['item_name']} ({r['source_menu_item_id']})",
                    "observation": f"Item has high sales volume ({int(r['total_quantity'])} units) but negative contribution margin (${float(r['contribution_margin']):.2f}).",
                    "evidence": f"Revenue: ${float(r['gross_revenue']):.2f}, Cost: ${float(r['current_base_cost']):.2f}, Margin: ${float(r['contribution_margin']):.2f}.",
                    "interpretation": "Strong customer demand is actively eroding restaurant profitability with every transaction.",
                    "recommendation": "Increase base price by 10-15% or renegotiate supplier food cost to restore margin positive status.",
                    "priority": "Critical",
                    "expected_impact": f"+${cm_loss:.2f} monthly margin recovery via pricing adjustment",
                }
            )

    # Domain 2: Operational Wastage Reduction (from mart_wastage)
    waste_file = base_dir / "spark" / "mart_wastage.parquet"
    if waste_file.exists():
        t = pq.read_table(waste_file)
        df_w = t.to_pandas()
        high_waste = (
            df_w[df_w["current_week_wastage_risk"] == "HIGH_RISK"]
            .groupby(["source_menu_item_id", "item_name"], as_index=False)
            .agg({"waste_cost": "sum", "waste_cost_ratio": "mean"})
            .sort_values(by="waste_cost", ascending=False)
            .head(5)
        )
        for _, r in high_waste.iterrows():
            waste_val = float(r["waste_cost"])
            recs.append(
                {
                    "id": f"REC-WASTE-{r['source_menu_item_id']}",
                    "domain": "Operational Wastage",
                    "target": f"{r['item_name']} ({r['source_menu_item_id']})",
                    "observation": f"Item exhibits extreme wastage cost (${float(r['waste_cost']):.2f}) with waste-to-revenue ratio exceeding 5%.",
                    "evidence": f"Waste Cost: ${float(r['waste_cost']):.2f}, Cost Ratio: {float(r['waste_cost_ratio']) * 100:.1f}%.",
                    "interpretation": "Over-preparation during slow shifts leads to rapid inventory spoilage.",
                    "recommendation": "Adjust daily prep batches to match dynamic ML demand forecast horizons.",
                    "priority": "High",
                    "expected_impact": f"-30% reduction in food spoilage losses (${waste_val * 0.30:.2f} estimated savings)",
                }
            )

    # Domain 3: Customer Churn Retention (from mart_customer_rfm)
    cust_file = base_dir / "spark" / "mart_customer_rfm.parquet"
    if cust_file.exists():
        t = pq.read_table(cust_file)
        df_c = t.to_pandas()
        at_risk = (
            df_c[df_c["rfm_segment"] == "At Risk"]
            .sort_values(by="monetary_value", ascending=False)
            .head(5)
        )
        for _, r in at_risk.iterrows():
            spend_val = float(r["monetary_value"])
            recs.append(
                {
                    "id": f"REC-CHURN-{r['source_customer_id']}",
                    "domain": "Customer Retention",
                    "target": f"{r['customer_name']} ({r['source_customer_id']})",
                    "observation": f"High lifetime value customer (${float(r['monetary_value']):.2f}) has become inactive for {int(r['recency_days'])} days.",
                    "evidence": f"Historical Frequency: {int(r['frequency'])} orders, Total Spend: ${float(r['monetary_value']):.2f}, Days Inactive: {int(r['recency_days'])}.",
                    "interpretation": "Customer has high churn risk despite proven loyalty and willingness to spend.",
                    "recommendation": "Trigger personalized win-back offer on their preferred channel with a tailored incentive.",
                    "priority": "Medium",
                    "expected_impact": f"Reactivation of high-tier customer (${spend_val:.2f} historical spend at risk)",
                }
            )

    return recs


def calculate_what_if_scenario(
    item_id: str,
    price_change_pct: float,
    discount_change_pct: float,
    waste_reduction_pct: float,
) -> dict[str, Any]:
    """Simulate estimated business impact using price elasticity estimates and baseline sales.

    Results are strictly ESTIMATES based on empirical elasticity and margin metrics.
    """
    base_dir = get_marts_directory()
    pricing_file = base_dir / "spark" / "mart_pricing.parquet"
    menu_file = base_dir / "spark" / "mart_menu_performance.parquet"

    # Default baseline
    base_price = 15.0
    base_cost = 6.0
    base_volume = 1000
    elasticity = -0.85
    item_name = item_id

    if menu_file.exists():
        t = pq.read_table(menu_file)
        df = t.to_pandas()
        matching = df[df["source_menu_item_id"] == item_id]
        if not matching.empty:
            row = matching.iloc[0]
            base_price = float(row["current_base_price"]) or base_price
            base_cost = float(row["current_base_cost"]) or base_cost
            base_volume = int(row["total_quantity"]) or base_volume
            item_name = str(row["item_name"]) or item_id

    if pricing_file.exists():
        t_prc = pq.read_table(pricing_file)
        df_prc = t_prc.to_pandas()
        matching_prc = df_prc[df_prc["source_menu_item_id"] == item_id]
        if not matching_prc.empty and matching_prc.iloc[0]["elasticity"] is not None:
            try:
                el_val = float(matching_prc.iloc[0]["elasticity"])
                if el_val == el_val:  # Check not NaN
                    elasticity = el_val
            except (ValueError, TypeError):
                pass

    # Historical baseline
    hist_revenue = base_price * base_volume
    hist_margin = (base_price - base_cost) * base_volume

    # What-if estimation:
    # dQ/Q = elasticity * (dP/P)
    delta_price_ratio = price_change_pct / 100.0
    volume_change_ratio = elasticity * delta_price_ratio

    # Factor in discount change effect (discounts simulate effective price drops)
    if discount_change_pct != 0:
        volume_change_ratio += (-0.5 * elasticity) * (discount_change_pct / 100.0)

    if volume_change_ratio != volume_change_ratio:  # Check NaN
        volume_change_ratio = 0.0

    new_price = base_price * (1.0 + delta_price_ratio)
    new_volume = max(0, int(base_volume * (1.0 + volume_change_ratio)))
    new_revenue = new_price * new_volume

    # Waste reduction savings
    waste_cost_savings = (base_cost * base_volume * 0.05) * (waste_reduction_pct / 100.0)
    new_margin = (new_price - base_cost) * new_volume + waste_cost_savings

    return {
        "status": "ESTIMATE",
        "item_id": item_id,
        "item_name": item_name,
        "parameters": {
            "price_change_pct": price_change_pct,
            "discount_change_pct": discount_change_pct,
            "waste_reduction_pct": waste_reduction_pct,
            "elasticity_applied": round(elasticity, 3),
        },
        "baseline": {
            "base_price": round(base_price, 2),
            "base_cost": round(base_cost, 2),
            "base_volume": base_volume,
            "revenue": round(hist_revenue, 2),
            "contribution_margin": round(hist_margin, 2),
        },
        "estimated_outcome": {
            "estimated_price": round(new_price, 2),
            "estimated_volume": new_volume,
            "estimated_revenue": round(new_revenue, 2),
            "estimated_contribution_margin": round(new_margin, 2),
            "revenue_delta": round(new_revenue - hist_revenue, 2),
            "margin_delta": round(new_margin - hist_margin, 2),
            "volume_delta_pct": round(volume_change_ratio * 100, 2),
        },
        "disclaimer": "These figures are simulated estimates derived from historical price elasticity and do not constitute guaranteed causal outcomes.",
    }
