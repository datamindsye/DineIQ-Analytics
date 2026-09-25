"""Audit event logging and query service."""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from packages.common.logging import get_logger
from packages.core.schemas.audit import AuditEventCreate
from packages.db.models.audit import AuditEvent

logger = get_logger("dineiq.core.audit_service")


def record_audit_event(
    db: Session,
    payload: AuditEventCreate,
) -> AuditEvent:
    """Persist an audit trail event."""
    event = AuditEvent(
        user_id=payload.user_id,
        action=payload.action,
        resource=payload.resource,
        resource_id=payload.resource_id,
        ip_address=payload.ip_address,
        details=payload.details,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_audit_events(
    db: Session,
    resource: str | None = None,
    action: str | None = None,
    user_id: int | None = None,
    limit: int = 100,
) -> list[AuditEvent]:
    """Query recent audit events with optional filtering."""
    stmt = select(AuditEvent).order_by(desc(AuditEvent.timestamp)).limit(limit)
    if resource:
        stmt = stmt.where(AuditEvent.resource == resource)
    if action:
        stmt = stmt.where(AuditEvent.action == action)
    if user_id is not None:
        stmt = stmt.where(AuditEvent.user_id == user_id)
    return list(db.execute(stmt).scalars().all())
