"""Base settings with composition of all modular settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .celery import CelerySettings
from .database import DatabaseSettings
from .rate_limit import RateLimitSettings
from .redis import RedisSettings
from .security import SecuritySettings
from .storage import StorageSettings
from .supabase import SupabaseSettings
from .temp_storage_cleanup import TempStorageCleanupSettings

__all__ = ["CommonSettings"]


class CommonSettings(BaseSettings):
    """
    Base application settings with composition pattern.
    
    Nested settings are automatically populated from environment variables
    using their respective prefixes (SUPABASE_, DATABASE_, REDIS_, etc.)
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
    
    # Composition: Nested settings
    supabase: SupabaseSettings = Field(default_factory=SupabaseSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    rate_limit: RateLimitSettings = Field(default_factory=RateLimitSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    temp_storage_cleanup: TempStorageCleanupSettings = Field(default_factory=TempStorageCleanupSettings)
