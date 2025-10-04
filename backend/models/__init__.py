"""
Pydantic models for request/response schemas and data validation.

This package provides all Pydantic models used throughout the PixCrawler backend
for request/response validation, data serialization, and type safety.

Modules:
    base: Base schemas and common models
    user: User-related schemas and authentication models
    dataset: Dataset-related schemas and processing models

Features:
    - Comprehensive data validation with Pydantic v2
    - Type-safe request/response schemas
    - Consistent error handling structures
    - Generic pagination support
"""

from .base import (
    BaseSchema,
    TimestampMixin,
    PaginationParams,
    PaginatedResponse,
    ErrorDetail,
    HealthCheck
)
from .dataset import (
    DatasetStatus,
    SearchEngine,
    DatasetBase,
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetStats
)
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    TokenResponse,
    TokenRefresh
)

__all__ = [
    # Base models
    'BaseSchema',
    'TimestampMixin',
    'PaginationParams',
    'PaginatedResponse',
    'ErrorDetail',
    'HealthCheck',
    # User models
    'UserBase',
    'UserCreate',
    'UserUpdate',
    'UserResponse',
    'UserLogin',
    'TokenResponse',
    'TokenRefresh',
    # Dataset models
    'DatasetStatus',
    'SearchEngine',
    'DatasetBase',
    'DatasetCreate',
    'DatasetUpdate',
    'DatasetResponse',
    'DatasetStats'
]
