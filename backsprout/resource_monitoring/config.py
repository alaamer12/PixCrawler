import os
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from backend.core.config import get_settings as get_backend_settings
    BACKEND_DB_URL = str(get_backend_settings().database.url) if hasattr(get_backend_settings(), 'database') else None
except ImportError:
    BACKEND_DB_URL = None

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    MODE: Literal["local", "azure"] = Field(default="local", description="Operation mode")
    POLL_INTERVAL_SECONDS: int = Field(default=60, description="Poll interval in seconds")
    
    # Thresholds
    DISK_THRESHOLD_WARN: float = Field(default=80.0, description="Disk usage warning threshold %")
    DISK_THRESHOLD_ALERT: float = Field(default=90.0, description="Disk usage alert threshold %")
    
    MEMORY_THRESHOLD_WARN: float = Field(default=80.0, description="Memory usage warning threshold %")
    MEMORY_THRESHOLD_ALERT: float = Field(default=90.0, description="Memory usage alert threshold %")
    
    CHUNK_THRESHOLD_WARN: int = Field(default=35, description="Active chunks warning threshold")
    CHUNK_THRESHOLD_ALERT: int = Field(default=40, description="Active chunks alert threshold")
    
    # Azure
    AZURE_RESOURCE_ID: Optional[str] = Field(default=None, description="Azure Resource ID for metrics")
    AZURE_METRIC_NAMES: list[str] = Field(
        default=["MemoryPercentage", "DiskQueueLength"], 
        description="List of Azure metrics to query"
    )
    
    # Database
    # Prefer backend config if available, else env var, else default
    DB_URL: str = Field(
        default=BACKEND_DB_URL or os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/pixcrawler"),
        description="Database connection string"
    )

settings = Settings()
