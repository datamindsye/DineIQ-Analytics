"""Model Registry and Prediction metadata API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from apps.api.dependencies.auth import get_current_user, require_roles
from apps.api.dependencies.db import get_db
from packages.core.schemas.common import DataEnvelope
from packages.core.schemas.ml_metadata import (
    ModelVersionCreate,
    ModelVersionResponse,
    PredictionMetadataCreate,
    PredictionMetadataResponse,
)
from packages.core.services.model_registry_service import (
    get_model_version,
    list_model_versions,
    list_predictions_for_model,
    record_batch_prediction,
    register_model_version,
)
from packages.db.models.auth import User

router = APIRouter(prefix="/models", tags=["Model Registry"])


@router.get(
    "",
    response_model=DataEnvelope[list[ModelVersionResponse]],
    status_code=status.HTTP_200_OK,
)
def get_models(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    pipeline_type: str | None = Query(None, description="Filter by SPARK_MLLIB or PYTHON_SKLEARN"),
    target_name: str | None = Query(None, description="Filter by target name"),
    limit: int = Query(50, ge=1, le=100),
) -> DataEnvelope[list[ModelVersionResponse]]:
    """List registered machine learning models across Spark MLlib and Python pipelines."""
    models = list_model_versions(
        db=db,
        pipeline_type=pipeline_type,
        target_name=target_name,
        limit=limit,
    )
    model_responses = [ModelVersionResponse.model_validate(m) for m in models]
    return DataEnvelope(data=model_responses)


@router.get(
    "/{model_id}",
    response_model=DataEnvelope[ModelVersionResponse],
    status_code=status.HTTP_200_OK,
)
def get_model_by_id(
    model_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[ModelVersionResponse]:
    """Retrieve detailed hyperparameters, metrics, and artifact references for a model."""
    model_ver = get_model_version(db=db, model_id=model_id)
    if not model_ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version '{model_id}' not found in registry",
        )
    return DataEnvelope(data=ModelVersionResponse.model_validate(model_ver))


@router.post(
    "",
    response_model=DataEnvelope[ModelVersionResponse],
    status_code=status.HTTP_201_CREATED,
)
def register_model(
    payload: ModelVersionCreate,
    current_user: Annotated[User, Depends(require_roles("Admin", "DataScientist"))],
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[ModelVersionResponse]:
    """Register a newly trained model version from Spark or Python pipeline."""
    try:
        model_ver = register_model_version(db=db, payload=payload)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    return DataEnvelope(data=ModelVersionResponse.model_validate(model_ver))


@router.get(
    "/{model_id}/predictions",
    response_model=DataEnvelope[list[PredictionMetadataResponse]],
    status_code=status.HTTP_200_OK,
)
def get_predictions_for_model(
    model_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(50, ge=1, le=100),
) -> DataEnvelope[list[PredictionMetadataResponse]]:
    """Retrieve batch inference runs associated with a specific model version."""
    model_ver = get_model_version(db=db, model_id=model_id)
    if not model_ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version '{model_id}' not found",
        )
    predictions = list_predictions_for_model(db=db, model_version_id=model_ver.id, limit=limit)
    pred_responses = [PredictionMetadataResponse.model_validate(p) for p in predictions]
    return DataEnvelope(data=pred_responses)


@router.post(
    "/{model_id}/predictions",
    response_model=DataEnvelope[PredictionMetadataResponse],
    status_code=status.HTTP_201_CREATED,
)
def record_prediction(
    model_id: str,
    payload: PredictionMetadataCreate,
    current_user: Annotated[User, Depends(require_roles("Admin", "DataScientist"))],
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[PredictionMetadataResponse]:
    """Record batch scoring execution output for a registered model."""
    try:
        pred = record_batch_prediction(db=db, payload=payload)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    return DataEnvelope(data=PredictionMetadataResponse.model_validate(pred))
