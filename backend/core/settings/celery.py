"""Celery task queue configuration settings."""

import warnings
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["CelerySettings"]


class CelerySettings(BaseSettings):
    """
    Celery distributed task queue configuration.

    Environment variables:
        CELERY_BROKER_URL: Message broker URL (optional, defaults to redis://localhost:6379/1)
        CELERY_RESULT_BACKEND: Result backend URL (optional, defaults to redis://localhost:6379/2)
    """

    model_config = SettingsConfigDict(
        env_prefix="CELERY_",
        env_file=".env",
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
    
    @field_validator("broker_url", "result_backend")
    @classmethod
    def warn_if_default(cls, v: str, info) -> str:
        """Warn if using default Celery URLs."""
        defaults = {
            "broker_url": "redis://localhost:6379/1",
            "result_backend": "redis://localhost:6379/2"
        }
        
        if info.field_name in defaults and v == defaults[info.field_name]:
            warnings.warn(
                f"Using default Celery {info.field_name} ({v}). "
                f"Set CELERY_{info.field_name.upper()} environment variable for production.",
                UserWarning,
                stacklevel=2
            )
        return v
