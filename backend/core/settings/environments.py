"""Environment-specific settings with inheritance pattern."""

from functools import lru_cache

from .base import CommonSettings

__all__ = ["DevSettings", "ProdSettings", "TestSettings", "Settings", "get_settings"]


class DevSettings(CommonSettings):
    """Development environment settings."""
    
    environment: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"


class ProdSettings(CommonSettings):
    """Production environment settings."""
    
    environment: str = "production"
    debug: bool = False
    log_level: str = "INFO"


class TestSettings(CommonSettings):
    """Test environment settings."""
    
    environment: str = "test"
    debug: bool = True
    log_level: str = "DEBUG"


class Settings(CommonSettings):
    """
    Dynamic settings that resolve based on environment.
    
    This is the main settings class that should be used throughout the application.
    It automatically selects the correct environment-specific settings.
    
    Usage:
        from backend.core.settings import get_settings
        
        settings = get_settings()
        print(settings.database.url)
        print(settings.redis.expire_seconds)
    """
    
    def resolve(self) -> CommonSettings:
        """
        Resolve to environment-specific settings.
        
        Returns:
            Environment-specific settings instance
        """
        env_map = {
            "development": DevSettings,
            "production": ProdSettings,
            "test": TestSettings,
        }
        settings_class = env_map.get(self.environment, CommonSettings)
        return settings_class()


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    This function maintains backward compatibility with the old API
    while providing the new modular settings structure.
    
    Returns:
        Cached Settings instance
    """
    return Settings()
from pydantic import Field
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    url: str = Field(..., env="DATABASE_URL")  # alias to match .env
    max_overflow: int = 20

    class Config:
        env_file = r"D:\DEPI\PixCrawler\backend\.env"
        env_file_encoding = "utf-8"
        extra = "ignore"
