"""Rate limiting configuration settings."""

import os
import re
import warnings
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["RateLimitSettings"]


class RateLimitSettings(BaseSettings):
    """
    API rate limiting configuration with Redis backend.
    
    Environment variables:
        LIMITER_ENABLED: Enable rate limiting (required in production)
        LIMITER_REDIS_HOST: Redis host address (required in production)
        LIMITER_REDIS_PORT: Redis port number
        LIMITER_REDIS_PASSWORD: Redis password (optional)
        LIMITER_REDIS_DB: Redis database number
        LIMITER_PREFIX: Key prefix for rate limiter entries
        LIMITER_DEFAULT_TIMES: Default request count
        LIMITER_DEFAULT_SECONDS: Default time window in seconds
        RATE_LIMIT_CREATE_DATASET: Dataset creation limit (legacy)
        RATE_LIMIT_CREATE_CRAWL_JOB: Crawl job creation limit (legacy)
        RATE_LIMIT_RETRY_JOB: Job retry limit (legacy)
        RATE_LIMIT_BUILD_JOB: Build job start limit (legacy)
        ENVIRONMENT: Application environment (development/production)
    
    Production Requirements:
        - LIMITER_ENABLED must be True
        - LIMITER_REDIS_HOST must not be localhost
        - Rate limiting is mandatory for API protection
    
    Development Behavior:
        - Defaults to localhost with warning
        - Rate limiting can be disabled for testing
    
    Note:
        Uses LIMITER_ prefix for Redis configuration to avoid conflicts with CACHE_.
        Legacy RATE_LIMIT_ prefixed variables are still supported for backward compatibility.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="LIMITER_",
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    enabled: bool = Field(
        default=True,
        description="Enable API rate limiting",
        examples=[True, False]
    )
    redis_host: str = Field(
        default="localhost",
        min_length=1,
        description="Redis host address for rate limiter",
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
        default=1,
        ge=0,
        le=15,
        description="Redis database number (0-15), use different from cache",
        examples=[1, 2, 3]
    )
    prefix: str = Field(
        default="pixcrawler:limiter:",
        min_length=1,
        description="Key prefix for rate limiter entries",
        examples=["pixcrawler:limiter:", "app:limiter:", "limiter:"]
    )
    default_times: int = Field(
        default=10,
        ge=1,
        description="Default number of requests allowed",
        examples=[10, 20, 50]
    )
    default_seconds: int = Field(
        default=60,
        ge=1,
        description="Default time window in seconds",
        examples=[60, 120, 300]
    )
    
    # Legacy rate limit configurations (backward compatibility)
    create_dataset: str = Field(
        default="10/60",
        description="Rate limit for dataset creation (times/seconds)",
        examples=["10/60", "20/120", "5/30"]
    )
    create_crawl_job: str = Field(
        default="10/60",
        description="Rate limit for crawl job creation (times/seconds)",
        examples=["10/60", "15/60", "5/30"]
    )
    retry_job: str = Field(
        default="5/60",
        description="Rate limit for job retry (times/seconds)",
        examples=["5/60", "10/120", "3/30"]
    )
    build_job: str = Field(
        default="5/60",
        description="Rate limit for build job start (times/seconds)",
        examples=["5/60", "10/120", "3/30"]
    )
    
    @field_validator("prefix")
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        """Ensure prefix ends with colon for proper key namespacing."""
        if not v.endswith(":"):
            return f"{v}:"
        return v
    
    @field_validator("create_dataset", "create_crawl_job", "retry_job", "build_job")
    @classmethod
    def validate_rate_limit_format(cls, v: str) -> str:
        """
        Validate rate limit format is 'times/seconds'.
        
        Args:
            v: Rate limit string
            
        Returns:
            Validated rate limit string
            
        Raises:
            ValueError: If format is invalid
        """
        pattern = r'^\d+/\d+$'
        if not re.match(pattern, v):
            raise ValueError(
                f"Rate limit must be in format 'times/seconds' (e.g., '10/60'), got: {v}"
            )
        
        times, seconds = v.split('/')
        if int(times) < 1:
            raise ValueError(f"Times must be at least 1, got: {times}")
        if int(seconds) < 1:
            raise ValueError(f"Seconds must be at least 1, got: {seconds}")
        
        return v
    
    @model_validator(mode='after')
    def validate_production_config(self) -> 'RateLimitSettings':
        """Enforce rate limiting configuration in production, warn in development."""
        # Get environment from environment variable
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        is_production = environment in ('production', 'prod')
        is_azure = bool(os.getenv('WEBSITE_INSTANCE_ID'))  # Azure App Service indicator
        
        is_localhost = self.redis_host in ('localhost', '127.0.0.1')
        
        if is_production or is_azure:
            # PRODUCTION: Enforce proper configuration
            if not self.enabled:
                raise ValueError(
                    "Rate limiting must be enabled in production for API protection. "
                    "Set LIMITER_ENABLED=true in environment variables."
                )
            if is_localhost:
                raise ValueError(
                    "Rate limiter cannot use localhost Redis in production. "
                    f"Current host: {self.redis_host}. "
                    "Set LIMITER_REDIS_HOST to a proper Redis server address."
                )
        else:
            # DEVELOPMENT: Warn about localhost configuration
            if is_localhost:
                warnings.warn(
                    "⚠️  Using localhost Redis for rate limiting (localhost:6379). "
                    "This is OK for local development. "
                    "For production, set LIMITER_REDIS_HOST environment variable.",
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
