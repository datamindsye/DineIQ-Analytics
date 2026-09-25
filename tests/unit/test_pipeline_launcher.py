"""Unit tests for asynchronous pipeline launcher and job tracking."""

from sqlalchemy.orm import Session

from packages.core.services.pipeline_launcher import (
    create_job_run,
    get_job_run,
    list_job_runs,
    update_job_status,
)


def test_create_and_query_job_run(db_session: Session):
    """Test creating and retrieving an asynchronous job run."""
    job = create_job_run(
        db=db_session,
        pipeline_type="PYTHON",
        job_type="CUSTOMER_SEGMENTATION",
        source_snapshot_id="v20260924_01",
    )
    assert job.status == "PENDING"
    assert job.pipeline_type == "PYTHON"

    fetched = get_job_run(db=db_session, job_id=job.job_id)
    assert fetched is not None
    assert fetched.job_id == job.job_id


def test_update_job_status_and_metrics(db_session: Session):
    """Test updating job progress and completion metrics."""
    job = create_job_run(
        db=db_session,
        pipeline_type="SPARK",
        job_type="INGESTION_CLEANING",
    )

    updated = update_job_status(
        db=db_session,
        job_id=job.job_id,
        status="RUNNING",
        records_processed=50000,
    )
    assert updated.status == "RUNNING"
    assert updated.records_processed == 50000
    assert updated.started_at is not None

    completed = update_job_status(
        db=db_session,
        job_id=job.job_id,
        status="SUCCESS",
        records_cleaned=49800,
        metrics_summary={"cleaning_efficiency": 0.996},
    )
    assert completed.status == "SUCCESS"
    assert completed.completed_at is not None
    assert completed.metrics_summary["cleaning_efficiency"] == 0.996


def test_list_job_runs_filtering(db_session: Session):
    """Test filtering jobs by pipeline type and status."""
    create_job_run(db=db_session, pipeline_type="SPARK", job_type="JOB_A")
    create_job_run(db=db_session, pipeline_type="PYTHON", job_type="JOB_B")

    spark_jobs = list_job_runs(db=db_session, pipeline_type="SPARK")
    assert all(j.pipeline_type == "SPARK" for j in spark_jobs)

    python_jobs = list_job_runs(db=db_session, pipeline_type="PYTHON")
    assert all(j.pipeline_type == "PYTHON" for j in python_jobs)
