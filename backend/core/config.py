"""
Application configuration management.

Centralized configuration using Pydantic Settings for environment-based configuration.
"""

from functools import lru_cache
from typing import Any

from pydantic import Field, PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")

    # Security
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    access_token_expire_minutes: int = Field(default=30,
                                             description="Access token expiration")
    refresh_token_expire_days: int = Field(default=7,
                                           description="Refresh token expiration")
    algorithm: str = Field(default="HS256", description="JWT algorithm")

    # CORS
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Database
    database_url: PostgresDsn = Field(..., description="PostgreSQL database URL")

    # Redis
    redis_url: RedisDsn = Field(..., description="Redis URL for caching and sessions")
    redis_expire_seconds: int = Field(default=3600,
                                      description="Default Redis expiration")

    # Celery
    celery_broker_url: str = Field(..., description="Celery broker URL")
    celery_result_backend: str = Field(..., description="Celery result backend URL")

    # File Storage
    upload_max_size: int = Field(default=10 * 1024 * 1024,
                                 description="Max upload size in bytes")
    upload_allowed_extensions: list[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
        description="Allowed file extensions"
    )

    @classmethod
    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
