"""Background job management and pipeline trigger API router."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, sessionmaker

from apps.api.dependencies.auth import get_current_user, require_roles
from apps.api.dependencies.db import get_db
from packages.core.schemas.common import DataEnvelope
from packages.core.schemas.jobs import JobRunResponse, JobRunTrigger
from packages.core.services.pipeline_launcher import (
    create_job_run,
    get_job_run,
    launch_pipeline_job_async,
    list_job_runs,
)
from packages.db.models.auth import User

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get(
    "",
    response_model=DataEnvelope[list[JobRunResponse]],
    status_code=status.HTTP_200_OK,
)
def get_jobs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    pipeline_type: str | None = Query(None, description="Filter by SPARK or PYTHON"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
) -> DataEnvelope[list[JobRunResponse]]:
    """List recent background processing jobs with optional filtering."""
    jobs = list_job_runs(
        db=db,
        pipeline_type=pipeline_type,
        status=status_filter,
        limit=limit,
    )
    job_responses = [JobRunResponse.model_validate(job) for job in jobs]
    return DataEnvelope(data=job_responses)


@router.get(
    "/{job_id}",
    response_model=DataEnvelope[JobRunResponse],
    status_code=status.HTTP_200_OK,
)
def get_job_by_id(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[JobRunResponse]:
    """Retrieve details and execution metrics for a specific background job."""
    job = get_job_run(db=db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job run with ID '{job_id}' not found",
        )
    return DataEnvelope(data=JobRunResponse.model_validate(job))


@router.post(
    "/trigger",
    response_model=DataEnvelope[JobRunResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_pipeline_job(
    payload: JobRunTrigger,
    current_user: Annotated[User, Depends(require_roles("Admin", "DataScientist"))],
    db: Annotated[Session, Depends(get_db)],
) -> DataEnvelope[JobRunResponse]:
    """Trigger an asynchronous Spark or Python pipeline execution.

    Heavy analytical computations are never run synchronously inside this handler;
    the task is dispatched asynchronously and tracked via the job_runs table.
    """
    job = create_job_run(
        db=db,
        pipeline_type=payload.pipeline_type,
        job_type=payload.job_type,
        source_snapshot_id=payload.source_snapshot_id,
    )

    worker_factory = sessionmaker(bind=db.get_bind(), autocommit=False, autoflush=False)

    # Launch asynchronous background execution
    launch_pipeline_job_async(
        job_id=job.job_id,
        pipeline_type=payload.pipeline_type,
        job_type=payload.job_type,
        parameters=payload.parameters,
        session_factory=worker_factory,
    )

    return DataEnvelope(data=JobRunResponse.model_validate(job))
