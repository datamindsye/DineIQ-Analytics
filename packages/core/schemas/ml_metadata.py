"""Machine learning model registry and batch predictions metadata schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModelVersionCreate(BaseModel):
    """Payload to register a trained model in the registry."""

    model_id: str = Field(..., min_length=3, max_length=64)
    pipeline_type: str = Field(..., pattern="^(SPARK_MLLIB|PYTHON_SKLEARN)$")
    algorithm_name: str = Field(..., min_length=2, max_length=128)
    target_name: str = Field(..., min_length=2, max_length=128)
    training_snapshot_id: str = Field(..., min_length=2, max_length=64)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    artifact_path: str = Field(..., min_length=1, max_length=512)
    is_active: bool = True


class ModelVersionResponse(BaseModel):
    """Model registry record schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: str
    pipeline_type: str
    algorithm_name: str
    target_name: str
    training_snapshot_id: str
    hyperparameters: dict[str, Any] | None = None
    metrics: dict[str, Any] | None = None
    artifact_path: str
    is_active: bool
    created_at: datetime


class PredictionMetadataCreate(BaseModel):
    """Payload to record a batch inference execution run."""

    prediction_id: str = Field(..., min_length=3, max_length=64)
    model_version_id: int
    pipeline_type: str = Field(..., pattern="^(SPARK_MLLIB|PYTHON_SKLEARN)$")
    target_name: str = Field(..., min_length=2, max_length=128)
    input_snapshot_id: str = Field(..., min_length=2, max_length=64)
    output_mart_path: str = Field(..., min_length=1, max_length=512)
    row_count: int = Field(default=0, ge=0)


class PredictionMetadataResponse(BaseModel):
    """Batch inference record response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_id: str
    model_version_id: int
    pipeline_type: str
    target_name: str
    input_snapshot_id: str
    output_mart_path: str
    row_count: int
    scored_at: datetime
