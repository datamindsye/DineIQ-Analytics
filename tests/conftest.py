"""Pytest shared fixtures, in-memory SQLite database, and authenticated clients."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import packages.db.models  # noqa: F401
from apps.api.dependencies.db import get_db
from apps.api.main import app
from apps.api.services.auth_service import create_user_token, register_user, seed_security_defaults
from packages.core.config.settings import Settings, get_settings
from packages.core.schemas.auth import UserCreate
from packages.db.base import Base


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide application settings for testing."""
    return get_settings()


@pytest.fixture(scope="session")
def test_engine():
    """Create a persistent in-memory SQLite engine for the test session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session")
def session_factory(test_engine):
    """Create session factory for the test SQLite engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def seed_test_database(session_factory):
    """Seed standard roles and initial users for testing."""
    with session_factory() as db:
        seed_security_defaults(db)

        # Create additional test users with specific roles
        users_to_create = [
            (
                "manager",
                "manager@dineiq.local",
                "ManagerPass123!",
                "Store Manager",
                ["StoreManager"],
            ),
            (
                "scientist",
                "scientist@dineiq.local",
                "ScientistPass123!",
                "Data Scientist",
                ["DataScientist"],
            ),
            ("cashier", "cashier@dineiq.local", "CashierPass123!", "Cashier Staff", ["Cashier"]),
        ]
        for username, email, pwd, name, roles in users_to_create:
            try:
                register_user(
                    db,
                    UserCreate(
                        username=username,
                        email=email,
                        password=pwd,
                        full_name=name,
                        roles=roles,
                    ),
                )
            except ValueError:
                pass


@pytest.fixture
def db_session(session_factory) -> Generator[Session, None, None]:
    """Provide an isolated database session per test function with rollback."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def client(session_factory) -> Generator[TestClient, None, None]:
    """Provide a FastAPI test client instance with database dependency override."""

    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _get_auth_header(session_factory, username: str) -> dict[str, str]:
    """Helper to generate Authorization Bearer header for a given username."""
    from apps.api.services.auth_service import get_user_by_username

    with session_factory() as db:
        user = get_user_by_username(db, username)
        if not user:
            raise ValueError(f"User '{username}' not found in test database")
        token_resp = create_user_token(user)
        return {"Authorization": f"Bearer {token_resp.access_token}"}


@pytest.fixture(scope="session")
def admin_headers(session_factory) -> dict[str, str]:
    """Bearer authorization header for system administrator."""
    return _get_auth_header(session_factory, "admin")


@pytest.fixture(scope="session")
def manager_headers(session_factory) -> dict[str, str]:
    """Bearer authorization header for restaurant store manager."""
    return _get_auth_header(session_factory, "manager")


@pytest.fixture(scope="session")
def scientist_headers(session_factory) -> dict[str, str]:
    """Bearer authorization header for data scientist."""
    return _get_auth_header(session_factory, "scientist")


@pytest.fixture(scope="session")
def cashier_headers(session_factory) -> dict[str, str]:
    """Bearer authorization header for frontline cashier."""
    return _get_auth_header(session_factory, "cashier")
