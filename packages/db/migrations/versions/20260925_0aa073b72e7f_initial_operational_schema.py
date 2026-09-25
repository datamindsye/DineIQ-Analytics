"""Initial operational and metadata schema migration.

Revision ID: 0aa073b72e7f
Revises: None
Create Date: 2026-09-25 15:28:28.774577

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0aa073b72e7f"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. permissions
    op.create_table(
        "permissions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_permissions_name"), "permissions", ["name"], unique=True)

    # 2. roles
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    # 3. users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("username", sa.String(length=60), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # 4. role_permissions
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("permission_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    # 5. user_roles
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    # 6. job_runs
    op.create_table(
        "job_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("pipeline_type", sa.String(length=32), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("source_snapshot_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="PENDING", nullable=False),
        sa.Column("records_processed", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("records_cleaned", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metrics_summary", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_runs_job_id"), "job_runs", ["job_id"], unique=True)
    op.create_index(op.f("ix_job_runs_job_type"), "job_runs", ["job_type"], unique=False)
    op.create_index(op.f("ix_job_runs_pipeline_type"), "job_runs", ["pipeline_type"], unique=False)
    op.create_index(
        op.f("ix_job_runs_source_snapshot_id"), "job_runs", ["source_snapshot_id"], unique=False
    )
    op.create_index(op.f("ix_job_runs_status"), "job_runs", ["status"], unique=False)

    # 7. model_versions
    op.create_table(
        "model_versions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("pipeline_type", sa.String(length=32), nullable=False),
        sa.Column("algorithm_name", sa.String(length=128), nullable=False),
        sa.Column("target_name", sa.String(length=128), nullable=False),
        sa.Column("training_snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("hyperparameters", sa.JSON(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("artifact_path", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_model_versions_model_id"), "model_versions", ["model_id"], unique=True)
    op.create_index(
        op.f("ix_model_versions_pipeline_type"), "model_versions", ["pipeline_type"], unique=False
    )
    op.create_index(
        op.f("ix_model_versions_training_snapshot_id"),
        "model_versions",
        ["training_snapshot_id"],
        unique=False,
    )

    # 8. predictions_metadata
    op.create_table(
        "predictions_metadata",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("prediction_id", sa.String(length=64), nullable=False),
        sa.Column("model_version_id", sa.BigInteger(), nullable=False),
        sa.Column("pipeline_type", sa.String(length=32), nullable=False),
        sa.Column("target_name", sa.String(length=128), nullable=False),
        sa.Column("input_snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("output_mart_path", sa.String(length=512), nullable=False),
        sa.Column("row_count", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column(
            "scored_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["model_version_id"], ["model_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_predictions_metadata_input_snapshot_id"),
        "predictions_metadata",
        ["input_snapshot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_predictions_metadata_pipeline_type"),
        "predictions_metadata",
        ["pipeline_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_predictions_metadata_prediction_id"),
        "predictions_metadata",
        ["prediction_id"],
        unique=True,
    )

    # 9. recommendations
    op.create_table(
        "recommendations",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("recommendation_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("impact_estimate", sa.String(length=255), nullable=False),
        sa.Column("priority", sa.String(length=20), server_default="MEDIUM", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PROPOSED", nullable=False),
        sa.Column(
            "source_pipeline", sa.String(length=32), server_default="COMPARISON", nullable=False
        ),
        sa.Column("metadata_payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_recommendations_category"), "recommendations", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_recommendations_recommendation_id"),
        "recommendations",
        ["recommendation_id"],
        unique=True,
    )
    op.create_index(op.f("ix_recommendations_status"), "recommendations", ["status"], unique=False)

    # 10. audit_events
    op.create_table(
        "audit_events",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_events_action"), "audit_events", ["action"], unique=False)
    op.create_index(op.f("ix_audit_events_resource"), "audit_events", ["resource"], unique=False)
    op.create_index(op.f("ix_audit_events_timestamp"), "audit_events", ["timestamp"], unique=False)
    op.create_index(op.f("ix_audit_events_user_id"), "audit_events", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("recommendations")
    op.drop_table("predictions_metadata")
    op.drop_table("model_versions")
    op.drop_table("job_runs")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("permissions")
