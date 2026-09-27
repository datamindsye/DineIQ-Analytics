"""Tests for Phase 3 analytical contracts, mathematical formulas, and classification rules."""

from packages.core.contracts.analytical_contracts import (
    DemandForecastContract,
    MenuPerformanceCategory,
    MenuPerformanceContract,
    MenuTrickyFlags,
    PriceElasticityContract,
    PriceSensitivityClass,
    PromotionContract,
    WastageRiskClass,
    WastageRiskContract,
)


def test_wastage_risk_ratios_and_decision():
    """Verify wastage cost and quantity ratios and binary risk evaluation."""
    # Low risk case
    c_ratio, q_ratio, extreme = WastageRiskContract.compute_ratios(
        waste_cost=2.0, gross_revenue=100.0, waste_quantity=1.0, sold_quantity=20.0
    )
    assert c_ratio == 0.02
    assert q_ratio == 0.05
    assert not extreme
    assert (
        WastageRiskContract.evaluate_risk(c_ratio, q_ratio, extreme)
        == WastageRiskClass.LOW_RISK.value
    )

    # High cost ratio case (> 0.05)
    c_ratio, q_ratio, extreme = WastageRiskContract.compute_ratios(
        waste_cost=6.0, gross_revenue=100.0, waste_quantity=1.0, sold_quantity=20.0
    )
    assert c_ratio == 0.06
    assert (
        WastageRiskContract.evaluate_risk(c_ratio, q_ratio, extreme)
        == WastageRiskClass.HIGH_RISK.value
    )

    # High quantity ratio case (> 0.10)
    c_ratio, q_ratio, extreme = WastageRiskContract.compute_ratios(
        waste_cost=3.0, gross_revenue=100.0, waste_quantity=3.0, sold_quantity=20.0
    )
    assert q_ratio == 0.15
    assert (
        WastageRiskContract.evaluate_risk(c_ratio, q_ratio, extreme)
        == WastageRiskClass.HIGH_RISK.value
    )


def test_wastage_risk_zero_denominators():
    """Verify strict zero-denominator handling without fabricating ratios."""
    # Zero revenue: cost ratio is None
    c_ratio, q_ratio, extreme = WastageRiskContract.compute_ratios(
        waste_cost=10.0, gross_revenue=0.0, waste_quantity=2.0, sold_quantity=10.0
    )
    assert c_ratio is None
    assert q_ratio == 0.20
    assert not extreme
    assert (
        WastageRiskContract.evaluate_risk(c_ratio, q_ratio, extreme)
        == WastageRiskClass.HIGH_RISK.value
    )

    # Zero sold quantity but waste > 0: extreme operational risk
    c_ratio, q_ratio, extreme = WastageRiskContract.compute_ratios(
        waste_cost=15.0, gross_revenue=0.0, waste_quantity=5.0, sold_quantity=0.0
    )
    assert c_ratio is None
    assert q_ratio is None
    assert extreme is True
    assert (
        WastageRiskContract.evaluate_risk(c_ratio, q_ratio, extreme)
        == WastageRiskClass.HIGH_RISK.value
    )


def test_menu_performance_composite_score():
    """Verify composite menu scoring weights and range."""
    score = MenuPerformanceContract.calculate_composite_score(
        demand_score=80.0,
        profitability_score=90.0,
        customer_signal_score=85.0,
        wastage_health_score=70.0,
        sales_trend_score=60.0,
        promotion_independence_score=75.0,
    )
    # 0.25*80 + 0.25*90 + 0.15*85 + 0.15*70 + 0.10*60 + 0.10*75 = 20 + 22.5 + 12.75 + 10.5 + 6.0 + 7.5 = 79.25
    assert score == 79.25


def test_menu_performance_classification_gating():
    """Verify the four canonical menu performance classifications."""
    # Profit Driver: high demand, high profit, acceptable waste, not promo-dependent
    cat1 = MenuPerformanceContract.classify_menu_item(
        demand_score=80.0,
        profitability_score=85.0,
        customer_signal_score=70.0,
        wastage_health_score=80.0,
        promotion_independence_score=70.0,
    )
    assert cat1 == MenuPerformanceCategory.PROFIT_DRIVER

    # Volume Driver: high demand, lower profit
    cat2 = MenuPerformanceContract.classify_menu_item(
        demand_score=85.0,
        profitability_score=50.0,
        customer_signal_score=60.0,
        wastage_health_score=80.0,
        promotion_independence_score=80.0,
    )
    assert cat2 == MenuPerformanceCategory.VOLUME_DRIVER

    # Hidden Opportunity: lower demand, high profit or customer signal
    cat3 = MenuPerformanceContract.classify_menu_item(
        demand_score=40.0,
        profitability_score=80.0,
        customer_signal_score=85.0,
        wastage_health_score=75.0,
        promotion_independence_score=80.0,
    )
    assert cat3 == MenuPerformanceCategory.HIDDEN_OPPORTUNITY

    # Low Performer: low across all dimensions
    cat4 = MenuPerformanceContract.classify_menu_item(
        demand_score=20.0,
        profitability_score=15.0,
        customer_signal_score=25.0,
        wastage_health_score=10.0,
        promotion_independence_score=20.0,
    )
    assert cat4 == MenuPerformanceCategory.LOW_PERFORMER


def test_menu_tricky_flags_instantiation():
    """Verify all 10 tricky edge case boolean flags are testable."""
    flags = MenuTrickyFlags(
        high_selling_loss_making=True,
        profitable_rarely_purchased=False,
        popular_high_wastage=False,
        high_rating_low_profitability=False,
        low_rating_high_sales=False,
        promotion_dependent=True,
        location_performance_divergence=False,
        weekend_only_pattern=True,
        seasonal_item=False,
        new_item_insufficient_history=False,
    )
    assert flags.high_selling_loss_making is True
    assert flags.promotion_dependent is True
    assert flags.weekend_only_pattern is True
    assert flags.popular_high_wastage is False


def test_price_elasticity_computation_and_sensitivity():
    """Verify point price elasticity and sensitivity classification."""
    # Price increased 10%, quantity dropped 20% -> Elasticity = -0.20 / 0.10 = -2.0 (High)
    e1 = PriceElasticityContract.compute_elasticity(
        pre_quantity=100.0, post_quantity=80.0, pre_price=10.0, post_price=11.0
    )
    assert e1 == -2.0
    assert PriceElasticityContract.classify_sensitivity(e1) == PriceSensitivityClass.HIGH

    # Price increased 10%, quantity dropped 10% -> Elasticity = -1.0 (Moderate)
    e2 = PriceElasticityContract.compute_elasticity(
        pre_quantity=100.0, post_quantity=90.0, pre_price=10.0, post_price=11.0
    )
    assert e2 == -1.0
    assert PriceElasticityContract.classify_sensitivity(e2) == PriceSensitivityClass.MODERATE

    # Price increased 10%, quantity dropped 4% -> Elasticity = -0.4 (Low)
    e3 = PriceElasticityContract.compute_elasticity(
        pre_quantity=100.0, post_quantity=96.0, pre_price=10.0, post_price=11.0
    )
    assert e3 == -0.4
    assert PriceElasticityContract.classify_sensitivity(e3) == PriceSensitivityClass.LOW

    # Zero price change -> None
    assert (
        PriceElasticityContract.compute_elasticity(
            pre_quantity=100.0, post_quantity=90.0, pre_price=10.0, post_price=10.0
        )
        is None
    )


def test_promotion_trap_detection():
    """Verify detection of promotion traps (volume up but margin down)."""
    assert PromotionContract.detect_promotion_trap(
        incremental_volume_pct=0.25, incremental_margin_pct=-0.15
    )
    assert not PromotionContract.detect_promotion_trap(
        incremental_volume_pct=0.25, incremental_margin_pct=0.10
    )


def test_demand_forecast_contract_layers():
    """Verify 3-layer architecture and anti-leakage configuration."""
    assert "mart_demand_historical" in DemandForecastContract.LAYERS
    assert "demand_ml_features" in DemandForecastContract.LAYERS
    assert "mart_demand_forecast" in DemandForecastContract.LAYERS
    assert DemandForecastContract.BASELINE_METHOD == "seasonal_naive"
