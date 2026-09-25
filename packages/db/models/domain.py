"""SQLAlchemy models for the eleven business domain entities."""

from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base


class Customer(Base):
    """Customer profile and loyalty tier master record."""

    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint(
            "loyalty_tier IN ('Bronze', 'Silver', 'Gold', 'Platinum', 'None')",
            name="chk_customers_loyalty_tier",
        ),
        CheckConstraint(
            "preferred_channel IS NULL OR preferred_channel IN ('Dine-in', 'Takeaway', 'Delivery Direct', 'Delivery Aggregator')",
            name="chk_customers_channel",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_customer_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    first_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(60), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    registration_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    loyalty_tier: Mapped[str] = mapped_column(
        String(20), default="Bronze", nullable=False, index=True
    )
    preferred_channel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    home_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer")
    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="customer")


class Restaurant(Base):
    """Physical branch location and operating attributes."""

    __tablename__ = "restaurants"
    __table_args__ = (
        CheckConstraint("seating_capacity > 0", name="chk_restaurants_capacity"),
        CheckConstraint(
            "dining_type IN ('Fast Casual', 'Casual Dining', 'Fine Dining', 'Express Kiosk')",
            name="chk_restaurants_dining_type",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_restaurant_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    location_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state_region: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    seating_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    dining_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    manager_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    opening_date: Mapped[date] = mapped_column(Date, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="restaurant")
    inventory_items: Mapped[list["Inventory"]] = relationship(
        "Inventory", back_populates="restaurant"
    )
    wastage_records: Mapped[list["Wastage"]] = relationship("Wastage", back_populates="restaurant")
    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="restaurant")


class MenuCategory(Base):
    """Culinary classification groupings for dishes."""

    __tablename__ = "menu_categories"
    __table_args__ = (CheckConstraint("display_order >= 0", name="chk_categories_display_order"),)

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_category_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    category_name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    """Menu dish offering, standard pricing, and recipe attributes."""

    __tablename__ = "menu_items"
    __table_args__ = (
        CheckConstraint("current_base_price >= 0.00", name="chk_menu_items_price"),
        CheckConstraint("current_base_cost >= 0.00", name="chk_menu_items_cost"),
        CheckConstraint("spiciness_level BETWEEN 0 AND 4", name="chk_menu_items_spiciness"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_menu_item_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("menu_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    item_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    current_base_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    prep_time_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    is_seasonal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    spiciness_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    allergens: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    category: Mapped[MenuCategory] = relationship("MenuCategory", back_populates="items")
    pricing_history: Mapped[list["PricingHistory"]] = relationship(
        "PricingHistory", back_populates="menu_item"
    )
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="menu_item")
    wastage_records: Mapped[list["Wastage"]] = relationship("Wastage", back_populates="menu_item")
    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="menu_item")


class PricingHistory(Base):
    """Slowly Changing Dimension Type 2 tracking price and recipe cost modifications."""

    __tablename__ = "pricing_history"
    __table_args__ = (
        CheckConstraint("base_price >= 0.00", name="chk_pricing_history_price"),
        CheckConstraint("base_cost >= 0.00", name="chk_pricing_history_cost"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to > effective_from",
            name="chk_pricing_history_dates",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_pricing_history_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    menu_item_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("menu_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    restaurant_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("restaurants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    base_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    effective_to: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    change_reason: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    menu_item: Mapped[MenuItem] = relationship("MenuItem", back_populates="pricing_history")
    restaurant: Mapped[Restaurant | None] = relationship("Restaurant")


class Promotion(Base):
    """Marketing discount campaign or coupon code definition."""

    __tablename__ = "promotions"
    __table_args__ = (
        CheckConstraint(
            "discount_type IN ('Percentage', 'Fixed Amount', 'Buy One Get One', 'Combo Bundle')",
            name="chk_promotions_discount_type",
        ),
        CheckConstraint("end_date >= start_date", name="chk_promotions_dates"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_promotion_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    campaign_name: Mapped[str] = mapped_column(String(120), nullable=False)
    promo_code: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    discount_type: Mapped[str] = mapped_column(String(30), nullable=False)
    discount_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    minimum_order_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0.00, nullable=False
    )
    applicable_category_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("menu_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    applicable_menu_item_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("menu_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    applicable_channel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_misleading: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="promotion")


class Order(Base):
    """Point of sale transaction header."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "order_channel IN ('Dine-in', 'Takeaway', 'Delivery Direct', 'Delivery Aggregator')",
            name="chk_orders_channel",
        ),
        CheckConstraint(
            "order_status IN ('Completed', 'Cancelled', 'Refunded', 'Voided')",
            name="chk_orders_status",
        ),
        CheckConstraint(
            "payment_method IN ('Credit Card', 'Debit Card', 'Cash', 'Digital Wallet', 'Gift Card')",
            name="chk_orders_payment_method",
        ),
        CheckConstraint(
            "subtotal_amount >= 0.00 AND discount_amount >= 0.00 AND total_amount >= 0.00",
            name="chk_orders_amounts",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_order_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    restaurant_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("restaurants.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    order_channel: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    order_status: Mapped[str] = mapped_column(
        String(20), default="Completed", nullable=False, index=True
    )
    subtotal_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    tip_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="orders")
    customer: Mapped[Customer | None] = relationship("Customer", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="order")


class OrderItem(Base):
    """Detailed transaction line recording quantity, historical price, cost, and margin."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_order_items_quantity"),
        CheckConstraint("unit_price_at_sale >= 0.00", name="chk_order_items_price"),
        CheckConstraint("unit_cost_at_sale >= 0.00", name="chk_order_items_cost"),
        CheckConstraint("line_discount >= 0.00", name="chk_order_items_discount"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_order_item_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    order_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    menu_item_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("menu_items.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_at_sale: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_cost_at_sale: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    line_discount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    promotion_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("promotions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    line_net_revenue: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    line_contribution_margin: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    special_instructions: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    order: Mapped[Order] = relationship("Order", back_populates="items")
    menu_item: Mapped[MenuItem] = relationship("MenuItem", back_populates="order_items")
    promotion: Mapped[Promotion | None] = relationship("Promotion", back_populates="order_items")


class Rating(Base):
    """Customer satisfaction feedback and quality rating score."""

    __tablename__ = "ratings"
    __table_args__ = (
        CheckConstraint("rating_score BETWEEN 1 AND 5", name="chk_ratings_score"),
        CheckConstraint(
            "food_rating IS NULL OR food_rating BETWEEN 1 AND 5", name="chk_ratings_food"
        ),
        CheckConstraint(
            "service_rating IS NULL OR service_rating BETWEEN 1 AND 5",
            name="chk_ratings_service",
        ),
        CheckConstraint(
            "ambiance_rating IS NULL OR ambiance_rating BETWEEN 1 AND 5",
            name="chk_ratings_ambiance",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_rating_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    restaurant_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    customer_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    menu_item_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("menu_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rating_score: Mapped[int] = mapped_column(Integer, nullable=False)
    food_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    service_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ambiance_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="ratings")
    order: Mapped[Order | None] = relationship("Order", back_populates="ratings")
    customer: Mapped[Customer | None] = relationship("Customer", back_populates="ratings")
    menu_item: Mapped[MenuItem | None] = relationship("MenuItem", back_populates="ratings")


class Inventory(Base):
    """Current raw ingredient stock balance and procurement thresholds."""

    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("current_stock_quantity >= 0.00", name="chk_inventory_stock"),
        CheckConstraint("reorder_threshold >= 0.00", name="chk_inventory_threshold"),
        CheckConstraint("unit_purchase_cost >= 0.00", name="chk_inventory_cost"),
        UniqueConstraint(
            "restaurant_id", "ingredient_name", name="uq_inventory_restaurant_ingredient"
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_inventory_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    restaurant_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ingredient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    ingredient_category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    current_stock_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    reorder_threshold: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reorder_quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_purchase_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    last_restock_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="inventory_items")


class Wastage(Base):
    """Discard logs tracking spoilage, prep trim, and cooking errors."""

    __tablename__ = "wastage"
    __table_args__ = (
        CheckConstraint("quantity_lost > 0.00", name="chk_wastage_quantity"),
        CheckConstraint("cost_loss_amount >= 0.00", name="chk_wastage_cost"),
        CheckConstraint(
            "wastage_reason IN ('Expired', 'Over-preparation', 'Cooking Error', 'Equipment Failure', 'Customer Returned', 'Spillage')",
            name="chk_wastage_reason",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    source_wastage_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    restaurant_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    menu_item_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("menu_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ingredient_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    wastage_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    quantity_lost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False)
    cost_loss_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    wastage_reason: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    reported_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="wastage_records")
    menu_item: Mapped[MenuItem | None] = relationship("MenuItem", back_populates="wastage_records")
