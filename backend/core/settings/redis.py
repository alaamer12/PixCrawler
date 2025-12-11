"""Redis configuration settings."""

import os
import warnings
from typing import Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["RedisSettings"]


class RedisSettings(BaseSettings):
    """
    Redis cache and session configuration.
    
    Environment variables:
        REDIS_URL: Redis connection URL (required in production)
        REDIS_EXPIRE_SECONDS: Default key expiration
        ENVIRONMENT: Application environment (development/production)
    
    Production Requirements:
        - REDIS_URL must be explicitly set (no defaults)
        - Cannot use localhost URLs in production
    
    Development Behavior:
        - Defaults to redis://localhost:6379/0 with warning
        - Allows localhost URLs
    """
    
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=[".env", "backend/.env"],
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
    
    @model_validator(mode='after')
    def validate_production_config(self) -> 'RedisSettings':
        """Enforce Redis configuration in production, warn in development."""
        # Get environment from environment variable
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        is_production = environment in ('production', 'prod')
        is_azure = bool(os.getenv('WEBSITE_INSTANCE_ID'))  # Azure App Service indicator
        
        # Check if using default/localhost URL
        is_default = self.url == "redis://localhost:6379/0"
        is_localhost = 'localhost' in self.url or '127.0.0.1' in self.url
        
        if is_production or is_azure:
            # PRODUCTION: Enforce proper configuration
            if is_default:
                raise ValueError(
                    "Redis configuration required in production. "
                    "REDIS_URL environment variable must be set. "
                    "Example: redis://your-redis-server:6379/0"
                )
            if is_localhost:
                raise ValueError(
                    "Redis cannot use localhost in production. "
                    f"Current URL: {self.url}. "
                    "Set REDIS_URL to a proper Redis server address."
                )
        else:
            # DEVELOPMENT: Warn about default configuration
            if is_default:
                warnings.warn(
                    "⚠️  Using default Redis URL (redis://localhost:6379/0). "
                    "This is OK for local development. "
                    "For production, set REDIS_URL environment variable.",
                    UserWarning,
                    stacklevel=2
                )
        
        return self
