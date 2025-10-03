"""
Application configuration management using Pydantic Settings.

This module provides centralized configuration management for the PixCrawler backend
service, supporting environment-based configuration with type validation and
comprehensive settings for all application components.

Classes:
    Settings: Main application settings with environment variable support

Functions:
    get_settings: Get cached application settings instance

Features:
    - Environment-based configuration with .env file support
    - Type-safe configuration with Pydantic validation
    - Comprehensive settings for database, Redis, security, and external APIs
    - Cached settings instance for performance
"""

from functools import lru_cache
from typing import Any, Optional, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'Settings',
    'get_settings'
]


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class defines all configuration options for the PixCrawler backend,
    including application settings, security configuration, database connections,
    and external service integrations.

    Attributes:
        environment: Environment name (development, staging, production)
        debug: Debug mode flag
        host: Server host address
        port: Server port number
        log_level: Logging level
        secret_key: Secret key for JWT tokens
        access_token_expire_minutes: Access token expiration time
        refresh_token_expire_days: Refresh token expiration time
        algorithm: JWT algorithm
        allowed_origins: List of allowed CORS origins
        database_url: PostgreSQL database connection URL
        redis_url: Redis connection URL
        redis_expire_seconds: Default Redis key expiration
        celery_broker_url: Celery broker URL
        celery_result_backend: Celery result backend URL
        upload_max_size: Maximum upload file size in bytes
        upload_allowed_extensions: List of allowed file extensions
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    environment: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")

    # Security settings
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")
    algorithm: str = Field(default="HS256", description="JWT algorithm")

    # CORS settings
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )

    # Database settings
    database_url: str = Field(..., description="PostgreSQL database URL")

    # Redis settings
    redis_url: str = Field(..., description="Redis URL for caching and sessions")
    redis_expire_seconds: int = Field(default=3600, description="Default Redis expiration")

    # Celery settings
    celery_broker_url: str = Field(..., description="Celery broker URL")
    celery_result_backend: str = Field(..., description="Celery result backend URL")

    # File storage settings
    upload_max_size: int = Field(default=10 * 1024 * 1024, description="Max upload size in bytes")
    upload_allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
        description="Allowed file extensions"
    )

    @classmethod
    @field_validator("allowed_origins", mode="before")
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """
        Parse CORS origins from string or list.

        Args:
            v: Input value (string or list)

        Returns:
            List of origin strings
        """
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Cached Settings instance
    """
    return Settings()
