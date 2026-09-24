"""Tests for system configuration loading and validation."""

from packages.core.config.settings import Settings


def test_settings_default_values():
    """Verify default configuration attributes are set correctly."""
    settings = Settings()
    assert settings.APP_NAME == "DineIQ Analytics API"
    assert settings.APP_PORT == 8000
    assert "http://localhost:5173" in settings.CORS_ORIGINS
    assert settings.DATA_DIR == "data"
    assert settings.SNAPSHOTS_DIR == "data/snapshots"


def test_settings_environment_override(monkeypatch):
    """Verify environment variable overrides work as expected."""
    monkeypatch.setenv("APP_NAME", "Custom DineIQ")
    monkeypatch.setenv("APP_PORT", "9000")
    settings = Settings()
    assert settings.APP_NAME == "Custom DineIQ"
    assert settings.APP_PORT == 9000
