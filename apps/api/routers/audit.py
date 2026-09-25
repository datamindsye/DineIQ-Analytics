"""Audit log inspection API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from apps.api.dependencies.auth import require_roles
from apps.api.dependencies.db import get_db
from packages.core.schemas.audit import AuditEventResponse
from packages.core.schemas.common import DataEnvelope
from packages.core.services.audit_service import list_audit_events
from packages.db.models.auth import User

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get(
    "",
    response_model=DataEnvelope[list[AuditEventResponse]],
    status_code=status.HTTP_200_OK,
)
def get_audit_events(
    current_admin: Annotated[User, Depends(require_roles("Admin"))],
    db: Annotated[Session, Depends(get_db)],
    resource: str | None = Query(None, description="Filter by resource type"),
    action: str | None = Query(None, description="Filter by action name"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=200),
) -> DataEnvelope[list[AuditEventResponse]]:
    """Retrieve security and administrative audit event trail (Admin only)."""
    events = list_audit_events(
        db=db,
        resource=resource,
        action=action,
        user_id=user_id,
        limit=limit,
    )
    event_responses = [AuditEventResponse.model_validate(e) for e in events]
    return DataEnvelope(data=event_responses)
