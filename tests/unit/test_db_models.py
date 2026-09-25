"""Unit tests verifying SQLAlchemy operational and metadata models."""

from sqlalchemy.orm import Session

from packages.db.models.audit import AuditEvent
from packages.db.models.auth import Permission, Role, User
from packages.db.models.jobs import JobRun
from packages.db.models.ml_metadata import ModelVersion, PredictionMetadata
from packages.db.models.recommendations import Recommendation


def test_user_and_role_relationships(db_session: Session):
    """Test user, role, and permission association logic."""
    perm = Permission(name="reports:export", description="Export executive reports")
    role = Role(name="Analyst", description="Financial and menu analyst")
    role.permissions.append(perm)

    user = User(
        username="analyst_jane",
        email="jane@dineiq.local",
        hashed_password="some_hashed_password",
        full_name="Jane Analyst",
    )
    user.roles.append(role)

    db_session.add_all([perm, role, user])
    db_session.commit()

    queried_user = db_session.query(User).filter_by(username="analyst_jane").one()
    assert queried_user.id is not None
    assert len(queried_user.roles) == 1
    assert queried_user.roles[0].name == "Analyst"
    assert len(queried_user.roles[0].permissions) == 1
    assert queried_user.roles[0].permissions[0].name == "reports:export"


def test_job_run_lifecycle_and_metrics(db_session: Session):
    """Test JobRun operational states and json metrics payload."""
    job = JobRun(
        job_id="job_test_12345",
        pipeline_type="SPARK",
        job_type="MENU_PROFITABILITY",
        source_snapshot_id="v20260924_120000",
        status="RUNNING",
        records_processed=100000,
        records_cleaned=99500,
        metrics_summary={"null_rate": 0.005, "execution_seconds": 12.4},
    )
    db_session.add(job)
    db_session.commit()

    saved_job = db_session.query(JobRun).filter_by(job_id="job_test_12345").one()
    assert saved_job.status == "RUNNING"
    assert saved_job.records_processed == 100000
    assert saved_job.metrics_summary["null_rate"] == 0.005

    # Update to success
    saved_job.status = "SUCCESS"
    db_session.commit()
    assert db_session.query(JobRun).filter_by(job_id="job_test_12345").one().status == "SUCCESS"


def test_model_version_and_prediction_metadata(db_session: Session):
    """Test model version registration and batch prediction linkages."""
    model_ver = ModelVersion(
        model_id="spark_rf_churn_v1",
        pipeline_type="SPARK_MLLIB",
        algorithm_name="RandomForestClassifier",
        target_name="customer_churn_30d",
        training_snapshot_id="v20260924_120000",
        hyperparameters={"num_trees": 100, "max_depth": 8},
        metrics={"auc_roc": 0.88, "f1_score": 0.82},
        artifact_path="data/artifacts/spark/rf_churn_v1.zip",
        is_active=True,
    )
    db_session.add(model_ver)
    db_session.commit()

    pred = PredictionMetadata(
        prediction_id="pred_batch_001",
        model_version_id=model_ver.id,
        pipeline_type="SPARK_MLLIB",
        target_name="customer_churn_30d",
        input_snapshot_id="v20260924_120000",
        output_mart_path="data/marts/spark/customer_churn_predictions.parquet",
        row_count=50000,
    )
    db_session.add(pred)
    db_session.commit()

    queried_model = db_session.query(ModelVersion).filter_by(model_id="spark_rf_churn_v1").one()
    assert len(queried_model.predictions) == 1
    assert queried_model.predictions[0].prediction_id == "pred_batch_001"
    assert queried_model.predictions[0].row_count == 50000


def test_recommendation_model(db_session: Session):
    """Test business recommendation persistence and status updates."""
    rec = Recommendation(
        recommendation_id="rec_opt_001",
        category="MENU_OPTIMIZATION",
        title="Increase margin on Signature Truffle Burger",
        description="Raise base price by 1.50 to offset rising brioche bun supplier cost",
        impact_estimate="+4,200 USD monthly contribution margin",
        priority="HIGH",
        status="PROPOSED",
        source_pipeline="COMPARISON",
        metadata_payload={"dish_id": "DISH-001", "recommended_price": 16.50},
    )
    db_session.add(rec)
    db_session.commit()

    saved_rec = db_session.query(Recommendation).filter_by(recommendation_id="rec_opt_001").one()
    assert saved_rec.priority == "HIGH"
    assert saved_rec.status == "PROPOSED"

    saved_rec.status = "ACCEPTED"
    db_session.commit()
    assert (
        db_session.query(Recommendation).filter_by(recommendation_id="rec_opt_001").one().status
        == "ACCEPTED"
    )


def test_audit_event_logging(db_session: Session):
    """Test recording of immutable audit event entries."""
    event = AuditEvent(
        action="CONFIG_UPDATED",
        resource="system_settings",
        resource_id="db_pool",
        ip_address="127.0.0.1",
        details={"previous_pool_size": 5, "new_pool_size": 10},
    )
    db_session.add(event)
    db_session.commit()

    saved_event = db_session.query(AuditEvent).filter_by(action="CONFIG_UPDATED").one()
    assert saved_event.resource == "system_settings"
    assert saved_event.details["new_pool_size"] == 10
    assert saved_event.timestamp is not None
