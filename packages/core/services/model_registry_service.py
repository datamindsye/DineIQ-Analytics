"""Model registry and predictions metadata service."""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from packages.common.logging import get_logger
from packages.core.schemas.ml_metadata import (
    ModelVersionCreate,
    PredictionMetadataCreate,
)
from packages.db.models.ml_metadata import ModelVersion, PredictionMetadata

logger = get_logger("dineiq.core.model_registry")


def register_model_version(
    db: Session,
    payload: ModelVersionCreate,
) -> ModelVersion:
    """Store a trained model version with hyperparameters and evaluation metrics."""
    stmt = select(ModelVersion).where(ModelVersion.model_id == payload.model_id)
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise ValueError(f"Model version with ID '{payload.model_id}' already exists")

    model_ver = ModelVersion(
        model_id=payload.model_id,
        pipeline_type=payload.pipeline_type,
        algorithm_name=payload.algorithm_name,
        target_name=payload.target_name,
        training_snapshot_id=payload.training_snapshot_id,
        hyperparameters=payload.hyperparameters,
        metrics=payload.metrics,
        artifact_path=payload.artifact_path,
        is_active=payload.is_active,
    )
    db.add(model_ver)
    db.commit()
    db.refresh(model_ver)
    logger.info("Registered model %s (%s)", model_ver.model_id, model_ver.pipeline_type)
    return model_ver


def list_model_versions(
    db: Session,
    pipeline_type: str | None = None,
    target_name: str | None = None,
    limit: int = 50,
) -> list[ModelVersion]:
    """Query registered model versions with optional pipeline and target filters."""
    stmt = select(ModelVersion).order_by(desc(ModelVersion.created_at)).limit(limit)
    if pipeline_type:
        stmt = stmt.where(ModelVersion.pipeline_type == pipeline_type)
    if target_name:
        stmt = stmt.where(ModelVersion.target_name == target_name)
    return list(db.execute(stmt).scalars().all())


def get_model_version(db: Session, model_id: str) -> ModelVersion | None:
    """Retrieve model registry record by model ID."""
    stmt = select(ModelVersion).where(ModelVersion.model_id == model_id)
    return db.execute(stmt).scalar_one_or_none()


def record_batch_prediction(
    db: Session,
    payload: PredictionMetadataCreate,
) -> PredictionMetadata:
    """Record batch inference scoring metadata."""
    model_ver = db.get(ModelVersion, payload.model_version_id)
    if not model_ver:
        raise ValueError(f"Referenced ModelVersion ID {payload.model_version_id} does not exist")

    pred = PredictionMetadata(
        prediction_id=payload.prediction_id,
        model_version_id=payload.model_version_id,
        pipeline_type=payload.pipeline_type,
        target_name=payload.target_name,
        input_snapshot_id=payload.input_snapshot_id,
        output_mart_path=payload.output_mart_path,
        row_count=payload.row_count,
    )
    db.add(pred)
    db.commit()
    db.refresh(pred)
    logger.info("Recorded prediction metadata %s", pred.prediction_id)
    return pred


def list_predictions_for_model(
    db: Session,
    model_version_id: int,
    limit: int = 50,
) -> list[PredictionMetadata]:
    """Query prediction runs for a specific model version."""
    stmt = (
        select(PredictionMetadata)
        .where(PredictionMetadata.model_version_id == model_version_id)
        .order_by(desc(PredictionMetadata.scored_at))
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())
