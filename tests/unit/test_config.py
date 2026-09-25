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


def test_production_settings_rejects_default_secret_key(monkeypatch):
    """Verify production environment rejects default development secret key."""
    import pytest

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv(
        "SECRET_KEY", "default-development-secret-key-change-in-production-min-32-chars"
    )
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "ProductionAdminSecurePass2026!")
    with pytest.raises(ValueError, match="SECRET_KEY must not use the development default"):
        Settings()


def test_production_settings_rejects_short_secret_key(monkeypatch):
    """Verify production environment rejects secret key shorter than 32 characters."""
    import pytest

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "too-short-key")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "ProductionAdminSecurePass2026!")
    with pytest.raises(ValueError, match="SECRET_KEY must be at least 32 characters"):
        Settings()


def test_production_settings_rejects_default_admin_password(monkeypatch):
    """Verify production environment rejects default admin password."""
    import pytest

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "super-secret-production-encryption-key-32chars")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "AdminDineIQ2026!")
    with pytest.raises(
        ValueError, match="DEFAULT_ADMIN_PASSWORD must not use the development default"
    ):
        Settings()


def test_production_settings_valid_configuration(monkeypatch):
    """Verify production environment succeeds with valid production secrets."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "super-secret-production-encryption-key-32chars")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "ProductionAdminSecurePass2026!")
    settings = Settings()
    assert settings.ENVIRONMENT == "production"
    assert settings.SECRET_KEY == "super-secret-production-encryption-key-32chars"
