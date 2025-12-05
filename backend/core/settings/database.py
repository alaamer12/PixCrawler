"""Database configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["DatabaseSettings"]


class DatabaseSettings(BaseSettings):
    """
    PostgreSQL database configuration.
    
    Environment variables:
        DATABASE_URL: PostgreSQL connection URL
        DATABASE_POOL_SIZE: Connection pool size
        DATABASE_MAX_OVERFLOW: Max overflow connections
    """
    
    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=[".env", "backend/.env"],  # Try root first, then backend directory
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    url: str = Field(
        ...,
        min_length=1,
        description="PostgreSQL database connection URL",
        examples=["postgresql://user:pass@localhost:5432/pixcrawler"]
    )
    pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Database connection pool size",
        examples=[5, 10, 20]
    )
    max_overflow: int = Field(
        default=20,
        ge=0,
        le=200,
        description="Database connection pool max overflow",
        examples=[10, 20, 50]
    )
