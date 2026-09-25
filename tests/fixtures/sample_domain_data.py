"""Small deterministic sample fixture for DineIQ Analytics business domain entities.

This module provides deterministic sample records across all eleven business domain
tables to validate:
- Foreign key and relational constraints
- Nullability (guest checkouts, optional ratings, unlinked wastage)
- Financial formula invariants:
    net_revenue = quantity * unit_price_at_sale - line_discount
    contribution_margin = net_revenue - quantity * unit_cost_at_sale
    total_amount = subtotal_amount - discount_amount + tax_amount + tip_amount
- Slowly Changing Dimension (SCD Type 2) historical pricing bounds
- Marketing campaigns and promotional discount calculations
- Quality ratings and verified purchase semantics
- Inventory balance and operational wastage tracking
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from packages.core.contracts.dataset_contract import (
    compute_line_contribution_margin,
    compute_line_net_revenue,
    compute_order_total_amount,
)
from packages.db.models.domain import (
    Customer,
    Inventory,
    MenuCategory,
    MenuItem,
    Order,
    OrderItem,
    PricingHistory,
    Promotion,
    Rating,
    Restaurant,
    Wastage,
)


def get_sample_categories_data() -> list[dict[str, Any]]:
    return [
        {
            "source_category_id": "CAT-001",
            "category_name": "Appetizers",
            "description": "Starters and small shareable plates",
            "display_order": 1,
            "is_active": True,
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_category_id": "CAT-002",
            "category_name": "Entrees",
            "description": "Main course culinary dishes",
            "display_order": 2,
            "is_active": True,
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_category_id": "CAT-003",
            "category_name": "Desserts",
            "description": "Sweet concluding courses and pastries",
            "display_order": 3,
            "is_active": True,
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_restaurants_data() -> list[dict[str, Any]]:
    return [
        {
            "source_restaurant_id": "REST-0001",
            "location_name": "Downtown Flagship",
            "city": "Chicago",
            "state_region": "IL",
            "postal_code": "60601",
            "seating_capacity": 120,
            "dining_type": "Fast Casual",
            "manager_name": "Elena Rostova",
            "opening_date": date(2023, 5, 15),
            "latitude": 41.881832,
            "longitude": -87.623177,
            "is_active": True,
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_restaurant_id": "REST-0002",
            "location_name": "Suburban Mall",
            "city": "Naperville",
            "state_region": "IL",
            "postal_code": "60540",
            "seating_capacity": 80,
            "dining_type": "Casual Dining",
            "manager_name": "Marcus Vance",
            "opening_date": date(2024, 2, 1),
            "latitude": 41.772500,
            "longitude": -88.147800,
            "is_active": True,
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_menu_items_data() -> list[dict[str, Any]]:
    return [
        {
            "source_menu_item_id": "DISH-0001",
            "source_category_id": "CAT-001",
            "item_name": "Truffle Fries",
            "description": "Hand cut russet potatoes with truffle oil and parmesan",
            "current_base_price": 8.50,
            "current_base_cost": 2.20,
            "prep_time_minutes": 10,
            "is_seasonal": False,
            "is_active": True,
            "spiciness_level": 0,
            "allergens": "Dairy",
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_menu_item_id": "DISH-0002",
            "source_category_id": "CAT-002",
            "item_name": "Wagyu Burger",
            "description": "Half pound prime wagyu patty with brioche bun",
            "current_base_price": 18.00,
            "current_base_cost": 6.50,
            "prep_time_minutes": 18,
            "is_seasonal": False,
            "is_active": True,
            "spiciness_level": 0,
            "allergens": "Gluten, Dairy",
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_menu_item_id": "DISH-0003",
            "source_category_id": "CAT-002",
            "item_name": "Margherita Pizza",
            "description": "Wood fired pizza with fresh mozzarella and basil",
            "current_base_price": 15.00,
            "current_base_cost": 4.00,
            "prep_time_minutes": 15,
            "is_seasonal": False,
            "is_active": True,
            "spiciness_level": 0,
            "allergens": "Gluten, Dairy",
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_menu_item_id": "DISH-0004",
            "source_category_id": "CAT-003",
            "item_name": "Molten Lava Cake",
            "description": "Warm chocolate fondant with vanilla ice cream",
            "current_base_price": 9.00,
            "current_base_cost": 2.50,
            "prep_time_minutes": 12,
            "is_seasonal": False,
            "is_active": True,
            "spiciness_level": 0,
            "allergens": "Gluten, Dairy, Eggs",
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_pricing_history_data() -> list[dict[str, Any]]:
    return [
        {
            "source_pricing_history_id": "PRC-000001",
            "source_menu_item_id": "DISH-0002",
            "source_restaurant_id": None,
            "base_price": 16.50,
            "base_cost": 6.00,
            "effective_from": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "effective_to": datetime(2025, 6, 30, 23, 59, 59, tzinfo=timezone.utc),
            "change_reason": "Initial introductory launch pricing",
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_pricing_history_id": "PRC-000002",
            "source_menu_item_id": "DISH-0002",
            "source_restaurant_id": None,
            "base_price": 18.00,
            "base_cost": 6.50,
            "effective_from": datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
            "effective_to": None,
            "change_reason": "Ingredient beef cost inflation adjustment",
            "created_at": datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_pricing_history_id": "PRC-000003",
            "source_menu_item_id": "DISH-0001",
            "source_restaurant_id": None,
            "base_price": 8.50,
            "base_cost": 2.20,
            "effective_from": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "effective_to": None,
            "change_reason": "Baseline catalog launch pricing",
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_promotions_data() -> list[dict[str, Any]]:
    return [
        {
            "source_promotion_id": "PROMO-0001",
            "campaign_name": "Summer Burger Special",
            "promo_code": "SUMMERBURGER",
            "discount_type": "Fixed Amount",
            "discount_value": 3.00,
            "start_date": date(2025, 7, 1),
            "end_date": date(2025, 7, 31),
            "minimum_order_amount": 15.00,
            "source_category_id": None,
            "source_menu_item_id": "DISH-0002",
            "applicable_channel": "Dine-in",
            "is_active": True,
            "is_misleading": False,
            "created_at": datetime(2025, 6, 25, 0, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_promotion_id": "PROMO-0002",
            "campaign_name": "Deep Discount Promo Trap",
            "promo_code": "HALFPRICEBURGER",
            "discount_type": "Percentage",
            "discount_value": 50.00,
            "start_date": date(2025, 8, 1),
            "end_date": date(2025, 8, 15),
            "minimum_order_amount": 20.00,
            "source_category_id": None,
            "source_menu_item_id": "DISH-0002",
            "applicable_channel": "Delivery Direct",
            "is_active": True,
            "is_misleading": True,
            "created_at": datetime(2025, 7, 28, 0, 0, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_customers_data() -> list[dict[str, Any]]:
    return [
        {
            "source_customer_id": "CUST-00000001",
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice.johnson@example.com",
            "phone": "+1-312-555-0101",
            "registration_date": date(2024, 3, 10),
            "loyalty_tier": "Gold",
            "preferred_channel": "Dine-in",
            "home_city": "Chicago",
            "is_active": True,
            "created_at": datetime(2024, 3, 10, 10, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_customer_id": "CUST-00000002",
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob.smith@example.com",
            "phone": "+1-312-555-0102",
            "registration_date": date(2024, 6, 20),
            "loyalty_tier": "Bronze",
            "preferred_channel": "Takeaway",
            "home_city": "Naperville",
            "is_active": True,
            "created_at": datetime(2024, 6, 20, 14, 30, 0, tzinfo=timezone.utc),
        },
        {
            "source_customer_id": "CUST-00000003",
            "first_name": "Charlie",
            "last_name": "Davis",
            "email": None,  # Intentionally null to test missing profile details
            "phone": None,
            "registration_date": date(2024, 9, 1),
            "loyalty_tier": "None",
            "preferred_channel": None,
            "home_city": None,
            "is_active": True,
            "created_at": datetime(2024, 9, 1, 9, 15, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_orders_data() -> list[dict[str, Any]]:
    # Order 1: Completed, customer Alice, dining in, discount applied
    o1_subtotal = 26.50  # 8.50 + 18.00
    o1_discount = 3.00
    o1_tax = 2.35
    o1_tip = 4.00
    o1_total = compute_order_total_amount(o1_subtotal, o1_discount, o1_tax, o1_tip)

    # Order 2: Completed guest checkout (source_customer_id is None)
    o2_subtotal = 15.00
    o2_discount = 0.00
    o2_tax = 1.50
    o2_tip = 0.00
    o2_total = compute_order_total_amount(o2_subtotal, o2_discount, o2_tax, o2_tip)

    # Order 3: Cancelled order (Bob)
    o3_subtotal = 18.00
    o3_discount = 0.00
    o3_tax = 1.80
    o3_tip = 0.00
    o3_total = compute_order_total_amount(o3_subtotal, o3_discount, o3_tax, o3_tip)

    # Order 4: Completed with misleading 50% discount
    o4_subtotal = 36.00  # 2 * 18.00
    o4_discount = 18.00
    o4_tax = 1.80
    o4_tip = 3.00
    o4_total = compute_order_total_amount(o4_subtotal, o4_discount, o4_tax, o4_tip)

    return [
        {
            "source_order_id": "ORD-00000001",
            "source_restaurant_id": "REST-0001",
            "source_customer_id": "CUST-00000001",
            "order_timestamp": datetime(2025, 7, 10, 19, 30, 0, tzinfo=timezone.utc),
            "order_channel": "Dine-in",
            "order_status": "Completed",
            "subtotal_amount": o1_subtotal,
            "discount_amount": o1_discount,
            "tax_amount": o1_tax,
            "tip_amount": o1_tip,
            "total_amount": o1_total,
            "payment_method": "Credit Card",
            "created_at": datetime(2025, 7, 10, 19, 30, 0, tzinfo=timezone.utc),
        },
        {
            "source_order_id": "ORD-00000002",
            "source_restaurant_id": "REST-0002",
            "source_customer_id": None,  # Guest order
            "order_timestamp": datetime(2025, 7, 11, 12, 15, 0, tzinfo=timezone.utc),
            "order_channel": "Takeaway",
            "order_status": "Completed",
            "subtotal_amount": o2_subtotal,
            "discount_amount": o2_discount,
            "tax_amount": o2_tax,
            "tip_amount": o2_tip,
            "total_amount": o2_total,
            "payment_method": "Digital Wallet",
            "created_at": datetime(2025, 7, 11, 12, 15, 0, tzinfo=timezone.utc),
        },
        {
            "source_order_id": "ORD-00000003",
            "source_restaurant_id": "REST-0001",
            "source_customer_id": "CUST-00000002",
            "order_timestamp": datetime(2025, 7, 12, 20, 0, 0, tzinfo=timezone.utc),
            "order_channel": "Delivery Direct",
            "order_status": "Cancelled",
            "subtotal_amount": o3_subtotal,
            "discount_amount": o3_discount,
            "tax_amount": o3_tax,
            "tip_amount": o3_tip,
            "total_amount": o3_total,
            "payment_method": "Credit Card",
            "created_at": datetime(2025, 7, 12, 20, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_order_id": "ORD-00000004",
            "source_restaurant_id": "REST-0001",
            "source_customer_id": "CUST-00000001",
            "order_timestamp": datetime(2025, 8, 5, 18, 45, 0, tzinfo=timezone.utc),
            "order_channel": "Delivery Direct",
            "order_status": "Completed",
            "subtotal_amount": o4_subtotal,
            "discount_amount": o4_discount,
            "tax_amount": o4_tax,
            "tip_amount": o4_tip,
            "total_amount": o4_total,
            "payment_method": "Credit Card",
            "created_at": datetime(2025, 8, 5, 18, 45, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_order_items_data() -> list[dict[str, Any]]:
    # Line 1: Truffle Fries on Order 1
    l1_qty = 1
    l1_price = 8.50
    l1_cost = 2.20
    l1_disc = 0.00
    l1_net = compute_line_net_revenue(l1_qty, l1_price, l1_disc)
    l1_cm = compute_line_contribution_margin(l1_net, l1_qty, l1_cost)

    # Line 2: Wagyu Burger on Order 1 with 3.00 promo discount
    l2_qty = 1
    l2_price = 18.00
    l2_cost = 6.50
    l2_disc = 3.00
    l2_net = compute_line_net_revenue(l2_qty, l2_price, l2_disc)
    l2_cm = compute_line_contribution_margin(l2_net, l2_qty, l2_cost)

    # Line 3: Margherita Pizza on Order 2 (Guest checkout)
    l3_qty = 1
    l3_price = 15.00
    l3_cost = 4.00
    l3_disc = 0.00
    l3_net = compute_line_net_revenue(l3_qty, l3_price, l3_disc)
    l3_cm = compute_line_contribution_margin(l3_net, l3_qty, l3_cost)

    # Line 4: Wagyu Burger on Order 3 (Cancelled)
    l4_qty = 1
    l4_price = 18.00
    l4_cost = 6.50
    l4_disc = 0.00
    l4_net = compute_line_net_revenue(l4_qty, l4_price, l4_disc)
    l4_cm = compute_line_contribution_margin(l4_net, l4_qty, l4_cost)

    # Line 5: 2 Wagyu Burgers on Order 4 with 18.00 (50%) discount promo trap
    l5_qty = 2
    l5_price = 18.00
    l5_cost = 6.50
    l5_disc = 18.00
    l5_net = compute_line_net_revenue(l5_qty, l5_price, l5_disc)
    l5_cm = compute_line_contribution_margin(l5_net, l5_qty, l5_cost)

    return [
        {
            "source_order_item_id": "ITEM-00000001",
            "source_order_id": "ORD-00000001",
            "source_menu_item_id": "DISH-0001",
            "quantity": l1_qty,
            "unit_price_at_sale": l1_price,
            "unit_cost_at_sale": l1_cost,
            "line_discount": l1_disc,
            "source_promotion_id": None,
            "line_net_revenue": l1_net,
            "line_contribution_margin": l1_cm,
            "special_instructions": "Extra crispy",
            "created_at": datetime(2025, 7, 10, 19, 30, 0, tzinfo=timezone.utc),
        },
        {
            "source_order_item_id": "ITEM-00000002",
            "source_order_id": "ORD-00000001",
            "source_menu_item_id": "DISH-0002",
            "quantity": l2_qty,
            "unit_price_at_sale": l2_price,
            "unit_cost_at_sale": l2_cost,
            "line_discount": l2_disc,
            "source_promotion_id": "PROMO-0001",
            "line_net_revenue": l2_net,
            "line_contribution_margin": l2_cm,
            "special_instructions": "Medium rare",
            "created_at": datetime(2025, 7, 10, 19, 30, 0, tzinfo=timezone.utc),
        },
        {
            "source_order_item_id": "ITEM-00000003",
            "source_order_id": "ORD-00000002",
            "source_menu_item_id": "DISH-0003",
            "quantity": l3_qty,
            "unit_price_at_sale": l3_price,
            "unit_cost_at_sale": l3_cost,
            "line_discount": l3_disc,
            "source_promotion_id": None,
            "line_net_revenue": l3_net,
            "line_contribution_margin": l3_cm,
            "special_instructions": None,
            "created_at": datetime(2025, 7, 11, 12, 15, 0, tzinfo=timezone.utc),
        },
        {
            "source_order_item_id": "ITEM-00000004",
            "source_order_id": "ORD-00000003",
            "source_menu_item_id": "DISH-0002",
            "quantity": l4_qty,
            "unit_price_at_sale": l4_price,
            "unit_cost_at_sale": l4_cost,
            "line_discount": l4_disc,
            "source_promotion_id": None,
            "line_net_revenue": l4_net,
            "line_contribution_margin": l4_cm,
            "special_instructions": None,
            "created_at": datetime(2025, 7, 12, 20, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_order_item_id": "ITEM-00000005",
            "source_order_id": "ORD-00000004",
            "source_menu_item_id": "DISH-0002",
            "quantity": l5_qty,
            "unit_price_at_sale": l5_price,
            "unit_cost_at_sale": l5_cost,
            "line_discount": l5_disc,
            "source_promotion_id": "PROMO-0002",
            "line_net_revenue": l5_net,
            "line_contribution_margin": l5_cm,
            "special_instructions": None,
            "created_at": datetime(2025, 8, 5, 18, 45, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_ratings_data() -> list[dict[str, Any]]:
    return [
        {
            "source_rating_id": "RAT-00000001",
            "source_restaurant_id": "REST-0001",
            "source_order_id": "ORD-00000001",
            "source_customer_id": "CUST-00000001",
            "source_menu_item_id": "DISH-0002",
            "rating_score": 5,
            "food_rating": 5,
            "service_rating": 5,
            "ambiance_rating": 4,
            "review_text": "Exceptional wagyu burger, perfectly cooked and tender.",
            "rating_timestamp": datetime(2025, 7, 10, 21, 0, 0, tzinfo=timezone.utc),
            "is_verified_purchase": True,
            "created_at": datetime(2025, 7, 10, 21, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_rating_id": "RAT-00000002",
            "source_restaurant_id": "REST-0002",
            "source_order_id": "ORD-00000002",
            "source_customer_id": None,  # Guest review
            "source_menu_item_id": "DISH-0003",
            "rating_score": 4,
            "food_rating": 4,
            "service_rating": 4,
            "ambiance_rating": None,
            "review_text": "Crispy pizza crust and fresh basil.",
            "rating_timestamp": datetime(2025, 7, 11, 13, 0, 0, tzinfo=timezone.utc),
            "is_verified_purchase": True,
            "created_at": datetime(2025, 7, 11, 13, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_rating_id": "RAT-00000003",
            "source_restaurant_id": "REST-0001",
            "source_order_id": None,  # Walk in without order tie
            "source_customer_id": "CUST-00000002",
            "source_menu_item_id": None,
            "rating_score": 2,
            "food_rating": 2,
            "service_rating": 1,
            "ambiance_rating": 3,
            "review_text": "Service was very slow during peak weekend hours.",
            "rating_timestamp": datetime(2025, 7, 13, 19, 0, 0, tzinfo=timezone.utc),
            "is_verified_purchase": False,
            "created_at": datetime(2025, 7, 13, 19, 0, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_inventory_data() -> list[dict[str, Any]]:
    return [
        {
            "source_inventory_id": "INV-REST01-0001",
            "source_restaurant_id": "REST-0001",
            "ingredient_name": "Ground Wagyu Beef",
            "ingredient_category": "Meat & Poultry",
            "current_stock_quantity": 45.50,
            "unit_of_measure": "kg",
            "reorder_threshold": 15.00,
            "reorder_quantity": 30.00,
            "unit_purchase_cost": 12.50,
            "last_restock_date": date(2025, 7, 8),
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 7, 8, 6, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_inventory_id": "INV-REST01-0002",
            "source_restaurant_id": "REST-0001",
            "ingredient_name": "Russet Potatoes",
            "ingredient_category": "Produce",
            "current_stock_quantity": 80.00,
            "unit_of_measure": "kg",
            "reorder_threshold": 25.00,
            "reorder_quantity": 50.00,
            "unit_purchase_cost": 1.20,
            "last_restock_date": date(2025, 7, 9),
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 7, 9, 6, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_inventory_id": "INV-REST02-0001",
            "source_restaurant_id": "REST-0002",
            "ingredient_name": "Mozzarella Cheese",
            "ingredient_category": "Dairy",
            "current_stock_quantity": 20.00,
            "unit_of_measure": "kg",
            "reorder_threshold": 8.00,
            "reorder_quantity": 15.00,
            "unit_purchase_cost": 7.80,
            "last_restock_date": date(2025, 7, 7),
            "created_at": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2025, 7, 7, 6, 0, 0, tzinfo=timezone.utc),
        },
    ]


def get_sample_wastage_data() -> list[dict[str, Any]]:
    return [
        {
            "source_wastage_id": "WASTE-00000001",
            "source_restaurant_id": "REST-0001",
            "source_menu_item_id": "DISH-0001",
            "ingredient_name": "Russet Potatoes",
            "wastage_timestamp": datetime(2025, 7, 10, 23, 0, 0, tzinfo=timezone.utc),
            "quantity_lost": 2.50,
            "unit_of_measure": "kg",
            "cost_loss_amount": 3.00,  # 2.5 kg * 1.20 cost
            "wastage_reason": "Expired",
            "reported_by": "Chef Carlos",
            "created_at": datetime(2025, 7, 10, 23, 0, 0, tzinfo=timezone.utc),
        },
        {
            "source_wastage_id": "WASTE-00000002",
            "source_restaurant_id": "REST-0001",
            "source_menu_item_id": None,
            "ingredient_name": "Ground Wagyu Beef",
            "wastage_timestamp": datetime(2025, 7, 11, 8, 30, 0, tzinfo=timezone.utc),
            "quantity_lost": 4.00,
            "unit_of_measure": "kg",
            "cost_loss_amount": 50.00,  # 4 kg * 12.50 cost
            "wastage_reason": "Equipment Failure",
            "reported_by": "Manager Elena",
            "created_at": datetime(2025, 7, 11, 8, 30, 0, tzinfo=timezone.utc),
        },
        {
            "source_wastage_id": "WASTE-00000003",
            "source_restaurant_id": "REST-0002",
            "source_menu_item_id": "DISH-0003",
            "ingredient_name": "Pizza Dough & Mozzarella",
            "wastage_timestamp": datetime(2025, 7, 11, 20, 15, 0, tzinfo=timezone.utc),
            "quantity_lost": 1.00,
            "unit_of_measure": "units",
            "cost_loss_amount": 4.00,  # 1 pizza unit cost
            "wastage_reason": "Cooking Error",
            "reported_by": "Cook Sam",
            "created_at": datetime(2025, 7, 11, 20, 15, 0, tzinfo=timezone.utc),
        },
    ]


def get_all_sample_domain_tables_dict() -> dict[str, list[dict[str, Any]]]:
    """Return in-memory dictionary representation of the small deterministic sample dataset."""
    return {
        "menu_categories": get_sample_categories_data(),
        "restaurants": get_sample_restaurants_data(),
        "menu_items": get_sample_menu_items_data(),
        "pricing_history": get_sample_pricing_history_data(),
        "promotions": get_sample_promotions_data(),
        "customers": get_sample_customers_data(),
        "orders": get_sample_orders_data(),
        "order_items": get_sample_order_items_data(),
        "ratings": get_sample_ratings_data(),
        "inventory": get_sample_inventory_data(),
        "wastage": get_sample_wastage_data(),
    }


def seed_domain_sample_into_db(session: Session) -> dict[str, int]:
    """Populate database with the small deterministic domain fixture resolving foreign key IDs.

    Returns:
        Mapping of table name to count of inserted rows.
    """
    # 1. Categories
    cat_map: dict[str, int] = {}
    for cat_data in get_sample_categories_data():
        cat = MenuCategory(
            source_category_id=cat_data["source_category_id"],
            category_name=cat_data["category_name"],
            description=cat_data["description"],
            display_order=cat_data["display_order"],
            is_active=cat_data["is_active"],
            created_at=cat_data["created_at"],
        )
        session.add(cat)
        session.flush()
        cat_map[cat.source_category_id] = cat.id

    # 2. Restaurants
    rest_map: dict[str, int] = {}
    for rest_data in get_sample_restaurants_data():
        rest = Restaurant(
            source_restaurant_id=rest_data["source_restaurant_id"],
            location_name=rest_data["location_name"],
            city=rest_data["city"],
            state_region=rest_data["state_region"],
            postal_code=rest_data["postal_code"],
            seating_capacity=rest_data["seating_capacity"],
            dining_type=rest_data["dining_type"],
            manager_name=rest_data["manager_name"],
            opening_date=rest_data["opening_date"],
            latitude=rest_data["latitude"],
            longitude=rest_data["longitude"],
            is_active=rest_data["is_active"],
            created_at=rest_data["created_at"],
        )
        session.add(rest)
        session.flush()
        rest_map[rest.source_restaurant_id] = rest.id

    # 3. Menu Items
    dish_map: dict[str, int] = {}
    for item_data in get_sample_menu_items_data():
        item = MenuItem(
            source_menu_item_id=item_data["source_menu_item_id"],
            category_id=cat_map[item_data["source_category_id"]],
            item_name=item_data["item_name"],
            description=item_data["description"],
            current_base_price=item_data["current_base_price"],
            current_base_cost=item_data["current_base_cost"],
            prep_time_minutes=item_data["prep_time_minutes"],
            is_seasonal=item_data["is_seasonal"],
            is_active=item_data["is_active"],
            spiciness_level=item_data["spiciness_level"],
            allergens=item_data["allergens"],
            created_at=item_data["created_at"],
        )
        session.add(item)
        session.flush()
        dish_map[item.source_menu_item_id] = item.id

    # 4. Pricing History
    pricing_count = 0
    for prc_data in get_sample_pricing_history_data():
        rest_id = (
            rest_map[prc_data["source_restaurant_id"]] if prc_data["source_restaurant_id"] else None
        )
        prc = PricingHistory(
            source_pricing_history_id=prc_data["source_pricing_history_id"],
            menu_item_id=dish_map[prc_data["source_menu_item_id"]],
            restaurant_id=rest_id,
            base_price=prc_data["base_price"],
            base_cost=prc_data["base_cost"],
            effective_from=prc_data["effective_from"],
            effective_to=prc_data["effective_to"],
            change_reason=prc_data["change_reason"],
            created_at=prc_data["created_at"],
        )
        session.add(prc)
        pricing_count += 1
    session.flush()

    # 5. Promotions
    promo_map: dict[str, int] = {}
    for promo_data in get_sample_promotions_data():
        cat_id = (
            cat_map[promo_data["source_category_id"]] if promo_data["source_category_id"] else None
        )
        dish_id = (
            dish_map[promo_data["source_menu_item_id"]]
            if promo_data["source_menu_item_id"]
            else None
        )
        promo = Promotion(
            source_promotion_id=promo_data["source_promotion_id"],
            campaign_name=promo_data["campaign_name"],
            promo_code=promo_data["promo_code"],
            discount_type=promo_data["discount_type"],
            discount_value=promo_data["discount_value"],
            start_date=promo_data["start_date"],
            end_date=promo_data["end_date"],
            minimum_order_amount=promo_data["minimum_order_amount"],
            applicable_category_id=cat_id,
            applicable_menu_item_id=dish_id,
            applicable_channel=promo_data["applicable_channel"],
            is_active=promo_data["is_active"],
            is_misleading=promo_data["is_misleading"],
            created_at=promo_data["created_at"],
        )
        session.add(promo)
        session.flush()
        promo_map[promo.source_promotion_id] = promo.id

    # 6. Customers
    cust_map: dict[str, int] = {}
    for cust_data in get_sample_customers_data():
        cust = Customer(
            source_customer_id=cust_data["source_customer_id"],
            first_name=cust_data["first_name"],
            last_name=cust_data["last_name"],
            email=cust_data["email"],
            phone=cust_data["phone"],
            registration_date=cust_data["registration_date"],
            loyalty_tier=cust_data["loyalty_tier"],
            preferred_channel=cust_data["preferred_channel"],
            home_city=cust_data["home_city"],
            is_active=cust_data["is_active"],
            created_at=cust_data["created_at"],
        )
        session.add(cust)
        session.flush()
        cust_map[cust.source_customer_id] = cust.id

    # 7. Orders
    order_map: dict[str, int] = {}
    for ord_data in get_sample_orders_data():
        cid = cust_map[ord_data["source_customer_id"]] if ord_data["source_customer_id"] else None
        order = Order(
            source_order_id=ord_data["source_order_id"],
            restaurant_id=rest_map[ord_data["source_restaurant_id"]],
            customer_id=cid,
            order_timestamp=ord_data["order_timestamp"],
            order_channel=ord_data["order_channel"],
            order_status=ord_data["order_status"],
            subtotal_amount=ord_data["subtotal_amount"],
            discount_amount=ord_data["discount_amount"],
            tax_amount=ord_data["tax_amount"],
            tip_amount=ord_data["tip_amount"],
            total_amount=ord_data["total_amount"],
            payment_method=ord_data["payment_method"],
            created_at=ord_data["created_at"],
        )
        session.add(order)
        session.flush()
        order_map[order.source_order_id] = order.id

    # 8. Order Items
    order_items_count = 0
    for item_data in get_sample_order_items_data():
        pid = (
            promo_map[item_data["source_promotion_id"]]
            if item_data["source_promotion_id"]
            else None
        )
        oi = OrderItem(
            source_order_item_id=item_data["source_order_item_id"],
            order_id=order_map[item_data["source_order_id"]],
            menu_item_id=dish_map[item_data["source_menu_item_id"]],
            quantity=item_data["quantity"],
            unit_price_at_sale=item_data["unit_price_at_sale"],
            unit_cost_at_sale=item_data["unit_cost_at_sale"],
            line_discount=item_data["line_discount"],
            promotion_id=pid,
            line_net_revenue=item_data["line_net_revenue"],
            line_contribution_margin=item_data["line_contribution_margin"],
            special_instructions=item_data["special_instructions"],
            created_at=item_data["created_at"],
        )
        session.add(oi)
        order_items_count += 1
    session.flush()

    # 9. Ratings
    ratings_count = 0
    for rat_data in get_sample_ratings_data():
        oid = order_map[rat_data["source_order_id"]] if rat_data["source_order_id"] else None
        cid = cust_map[rat_data["source_customer_id"]] if rat_data["source_customer_id"] else None
        did = dish_map[rat_data["source_menu_item_id"]] if rat_data["source_menu_item_id"] else None
        rating = Rating(
            source_rating_id=rat_data["source_rating_id"],
            restaurant_id=rest_map[rat_data["source_restaurant_id"]],
            order_id=oid,
            customer_id=cid,
            menu_item_id=did,
            rating_score=rat_data["rating_score"],
            food_rating=rat_data["food_rating"],
            service_rating=rat_data["service_rating"],
            ambiance_rating=rat_data["ambiance_rating"],
            review_text=rat_data["review_text"],
            rating_timestamp=rat_data["rating_timestamp"],
            is_verified_purchase=rat_data["is_verified_purchase"],
            created_at=rat_data["created_at"],
        )
        session.add(rating)
        ratings_count += 1
    session.flush()

    # 10. Inventory
    inventory_count = 0
    for inv_data in get_sample_inventory_data():
        inv = Inventory(
            source_inventory_id=inv_data["source_inventory_id"],
            restaurant_id=rest_map[inv_data["source_restaurant_id"]],
            ingredient_name=inv_data["ingredient_name"],
            ingredient_category=inv_data["ingredient_category"],
            current_stock_quantity=inv_data["current_stock_quantity"],
            unit_of_measure=inv_data["unit_of_measure"],
            reorder_threshold=inv_data["reorder_threshold"],
            reorder_quantity=inv_data["reorder_quantity"],
            unit_purchase_cost=inv_data["unit_purchase_cost"],
            last_restock_date=inv_data["last_restock_date"],
            created_at=inv_data["created_at"],
            updated_at=inv_data["updated_at"],
        )
        session.add(inv)
        inventory_count += 1
    session.flush()

    # 11. Wastage
    wastage_count = 0
    for wst_data in get_sample_wastage_data():
        did = dish_map[wst_data["source_menu_item_id"]] if wst_data["source_menu_item_id"] else None
        wst = Wastage(
            source_wastage_id=wst_data["source_wastage_id"],
            restaurant_id=rest_map[wst_data["source_restaurant_id"]],
            menu_item_id=did,
            ingredient_name=wst_data["ingredient_name"],
            wastage_timestamp=wst_data["wastage_timestamp"],
            quantity_lost=wst_data["quantity_lost"],
            unit_of_measure=wst_data["unit_of_measure"],
            cost_loss_amount=wst_data["cost_loss_amount"],
            wastage_reason=wst_data["wastage_reason"],
            reported_by=wst_data["reported_by"],
            created_at=wst_data["created_at"],
        )
        session.add(wst)
        wastage_count += 1
    session.flush()

    return {
        "menu_categories": len(cat_map),
        "restaurants": len(rest_map),
        "menu_items": len(dish_map),
        "pricing_history": pricing_count,
        "promotions": len(promo_map),
        "customers": len(cust_map),
        "orders": len(order_map),
        "order_items": order_items_count,
        "ratings": ratings_count,
        "inventory": inventory_count,
        "wastage": wastage_count,
    }
