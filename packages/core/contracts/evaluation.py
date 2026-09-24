"""Formal evaluation contract interface for cross pipeline model comparison."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationMetricResult:
    """Standard evaluation metrics computed for an analytics model."""

    precision: float
    recall: float
    f1_score: float
    roc_auc: float | None = None
    pr_auc: float | None = None
    brier_score: float | None = None
    runtime_seconds: float = 0.0
    throughput_samples_per_sec: float = 0.0


@dataclass(frozen=True)
class PipelineComparisonResult:
    """Side by side evaluation results for Spark vs Python pipelines."""

    comparison_id: str
    target_name: str
    spark_metrics: EvaluationMetricResult
    python_metrics: EvaluationMetricResult
    metric_differences: dict[str, float]
    agreement_rate: float
    timestamp: str


class EvaluationContract:
    """Formal mathematical contract defining target and metrics calculation."""

    TARGET_NAME: str = "next_week_wastage_risk"
    DEFAULT_WASTAGE_COST_THRESHOLD: float = 0.05
    DEFAULT_WASTAGE_QUANTITY_RATIO: float = 0.10
    DECISION_THRESHOLD: float = 0.50
