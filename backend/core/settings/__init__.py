"""
Modular settings with composition and environment-based configuration.

This module provides a refactored settings architecture using:
- Composition: Nested settings classes for modularity
- Inheritance: Environment-specific configurations
- Prefix-based environment variables for each settings module

Example environment variables:
    SUPABASE_URL=https://project.supabase.co
    DATABASE_URL=postgresql://...
    REDIS_EXPIRE_SECONDS=7200
    SECURITY_ALLOWED_ORIGINS=http://localhost:3000,https://app.com
"""

from .base import CommonSettings
from .database import DatabaseSettings
from .redis import RedisSettings
from .celery import CelerySettings as CeleryConfigSettings
from .security import SecuritySettings
from .supabase import SupabaseSettings
from .rate_limit import RateLimitSettings
from .storage import StorageSettings
from .environments import DevSettings, ProdSettings, TestSettings, Settings, get_settings

__all__ = [
    # Modular settings
    "CommonSettings",
    "DatabaseSettings",
    "RedisSettings",
    "CeleryConfigSettings",
    "SecuritySettings",
    "SupabaseSettings",
    "RateLimitSettings",
    "StorageSettings",
    # Environment-based settings
    "DevSettings",
    "ProdSettings",
    "TestSettings",
    "Settings",
    "get_settings",
]
