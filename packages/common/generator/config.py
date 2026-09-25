"""Configuration models and profile definitions for the deterministic dataset generator."""

from __future__ import annotations

from datetime import date
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class GenerationProfile(str, Enum):
    """Supported dataset generation scale profiles."""

    SMALL = "small"
    MEDIUM = "medium"
    COMPETITION = "competition"


class QualityAnomalyConfig(BaseModel):
    """Configurable injection rates for realistic operational complexities and anomalies."""

    missing_customer_rate: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Fraction of orders with missing customer identifier (guest checkout).",
    )
    missing_customer_contact_rate: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Fraction of customer profiles with missing phone or email.",
    )
    missing_rating_text_rate: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Fraction of ratings with null review commentary.",
    )
    duplicate_order_rate: float = Field(
        default=0.005,
        ge=0.0,
        le=0.10,
        description="Fraction of orders duplicated with identical identifiers.",
    )
    duplicate_order_item_rate: float = Field(
        default=0.005,
        ge=0.0,
        le=0.10,
        description="Fraction of order items duplicated with identical identifiers.",
    )
    cancelled_order_rate: float = Field(
        default=0.035,
        ge=0.0,
        le=0.50,
        description="Fraction of orders in Cancelled status.",
    )
    voided_order_rate: float = Field(
        default=0.005,
        ge=0.0,
        le=0.20,
        description="Fraction of orders in Voided status.",
    )
    invalid_negative_price_rate: float = Field(
        default=0.002,
        ge=0.0,
        le=0.05,
        description="Fraction of order items with negative unit price (data quality defect).",
    )
    invalid_zero_quantity_rate: float = Field(
        default=0.001,
        ge=0.0,
        le=0.05,
        description="Fraction of order items with zero quantity (data quality defect).",
    )
    future_timestamp_rate: float = Field(
        default=0.0005,
        ge=0.0,
        le=0.02,
        description="Fraction of order timestamps recorded in the future.",
    )
    rating_anomaly_drop_count: int = Field(
        default=2,
        ge=0,
        description="Number of localized dishes experiencing recipe defect rating drops.",
    )
    promotion_trap_count: int = Field(
        default=3,
        ge=0,
        description="Number of campaigns configured with negative contribution margins.",
    )


class ProfileScaleConfig(BaseModel):
    """Target cardinality thresholds for a generation profile."""

    num_restaurants: int
    num_categories: int
    num_menu_items: int
    num_customers: int
    num_orders: int
    num_order_items: int
    num_ratings: int
    num_inventory_records: int
    num_wastage_records: int
    num_pricing_history: int
    num_promotions: int
    history_days: int = 365
    chunk_size_orders: int = 10000


# Authoritative profile definitions matching SRS and architecture specifications
PROFILE_CONFIGS: dict[GenerationProfile, ProfileScaleConfig] = {
    GenerationProfile.SMALL: ProfileScaleConfig(
        num_restaurants=2,
        num_categories=10,
        num_menu_items=20,
        num_customers=100,
        num_orders=200,
        num_order_items=1500,
        num_ratings=200,
        num_inventory_records=100,
        num_wastage_records=100,
        num_pricing_history=30,
        num_promotions=5,
        history_days=30,
        chunk_size_orders=100,
    ),
    GenerationProfile.MEDIUM: ProfileScaleConfig(
        num_restaurants=5,
        num_categories=10,
        num_menu_items=50,
        num_customers=5000,
        num_orders=10000,
        num_order_items=100000,
        num_ratings=10000,
        num_inventory_records=500,
        num_wastage_records=5000,
        num_pricing_history=150,
        num_promotions=10,
        history_days=180,
        chunk_size_orders=2000,
    ),
    GenerationProfile.COMPETITION: ProfileScaleConfig(
        num_restaurants=20,
        num_categories=10,
        num_menu_items=150,
        num_customers=50000,
        num_orders=100000,
        num_order_items=1000000,
        num_ratings=100000,
        num_inventory_records=3000,  # 150 items across 20 restaurants
        num_wastage_records=50000,
        num_pricing_history=1500,
        num_promotions=25,
        history_days=365,
        chunk_size_orders=10000,
    ),
}


class GeneratorConfig(BaseModel):
    """Complete configuration specification for a dataset generation run."""

    profile: GenerationProfile = GenerationProfile.SMALL
    seed: int = 42
    start_date: date = date(2025, 1, 1)
    output_dir: Path = Path("data/snapshots")
    snapshot_id: str | None = None
    anomalies: QualityAnomalyConfig = Field(default_factory=QualityAnomalyConfig)
    enable_anomalies: bool = True

    @property
    def scale(self) -> ProfileScaleConfig:
        """Resolve the target scale configuration for the active profile."""
        return PROFILE_CONFIGS[self.profile]
