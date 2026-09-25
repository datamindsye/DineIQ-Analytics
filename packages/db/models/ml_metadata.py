"""Machine learning model registry and batch predictions metadata models."""

from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.db.base import Base


class ModelVersion(Base):
    """Model registry record tracking trained models from Spark MLlib or Python."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    model_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    pipeline_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    algorithm_name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_name: Mapped[str] = mapped_column(String(128), nullable=False)
    training_snapshot_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    hyperparameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    artifact_path: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    predictions: Mapped[list["PredictionMetadata"]] = relationship(
        "PredictionMetadata",
        back_populates="model_version",
        cascade="all, delete-orphan",
    )


class PredictionMetadata(Base):
    """Metadata tracking batch scoring and prediction runs produced by models."""

    __tablename__ = "predictions_metadata"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        Identity(),
        primary_key=True,
    )
    prediction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    model_version_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("model_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    pipeline_type: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    target_name: Mapped[str] = mapped_column(String(128), nullable=False)
    input_snapshot_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    output_mart_path: Mapped[str] = mapped_column(String(512), nullable=False)
    row_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    model_version: Mapped[ModelVersion] = relationship(
        "ModelVersion",
        back_populates="predictions",
    )
