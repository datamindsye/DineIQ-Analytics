"""Core contracts package for formal mathematical and pipeline interfaces."""

from packages.core.contracts.evaluation import (
    EvaluationContract,
    EvaluationMetricResult,
    PipelineComparisonResult,
)

__all__ = [
    "EvaluationContract",
    "EvaluationMetricResult",
    "PipelineComparisonResult",
]
