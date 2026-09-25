"""Pipeline job execution tracking database models."""

from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, DateTime, Identity, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.db.base import Base


class JobRun(Base):
    """Execution record for asynchronous Spark or Python pipeline tasks."""

    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    pipeline_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    job_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_snapshot_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="PENDING", nullable=False)
    records_processed: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    records_cleaned: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
