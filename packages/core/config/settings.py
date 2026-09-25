"""Application settings powered by Pydantic Settings."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System configuration parameters and operational defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "DineIQ Analytics API"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database
    POSTGRES_USER: str = "dineiq_user"
    POSTGRES_PASSWORD: str = "dineiq_password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "dineiq_analytics"
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://dineiq_user:dineiq_password@localhost:5432/dineiq_analytics"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True

    # Security & RBAC
    SECRET_KEY: str = "default-development-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_EMAIL: str = "admin@dineiq.local"
    DEFAULT_ADMIN_PASSWORD: str = "AdminDineIQ2026!"

    # Business & Analytics Defaults
    DEFAULT_CURRENCY: str = "USD"

    # Storage paths
    DATA_DIR: str = "data"
    SNAPSHOTS_DIR: str = "data/snapshots"
    MARTS_DIR: str = "data/marts"
    ARTIFACTS_DIR: str = "data/artifacts"

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforce strict production security policies."""
        if self.ENVIRONMENT.lower() == "production":
            insecure_secret_keys = {
                "default-development-secret-key-change-in-production-min-32-chars",
                "change-this-in-production-super-secret-key-min-32-chars",
            }
            if self.SECRET_KEY in insecure_secret_keys:
                raise ValueError("SECRET_KEY must not use the development default in production")
            if len(self.SECRET_KEY) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters in production")
            insecure_admin_passwords = {
                "AdminDineIQ2026!",
                "change-admin-password-in-production",
            }
            if self.DEFAULT_ADMIN_PASSWORD in insecure_admin_passwords:
                raise ValueError(
                    "DEFAULT_ADMIN_PASSWORD must not use the development default in production"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
