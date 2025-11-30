"""Cache configuration settings."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["CacheSettings"]


class CacheSettings(BaseSettings):
    """
    Redis cache configuration.
    
    Environment variables:
        CACHE_ENABLED: Enable caching
        CACHE_REDIS_HOST: Redis host address
        CACHE_REDIS_PORT: Redis port number
        CACHE_REDIS_PASSWORD: Redis password (optional)
        CACHE_REDIS_DB: Redis database number
        CACHE_PREFIX: Key prefix for cache entries
        CACHE_DEFAULT_TTL: Default time-to-live in seconds
    """
    
    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    enabled: bool = Field(
        default=True,
        description="Enable Redis caching",
        examples=[True, False]
    )
    redis_host: str = Field(
        default="localhost",
        min_length=1,
        description="Redis host address for cache",
        examples=["localhost", "redis", "127.0.0.1", "redis.example.com"]
    )
    redis_port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Redis port number",
        examples=[6379, 6380]
    )
    redis_password: str | None = Field(
        default=None,
        description="Redis password (optional)",
        examples=["mypassword", None]
    )
    redis_db: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis database number (0-15)",
        examples=[0, 1, 2]
    )
    prefix: str = Field(
        default="pixcrawler:cache:",
        min_length=1,
        description="Key prefix for cache entries",
        examples=["pixcrawler:cache:", "app:cache:", "cache:"]
    )
    default_ttl: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Default TTL (time-to-live) in seconds",
        examples=[3600, 7200, 86400]
    )
    
    @field_validator("prefix")
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        """Ensure prefix ends with colon for proper key namespacing."""
        if not v.endswith(":"):
            return f"{v}:"
        return v
    
    def get_redis_url(self) -> str:
        """
        Build Redis connection URL from components.
        
        Returns:
            Redis URL string in format: redis://[:password@]host:port/db
        """
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
