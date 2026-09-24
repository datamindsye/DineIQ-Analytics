"""Pytest shared fixtures and configuration."""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from packages.core.config.settings import Settings, get_settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide application settings for testing."""
    return get_settings()


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provide a FastAPI test client instance."""
    with TestClient(app) as test_client:
        yield test_client
