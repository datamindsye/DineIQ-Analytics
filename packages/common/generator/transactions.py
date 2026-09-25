"""High-volume transactional generator for orders, order lines, ratings, and wastage.

Implements streaming/chunked generation to support 100K+ orders and 1M+ order lines
with deterministic behavior, statistical distributions, point-in-time pricing,
and configurable data quality anomalies.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any

import numpy as np

from packages.common.generator.config import GeneratorConfig
from packages.core.contracts.dataset_contract import (
    CHANNELS,
    PAYMENT_METHODS,
    WASTAGE_REASONS,
    compute_line_contribution_margin,
    compute_line_net_revenue,
    compute_order_total_amount,
)


def _build_pricing_lookup_index(
    pricing_history: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Index pricing history by menu item identifier for rapid point in time lookups."""
    index: dict[str, list[dict[str, Any]]] = {}
    for prc in pricing_history:
        item_id = prc["source_menu_item_id"]
        if item_id not in index:
            index[item_id] = []
        index[item_id].append(prc)

    # Sort intervals by effective_from
    for item_id in index:
        index[item_id].sort(key=lambda x: x["effective_from"])
    return index


def resolve_point_in_time_price(
    menu_item_id: str,
    order_dt: datetime,
    pricing_index: dict[str, list[dict[str, Any]]],
    default_price: float,
    default_cost: float,
) -> tuple[float, float]:
    """Retrieve the effective price and cost for a dish at the transaction instant."""
    records = pricing_index.get(menu_item_id)
    if not records:
        return default_price, default_cost

    for rec in records:
        from_dt = rec["effective_from"]
        to_dt = rec["effective_to"]
        if from_dt <= order_dt and (to_dt is None or to_dt > order_dt):
            return float(rec["base_price"]), float(rec["base_cost"])

    # Fallback to the latest record or default
    return float(records[-1]["base_price"]), float(records[-1]["base_cost"])


def generate_orders_and_items_stream(
    config: GeneratorConfig,
    restaurants: list[dict[str, Any]],
    customers: list[dict[str, Any]],
    menu_items: list[dict[str, Any]],
    pricing_history: list[dict[str, Any]],
    promotions: list[dict[str, Any]],
    rng: np.random.Generator,
) -> Generator[tuple[list[dict[str, Any]], list[dict[str, Any]]], None, None]:
    """Yield chunks of orders and order items to avoid holding 1M+ rows in memory.

    Each yielded tuple contains:
        (chunk_orders, chunk_order_items)
    """
    total_orders = config.scale.num_orders
    chunk_size = config.scale.chunk_size_orders
    history_days = config.scale.history_days
    start_date = config.start_date
    pricing_index = _build_pricing_lookup_index(pricing_history)

    # 1. Restaurant selection weights (urban flagships have higher volume)
    rest_weights = np.array(
        [2.2 if r["seating_capacity"] > 140 else 1.0 for r in restaurants],
        dtype=np.float64,
    )
    rest_weights /= rest_weights.sum()

    # 2. Customer frequency weights (Pareto distribution: top 5% generate 25% of orders)
    num_cust = len(customers)
    cust_weights = np.zeros(num_cust, dtype=np.float64)
    top_5_pct = max(1, int(num_cust * 0.05))
    next_20_pct = max(1, int(num_cust * 0.20))

    cust_weights[:top_5_pct] = 0.25 / top_5_pct
    cust_weights[top_5_pct : top_5_pct + next_20_pct] = 0.35 / next_20_pct
    remaining = num_cust - (top_5_pct + next_20_pct)
    if remaining > 0:
        cust_weights[top_5_pct + next_20_pct :] = 0.40 / remaining
    cust_weights /= cust_weights.sum()

    # 3. Item popularity weights (Zipf distribution)
    num_items = len(menu_items)
    ranks = np.arange(1, num_items + 1)
    item_weights = 1.0 / (ranks**0.85)
    item_weights /= item_weights.sum()
    item_lookup = {item["source_menu_item_id"]: item for item in menu_items}
    item_ids = [item["source_menu_item_id"] for item in menu_items]

    # Quality anomaly configuration
    anomalies = config.anomalies
    enable_anomalies = config.enable_anomalies

    order_counter = 0
    item_counter = 0

    while order_counter < total_orders:
        current_chunk_orders = min(chunk_size, total_orders - order_counter)
        chunk_orders_list: list[dict[str, Any]] = []
        chunk_items_list: list[dict[str, Any]] = []

        for _ in range(current_chunk_orders):
            order_counter += 1
            source_order_id = f"ORD-{order_counter:08d}"

            # Restaurant selection
            rest_idx = int(rng.choice(len(restaurants), p=rest_weights))
            restaurant = restaurants[rest_idx]
            rest_id = restaurant["source_restaurant_id"]

            # Customer selection (with guest checkout anomaly)
            is_guest = enable_anomalies and (rng.random() < anomalies.missing_customer_rate)
            if is_guest:
                source_customer_id = None
            else:
                cust_idx = int(rng.choice(num_cust, p=cust_weights))
                source_customer_id = customers[cust_idx]["source_customer_id"]

            # Temporal distribution: Day offset with seasonality and weekend surge
            # Days: 0 to history_days - 1
            day_offset = int(rng.integers(0, history_days))
            order_date = start_date + timedelta(days=day_offset)

            # Hour: Bimodal Gaussian curve for Lunch (12-14) and Dinner (18-21)
            is_lunch = rng.random() < 0.38
            if is_lunch:
                hour = int(np.clip(rng.normal(12.8, 1.1), 11, 15))
            else:
                hour = int(np.clip(rng.normal(19.2, 1.4), 17, 23))

            minute = int(rng.integers(0, 60))
            second = int(rng.integers(0, 60))
            order_timestamp = datetime.combine(
                order_date, time(hour, minute, second), tzinfo=timezone.utc
            )

            # Future timestamp defect
            if enable_anomalies and (rng.random() < anomalies.future_timestamp_rate):
                order_timestamp += timedelta(days=500)

            # Channel and payment method
            order_channel = str(rng.choice(CHANNELS, p=[0.45, 0.25, 0.20, 0.10]))
            payment_method = str(rng.choice(PAYMENT_METHODS, p=[0.55, 0.20, 0.10, 0.12, 0.03]))

            # Order status: cancelled and voided anomalies
            if enable_anomalies and (rng.random() < anomalies.cancelled_order_rate):
                order_status = "Cancelled"
            elif enable_anomalies and (rng.random() < anomalies.voided_order_rate):
                order_status = "Voided"
            else:
                order_status = "Completed"

            # Number of order line items: Poisson distribution targeting mean 10.0
            num_lines = int(np.clip(rng.poisson(10.0), 1, 35))

            order_subtotal = Decimal("0.00")
            order_discount = Decimal("0.00")

            # Generate order line items
            for _ in range(num_lines):
                item_counter += 1
                source_order_item_id = f"ITEM-{item_counter:08d}"

                chosen_dish_id = str(rng.choice(item_ids, p=item_weights))
                dish_meta = item_lookup[chosen_dish_id]

                # Point in time price lookup from pricing_history
                unit_price, unit_cost = resolve_point_in_time_price(
                    menu_item_id=chosen_dish_id,
                    order_dt=order_timestamp,
                    pricing_index=pricing_index,
                    default_price=dish_meta["current_base_price"],
                    default_cost=dish_meta["current_base_cost"],
                )

                quantity = int(
                    rng.choice([1, 1, 1, 2, 2, 3], p=[0.50, 0.20, 0.10, 0.10, 0.05, 0.05])
                )

                # Quality anomaly: invalid zero quantity
                if enable_anomalies and (rng.random() < anomalies.invalid_zero_quantity_rate):
                    quantity = 0

                # Quality anomaly: invalid negative price
                if enable_anomalies and (rng.random() < anomalies.invalid_negative_price_rate):
                    unit_price = -abs(unit_price)

                # Promotion evaluation: check if a campaign matches this item/channel/date
                promo_id = None
                line_discount = 0.00

                # Match active promotion
                for promo in promotions:
                    if promo["start_date"] <= order_date <= promo["end_date"]:
                        if promo["source_menu_item_id"] == chosen_dish_id or (
                            promo["applicable_channel"] == order_channel
                        ):
                            promo_id = promo["source_promotion_id"]
                            if promo["discount_type"] == "Fixed Amount":
                                line_discount = min(promo["discount_value"], unit_price * quantity)
                            elif promo["discount_type"] == "Percentage":
                                line_discount = round(
                                    unit_price * quantity * (promo["discount_value"] / 100.0), 2
                                )
                            break

                line_net = compute_line_net_revenue(quantity, unit_price, line_discount)
                line_cm = compute_line_contribution_margin(line_net, quantity, unit_cost)

                order_subtotal += Decimal(str(round(unit_price * quantity, 2)))
                order_discount += Decimal(str(line_discount))

                chunk_items_list.append(
                    {
                        "source_order_item_id": source_order_item_id,
                        "source_order_id": source_order_id,
                        "source_menu_item_id": chosen_dish_id,
                        "quantity": quantity,
                        "unit_price_at_sale": float(unit_price),
                        "unit_cost_at_sale": float(unit_cost),
                        "line_discount": float(line_discount),
                        "source_promotion_id": promo_id,
                        "line_net_revenue": float(line_net),
                        "line_contribution_margin": float(line_cm),
                        "special_instructions": "Special chef request"
                        if item_counter % 20 == 0
                        else None,
                        "created_at": order_timestamp,
                    }
                )

                # Inject duplicate order item anomaly
                if enable_anomalies and (rng.random() < anomalies.duplicate_order_item_rate):
                    chunk_items_list.append(dict(chunk_items_list[-1]))

            subtotal_flt = max(0.0, float(round(order_subtotal, 2)))
            discount_flt = max(0.0, float(round(order_discount, 2)))
            net_before_tax = max(0.0, subtotal_flt - discount_flt)

            tax_amount = round(net_before_tax * 0.0825, 2) if order_status == "Completed" else 0.00
            tip_amount = (
                round(net_before_tax * 0.15, 2)
                if (order_status == "Completed" and order_channel in ("Dine-in", "Delivery Direct"))
                else 0.00
            )
            total_amount = compute_order_total_amount(
                subtotal_flt, discount_flt, tax_amount, tip_amount
            )

            chunk_orders_list.append(
                {
                    "source_order_id": source_order_id,
                    "source_restaurant_id": rest_id,
                    "source_customer_id": source_customer_id,
                    "order_timestamp": order_timestamp,
                    "order_channel": order_channel,
                    "order_status": order_status,
                    "subtotal_amount": subtotal_flt,
                    "discount_amount": discount_flt,
                    "tax_amount": tax_amount,
                    "tip_amount": tip_amount,
                    "total_amount": total_amount,
                    "payment_method": payment_method,
                    "created_at": order_timestamp,
                }
            )

            # Inject duplicate order anomaly
            if enable_anomalies and (rng.random() < anomalies.duplicate_order_rate):
                chunk_orders_list.append(dict(chunk_orders_list[-1]))

        yield chunk_orders_list, chunk_items_list


def generate_ratings(
    config: GeneratorConfig,
    restaurants: list[dict[str, Any]],
    customers: list[dict[str, Any]],
    menu_items: list[dict[str, Any]],
    completed_orders_sample: list[dict[str, Any]],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    """Generate customer ratings with verified purchase links and localized anomaly drops."""
    ratings: list[dict[str, Any]] = []
    target_count = config.scale.num_ratings
    start_date = config.start_date
    history_days = config.scale.history_days
    anomalies = config.anomalies
    enable_anomalies = config.enable_anomalies

    # Designate 2 dishes experiencing localized rating drops (recipe change defect)
    anomaly_dish_ids = (
        [menu_items[3]["source_menu_item_id"], menu_items[7]["source_menu_item_id"]]
        if enable_anomalies and len(menu_items) > 7
        else []
    )

    review_snippets_positive = [
        "Outstanding meal and attentive staff.",
        "Delicious presentation, flavorful and tender.",
        "A regular favorite at this branch.",
        "Crispy, hot, and seasoned to perfection.",
        "Great atmosphere and prompt service.",
    ]
    review_snippets_negative = [
        "Food arrived cold and service was sluggish.",
        "Unusually bitter aftertaste in this recipe.",
        "Disappointed with the texture and portion size.",
        "Order took over 45 minutes during peak hours.",
    ]

    for idx in range(1, target_count + 1):
        source_rating_id = f"RAT-{idx:08d}"

        # 75% of ratings tie to a verified completed purchase
        is_verified = len(completed_orders_sample) > 0 and (rng.random() < 0.75)
        if is_verified:
            order_sample = completed_orders_sample[idx % len(completed_orders_sample)]
            order_id = order_sample["source_order_id"]
            rest_id = order_sample["source_restaurant_id"]
            cust_id = order_sample["source_customer_id"]
            rating_dt = order_sample["order_timestamp"] + timedelta(hours=int(rng.integers(1, 48)))
        else:
            order_id = None
            rest_id = restaurants[int(rng.integers(0, len(restaurants)))]["source_restaurant_id"]
            cust_id = (
                customers[int(rng.integers(0, len(customers)))]["source_customer_id"]
                if rng.random() > 0.20
                else None
            )
            rating_dt = datetime.combine(
                start_date + timedelta(days=int(rng.integers(0, history_days))),
                time(int(rng.integers(12, 23)), int(rng.integers(0, 60))),
                tzinfo=timezone.utc,
            )

        dish_id = (
            menu_items[int(rng.integers(0, len(menu_items)))]["source_menu_item_id"]
            if rng.random() > 0.15
            else None
        )

        # Check for localized rating drop anomaly (e.g. recipe defect on anomaly dish during days 90-130)
        is_anomaly_drop = False
        if dish_id in anomaly_dish_ids:
            day_num = (rating_dt.date() - start_date).days
            if 90 <= day_num <= 130:
                is_anomaly_drop = True

        if is_anomaly_drop:
            score = int(rng.choice([1, 2], p=[0.70, 0.30]))
            food_score = score
            service_score = int(rng.choice([2, 3]))
            ambiance_score = 3
            review_text = "Severe quality drop. Recipe tastes sour and spoiled."
        else:
            score = int(rng.choice([5, 4, 3, 2, 1], p=[0.50, 0.25, 0.12, 0.08, 0.05]))
            food_score = int(np.clip(score + rng.choice([-1, 0, 1]), 1, 5))
            service_score = int(np.clip(score + rng.choice([-1, 0, 1]), 1, 5))
            ambiance_score = (
                int(np.clip(score + rng.choice([-1, 0, 1]), 1, 5)) if score >= 3 else None
            )

            # Missing review text anomaly (40% blank review text)
            if enable_anomalies and (rng.random() < anomalies.missing_rating_text_rate):
                review_text = None
            else:
                review_text = (
                    review_snippets_positive[int(rng.integers(0, len(review_snippets_positive)))]
                    if score >= 4
                    else review_snippets_negative[
                        int(rng.integers(0, len(review_snippets_negative)))
                    ]
                )

        ratings.append(
            {
                "source_rating_id": source_rating_id,
                "source_restaurant_id": rest_id,
                "source_order_id": order_id,
                "source_customer_id": cust_id,
                "source_menu_item_id": dish_id,
                "rating_score": score,
                "food_rating": food_score,
                "service_rating": service_score,
                "ambiance_rating": ambiance_score,
                "review_text": review_text,
                "rating_timestamp": rating_dt,
                "is_verified_purchase": is_verified,
                "created_at": rating_dt,
            }
        )

    return ratings


def generate_wastage(
    config: GeneratorConfig,
    restaurants: list[dict[str, Any]],
    menu_items: list[dict[str, Any]],
    rng: np.random.Generator,
) -> list[dict[str, Any]]:
    """Generate operational discard records reflecting perishability hazard rates."""
    wastage: list[dict[str, Any]] = []
    target_count = config.scale.num_wastage_records
    start_date = config.start_date
    history_days = config.scale.history_days

    # Perishable ingredients have higher hazard rates
    perishables = [
        ("Fresh Atlantic Salmon", "kg", 18.00, 3.5),
        ("Ground Wagyu Beef", "kg", 12.50, 2.8),
        ("Fresh Mozzarella", "kg", 7.80, 2.0),
        ("Heavy Cream 36%", "L", 4.20, 1.8),
        ("Prepped House Salads", "units", 3.50, 4.0),
        ("Chef Clam Chowder Soup", "L", 5.00, 3.0),
        ("Artisan Burger Buns", "units", 0.65, 1.2),
        ("Hand-cut Russet Potatoes", "kg", 1.20, 2.5),
    ]

    staff_reporters = [
        "Chef Carlos",
        "Sous Chef Maya",
        "Manager Elena",
        "Cook Sam",
        "Line Cook Tyler",
    ]

    for idx in range(1, target_count + 1):
        source_wastage_id = f"WASTE-{idx:08d}"
        rest = restaurants[int(rng.integers(0, len(restaurants)))]
        rest_id = rest["source_restaurant_id"]

        day_offset = int(rng.integers(0, history_days))
        waste_date = start_date + timedelta(days=day_offset)
        waste_dt = datetime.combine(
            waste_date,
            time(int(rng.integers(21, 23)), int(rng.integers(0, 60))),
            tzinfo=timezone.utc,
        )

        ing_name, uom, unit_cost, hazard = perishables[int(rng.integers(0, len(perishables)))]

        # Quantities lost (kg, L, units)
        lost_qty = round(float(rng.uniform(0.5, 5.0) * (hazard / 2.0)), 2)
        cost_loss = round(lost_qty * unit_cost, 2)
        reason = str(rng.choice(WASTAGE_REASONS, p=[0.40, 0.25, 0.15, 0.10, 0.05, 0.05]))

        dish_id = (
            menu_items[int(rng.integers(0, len(menu_items)))]["source_menu_item_id"]
            if idx % 3 == 0
            else None
        )

        wastage.append(
            {
                "source_wastage_id": source_wastage_id,
                "source_restaurant_id": rest_id,
                "source_menu_item_id": dish_id,
                "ingredient_name": ing_name,
                "wastage_timestamp": waste_dt,
                "quantity_lost": lost_qty,
                "unit_of_measure": uom,
                "cost_loss_amount": cost_loss,
                "wastage_reason": reason,
                "reported_by": staff_reporters[idx % len(staff_reporters)],
                "created_at": waste_dt,
            }
        )

    return wastage
