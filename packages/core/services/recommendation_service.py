"""Actionable business recommendations domain service."""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from packages.common.logging import get_logger
from packages.core.schemas.recommendations import RecommendationCreate
from packages.db.models.recommendations import Recommendation

logger = get_logger("dineiq.core.recommendation_service")


def create_recommendation(
    db: Session,
    payload: RecommendationCreate,
) -> Recommendation:
    """Store a generated business recommendation."""
    stmt = select(Recommendation).where(
        Recommendation.recommendation_id == payload.recommendation_id
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise ValueError(f"Recommendation with ID '{payload.recommendation_id}' already exists")

    rec = Recommendation(
        recommendation_id=payload.recommendation_id,
        category=payload.category,
        title=payload.title,
        description=payload.description,
        impact_estimate=payload.impact_estimate,
        priority=payload.priority,
        status=payload.status,
        source_pipeline=payload.source_pipeline,
        metadata_payload=payload.metadata_payload,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    logger.info("Created recommendation %s [%s]", rec.recommendation_id, rec.category)
    return rec


def list_recommendations(
    db: Session,
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    limit: int = 50,
) -> list[Recommendation]:
    """Query recommendations with optional status, category, and priority filtering."""
    stmt = select(Recommendation).order_by(desc(Recommendation.created_at)).limit(limit)
    if status:
        stmt = stmt.where(Recommendation.status == status)
    if category:
        stmt = stmt.where(Recommendation.category == category)
    if priority:
        stmt = stmt.where(Recommendation.priority == priority)
    return list(db.execute(stmt).scalars().all())


def get_recommendation(db: Session, recommendation_id: str) -> Recommendation | None:
    """Retrieve recommendation by unique ID."""
    stmt = select(Recommendation).where(Recommendation.recommendation_id == recommendation_id)
    return db.execute(stmt).scalar_one_or_none()


def update_recommendation_status(
    db: Session,
    recommendation_id: str,
    new_status: str,
) -> Recommendation:
    """Update recommendation lifecycle status (PROPOSED, ACCEPTED, REJECTED, IMPLEMENTED)."""
    rec = get_recommendation(db, recommendation_id)
    if not rec:
        raise ValueError(f"Recommendation with ID '{recommendation_id}' not found")

    rec.status = new_status
    db.commit()
    db.refresh(rec)
    logger.info("Updated recommendation %s status to %s", recommendation_id, new_status)
    return rec
