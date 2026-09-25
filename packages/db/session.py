"""Database connection, engine creation, and session lifecycle management."""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from packages.common.logging import get_logger
from packages.core.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

_engine = None
_session_factory = None


def get_engine():
    """Retrieve or initialize the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        engine_kwargs = {
            "echo": settings.DEBUG and settings.ENVIRONMENT == "development",
            "pool_pre_ping": settings.DB_POOL_PRE_PING,
        }
        if not settings.DATABASE_URL.startswith("sqlite"):
            engine_kwargs.update(
                {
                    "pool_size": settings.DB_POOL_SIZE,
                    "max_overflow": settings.DB_MAX_OVERFLOW,
                    "pool_timeout": settings.DB_POOL_TIMEOUT,
                }
            )
        _engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
    return _engine


def reset_engine() -> None:
    """Reset the engine and session factory (useful for testing)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_session_factory() -> sessionmaker:
    """Retrieve or initialize the scoped session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session per request."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()


def check_db_connection() -> bool:
    """Check whether the PostgreSQL database is reachable."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database connection check failed: %s", exc)
        return False
