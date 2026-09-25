"""Domain tables schema migration.

Revision ID: 1b92e8c5678a
Revises: 0aa073b72e7f
Create Date: 2026-09-25 16:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1b92e8c5678a"
down_revision: str | None = "0aa073b72e7f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. customers
    op.create_table(
        "customers",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_customer_id", sa.String(length=64), nullable=False),
        sa.Column("first_name", sa.String(length=60), nullable=True),
        sa.Column("last_name", sa.String(length=60), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("registration_date", sa.Date(), nullable=False),
        sa.Column("loyalty_tier", sa.String(length=20), server_default="Bronze", nullable=False),
        sa.Column("preferred_channel", sa.String(length=30), nullable=True),
        sa.Column("home_city", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "loyalty_tier IN ('Bronze', 'Silver', 'Gold', 'Platinum', 'None')",
            name="chk_customers_loyalty_tier",
        ),
        sa.CheckConstraint(
            "preferred_channel IS NULL OR preferred_channel IN ('Dine-in', 'Takeaway', 'Delivery Direct', 'Delivery Aggregator')",
            name="chk_customers_channel",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_email"), "customers", ["email"], unique=True)
    op.create_index(op.f("ix_customers_loyalty_tier"), "customers", ["loyalty_tier"], unique=False)
    op.create_index(
        op.f("ix_customers_registration_date"), "customers", ["registration_date"], unique=False
    )
    op.create_index(
        op.f("ix_customers_source_customer_id"), "customers", ["source_customer_id"], unique=True
    )

    # 2. restaurants
    op.create_table(
        "restaurants",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_restaurant_id", sa.String(length=64), nullable=False),
        sa.Column("location_name", sa.String(length=100), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state_region", sa.String(length=100), nullable=False),
        sa.Column("postal_code", sa.String(length=20), nullable=False),
        sa.Column("seating_capacity", sa.Integer(), nullable=False),
        sa.Column("dining_type", sa.String(length=40), nullable=False),
        sa.Column("manager_name", sa.String(length=100), nullable=True),
        sa.Column("opening_date", sa.Date(), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("seating_capacity > 0", name="chk_restaurants_capacity"),
        sa.CheckConstraint(
            "dining_type IN ('Fast Casual', 'Casual Dining', 'Fine Dining', 'Express Kiosk')",
            name="chk_restaurants_dining_type",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_name", name="uq_restaurants_location_name"),
    )
    op.create_index(op.f("ix_restaurants_city"), "restaurants", ["city"], unique=False)
    op.create_index(
        op.f("ix_restaurants_dining_type"), "restaurants", ["dining_type"], unique=False
    )
    op.create_index(
        op.f("ix_restaurants_source_restaurant_id"),
        "restaurants",
        ["source_restaurant_id"],
        unique=True,
    )

    # 3. menu_categories
    op.create_table(
        "menu_categories",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_category_id", sa.String(length=64), nullable=False),
        sa.Column("category_name", sa.String(length=60), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("display_order >= 0", name="chk_categories_display_order"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_name", name="uq_menu_categories_name"),
    )
    op.create_index(
        op.f("ix_menu_categories_source_category_id"),
        "menu_categories",
        ["source_category_id"],
        unique=True,
    )

    # 4. menu_items
    op.create_table(
        "menu_items",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_menu_item_id", sa.String(length=64), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("item_name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("current_base_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("current_base_cost", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("prep_time_minutes", sa.Integer(), server_default="15", nullable=False),
        sa.Column("is_seasonal", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("spiciness_level", sa.Integer(), server_default="0", nullable=False),
        sa.Column("allergens", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("current_base_price >= 0.00", name="chk_menu_items_price"),
        sa.CheckConstraint("current_base_cost >= 0.00", name="chk_menu_items_cost"),
        sa.CheckConstraint("spiciness_level BETWEEN 0 AND 4", name="chk_menu_items_spiciness"),
        sa.ForeignKeyConstraint(["category_id"], ["menu_categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_menu_items_category_id"), "menu_items", ["category_id"], unique=False)
    op.create_index(
        op.f("ix_menu_items_source_menu_item_id"),
        "menu_items",
        ["source_menu_item_id"],
        unique=True,
    )

    # 5. pricing_history
    op.create_table(
        "pricing_history",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_pricing_history_id", sa.String(length=64), nullable=False),
        sa.Column("menu_item_id", sa.BigInteger(), nullable=False),
        sa.Column("restaurant_id", sa.BigInteger(), nullable=True),
        sa.Column("base_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("base_cost", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("change_reason", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("base_price >= 0.00", name="chk_pricing_history_price"),
        sa.CheckConstraint("base_cost >= 0.00", name="chk_pricing_history_cost"),
        sa.CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="chk_pricing_history_dates",
        ),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_pricing_history_effective_from"),
        "pricing_history",
        ["effective_from"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pricing_history_effective_to"), "pricing_history", ["effective_to"], unique=False
    )
    op.create_index(
        op.f("ix_pricing_history_menu_item_id"), "pricing_history", ["menu_item_id"], unique=False
    )
    op.create_index(
        op.f("ix_pricing_history_restaurant_id"),
        "pricing_history",
        ["restaurant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pricing_history_source_pricing_history_id"),
        "pricing_history",
        ["source_pricing_history_id"],
        unique=True,
    )

    # 6. promotions
    op.create_table(
        "promotions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_promotion_id", sa.String(length=64), nullable=False),
        sa.Column("campaign_name", sa.String(length=120), nullable=False),
        sa.Column("promo_code", sa.String(length=40), nullable=True),
        sa.Column("discount_type", sa.String(length=30), nullable=False),
        sa.Column("discount_value", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "minimum_order_amount",
            sa.Numeric(precision=10, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column("applicable_category_id", sa.BigInteger(), nullable=True),
        sa.Column("applicable_menu_item_id", sa.BigInteger(), nullable=True),
        sa.Column("applicable_channel", sa.String(length=30), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_misleading", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "discount_type IN ('Percentage', 'Fixed Amount', 'Buy One Get One', 'Combo Bundle')",
            name="chk_promotions_discount_type",
        ),
        sa.CheckConstraint("end_date >= start_date", name="chk_promotions_dates"),
        sa.ForeignKeyConstraint(
            ["applicable_category_id"], ["menu_categories.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["applicable_menu_item_id"], ["menu_items.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_promotions_end_date"), "promotions", ["end_date"], unique=False)
    op.create_index(op.f("ix_promotions_promo_code"), "promotions", ["promo_code"], unique=False)
    op.create_index(
        op.f("ix_promotions_source_promotion_id"),
        "promotions",
        ["source_promotion_id"],
        unique=True,
    )
    op.create_index(op.f("ix_promotions_start_date"), "promotions", ["start_date"], unique=False)

    # 7. orders
    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_order_id", sa.String(length=64), nullable=False),
        sa.Column("restaurant_id", sa.BigInteger(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("order_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("order_channel", sa.String(length=30), nullable=False),
        sa.Column("order_status", sa.String(length=20), server_default="Completed", nullable=False),
        sa.Column("subtotal_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "discount_amount",
            sa.Numeric(precision=10, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column(
            "tax_amount", sa.Numeric(precision=10, scale=2), server_default="0.00", nullable=False
        ),
        sa.Column(
            "tip_amount", sa.Numeric(precision=10, scale=2), server_default="0.00", nullable=False
        ),
        sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "order_channel IN ('Dine-in', 'Takeaway', 'Delivery Direct', 'Delivery Aggregator')",
            name="chk_orders_channel",
        ),
        sa.CheckConstraint(
            "order_status IN ('Completed', 'Cancelled', 'Refunded', 'Voided')",
            name="chk_orders_status",
        ),
        sa.CheckConstraint(
            "payment_method IN ('Credit Card', 'Debit Card', 'Cash', 'Digital Wallet', 'Gift Card')",
            name="chk_orders_payment_method",
        ),
        sa.CheckConstraint(
            "subtotal_amount >= 0.00 AND discount_amount >= 0.00 AND total_amount >= 0.00",
            name="chk_orders_amounts",
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_customer_id"), "orders", ["customer_id"], unique=False)
    op.create_index(op.f("ix_orders_order_channel"), "orders", ["order_channel"], unique=False)
    op.create_index(op.f("ix_orders_order_status"), "orders", ["order_status"], unique=False)
    op.create_index(op.f("ix_orders_order_timestamp"), "orders", ["order_timestamp"], unique=False)
    op.create_index(op.f("ix_orders_restaurant_id"), "orders", ["restaurant_id"], unique=False)
    op.create_index(op.f("ix_orders_source_order_id"), "orders", ["source_order_id"], unique=True)

    # 8. order_items
    op.create_table(
        "order_items",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_order_item_id", sa.String(length=64), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("menu_item_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price_at_sale", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit_cost_at_sale", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "line_discount",
            sa.Numeric(precision=10, scale=2),
            server_default="0.00",
            nullable=False,
        ),
        sa.Column("promotion_id", sa.BigInteger(), nullable=True),
        sa.Column("line_net_revenue", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("line_contribution_margin", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("special_instructions", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name="chk_order_items_quantity"),
        sa.CheckConstraint("unit_price_at_sale >= 0.00", name="chk_order_items_price"),
        sa.CheckConstraint("unit_cost_at_sale >= 0.00", name="chk_order_items_cost"),
        sa.CheckConstraint("line_discount >= 0.00", name="chk_order_items_discount"),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["promotion_id"], ["promotions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_order_items_menu_item_id"), "order_items", ["menu_item_id"], unique=False
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(
        op.f("ix_order_items_promotion_id"), "order_items", ["promotion_id"], unique=False
    )
    op.create_index(
        op.f("ix_order_items_source_order_item_id"),
        "order_items",
        ["source_order_item_id"],
        unique=True,
    )

    # 9. ratings
    op.create_table(
        "ratings",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_rating_id", sa.String(length=64), nullable=False),
        sa.Column("restaurant_id", sa.BigInteger(), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=True),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("menu_item_id", sa.BigInteger(), nullable=True),
        sa.Column("rating_score", sa.Integer(), nullable=False),
        sa.Column("food_rating", sa.Integer(), nullable=True),
        sa.Column("service_rating", sa.Integer(), nullable=True),
        sa.Column("ambiance_rating", sa.Integer(), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("rating_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "is_verified_purchase",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("rating_score BETWEEN 1 AND 5", name="chk_ratings_score"),
        sa.CheckConstraint(
            "food_rating IS NULL OR food_rating BETWEEN 1 AND 5", name="chk_ratings_food"
        ),
        sa.CheckConstraint(
            "service_rating IS NULL OR service_rating BETWEEN 1 AND 5",
            name="chk_ratings_service",
        ),
        sa.CheckConstraint(
            "ambiance_rating IS NULL OR ambiance_rating BETWEEN 1 AND 5",
            name="chk_ratings_ambiance",
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ratings_customer_id"), "ratings", ["customer_id"], unique=False)
    op.create_index(op.f("ix_ratings_menu_item_id"), "ratings", ["menu_item_id"], unique=False)
    op.create_index(op.f("ix_ratings_order_id"), "ratings", ["order_id"], unique=False)
    op.create_index(
        op.f("ix_ratings_rating_timestamp"), "ratings", ["rating_timestamp"], unique=False
    )
    op.create_index(op.f("ix_ratings_restaurant_id"), "ratings", ["restaurant_id"], unique=False)
    op.create_index(
        op.f("ix_ratings_source_rating_id"), "ratings", ["source_rating_id"], unique=True
    )

    # 10. inventory
    op.create_table(
        "inventory",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_inventory_id", sa.String(length=64), nullable=False),
        sa.Column("restaurant_id", sa.BigInteger(), nullable=False),
        sa.Column("ingredient_name", sa.String(length=100), nullable=False),
        sa.Column("ingredient_category", sa.String(length=40), nullable=False),
        sa.Column("current_stock_quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit_of_measure", sa.String(length=20), nullable=False),
        sa.Column("reorder_threshold", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("reorder_quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit_purchase_cost", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("last_restock_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("current_stock_quantity >= 0.00", name="chk_inventory_stock"),
        sa.CheckConstraint("reorder_threshold >= 0.00", name="chk_inventory_threshold"),
        sa.CheckConstraint("unit_purchase_cost >= 0.00", name="chk_inventory_cost"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "restaurant_id", "ingredient_name", name="uq_inventory_restaurant_ingredient"
        ),
    )
    op.create_index(
        op.f("ix_inventory_ingredient_category"),
        "inventory",
        ["ingredient_category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_inventory_restaurant_id"), "inventory", ["restaurant_id"], unique=False
    )
    op.create_index(
        op.f("ix_inventory_source_inventory_id"),
        "inventory",
        ["source_inventory_id"],
        unique=True,
    )

    # 11. wastage
    op.create_table(
        "wastage",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("source_wastage_id", sa.String(length=64), nullable=False),
        sa.Column("restaurant_id", sa.BigInteger(), nullable=False),
        sa.Column("menu_item_id", sa.BigInteger(), nullable=True),
        sa.Column("ingredient_name", sa.String(length=100), nullable=True),
        sa.Column("wastage_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quantity_lost", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit_of_measure", sa.String(length=20), nullable=False),
        sa.Column("cost_loss_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("wastage_reason", sa.String(length=40), nullable=False),
        sa.Column("reported_by", sa.String(length=80), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("quantity_lost > 0.00", name="chk_wastage_quantity"),
        sa.CheckConstraint("cost_loss_amount >= 0.00", name="chk_wastage_cost"),
        sa.CheckConstraint(
            "wastage_reason IN ('Expired', 'Over-preparation', 'Cooking Error', 'Equipment Failure', 'Customer Returned', 'Spillage')",
            name="chk_wastage_reason",
        ),
        sa.ForeignKeyConstraint(["menu_item_id"], ["menu_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_wastage_menu_item_id"), "wastage", ["menu_item_id"], unique=False)
    op.create_index(op.f("ix_wastage_restaurant_id"), "wastage", ["restaurant_id"], unique=False)
    op.create_index(
        op.f("ix_wastage_source_wastage_id"), "wastage", ["source_wastage_id"], unique=True
    )
    op.create_index(op.f("ix_wastage_wastage_reason"), "wastage", ["wastage_reason"], unique=False)
    op.create_index(
        op.f("ix_wastage_wastage_timestamp"), "wastage", ["wastage_timestamp"], unique=False
    )


def downgrade() -> None:
    # Drop in exact reverse order
    op.drop_table("wastage")
    op.drop_table("inventory")
    op.drop_table("ratings")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("promotions")
    op.drop_table("pricing_history")
    op.drop_table("menu_items")
    op.drop_table("menu_categories")
    op.drop_table("restaurants")
    op.drop_table("customers")
