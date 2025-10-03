"""
Core module for shared utilities, configuration, and base classes.
"""

from .config import Settings, get_settings
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ExternalServiceError,
    NotFoundError,
    PixCrawlerException,
    RateLimitError,
    ValidationError,
)

__all__ = [
    "Settings",
    "get_settings",
    "PixCrawlerException",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ExternalServiceError",
    "RateLimitError",
]
