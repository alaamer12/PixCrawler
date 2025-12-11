"""Celery task queue configuration settings."""

import os
import warnings
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["CelerySettings"]


class CelerySettings(BaseSettings):
    """
    Celery distributed task queue configuration.

    Environment variables:
        CELERY_BROKER_URL: Message broker URL (required in production)
        CELERY_RESULT_BACKEND: Result backend URL (required in production)
        ENVIRONMENT: Application environment (development/production)
    
    Production Requirements:
        - CELERY_BROKER_URL must be explicitly set (no defaults)
        - CELERY_RESULT_BACKEND must be explicitly set (no defaults)
        - Cannot use localhost URLs in production
    
    Development Behavior:
        - Defaults to redis://localhost:6379/1 (broker) with warning
        - Defaults to redis://localhost:6379/2 (result backend) with warning
        - Allows localhost URLs
    """

    model_config = SettingsConfigDict(
        env_prefix="CELERY_",
        env_file=[".env", "backend/.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    broker_url: str = Field(
        default="redis://localhost:6379/1",
        min_length=1,
        description="Celery broker URL",
        examples=["redis://localhost:6379/1", "amqp://guest@localhost//"]
    )
    result_backend: str = Field(
        default="redis://localhost:6379/2",
        min_length=1,
        description="Celery result backend URL",
        examples=["redis://localhost:6379/2",
                  "db+postgresql://user:pass@localhost/celery"]
    )
    
    @model_validator(mode='after')
    def validate_production_config(self) -> 'CelerySettings':
        """Enforce Celery configuration in production, warn in development."""
        # Get environment from environment variable
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        is_production = environment in ('production', 'prod')
        is_azure = bool(os.getenv('WEBSITE_INSTANCE_ID'))  # Azure App Service indicator
        
        # Check defaults and localhost usage
        defaults = {
            "broker_url": "redis://localhost:6379/1",
            "result_backend": "redis://localhost:6379/2"
        }
        
        broker_is_default = self.broker_url == defaults["broker_url"]
        backend_is_default = self.result_backend == defaults["result_backend"]
        broker_is_localhost = 'localhost' in self.broker_url or '127.0.0.1' in self.broker_url
        backend_is_localhost = 'localhost' in self.result_backend or '127.0.0.1' in self.result_backend
        
        if is_production or is_azure:
            # PRODUCTION: Enforce proper configuration
            if broker_is_default:
                raise ValueError(
                    "Celery broker configuration required in production. "
                    "CELERY_BROKER_URL environment variable must be set. "
                    "Example: redis://your-redis-server:6379/1"
                )
            if backend_is_default:
                raise ValueError(
                    "Celery result backend configuration required in production. "
                    "CELERY_RESULT_BACKEND environment variable must be set. "
                    "Example: redis://your-redis-server:6379/2"
                )
            if broker_is_localhost:
                raise ValueError(
                    "Celery broker cannot use localhost in production. "
                    f"Current URL: {self.broker_url}. "
                    "Set CELERY_BROKER_URL to a proper Redis/AMQP server address."
                )
            if backend_is_localhost:
                raise ValueError(
                    "Celery result backend cannot use localhost in production. "
                    f"Current URL: {self.result_backend}. "
                    "Set CELERY_RESULT_BACKEND to a proper Redis/database server address."
                )
        else:
            # DEVELOPMENT: Warn about default configuration
            if broker_is_default:
                warnings.warn(
                    "⚠️  Using default Celery broker URL (redis://localhost:6379/1). "
                    "This is OK for local development. "
                    "For production, set CELERY_BROKER_URL environment variable.",
                    UserWarning,
                    stacklevel=2
                )
            if backend_is_default:
                warnings.warn(
                    "⚠️  Using default Celery result backend (redis://localhost:6379/2). "
                    "This is OK for local development. "
                    "For production, set CELERY_RESULT_BACKEND environment variable.",
                    UserWarning,
                    stacklevel=2
                )
        
        return self
