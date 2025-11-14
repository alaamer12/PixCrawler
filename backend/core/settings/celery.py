"""Celery task queue configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["CelerySettings"]


class CelerySettings(BaseSettings):
    """
    Celery distributed task queue configuration.
    
    Environment variables:
        CELERY_BROKER_URL: Message broker URL
        CELERY_RESULT_BACKEND: Result backend URL
    """
    
    model_config = SettingsConfigDict(
        env_prefix="CELERY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    broker_url: str = Field(
        ...,
        min_length=1,
        description="Celery broker URL",
        examples=["redis://localhost:6379/0", "amqp://guest@localhost//"]
    )
    result_backend: str = Field(
        ...,
        min_length=1,
        description="Celery result backend URL",
        examples=["redis://localhost:6379/0", "db+postgresql://user:pass@localhost/celery"]
    )
