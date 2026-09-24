"""Analytics API router foundation."""

from typing import Any

from fastapi import APIRouter, status

from packages.core.schemas.common import DataEnvelope

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/status", response_model=DataEnvelope[dict[str, Any]], status_code=status.HTTP_200_OK)
def get_analytics_status() -> DataEnvelope[dict[str, Any]]:
    """Return status of analytical marts and pipelines."""
    return DataEnvelope(
        data={
            "marts_available": False,
            "message": "Analytical marts have not been generated yet.",
            "pipeline_modes": ["spark", "python"],
        }
    )
