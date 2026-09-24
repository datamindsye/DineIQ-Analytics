"""Cross pipeline comparison evaluator interface."""

from packages.common.logging import get_logger
from packages.core.contracts.evaluation import (
    EvaluationMetricResult,
    PipelineComparisonResult,
)

logger = get_logger(__name__)


class PipelineComparator:
    """Compares metrics and prediction alignment between Spark and Python pipelines."""

    def compare_metrics(
        self,
        spark_metrics: EvaluationMetricResult,
        python_metrics: EvaluationMetricResult,
        target_name: str,
        comparison_id: str,
    ) -> PipelineComparisonResult:
        """Compute absolute metric diffs between both pipeline evaluations."""
        diffs: dict[str, float] = {
            "f1_difference": abs(spark_metrics.f1_score - python_metrics.f1_score),
            "precision_difference": abs(spark_metrics.precision - python_metrics.precision),
            "recall_difference": abs(spark_metrics.recall - python_metrics.recall),
            "runtime_difference_sec": abs(
                spark_metrics.runtime_seconds - python_metrics.runtime_seconds
            ),
        }
        logger.info("Executed comparison %s for target %s", comparison_id, target_name)
        return PipelineComparisonResult(
            comparison_id=comparison_id,
            target_name=target_name,
            spark_metrics=spark_metrics,
            python_metrics=python_metrics,
            metric_differences=diffs,
            agreement_rate=1.0 - diffs["f1_difference"],
            timestamp="",
        )
