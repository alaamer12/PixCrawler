"""Cache configuration settings."""

import os
import warnings
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["CacheSettings"]


class CacheSettings(BaseSettings):
    """
    Redis cache configuration.
    
    Environment variables:
        CACHE_ENABLED: Enable caching (required in production)
        CACHE_REDIS_HOST: Redis host address (required in production)
        CACHE_REDIS_PORT: Redis port number
        CACHE_REDIS_PASSWORD: Redis password (optional)
        CACHE_REDIS_DB: Redis database number
        CACHE_PREFIX: Key prefix for cache entries
        CACHE_DEFAULT_TTL: Default time-to-live in seconds
        ENVIRONMENT: Application environment (development/production)
    
    Production Requirements:
        - CACHE_ENABLED must be True
        - CACHE_REDIS_HOST must not be localhost
        - Caching is mandatory for performance
    
    Development Behavior:
        - Defaults to localhost with warning
        - Caching can be disabled for testing
    """
    
    model_config = SettingsConfigDict(
        env_prefix="CACHE_",
        env_file=[".env", "backend/.env"],
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
    
    @model_validator(mode='after')
    def validate_production_config(self) -> 'CacheSettings':
        """Enforce cache configuration in production, warn in development."""
        # Get environment from environment variable
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        is_production = environment in ('production', 'prod')
        is_azure = bool(os.getenv('WEBSITE_INSTANCE_ID'))  # Azure App Service indicator
        
        is_localhost = self.redis_host in ('localhost', '127.0.0.1')
        
        if is_production or is_azure:
            # PRODUCTION: Enforce proper configuration
            if not self.enabled:
                raise ValueError(
                    "Caching must be enabled in production for performance. "
                    "Set CACHE_ENABLED=true in environment variables."
                )
            if is_localhost:
                raise ValueError(
                    "Cache cannot use localhost Redis in production. "
                    f"Current host: {self.redis_host}. "
                    "Set CACHE_REDIS_HOST to a proper Redis server address."
                )
        else:
            # DEVELOPMENT: Warn about localhost configuration
            if is_localhost:
                warnings.warn(
                    "⚠️  Using localhost Redis for caching (localhost:6379). "
                    "This is OK for local development. "
                    "For production, set CACHE_REDIS_HOST environment variable.",
                    UserWarning,
                    stacklevel=2
                )
        
        return self
    
    def get_redis_url(self) -> str:
        """
        Build Redis connection URL from components.
        
        Returns:
            Redis URL string in format: redis://[:password@]host:port/db
        """
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
