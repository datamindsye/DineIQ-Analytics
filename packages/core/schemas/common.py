"""Standard schema envelopes for API responses, health, and errors."""

from datetime import datetime, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Specific field or validation error detail."""

    loc: list[str] | None = None
    msg: str
    type: str | None = None


class ErrorPayload(BaseModel):
    """Error payload containing an error code, message, and details."""

    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorEnvelope(BaseModel):
    """Standardized top level error envelope."""

    error: ErrorPayload


class HealthStatus(BaseModel):
    """API health check response status."""

    status: str = "ok"
    environment: str
    version: str = "0.1.0"
    database: str = "unknown"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DataEnvelope(BaseModel, Generic[T]):
    """Standardized top level data response wrapper."""

    data: T
    meta: dict | None = None
