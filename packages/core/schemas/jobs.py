"""Pipeline job execution tracking schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobRunTrigger(BaseModel):
    """Payload to trigger an asynchronous pipeline execution."""

    pipeline_type: str = Field(..., pattern="^(SPARK|PYTHON|COMPARISON)$")
    job_type: str = Field(..., min_length=2, max_length=64)
    source_snapshot_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class JobRunResponse(BaseModel):
    """Job execution record response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    pipeline_type: str
    job_type: str
    source_snapshot_id: str | None = None
    status: str
    records_processed: int = 0
    records_cleaned: int = 0
    error_message: str | None = None
    metrics_summary: dict[str, Any] | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class JobRunStatusUpdate(BaseModel):
    """Internal update payload for background pipeline status."""

    status: str
    records_processed: int | None = None
    records_cleaned: int | None = None
    error_message: str | None = None
    metrics_summary: dict[str, Any] | None = None
