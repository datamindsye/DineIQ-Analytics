"""Health check and readiness endpoints."""

from fastapi import APIRouter, status

from packages.core.config.settings import get_settings
from packages.core.schemas.common import HealthStatus
from packages.db.session import check_db_connection

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("", response_model=HealthStatus, status_code=status.HTTP_200_OK)
def get_liveness() -> HealthStatus:
    """Check API server liveness."""
    return HealthStatus(
        status="ok",
        environment=settings.ENVIRONMENT,
        version="0.1.0",
        database="untested",
    )


@router.get("/ready", response_model=HealthStatus, status_code=status.HTTP_200_OK)
def get_readiness() -> HealthStatus:
    """Check API and database readiness."""
    db_connected = check_db_connection()
    db_status = "connected" if db_connected else "disconnected"
    overall_status = "ok" if db_connected else "degraded"
    return HealthStatus(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        version="0.1.0",
        database=db_status,
    )
