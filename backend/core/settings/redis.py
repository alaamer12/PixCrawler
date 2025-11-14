"""Redis configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["RedisSettings"]


class RedisSettings(BaseSettings):
    """
    Redis cache and session configuration.
    
    Environment variables:
        REDIS_URL: Redis connection URL
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
        ...,
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
