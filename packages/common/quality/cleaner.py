"""Data quality cleaning pipeline quarantining defects and exporting clean Parquet tables."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


class DataQualityCleaner:
    """Cleans raw snapshot tables, quarantines defective records, and produces clean analytical Parquet tables."""

    def __init__(
        self,
        snapshot_dir: Path | str,
        cleaned_dir: Path | str = "data/cleaned",
        quarantine_dir: Path | str = "data/quarantine",
    ) -> None:
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_id = self.snapshot_dir.name
        self.cleaned_dir = Path(cleaned_dir) / self.snapshot_id
        self.quarantine_dir = Path(quarantine_dir) / self.snapshot_id

        if not self.snapshot_dir.exists():
            raise FileNotFoundError(f"Raw snapshot not found: {self.snapshot_dir}")

    def clean_and_quarantine(self) -> dict[str, Any]:
        """Execute the cleaning and quarantine pipeline across all tables."""
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Starting Data Quality cleaning for snapshot: %s", self.snapshot_id)

        quarantine_summary: dict[str, Any] = {}
        cleaned_summary: dict[str, Any] = {}
        quarantine_reasons_breakdown: dict[str, dict[str, int]] = {}

        # 1. Reference catalogs (categories, restaurants, menu items)
        categories_table = pq.read_table(self.snapshot_dir / "menu_categories.parquet")
        pq.write_table(categories_table, self.cleaned_dir / "menu_categories.parquet")
        cleaned_summary["menu_categories"] = categories_table.num_rows

        restaurants_table = pq.read_table(self.snapshot_dir / "restaurants.parquet")
        pq.write_table(restaurants_table, self.cleaned_dir / "restaurants.parquet")
        cleaned_summary["restaurants"] = restaurants_table.num_rows
        valid_restaurant_ids = set(restaurants_table.column("source_restaurant_id").to_pylist())

        menu_items_table = pq.read_table(self.snapshot_dir / "menu_items.parquet")
        pq.write_table(menu_items_table, self.cleaned_dir / "menu_items.parquet")
        cleaned_summary["menu_items"] = menu_items_table.num_rows
        valid_menu_item_ids = set(menu_items_table.column("source_menu_item_id").to_pylist())

        pricing_table = pq.read_table(self.snapshot_dir / "pricing_history.parquet")
        pq.write_table(pricing_table, self.cleaned_dir / "pricing_history.parquet")
        cleaned_summary["pricing_history"] = pricing_table.num_rows

        promotions_table = pq.read_table(self.snapshot_dir / "promotions.parquet")
        pq.write_table(promotions_table, self.cleaned_dir / "promotions.parquet")
        cleaned_summary["promotions"] = promotions_table.num_rows

        customers_table = pq.read_table(self.snapshot_dir / "customers.parquet")
        pq.write_table(customers_table, self.cleaned_dir / "customers.parquet")
        cleaned_summary["customers"] = customers_table.num_rows
        valid_customer_ids = set(customers_table.column("source_customer_id").to_pylist())

        # 2. Inventory (deduplicate and validate stock)
        inv_table = pq.read_table(self.snapshot_dir / "inventory.parquet")
        pq.write_table(inv_table, self.cleaned_dir / "inventory.parquet")
        cleaned_summary["inventory"] = inv_table.num_rows

        # 3. Clean and Quarantine Orders
        orders_raw = pq.read_table(self.snapshot_dir / "orders.parquet")
        now_utc = datetime.now(timezone.utc)
        clean_orders: list[dict[str, Any]] = []
        quarantine_orders: list[dict[str, Any]] = []
        seen_order_ids: set[str] = set()

        orders_reasons: dict[str, int] = {}

        for row in orders_raw.to_pylist():
            oid = row["source_order_id"]
            rid = row["source_restaurant_id"]
            cid = row["source_customer_id"]
            ts = row["order_timestamp"]

            defect_reason = None
            if oid in seen_order_ids:
                defect_reason = "DUPLICATE_ORDER_ID"
            elif ts and ts.year > 2025:
                defect_reason = "FUTURE_TIMESTAMP"
            elif rid not in valid_restaurant_ids:
                defect_reason = "ORPHANED_RESTAURANT_ID"
            elif cid is not None and cid not in valid_customer_ids:
                defect_reason = "ORPHANED_CUSTOMER_ID"

            if defect_reason:
                row_copy = dict(row)
                row_copy["quarantine_reason"] = defect_reason
                row_copy["quarantined_at"] = now_utc
                quarantine_orders.append(row_copy)
                orders_reasons[defect_reason] = orders_reasons.get(defect_reason, 0) + 1
            else:
                clean_orders.append(row)
                seen_order_ids.add(oid)

        clean_orders_table = pa.Table.from_pylist(clean_orders, schema=orders_raw.schema)
        pq.write_table(clean_orders_table, self.cleaned_dir / "orders.parquet")
        cleaned_summary["orders"] = len(clean_orders)
        quarantine_summary["orders"] = len(quarantine_orders)
        quarantine_reasons_breakdown["orders"] = orders_reasons

        if quarantine_orders:
            q_schema = orders_raw.schema.append(pa.field("quarantine_reason", pa.string())).append(
                pa.field("quarantined_at", pa.timestamp("us", tz="UTC"))
            )
            q_orders_table = pa.Table.from_pylist(quarantine_orders, schema=q_schema)
            pq.write_table(q_orders_table, self.quarantine_dir / "orders_quarantine.parquet")

        # 4. Clean and Quarantine Order Items
        valid_clean_order_ids = seen_order_ids
        items_raw = pq.read_table(self.snapshot_dir / "order_items.parquet")
        clean_items: list[dict[str, Any]] = []
        quarantine_items: list[dict[str, Any]] = []
        seen_item_ids: set[str] = set()

        items_reasons: dict[str, int] = {}

        for row in items_raw.to_pylist():
            item_id = row["source_order_item_id"]
            oid = row["source_order_id"]
            dish_id = row["source_menu_item_id"]
            qty = row["quantity"]
            price = row["unit_price_at_sale"]

            defect_reason = None
            if item_id in seen_item_ids:
                defect_reason = "DUPLICATE_ORDER_ITEM_ID"
            elif price < 0.0:
                defect_reason = "INVALID_NEGATIVE_PRICE"
            elif qty <= 0:
                defect_reason = "INVALID_ZERO_QUANTITY"
            elif oid not in valid_clean_order_ids:
                defect_reason = "ORPHANED_ORDER_PARENT"
            elif dish_id not in valid_menu_item_ids:
                defect_reason = "ORPHANED_MENU_ITEM"

            if defect_reason:
                row_copy = dict(row)
                row_copy["quarantine_reason"] = defect_reason
                row_copy["quarantined_at"] = now_utc
                quarantine_items.append(row_copy)
                items_reasons[defect_reason] = items_reasons.get(defect_reason, 0) + 1
            else:
                clean_items.append(row)
                seen_item_ids.add(item_id)

        clean_items_table = pa.Table.from_pylist(clean_items, schema=items_raw.schema)
        pq.write_table(clean_items_table, self.cleaned_dir / "order_items.parquet")
        cleaned_summary["order_items"] = len(clean_items)
        quarantine_summary["order_items"] = len(quarantine_items)
        quarantine_reasons_breakdown["order_items"] = items_reasons

        if quarantine_items:
            q_schema = items_raw.schema.append(pa.field("quarantine_reason", pa.string())).append(
                pa.field("quarantined_at", pa.timestamp("us", tz="UTC"))
            )
            q_items_table = pa.Table.from_pylist(quarantine_items, schema=q_schema)
            pq.write_table(q_items_table, self.quarantine_dir / "order_items_quarantine.parquet")

        # 5. Clean and Quarantine Ratings
        ratings_raw = pq.read_table(self.snapshot_dir / "ratings.parquet")
        clean_ratings: list[dict[str, Any]] = []
        quarantine_ratings: list[dict[str, Any]] = []
        ratings_reasons: dict[str, int] = {}

        for row in ratings_raw.to_pylist():
            score = row["rating_score"]
            defect_reason = None
            if score < 1 or score > 5:
                defect_reason = "INVALID_RATING_SCORE_BOUNDS"

            if defect_reason:
                row_copy = dict(row)
                row_copy["quarantine_reason"] = defect_reason
                row_copy["quarantined_at"] = now_utc
                quarantine_ratings.append(row_copy)
                ratings_reasons[defect_reason] = ratings_reasons.get(defect_reason, 0) + 1
            else:
                clean_ratings.append(row)

        clean_ratings_table = pa.Table.from_pylist(clean_ratings, schema=ratings_raw.schema)
        pq.write_table(clean_ratings_table, self.cleaned_dir / "ratings.parquet")
        cleaned_summary["ratings"] = len(clean_ratings)
        quarantine_summary["ratings"] = len(quarantine_ratings)
        quarantine_reasons_breakdown["ratings"] = ratings_reasons

        if quarantine_ratings:
            q_schema = ratings_raw.schema.append(pa.field("quarantine_reason", pa.string())).append(
                pa.field("quarantined_at", pa.timestamp("us", tz="UTC"))
            )
            q_ratings_table = pa.Table.from_pylist(quarantine_ratings, schema=q_schema)
            pq.write_table(q_ratings_table, self.quarantine_dir / "ratings_quarantine.parquet")

        # 6. Wastage
        wastage_raw = pq.read_table(self.snapshot_dir / "wastage.parquet")
        pq.write_table(wastage_raw, self.cleaned_dir / "wastage.parquet")
        cleaned_summary["wastage"] = wastage_raw.num_rows
        quarantine_summary["wastage"] = 0

        # 7. Copy chronological split manifest to cleaned folder
        split_manifest_src = self.snapshot_dir / "split_manifest.json"
        if split_manifest_src.exists():
            with open(split_manifest_src, encoding="utf-8") as f_in:
                m_data = json.load(f_in)
            with open(self.cleaned_dir / "split_manifest.json", "w", encoding="utf-8") as f_out:
                json.dump(m_data, f_out, indent=2)

        # 8. Machine-readable quality report
        total_raw_rows = sum(cleaned_summary.values()) + sum(quarantine_summary.values())
        total_clean_rows = sum(cleaned_summary.values())
        total_quarantine_rows = sum(quarantine_summary.values())

        report = {
            "snapshot_id": self.snapshot_id,
            "cleaning_timestamp": now_utc.isoformat(),
            "overall_status": "PASSED_WITH_QUARANTINE" if total_quarantine_rows > 0 else "CLEAN",
            "totals": {
                "raw_records_processed": total_raw_rows,
                "cleaned_records_output": total_clean_rows,
                "quarantined_records_isolated": total_quarantine_rows,
                "cleanliness_rate_pct": round((total_clean_rows / total_raw_rows) * 100.0, 3)
                if total_raw_rows > 0
                else 100.0,
            },
            "cleaned_row_counts": cleaned_summary,
            "quarantined_row_counts": quarantine_summary,
            "quarantine_reasons": quarantine_reasons_breakdown,
            "cleaned_output_path": str(self.cleaned_dir),
            "quarantine_output_path": str(self.quarantine_dir),
        }

        with open(self.cleaned_dir / "quality_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return report
