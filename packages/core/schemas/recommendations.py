"""Actionable business recommendation schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RecommendationCreate(BaseModel):
    """Payload to create a new actionable recommendation."""

    recommendation_id: str = Field(..., min_length=3, max_length=64)
    category: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    impact_estimate: str = Field(..., min_length=1, max_length=255)
    priority: str = Field(default="MEDIUM", pattern="^(HIGH|MEDIUM|LOW)$")
    status: str = Field(default="PROPOSED", pattern="^(PROPOSED|ACCEPTED|REJECTED|IMPLEMENTED)$")
    source_pipeline: str = Field(default="COMPARISON", pattern="^(SPARK|PYTHON|COMPARISON)$")
    metadata_payload: dict[str, Any] = Field(default_factory=dict)


class RecommendationStatusUpdate(BaseModel):
    """Payload to transition recommendation lifecycle status."""

    status: str = Field(..., pattern="^(PROPOSED|ACCEPTED|REJECTED|IMPLEMENTED)$")


class RecommendationResponse(BaseModel):
    """Actionable recommendation response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    recommendation_id: str
    category: str
    title: str
    description: str
    impact_estimate: str
    priority: str
    status: str
    source_pipeline: str
    metadata_payload: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
