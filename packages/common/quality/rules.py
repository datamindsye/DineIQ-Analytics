"""Data quality rules, defect taxonomies, and anomaly audit definitions."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class RuleSeverity(str, Enum):
    """Severity classification for data quality rule evaluations."""

    CRITICAL = "CRITICAL"  # Data corruption requiring row quarantine
    WARNING = "WARNING"  # Valid operational complexity or minor data flaw
    INFO = "INFO"  # Informational metric or distribution observation


class RuleCategory(str, Enum):
    """Categorical classification of quality validation checks."""

    NULLABILITY = "NULLABILITY"
    UNIQUENESS = "UNIQUENESS"
    VALIDITY = "VALIDITY"
    CHRONOLOGY = "CHRONOLOGY"
    REFERENTIAL_INTEGRITY = "REFERENTIAL_INTEGRITY"
    FINANCIAL_INVARIANT = "FINANCIAL_INVARIANT"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"


class QualityRule(BaseModel):
    """Formal definition of a data quality rule."""

    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: RuleSeverity
    entity_name: str
    field_name: str | None = None
    description: str


# Authoritative data quality rules catalogue for the DineIQ platform
QUALITY_RULES: list[QualityRule] = [
    # 1. Uniqueness Rules
    QualityRule(
        rule_id="UQ-001",
        rule_name="source_id_uniqueness",
        category=RuleCategory.UNIQUENESS,
        severity=RuleSeverity.CRITICAL,
        entity_name="all",
        field_name="source_*_id",
        description="Every entity table must possess strictly unique business source identifiers.",
    ),
    # 2. Validity Rules
    QualityRule(
        rule_id="VAL-001",
        rule_name="positive_item_quantity",
        category=RuleCategory.VALIDITY,
        severity=RuleSeverity.CRITICAL,
        entity_name="order_items",
        field_name="quantity",
        description="Order line quantity must be strictly greater than zero.",
    ),
    QualityRule(
        rule_id="VAL-002",
        rule_name="non_negative_unit_price",
        category=RuleCategory.VALIDITY,
        severity=RuleSeverity.CRITICAL,
        entity_name="order_items",
        field_name="unit_price_at_sale",
        description="Unit price at sale must be greater than or equal to zero.",
    ),
    QualityRule(
        rule_id="VAL-003",
        rule_name="rating_score_bounds",
        category=RuleCategory.VALIDITY,
        severity=RuleSeverity.CRITICAL,
        entity_name="ratings",
        field_name="rating_score",
        description="Rating scores must fall inclusively within the range of 1 to 5.",
    ),
    QualityRule(
        rule_id="VAL-004",
        rule_name="positive_wastage_quantity",
        category=RuleCategory.VALIDITY,
        severity=RuleSeverity.CRITICAL,
        entity_name="wastage",
        field_name="quantity_lost",
        description="Discarded quantity in wastage logs must be strictly greater than zero.",
    ),
    # 3. Chronology Rules
    QualityRule(
        rule_id="CHR-001",
        rule_name="timestamp_not_in_future",
        category=RuleCategory.CHRONOLOGY,
        severity=RuleSeverity.CRITICAL,
        entity_name="orders",
        field_name="order_timestamp",
        description="Order timestamp must not occur after the snapshot cutoff horizon.",
    ),
    QualityRule(
        rule_id="CHR-002",
        rule_name="pricing_history_valid_interval",
        category=RuleCategory.CHRONOLOGY,
        severity=RuleSeverity.CRITICAL,
        entity_name="pricing_history",
        field_name="effective_to",
        description="When populated, effective_to must be strictly greater than effective_from.",
    ),
    # 4. Referential Integrity Rules
    QualityRule(
        rule_id="REF-001",
        rule_name="order_items_order_exists",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        severity=RuleSeverity.CRITICAL,
        entity_name="order_items",
        field_name="source_order_id",
        description="Every order item must reference an existing order header record.",
    ),
    QualityRule(
        rule_id="REF-002",
        rule_name="order_items_menu_item_exists",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        severity=RuleSeverity.CRITICAL,
        entity_name="order_items",
        field_name="source_menu_item_id",
        description="Every order item must reference an existing menu catalog item.",
    ),
    QualityRule(
        rule_id="REF-003",
        rule_name="orders_restaurant_exists",
        category=RuleCategory.REFERENTIAL_INTEGRITY,
        severity=RuleSeverity.CRITICAL,
        entity_name="orders",
        field_name="source_restaurant_id",
        description="Every order must reference an existing branch location.",
    ),
    # 5. Financial Invariant Rules
    QualityRule(
        rule_id="FIN-001",
        rule_name="net_revenue_formula_match",
        category=RuleCategory.FINANCIAL_INVARIANT,
        severity=RuleSeverity.WARNING,
        entity_name="order_items",
        field_name="line_net_revenue",
        description="Line net revenue must equal quantity times unit price minus line discount.",
    ),
    QualityRule(
        rule_id="FIN-002",
        rule_name="contribution_margin_formula_match",
        category=RuleCategory.FINANCIAL_INVARIANT,
        severity=RuleSeverity.WARNING,
        entity_name="order_items",
        field_name="line_contribution_margin",
        description="Line contribution margin must equal net revenue minus quantity times unit cost.",
    ),
    QualityRule(
        rule_id="FIN-003",
        rule_name="order_total_settlement_match",
        category=RuleCategory.FINANCIAL_INVARIANT,
        severity=RuleSeverity.WARNING,
        entity_name="orders",
        field_name="total_amount",
        description="Order total amount must equal subtotal minus discount plus tax plus tip.",
    ),
    # 6. Operational Status Rules (Informational)
    QualityRule(
        rule_id="OPS-001",
        rule_name="cancelled_order_identified",
        category=RuleCategory.VALIDITY,
        severity=RuleSeverity.INFO,
        entity_name="orders",
        field_name="order_status",
        description="Cancelled or voided orders identified and preserved for cancellation rate analysis.",
    ),
    QualityRule(
        rule_id="OPS-002",
        rule_name="guest_checkout_identified",
        category=RuleCategory.NULLABILITY,
        severity=RuleSeverity.INFO,
        entity_name="orders",
        field_name="source_customer_id",
        description="Orders without registered customer account identified as anonymous guest checkouts.",
    ),
    QualityRule(
        rule_id="OPS-003",
        rule_name="promotion_trap_identified",
        category=RuleCategory.ANOMALY_DETECTION,
        severity=RuleSeverity.WARNING,
        entity_name="order_items",
        field_name="line_contribution_margin",
        description="Transactions with negative contribution margin identified as promotion trap campaigns.",
    ),
]
