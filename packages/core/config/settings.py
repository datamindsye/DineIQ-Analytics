"""Application settings powered by Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
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

    # Security
    SECRET_KEY: str = "default-development-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Storage paths
    DATA_DIR: str = "data"
    SNAPSHOTS_DIR: str = "data/snapshots"
    MARTS_DIR: str = "data/marts"
    ARTIFACTS_DIR: str = "data/artifacts"


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of application settings."""
    return Settings()
