"""Actionable business recommendations API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from apps.api.dependencies.auth import get_current_user, require_roles
from apps.api.dependencies.db import get_db
from packages.core.schemas.common import DataEnvelope
from packages.core.schemas.recommendations import (
    RecommendationCreate,
    RecommendationResponse,
    RecommendationStatusUpdate,
)
from packages.core.services.recommendation_service import (
    create_recommendation,
    get_recommendation,
    list_recommendations,
    update_recommendation_status,
)
from packages.db.models.auth import User

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get(
    "",
    response_model=DataEnvelope[list[RecommendationResponse]],
    status_code=status.HTTP_200_OK,
)
def get_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = Query(
        None, alias="status", description="Filter by PROPOSED, ACCEPTED, REJECTED, IMPLEMENTED"
    ),
    category: str | None = Query(None, description="Filter by recommendation category"),
    priority: str | None = Query(None, description="Filter by HIGH, MEDIUM, LOW"),
    limit: int = Query(50, ge=1, le=100),
) -> DataEnvelope[list[RecommendationResponse]]:
    """List actionable business recommendations with status and category filtering."""
    recs = list_recommendations(
        db=db,
        status=status_filter,
        category=category,
        priority=priority,
        limit=limit,
    )
    rec_responses = [RecommendationResponse.model_validate(r) for r in recs]
    return DataEnvelope(data=rec_responses)


@router.get(
    "/{recommendation_id}",
    response_model=DataEnvelope[RecommendationResponse],
    status_code=status.HTTP_200_OK,
)
def get_recommendation_by_id(
    recommendation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[RecommendationResponse]:
    """Retrieve detailed recommendation payload by unique identifier."""
    rec = get_recommendation(db=db, recommendation_id=recommendation_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found",
        )
    return DataEnvelope(data=RecommendationResponse.model_validate(rec))


@router.patch(
    "/{recommendation_id}/status",
    response_model=DataEnvelope[RecommendationResponse],
    status_code=status.HTTP_200_OK,
)
def patch_recommendation_status(
    recommendation_id: str,
    payload: RecommendationStatusUpdate,
    current_user: Annotated[User, Depends(require_roles("Admin", "StoreManager"))],
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[RecommendationResponse]:
    """Update recommendation lifecycle status (e.g. ACCEPTED, REJECTED, IMPLEMENTED)."""
    try:
        updated_rec = update_recommendation_status(
            db=db,
            recommendation_id=recommendation_id,
            new_status=payload.status,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    return DataEnvelope(data=RecommendationResponse.model_validate(updated_rec))


@router.post(
    "",
    response_model=DataEnvelope[RecommendationResponse],
    status_code=status.HTTP_201_CREATED,
)
def post_recommendation(
    payload: RecommendationCreate,
    current_user: Annotated[User, Depends(require_roles("Admin", "DataScientist"))],
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[RecommendationResponse]:
    """Record a newly generated recommendation from analytics or comparison pipeline."""
    try:
        rec = create_recommendation(db=db, payload=payload)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err
    return DataEnvelope(data=RecommendationResponse.model_validate(rec))
