"""Security and administrative audit event logging database models."""

from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from packages.db.base import Base


class AuditEvent(Base):
    """Immutable audit trail entry for authentication and operational events."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    user_id: Mapped[int | None] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
