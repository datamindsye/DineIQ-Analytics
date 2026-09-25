"""Security and operational audit trail schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventCreate(BaseModel):
    """Payload to record an audit log event."""

    user_id: int | None = None
    action: str = Field(..., min_length=2, max_length=128)
    resource: str = Field(..., min_length=2, max_length=128)
    resource_id: str | None = None
    ip_address: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AuditEventResponse(BaseModel):
    """Audit log event response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    action: str
    resource: str
    resource_id: str | None = None
    ip_address: str | None = None
    details: dict[str, Any] | None = None
    timestamp: datetime
