"""Background job management router foundation."""

from typing import Any

from fastapi import APIRouter, status

from packages.core.schemas.common import DataEnvelope

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("", response_model=DataEnvelope[list[dict[str, Any]]], status_code=status.HTTP_200_OK)
def list_jobs() -> DataEnvelope[list[dict[str, Any]]]:
    """List recent background processing jobs."""
    return DataEnvelope(data=[])
