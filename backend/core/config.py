"""
Application configuration management using Pydantic Settings.

DEPRECATED: This module is maintained for backward compatibility.
New code should use: from backend.core.settings import get_settings

This module provides centralized configuration management for the PixCrawler backend
service, supporting environment-based configuration with type validation and
comprehensive settings for all application components.

The new modular settings architecture uses:
- Composition: Nested settings classes (database, redis, celery, etc.)
- Inheritance: Environment-specific configurations (dev, prod, test)
- Prefix-based environment variables for each settings module

Classes:
    Settings: Main application settings (backward compatibility wrapper)

Functions:
    get_settings: Get cached application settings instance

Features:
    - Environment-based configuration with .env file support
    - Type-safe configuration with Pydantic validation
    - Modular settings with composition pattern
    - Cached settings instance for performance
"""

# Import new modular settings for backward compatibility
from backend.core.settings import Settings as _ModularSettings
from backend.core.settings import get_settings as _get_modular_settings

__all__ = [
    'Settings',
    'get_settings'
]

# Backward compatibility: Expose modular settings as Settings
Settings = _ModularSettings


def get_settings() -> Settings:
    """
    Get cached application settings.
    
    This function maintains backward compatibility while using
    the new modular settings architecture under the hood.
    
    Returns:
        Cached Settings instance with modular structure
    """
    return _get_modular_settings()
