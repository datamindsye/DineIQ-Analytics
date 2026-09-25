"""Dataset generator engine coordinating deterministic generation, streaming writes, and validation."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from packages.common.generator.catalogs import (
    generate_customers,
    generate_inventory,
    generate_menu_categories,
    generate_menu_items,
    generate_pricing_history,
    generate_promotions,
    generate_restaurants,
)
from packages.common.generator.config import GeneratorConfig
from packages.common.generator.transactions import (
    generate_orders_and_items_stream,
    generate_ratings,
    generate_wastage,
)
from packages.core.contracts.dataset_contract import (
    ARROW_SCHEMAS,
    CUSTOMERS_ARROW_SCHEMA,
    INVENTORY_ARROW_SCHEMA,
    MENU_CATEGORIES_ARROW_SCHEMA,
    MENU_ITEMS_ARROW_SCHEMA,
    ORDER_ITEMS_ARROW_SCHEMA,
    ORDERS_ARROW_SCHEMA,
    PRICING_HISTORY_ARROW_SCHEMA,
    PROMOTIONS_ARROW_SCHEMA,
    RATINGS_ARROW_SCHEMA,
    RESTAURANTS_ARROW_SCHEMA,
    WASTAGE_ARROW_SCHEMA,
    validate_arrow_table_schema,
    validate_source_identifier,
)

logger = logging.getLogger(__name__)


class DatasetGenerator:
    """Orchestrator for deterministic generation and streaming export of the DineIQ analytical dataset."""

    def __init__(self, config: GeneratorConfig | None = None) -> None:
        self.config = config or GeneratorConfig()
        self.snapshot_id = (
            self.config.snapshot_id
            or f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self.config.profile.value}"
        )
        self.output_path = self.config.output_dir / self.snapshot_id

    def generate(self) -> dict[str, Any]:
        """Execute deterministic generation of all eleven tables in dependency order."""
        start_time = time.perf_counter()
        self.output_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Starting dataset generation: profile=%s, seed=%d, output=%s",
            self.config.profile.value,
            self.config.seed,
            self.output_path,
        )

        base_seed = self.config.seed
        # Sub-generators with distinct, reproducible seeds
        cat_rng = np.random.default_rng(base_seed + 10)
        rest_rng = np.random.default_rng(base_seed + 20)
        item_rng = np.random.default_rng(base_seed + 30)
        prc_rng = np.random.default_rng(base_seed + 40)
        promo_rng = np.random.default_rng(base_seed + 50)
        cust_rng = np.random.default_rng(base_seed + 60)
        inv_rng = np.random.default_rng(base_seed + 70)
        txn_rng = np.random.default_rng(base_seed + 80)
        rat_rng = np.random.default_rng(base_seed + 90)
        wst_rng = np.random.default_rng(base_seed + 100)

        # 1. Categories
        categories = generate_menu_categories(self.config, cat_rng)
        cat_table = pa.Table.from_pylist(categories, schema=MENU_CATEGORIES_ARROW_SCHEMA)
        pq.write_table(cat_table, self.output_path / "menu_categories.parquet")

        # 2. Restaurants
        restaurants = generate_restaurants(self.config, rest_rng)
        rest_table = pa.Table.from_pylist(restaurants, schema=RESTAURANTS_ARROW_SCHEMA)
        pq.write_table(rest_table, self.output_path / "restaurants.parquet")

        # 3. Menu Items
        menu_items = generate_menu_items(self.config, categories, item_rng)
        items_table = pa.Table.from_pylist(menu_items, schema=MENU_ITEMS_ARROW_SCHEMA)
        pq.write_table(items_table, self.output_path / "menu_items.parquet")

        # 4. Pricing History
        pricing_history = generate_pricing_history(self.config, menu_items, prc_rng)
        prc_table = pa.Table.from_pylist(pricing_history, schema=PRICING_HISTORY_ARROW_SCHEMA)
        pq.write_table(prc_table, self.output_path / "pricing_history.parquet")

        # 5. Promotions
        promotions = generate_promotions(self.config, menu_items, categories, promo_rng)
        promo_table = pa.Table.from_pylist(promotions, schema=PROMOTIONS_ARROW_SCHEMA)
        pq.write_table(promo_table, self.output_path / "promotions.parquet")

        # 6. Customers
        customers = generate_customers(self.config, cust_rng)
        cust_table = pa.Table.from_pylist(customers, schema=CUSTOMERS_ARROW_SCHEMA)
        pq.write_table(cust_table, self.output_path / "customers.parquet")

        # 7. Inventory
        inventory = generate_inventory(self.config, restaurants, inv_rng)
        inv_table = pa.Table.from_pylist(inventory, schema=INVENTORY_ARROW_SCHEMA)
        pq.write_table(inv_table, self.output_path / "inventory.parquet")

        # 8 & 9. Orders and Order Items (Streaming Chunked Generation)
        orders_file = self.output_path / "orders.parquet"
        order_items_file = self.output_path / "order_items.parquet"

        orders_writer = pq.ParquetWriter(orders_file, ORDERS_ARROW_SCHEMA, compression="snappy")
        items_writer = pq.ParquetWriter(
            order_items_file, ORDER_ITEMS_ARROW_SCHEMA, compression="snappy"
        )

        total_orders_count = 0
        total_items_count = 0
        completed_orders_sample: list[dict[str, Any]] = []

        try:
            for chunk_orders, chunk_items in generate_orders_and_items_stream(
                config=self.config,
                restaurants=restaurants,
                customers=customers,
                menu_items=menu_items,
                pricing_history=pricing_history,
                promotions=promotions,
                rng=txn_rng,
            ):
                total_orders_count += len(chunk_orders)
                total_items_count += len(chunk_items)

                # Keep a sample of completed orders for rating generation
                if len(completed_orders_sample) < 2000:
                    for o in chunk_orders:
                        if o["order_status"] == "Completed" and o["source_customer_id"]:
                            completed_orders_sample.append(o)
                            if len(completed_orders_sample) >= 2000:
                                break

                # Write chunks directly to Parquet
                o_table = pa.Table.from_pylist(chunk_orders, schema=ORDERS_ARROW_SCHEMA)
                i_table = pa.Table.from_pylist(chunk_items, schema=ORDER_ITEMS_ARROW_SCHEMA)

                orders_writer.write_table(o_table)
                items_writer.write_table(i_table)
        finally:
            orders_writer.close()
            items_writer.close()

        # 10. Ratings
        ratings = generate_ratings(
            self.config,
            restaurants=restaurants,
            customers=customers,
            menu_items=menu_items,
            completed_orders_sample=completed_orders_sample,
            rng=rat_rng,
        )
        rat_table = pa.Table.from_pylist(ratings, schema=RATINGS_ARROW_SCHEMA)
        pq.write_table(rat_table, self.output_path / "ratings.parquet")

        # 11. Wastage
        wastage = generate_wastage(self.config, restaurants, menu_items, wst_rng)
        wst_table = pa.Table.from_pylist(wastage, schema=WASTAGE_ARROW_SCHEMA)
        pq.write_table(wst_table, self.output_path / "wastage.parquet")

        duration_sec = round(time.perf_counter() - start_time, 2)

        row_counts = {
            "menu_categories": len(categories),
            "restaurants": len(restaurants),
            "menu_items": len(menu_items),
            "pricing_history": len(pricing_history),
            "promotions": len(promotions),
            "customers": len(customers),
            "orders": total_orders_count,
            "order_items": total_items_count,
            "ratings": len(ratings),
            "inventory": len(inventory),
            "wastage": len(wastage),
        }

        # 12. Chronological Split Manifest (4-way leakage-safe calendar split)
        start_date = self.config.start_date
        history_days = self.config.scale.history_days

        if history_days >= 365 and start_date.month == 1 and start_date.day == 1:
            # Exact calendar months alignment matching SRS strategy
            train_start = start_date
            train_end = start_date.replace(month=8, day=31)
            val_start = start_date.replace(month=9, day=1)
            val_end = start_date.replace(month=10, day=31)
            test_start = start_date.replace(month=11, day=1)
            test_end = start_date.replace(month=11, day=30)
            unseen_start = start_date.replace(month=12, day=1)
            unseen_end = start_date.replace(month=12, day=31)
        else:
            # Proportional 4-way split for shorter development/test profiles (67% / 17% / 8% / 8%)
            train_days = max(1, int(history_days * 0.67))
            val_days = max(1, int(history_days * 0.17))
            test_days = max(1, int(history_days * 0.08))
            train_start = start_date
            train_end = train_start + timedelta(days=train_days - 1)
            val_start = train_end + timedelta(days=1)
            val_end = val_start + timedelta(days=val_days - 1)
            test_start = val_end + timedelta(days=1)
            test_end = test_start + timedelta(days=test_days - 1)
            unseen_start = test_end + timedelta(days=1)
            unseen_end = start_date + timedelta(days=history_days - 1)

        train_count = (train_end - train_start).days + 1
        val_count = (val_end - val_start).days + 1
        test_count = (test_end - test_start).days + 1
        unseen_count = (unseen_end - unseen_start).days + 1
        total_days = train_count + val_count + test_count + unseen_count

        manifest = {
            "snapshot_id": self.snapshot_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_horizon_days": total_days,
            "windows": {
                "TRAIN": {
                    "start_date": str(train_start),
                    "end_date": str(train_end),
                    "days": train_count,
                    "fraction": round(train_count / total_days, 4),
                    "description": "Historical training window for feature engineering and model baseline (Jan 1 - Aug 31)",
                },
                "VALIDATION": {
                    "start_date": str(val_start),
                    "end_date": str(val_end),
                    "days": val_count,
                    "fraction": round(val_count / total_days, 4),
                    "description": "Validation window for hyperparameter tuning and model selection (Sep 1 - Oct 31)",
                },
                "TEST": {
                    "start_date": str(test_start),
                    "end_date": str(test_end),
                    "days": test_count,
                    "fraction": round(test_count / total_days, 4),
                    "description": "Out of time test window for pre deployment model evaluation (Nov 1 - Nov 30)",
                },
                "UNSEEN_COMPARISON": {
                    "start_date": str(unseen_start),
                    "end_date": str(unseen_end),
                    "days": unseen_count,
                    "fraction": round(unseen_count / total_days, 4),
                    "description": "Unseen comparison period for cross pipeline evaluation (Spark vs Python) (Dec 1 - Dec 31)",
                },
            },
        }

        # Write both split_manifest.json and manifest.json for compatibility
        with open(self.output_path / "split_manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        with open(self.output_path / "manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        # 13. Metadata Artifact
        metadata = {
            "snapshot_id": self.snapshot_id,
            "profile": self.config.profile.value,
            "seed": self.config.seed,
            "start_date": str(self.config.start_date),
            "history_days": self.config.scale.history_days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generation_duration_seconds": duration_sec,
            "row_counts": row_counts,
            "quality_anomalies_enabled": self.config.enable_anomalies,
            "quality_anomalies_config": self.config.anomalies.model_dump(),
            "files": [p.name for p in self.output_path.glob("*.parquet")]
            + ["manifest.json", "metadata.json"],
        }

        with open(self.output_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info(
            "Generation completed successfully in %.2fs: %d orders, %d order items",
            duration_sec,
            total_orders_count,
            total_items_count,
        )

        return metadata

    def validate_snapshot(self) -> dict[str, Any]:
        """Validate the generated Parquet snapshot against schema contracts, foreign keys, and IDs."""
        defects: list[str] = []
        tables: dict[str, pa.Table] = {}

        for entity_name in ARROW_SCHEMAS:
            file_path = self.output_path / f"{entity_name}.parquet"
            if not file_path.exists():
                defects.append(f"Missing parquet file: {file_path.name}")
                continue

            table = pq.read_table(file_path)
            tables[entity_name] = table
            schema_res = validate_arrow_table_schema(entity_name, table)
            if not schema_res.is_valid:
                defects.extend([f"{entity_name}: {d}" for d in schema_res.defects])

        # Validate Foreign Key and Source Identifier Integrity if all tables loaded
        if len(tables) == 11:
            # Check source ID patterns
            for entity_name, table in tables.items():
                source_col = f"source_{entity_name[:-1] if entity_name.endswith('s') and entity_name != 'pricing_history' else entity_name}_id"
                if entity_name == "menu_categories":
                    source_col = "source_category_id"
                elif entity_name == "menu_items":
                    source_col = "source_menu_item_id"
                elif entity_name == "order_items":
                    source_col = "source_order_item_id"

                if source_col in table.column_names:
                    sample_ids = table.column(source_col).to_pylist()[:100]
                    for sid in sample_ids:
                        if not validate_source_identifier(entity_name, sid):
                            defects.append(
                                f"Invalid source identifier format '{sid}' in {entity_name}"
                            )
                            break

            # Foreign keys: order_items -> orders
            order_ids = set(tables["orders"].column("source_order_id").to_pylist())
            item_order_ids = set(tables["order_items"].column("source_order_id").to_pylist()[:1000])
            unmatched_orders = item_order_ids - order_ids
            if unmatched_orders:
                defects.append(
                    f"Order items reference nonexistent order IDs: {len(unmatched_orders)} samples"
                )

            # Foreign keys: order_items -> menu_items
            item_dish_ids = set(tables["menu_items"].column("source_menu_item_id").to_pylist())
            item_ref_dishes = set(
                tables["order_items"].column("source_menu_item_id").to_pylist()[:1000]
            )
            unmatched_dishes = item_ref_dishes - item_dish_ids
            if unmatched_dishes:
                defects.append(
                    f"Order items reference nonexistent menu items: {len(unmatched_dishes)} samples"
                )

        return {
            "snapshot_id": self.snapshot_id,
            "is_valid": len(defects) == 0,
            "defects": defects,
            "tables_inspected": list(tables.keys()),
        }
