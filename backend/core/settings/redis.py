"""Redis configuration settings."""

import warnings
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["RedisSettings"]


class RedisSettings(BaseSettings):
    """
    Redis cache and session configuration.
    
    Environment variables:
        REDIS_URL: Redis connection URL (optional, defaults to redis://localhost:6379/0)
        REDIS_EXPIRE_SECONDS: Default key expiration
    """
    
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    url: str = Field(
        default="redis://localhost:6379/0",
        min_length=1,
        description="Redis URL for caching and sessions",
        examples=["redis://localhost:6379/0", "redis://user:pass@redis-server:6379/1"]
    )
    expire_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Default Redis key expiration in seconds",
        examples=[3600, 7200, 86400]
    )
    
    @field_validator("url")
    @classmethod
    def warn_if_default(cls, v: str) -> str:
        """Warn if using default Redis URL."""
        if v == "redis://localhost:6379/0":
            warnings.warn(
                "Using default Redis URL (redis://localhost:6379/0). "
                "Set REDIS_URL environment variable for production.",
                UserWarning,
                stacklevel=2
            )
        return v
