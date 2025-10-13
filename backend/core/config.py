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
from typing import Any, List

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
        validate_default=True,
        str_strip_whitespace=True
    )

    # Application settings
    environment: str = Field(
        default="development", 
        pattern=r'^(development|staging|production|test)$',
        description="Environment name",
        examples=["development", "staging", "production"]
    )
    debug: bool = Field(
        default=False, 
        description="Debug mode flag",
        examples=[True, False]
    )
    host: str = Field(
        default="0.0.0.0", 
        description="Server host address",
        examples=["0.0.0.0", "127.0.0.1", "localhost"]
    )
    port: int = Field(
        default=8000, 
        ge=1024, 
        le=65535,
        description="Server port number",
        examples=[8000, 8080, 3000]
    )
    log_level: str = Field(
        default="INFO", 
        pattern=r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$',
        description="Logging level",
        examples=["DEBUG", "INFO", "WARNING", "ERROR"]
    )

    # Supabase settings
    supabase_url: str = Field(
        ..., 
        min_length=1,
        pattern=r'^https://[a-zA-Z0-9-]+\.supabase\.co$',
        description="Supabase project URL",
        examples=["https://your-project.supabase.co"]
    )
    supabase_service_role_key: str = Field(
        ..., 
        min_length=50,
        description="Supabase service role key"
    )
    supabase_anon_key: str = Field(
        ..., 
        min_length=50,
        description="Supabase anonymous key"
    )

    # CORS settings
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000"],
        min_length=1,
        description="Allowed CORS origins",
        examples=[["http://localhost:3000"], ["https://app.example.com", "https://admin.example.com"]]
    )
    
    # Security settings
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        min_length=1,
        description="Allowed host headers (production)",
        examples=[["localhost"], ["app.example.com", "www.app.example.com"]]
    )
    force_https: bool = Field(
        default=False,
        description="Force HTTPS redirect in production",
        examples=[True, False]
    )

    # Database settings
    database_url: str = Field(
        ..., 
        min_length=1,
        description="PostgreSQL database connection URL",
        examples=["postgresql://user:pass@localhost:5432/pixcrawler"]
    )
    database_pool_size: int = Field(
        default=10, 
        ge=1, 
        le=100,
        description="Database connection pool size",
        examples=[5, 10, 20]
    )
    database_max_overflow: int = Field(
        default=20, 
        ge=0, 
        le=200,
        description="Database connection pool max overflow",
        examples=[10, 20, 50]
    )

    # Redis settings
    redis_url: str = Field(
        ..., 
        min_length=1,
        description="Redis URL for caching and sessions",
        examples=["redis://localhost:6379/0", "redis://user:pass@redis-server:6379/1"]
    )
    redis_expire_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Default Redis key expiration in seconds",
        examples=[3600, 7200, 86400]
    )

    # Celery settings
    celery_broker_url: str = Field(
        ..., 
        min_length=1,
        description="Celery broker URL",
        examples=["redis://localhost:6379/0", "amqp://guest@localhost//"]
    )
    celery_result_backend: str = Field(
        ..., 
        min_length=1,
        description="Celery result backend URL",
        examples=["redis://localhost:6379/0", "db+postgresql://user:pass@localhost/celery"]
    )

    # File storage settings
    upload_max_size: int = Field(
        default=10 * 1024 * 1024,
        ge=1024,  # 1KB minimum
        le=100 * 1024 * 1024,  # 100MB maximum
        description="Maximum upload file size in bytes",
        examples=[1048576, 10485760, 52428800]  # 1MB, 10MB, 50MB
    )
    upload_allowed_extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
        min_length=1,
        description="Allowed file extensions for uploads",
        examples=[[".jpg", ".png"], [".jpg", ".jpeg", ".png", ".gif", ".webp"]]
    )

    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        """Validate CORS origins format."""
        validated = []
        for origin in v:
            origin = origin.strip()
            if not origin:
                continue
            if not (origin.startswith('http://') or origin.startswith('https://')):
                raise ValueError(f"Origin '{origin}' must start with http:// or https://")
            validated.append(origin)
        
        if not validated:
            raise ValueError("At least one valid origin is required")
        return validated

    @field_validator('upload_allowed_extensions')
    @classmethod
    def validate_extensions(cls, v: List[str]) -> List[str]:
        """Validate file extensions format."""
        validated = []
        for ext in v:
            ext = ext.strip().lower()
            if not ext.startswith('.'):
                raise ValueError(f"Extension '{ext}' must start with a dot")
            if len(ext) < 2:
                raise ValueError(f"Extension '{ext}' is too short")
            validated.append(ext)
        return validated

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
    """
    return Settings()
