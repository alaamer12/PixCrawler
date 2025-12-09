"""
PixCrawler SDK Configuration

This module manages the configuration for the PixCrawler SDK using Pydantic Settings.
It supports environment variables and `.env` files.
"""
from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, RedisDsn

class SDKConfig(BaseSettings):
    """
    Main configuration for the PixCrawler SDK.
    """
    model_config = SettingsConfigDict(
        env_prefix="PIXCRAWLER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # API Configuration
    API_BASE_URL: str = "http://localhost:8000/api/v1"
    API_KEY: Optional[str] = None
    API_TIMEOUT: int = 30  # seconds

    # Redis Configuration (for local orchestration/caching)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Paths
    DEFAULT_OUTPUT_DIR: Path = Field(default=Path("./datasets"))

    # Builder Defaults
    DEFAULT_FEEDER_THREADS: int = 4
    DEFAULT_PARSER_THREADS: int = 4
    DEFAULT_DOWNLOADER_THREADS: int = 4
    
    # Validation Defaults
    MIN_IMAGE_SIZE_BYTES: int = 5100  # ~5KB
    MIN_IMAGE_WIDTH: int = 200
    MIN_IMAGE_HEIGHT: int = 200

    def get_redis_url(self) -> str:
        return self.REDIS_URL

_config: Optional[SDKConfig] = None

def get_config() -> SDKConfig:
    """
    Get the singleton configuration instance.
    """
    global _config
    if _config is None:
        _config = SDKConfig()
    return _config
