"""Data quality profiling engine inspecting raw snapshot tables and quantifying defects."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq


class DataQualityProfiler:
    """Profiles raw Parquet snapshots to measure nullability, duplicates, anomalies, and referential integrity."""

    def __init__(self, snapshot_dir: Path | str) -> None:
        self.snapshot_dir = Path(snapshot_dir)
        if not self.snapshot_dir.exists():
            raise FileNotFoundError(f"Snapshot directory not found: {self.snapshot_dir}")

    def profile_all(self) -> dict[str, Any]:
        """Profile all eleven domain tables in the snapshot directory and return detailed metrics."""
        table_files = {p.stem: p for p in self.snapshot_dir.glob("*.parquet")}
        profile_results: dict[str, Any] = {}

        # 1. Profile individual tables
        for entity_name, file_path in table_files.items():
            profile_results[entity_name] = self.profile_table(entity_name, file_path)

        # 2. Profile cross-table referential integrity
        ref_integrity = self.profile_referential_integrity(table_files)

        # 3. Read metadata if available to compare against configured injection rates
        meta_file = self.snapshot_dir / "metadata.json"
        metadata: dict[str, Any] = {}
        if meta_file.exists():
            with open(meta_file, encoding="utf-8") as f:
                metadata = json.load(f)

        return {
            "snapshot_id": self.snapshot_dir.name,
            "profiled_at": datetime.now(timezone.utc).isoformat(),
            "table_profiles": profile_results,
            "referential_integrity": ref_integrity,
            "metadata_summary": metadata,
        }

    def profile_table(self, entity_name: str, file_path: Path) -> dict[str, Any]:
        """Profile a single Parquet table measuring nulls, duplicates, and column metrics."""
        table = pq.read_table(file_path)
        num_rows = table.num_rows

        source_col = f"source_{entity_name[:-1] if entity_name.endswith('s') and entity_name != 'pricing_history' else entity_name}_id"
        if entity_name == "menu_categories":
            source_col = "source_category_id"
        elif entity_name == "menu_items":
            source_col = "source_menu_item_id"
        elif entity_name == "order_items":
            source_col = "source_order_item_id"

        # Column nulls and types
        column_metrics: dict[str, Any] = {}
        for col_name in table.column_names:
            col = table.column(col_name)
            null_count = col.null_count
            null_pct = round((null_count / num_rows) * 100.0, 2) if num_rows > 0 else 0.0
            column_metrics[col_name] = {
                "type": str(col.type),
                "null_count": null_count,
                "null_percentage": null_pct,
            }

        # Duplicate source ID detection
        duplicate_source_id_count = 0
        if source_col in table.column_names:
            ids = table.column(source_col).to_pylist()
            unique_ids = set(ids)
            duplicate_source_id_count = len(ids) - len(unique_ids)

        table_summary: dict[str, Any] = {
            "entity_name": entity_name,
            "row_count": num_rows,
            "column_count": len(table.column_names),
            "duplicate_source_ids": duplicate_source_id_count,
            "columns": column_metrics,
        }

        # Specific profiling logic per entity
        if entity_name == "orders":
            status_col = table.column("order_status").to_pylist()
            cust_col = table.column("source_customer_id").to_pylist()
            ts_col = table.column("order_timestamp").to_pylist()

            table_summary["status_breakdown"] = {
                status: status_col.count(status) for status in set(status_col)
            }
            table_summary["guest_orders_count"] = cust_col.count(None)
            table_summary["guest_orders_pct"] = (
                round((cust_col.count(None) / num_rows) * 100.0, 2) if num_rows > 0 else 0.0
            )

            # Future timestamps (> 2026-01-01)
            future_ts_count = sum(1 for ts in ts_col if ts and ts.year > 2025)
            table_summary["future_timestamp_count"] = future_ts_count

            # Financial formula check on orders: subtotal - discount + tax + tip == total
            subtotals = table.column("subtotal_amount").to_pylist()
            discounts = table.column("discount_amount").to_pylist()
            taxes = table.column("tax_amount").to_pylist()
            tips = table.column("tip_amount").to_pylist()
            totals = table.column("total_amount").to_pylist()

            order_formula_discrepancies = 0
            for s, d, tx, tp, tot in zip(subtotals, discounts, taxes, tips, totals, strict=True):
                expected = round(s - d + tx + tp, 2)
                if abs(tot - expected) > 0.02:
                    order_formula_discrepancies += 1
            table_summary["financial_formula_discrepancies"] = order_formula_discrepancies

        elif entity_name == "order_items":
            quantities = table.column("quantity").to_pylist()
            unit_prices = table.column("unit_price_at_sale").to_pylist()
            unit_costs = table.column("unit_cost_at_sale").to_pylist()
            discounts = table.column("line_discount").to_pylist()
            net_revenues = table.column("line_net_revenue").to_pylist()
            margins = table.column("line_contribution_margin").to_pylist()

            negative_price_count = sum(1 for p in unit_prices if p < 0.0)
            zero_qty_count = sum(1 for q in quantities if q <= 0)
            negative_margin_count = sum(1 for m in margins if m < 0.0)

            # Invariant check
            net_formula_discrepancies = 0
            margin_formula_discrepancies = 0
            for q, p, c, d, net, cm in zip(
                quantities, unit_prices, unit_costs, discounts, net_revenues, margins, strict=True
            ):
                exp_net = round((q * p) - d, 2)
                exp_cm = round(exp_net - (q * c), 2)
                if abs(net - exp_net) > 0.02:
                    net_formula_discrepancies += 1
                if abs(cm - exp_cm) > 0.02:
                    margin_formula_discrepancies += 1

            table_summary["negative_price_count"] = negative_price_count
            table_summary["zero_quantity_count"] = zero_qty_count
            table_summary["promotion_trap_negative_margin_count"] = negative_margin_count
            table_summary["net_revenue_formula_discrepancies"] = net_formula_discrepancies
            table_summary["contribution_margin_formula_discrepancies"] = (
                margin_formula_discrepancies
            )

        elif entity_name == "ratings":
            scores = table.column("rating_score").to_pylist()
            out_of_bounds_scores = sum(1 for s in scores if s < 1 or s > 5)
            table_summary["out_of_bounds_scores_count"] = out_of_bounds_scores
            reviews = table.column("review_text").to_pylist()
            table_summary["missing_review_text_count"] = reviews.count(None)

        elif entity_name == "wastage":
            reasons = table.column("wastage_reason").to_pylist()
            table_summary["reason_breakdown"] = {r: reasons.count(r) for r in set(reasons)}
            costs = table.column("cost_loss_amount").to_pylist()
            table_summary["total_cost_loss"] = round(float(np.sum(costs)), 2)

        return table_summary

    def profile_referential_integrity(self, table_files: dict[str, Path]) -> dict[str, Any]:
        """Verify referential integrity constraints across the snapshot tables."""
        ref_summary: dict[str, Any] = {}

        if "orders" in table_files and "order_items" in table_files:
            orders = pq.read_table(table_files["orders"])
            items = pq.read_table(table_files["order_items"])

            order_ids = set(orders.column("source_order_id").to_pylist())
            item_order_refs = items.column("source_order_id").to_pylist()
            orphaned_order_items = sum(1 for oid in item_order_refs if oid not in order_ids)

            ref_summary["order_items_to_orders"] = {
                "total_foreign_keys_checked": len(item_order_refs),
                "orphaned_count": orphaned_order_items,
                "is_clean": orphaned_order_items == 0,
            }

        if "menu_items" in table_files and "order_items" in table_files:
            dishes = pq.read_table(table_files["menu_items"])
            items = pq.read_table(table_files["order_items"])

            dish_ids = set(dishes.column("source_menu_item_id").to_pylist())
            item_dish_refs = items.column("source_menu_item_id").to_pylist()
            orphaned_menu_items = sum(1 for did in item_dish_refs if did not in dish_ids)

            ref_summary["order_items_to_menu_items"] = {
                "total_foreign_keys_checked": len(item_dish_refs),
                "orphaned_count": orphaned_menu_items,
                "is_clean": orphaned_menu_items == 0,
            }

        if "restaurants" in table_files and "orders" in table_files:
            rests = pq.read_table(table_files["restaurants"])
            orders = pq.read_table(table_files["orders"])

            rest_ids = set(rests.column("source_restaurant_id").to_pylist())
            order_rest_refs = orders.column("source_restaurant_id").to_pylist()
            orphaned_rests = sum(1 for rid in order_rest_refs if rid not in rest_ids)

            ref_summary["orders_to_restaurants"] = {
                "total_foreign_keys_checked": len(order_rest_refs),
                "orphaned_count": orphaned_rests,
                "is_clean": orphaned_rests == 0,
            }

        if "customers" in table_files and "orders" in table_files:
            custs = pq.read_table(table_files["customers"])
            orders = pq.read_table(table_files["orders"])

            cust_ids = set(custs.column("source_customer_id").to_pylist())
            order_cust_refs = orders.column("source_customer_id").to_pylist()
            # Only check non-null customer references (guest orders have None)
            non_null_cust_refs = [cid for cid in order_cust_refs if cid is not None]
            orphaned_custs = sum(1 for cid in non_null_cust_refs if cid not in cust_ids)

            ref_summary["orders_to_customers"] = {
                "total_foreign_keys_checked": len(non_null_cust_refs),
                "orphaned_count": orphaned_custs,
                "is_clean": orphaned_custs == 0,
            }

        return ref_summary
