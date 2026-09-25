"""Actionable business recommendations metadata models."""

from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, DateTime, Identity, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.db.base import Base


class Recommendation(Base):
    """System generated actionable business recommendation."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    recommendation_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact_estimate: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PROPOSED", nullable=False)
    source_pipeline: Mapped[str] = mapped_column(String(32), default="COMPARISON", nullable=False)
    metadata_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
