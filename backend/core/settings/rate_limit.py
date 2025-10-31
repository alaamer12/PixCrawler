"""Rate limiting configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["RateLimitSettings"]


class RateLimitSettings(BaseSettings):
    """
    API rate limiting configuration.
    
    Environment variables:
        RATE_LIMIT_ENABLED: Enable rate limiting
        RATE_LIMIT_CREATE_DATASET: Dataset creation limit
        RATE_LIMIT_CREATE_CRAWL_JOB: Crawl job creation limit
        RATE_LIMIT_RETRY_JOB: Job retry limit
        RATE_LIMIT_BUILD_JOB: Build job start limit
    """
    
    model_config = SettingsConfigDict(
        env_prefix="RATE_LIMIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    enabled: bool = Field(
        default=True,
        description="Enable API rate limiting",
        examples=[True, False]
    )
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
