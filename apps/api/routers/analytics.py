"""Analytics API router for querying precomputed analytical marts."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from apps.api.dependencies.auth import get_current_user
from packages.core.schemas.common import DataEnvelope
from packages.core.services.mart_reader import (
    MartNotFoundError,
    check_marts_availability,
    read_mart_records,
)
from packages.db.models.auth import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/status",
    response_model=DataEnvelope[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def get_analytics_status() -> DataEnvelope[dict[str, Any]]:
    """Return status and availability of analytical marts on disk."""
    availability = check_marts_availability()
    return DataEnvelope(data=availability)


@router.get(
    "/mart",
    response_model=DataEnvelope[list[dict[str, Any]]],
    status_code=status.HTTP_200_OK,
)
def query_analytical_mart(
    mart_path: str = Query(..., description="Relative path to precomputed mart Parquet file"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    limit: int = Query(100, ge=1, le=1000),
) -> DataEnvelope[list[dict[str, Any]]]:
    """Query precomputed analytical mart records directly via PyArrow.

    High volume transaction order lines are never scanned during web requests;
    results are served directly from precomputed analytical Parquet marts.
    """
    try:
        records = read_mart_records(mart_relative_path=mart_path, limit=limit)
    except MartNotFoundError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

    return DataEnvelope(data=records, meta={"count": len(records), "mart_path": mart_path})
