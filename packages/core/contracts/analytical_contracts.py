"""Analytical business contracts, mathematical formulas, and classification rules.

This module defines formal thresholds, formulas, component scoring weights,
and dataclasses for all Phase 3 analytical marts and downstream ML targets.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WastageRiskClass(int, Enum):
    """Binary wastage risk classification."""

    LOW_RISK = 0
    HIGH_RISK = 1


class MenuPerformanceCategory(str, Enum):
    """The four canonical SRS menu performance categories."""

    PROFIT_DRIVER = "Profit Driver"
    VOLUME_DRIVER = "Volume Driver"
    HIDDEN_OPPORTUNITY = "Hidden Opportunity"
    LOW_PERFORMER = "Low Performer"


class PriceSensitivityClass(str, Enum):
    """Price elasticity sensitivity categories."""

    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"


# -----------------------------------------------------------------------------
# 1. Wastage Risk Contract
# -----------------------------------------------------------------------------


class WastageRiskContract:
    """Formal mathematical contract for next week wastage risk prediction."""

    TARGET_NAME: str = "next_week_wastage_risk"
    COST_RATIO_THRESHOLD: float = 0.05
    QUANTITY_RATIO_THRESHOLD: float = 0.10
    DECISION_THRESHOLD: float = 0.50

    # Strict isolation between prepared dishes and raw ingredients
    PREPARED_DISH_FILTER: str = "source_menu_item_id IS NOT NULL"
    RAW_INGREDIENT_FILTER: str = "source_menu_item_id IS NULL"

    @staticmethod
    def compute_ratios(
        waste_cost: float,
        gross_revenue: float,
        waste_quantity: float,
        sold_quantity: float,
    ) -> tuple[float | None, float | None, bool]:
        """Compute cost and quantity ratios with strict zero-denominator handling.

        Returns (waste_cost_ratio, waste_quantity_ratio, extreme_operational_risk).
        """
        cost_ratio: float | None = None
        qty_ratio: float | None = None
        extreme_risk: bool = False

        if gross_revenue > 0:
            cost_ratio = waste_cost / gross_revenue

        if sold_quantity > 0:
            qty_ratio = waste_quantity / sold_quantity
        elif waste_quantity > 0:
            # Extreme operational risk: items were wasted but none were sold
            extreme_risk = True

        return cost_ratio, qty_ratio, extreme_risk

    @classmethod
    def evaluate_risk(
        cls,
        waste_cost_ratio: float | None,
        waste_quantity_ratio: float | None,
        extreme_risk: bool = False,
    ) -> int:
        """Evaluate binary risk label: 1 if either threshold exceeded or extreme risk."""
        if extreme_risk:
            return WastageRiskClass.HIGH_RISK.value

        if waste_cost_ratio is not None and waste_cost_ratio > cls.COST_RATIO_THRESHOLD:
            return WastageRiskClass.HIGH_RISK.value

        if waste_quantity_ratio is not None and waste_quantity_ratio > cls.QUANTITY_RATIO_THRESHOLD:
            return WastageRiskClass.HIGH_RISK.value

        return WastageRiskClass.LOW_RISK.value


# -----------------------------------------------------------------------------
# 2. Menu Performance Classification Contract
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class MenuTrickyFlags:
    """The 10 tricky edge case boolean flags required by SRS Step 11."""

    high_selling_loss_making: bool = False
    profitable_rarely_purchased: bool = False
    popular_high_wastage: bool = False
    high_rating_low_profitability: bool = False
    low_rating_high_sales: bool = False
    promotion_dependent: bool = False
    location_performance_divergence: bool = False
    weekend_only_pattern: bool = False
    seasonal_item: bool = False
    new_item_insufficient_history: bool = False


class MenuPerformanceContract:
    """Formal mathematical contract for multi-factor menu classification."""

    # Percentile benchmarks
    HIGH_PERCENTILE: float = 75.0
    LOW_PERCENTILE: float = 25.0

    # Composite score weights (sum = 1.00)
    WEIGHT_DEMAND: float = 0.25
    WEIGHT_PROFITABILITY: float = 0.25
    WEIGHT_CUSTOMER_SIGNAL: float = 0.15
    WEIGHT_WASTAGE_HEALTH: float = 0.15
    WEIGHT_SALES_TREND: float = 0.10
    WEIGHT_PROMOTION_INDEPENDENCE: float = 0.10

    # Tricky case specific thresholds
    NEW_ITEM_MAX_ACTIVE_DAYS: int = 30
    WEEKEND_SALES_THRESHOLD: float = 0.60
    PROMOTION_DEPENDENCY_THRESHOLD: float = 0.50
    HIGH_RATING_THRESHOLD: float = 4.2
    LOW_RATING_THRESHOLD: float = 3.0

    @classmethod
    def calculate_composite_score(
        cls,
        demand_score: float,
        profitability_score: float,
        customer_signal_score: float,
        wastage_health_score: float,
        sales_trend_score: float,
        promotion_independence_score: float,
    ) -> float:
        """Calculate weighted composite menu performance score (0-100 scale)."""
        score = (
            cls.WEIGHT_DEMAND * demand_score
            + cls.WEIGHT_PROFITABILITY * profitability_score
            + cls.WEIGHT_CUSTOMER_SIGNAL * customer_signal_score
            + cls.WEIGHT_WASTAGE_HEALTH * wastage_health_score
            + cls.WEIGHT_SALES_TREND * sales_trend_score
            + cls.WEIGHT_PROMOTION_INDEPENDENCE * promotion_independence_score
        )
        return round(float(score), 2)

    @classmethod
    def classify_menu_item(
        cls,
        demand_score: float,
        profitability_score: float,
        customer_signal_score: float,
        wastage_health_score: float,
        promotion_independence_score: float,
    ) -> MenuPerformanceCategory:
        """Apply transparent gating logic to determine the canonical category.

        - PROFIT DRIVER: high demand, high profit, acceptable waste, not promo-dependent.
        - VOLUME DRIVER: high demand, lower profit.
        - HIDDEN OPPORTUNITY: low/moderate demand, strong profit or customer signals, acceptable waste.
        - LOW PERFORMER: weak across multiple dimensions.
        """
        high = cls.HIGH_PERCENTILE
        low = cls.LOW_PERCENTILE

        is_high_demand = demand_score >= high
        is_high_profit = profitability_score >= high
        is_acceptable_waste = wastage_health_score >= low  # wastage health is inverted (100 - rank)
        is_promo_independent = promotion_independence_score >= low  # promo indep is inverted

        if is_high_demand and is_high_profit and is_acceptable_waste and is_promo_independent:
            return MenuPerformanceCategory.PROFIT_DRIVER

        if is_high_demand and not is_high_profit:
            return MenuPerformanceCategory.VOLUME_DRIVER

        is_high_customer = customer_signal_score >= high
        if not is_high_demand and (is_high_profit or is_high_customer) and is_acceptable_waste:
            return MenuPerformanceCategory.HIDDEN_OPPORTUNITY

        return MenuPerformanceCategory.LOW_PERFORMER


# -----------------------------------------------------------------------------
# 3. Price Elasticity Contract
# -----------------------------------------------------------------------------


class PriceElasticityContract:
    """Formal mathematical contract for price elasticity and sensitivity analysis."""

    PRE_WINDOW_DAYS: int = 28
    POST_WINDOW_DAYS: int = 28

    THRESHOLD_HIGH_SENSITIVITY: float = 1.50
    THRESHOLD_MODERATE_SENSITIVITY: float = 0.75

    @classmethod
    def compute_elasticity(
        cls,
        pre_quantity: float,
        post_quantity: float,
        pre_price: float,
        post_price: float,
    ) -> float | None:
        """Compute point price elasticity: (% change in quantity) / (% change in price).

        Returns None if pre_quantity <= 0, pre_price <= 0, or price does not change.
        """
        if pre_quantity <= 0 or pre_price <= 0:
            return None

        price_change_pct = (post_price - pre_price) / pre_price
        if abs(price_change_pct) < 1e-6:
            return None

        qty_change_pct = (post_quantity - pre_quantity) / pre_quantity
        return round(float(qty_change_pct / price_change_pct), 4)

    @classmethod
    def classify_sensitivity(cls, elasticity: float | None) -> PriceSensitivityClass:
        """Classify price sensitivity based on absolute elasticity magnitude."""
        if elasticity is None:
            return PriceSensitivityClass.LOW

        abs_e = abs(elasticity)
        if abs_e >= cls.THRESHOLD_HIGH_SENSITIVITY:
            return PriceSensitivityClass.HIGH
        elif abs_e >= cls.THRESHOLD_MODERATE_SENSITIVITY:
            return PriceSensitivityClass.MODERATE
        else:
            return PriceSensitivityClass.LOW


# -----------------------------------------------------------------------------
# 4. Promotion Linkage Contract
# -----------------------------------------------------------------------------


class PromotionContract:
    """Formal contract for promotion analytics and promotion trap detection."""

    # Line-level foreign key linkage rule
    JOIN_KEY: str = "source_promotion_id"
    JOIN_TABLE_SOURCE: str = "order_items"
    JOIN_TABLE_TARGET: str = "promotions"

    @staticmethod
    def detect_promotion_trap(
        incremental_volume_pct: float,
        incremental_margin_pct: float,
    ) -> bool:
        """Detect promotion trap: promotional volume increased but margin eroded."""
        return incremental_volume_pct > 0.0 and incremental_margin_pct < 0.0


# -----------------------------------------------------------------------------
# 5. Demand Forecast Lifecycle Contract
# -----------------------------------------------------------------------------


class DemandForecastContract:
    """Formal contract separating historical observations, ML features, and forecasts."""

    LAYERS: tuple[str, ...] = (
        "mart_demand_historical",
        "demand_ml_features",
        "mart_demand_forecast",
    )

    BASELINE_METHOD: str = "seasonal_naive"
    BASELINE_LOOKBACK_WEEKS: int = 4

    METRICS: tuple[str, ...] = ("MAE", "RMSE", "MAPE", "R2")
