"""Database seeding CLI for initializing default security roles and evaluation users."""

import sys

from apps.api.services.auth_service import seed_security_defaults
from packages.common.logging import get_logger, setup_logging
from packages.db.session import check_db_connection, get_session_factory

logger = get_logger("dineiq.db.seed")


def main() -> None:
    """Seed security defaults (roles and evaluation accounts) into PostgreSQL."""
    setup_logging()
    if not check_db_connection():
        logger.error("Database is not reachable. Verify PostgreSQL server and DATABASE_URL in .env.")
        sys.exit(1)

    session_factory = get_session_factory()
    with session_factory() as db:
        seed_security_defaults(db)
    logger.info("Database security defaults successfully verified and seeded.")


if __name__ == "__main__":
    main()
