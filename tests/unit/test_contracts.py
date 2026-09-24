"""Tests for mathematical evaluation contracts and comparison logic."""

from packages.comparison.evaluator import PipelineComparator
from packages.core.contracts.evaluation import (
    EvaluationContract,
    EvaluationMetricResult,
)


def test_evaluation_contract_defaults():
    """Verify target definitions and default thresholds in evaluation contract."""
    contract = EvaluationContract()
    assert contract.TARGET_NAME == "next_week_wastage_risk"
    assert contract.DEFAULT_WASTAGE_COST_THRESHOLD == 0.05
    assert contract.DEFAULT_WASTAGE_QUANTITY_RATIO == 0.10


def test_pipeline_comparator_computes_differences():
    """Verify comparator computes metric differences between pipelines."""
    spark_res = EvaluationMetricResult(
        precision=0.85,
        recall=0.80,
        f1_score=0.824,
        roc_auc=0.91,
        runtime_seconds=12.5,
    )
    python_res = EvaluationMetricResult(
        precision=0.83,
        recall=0.79,
        f1_score=0.809,
        roc_auc=0.89,
        runtime_seconds=4.2,
    )
    comparator = PipelineComparator()
    comparison = comparator.compare_metrics(
        spark_metrics=spark_res,
        python_metrics=python_res,
        target_name="next_week_wastage_risk",
        comparison_id="comp_test_001",
    )
    assert comparison.comparison_id == "comp_test_001"
    assert "f1_difference" in comparison.metric_differences
    assert comparison.metric_differences["runtime_difference_sec"] == 8.3
