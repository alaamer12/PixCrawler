"""
Pydantic schemas for request/response validation and data serialization.

This package provides comprehensive Pydantic models for the PixCrawler backend
with full validation, type safety, and best practices from Pydantic 2.0+.

Schema Categories:
    - Base: Common schemas and error handling
    - User: User and authentication schemas
    - Profile: User profile and settings
    - Dataset: Dataset processing schemas
    - Credits: Credit and billing schemas
    - Notifications: Notification system schemas
    - API Keys: API key management schemas
    - Usage: Usage metrics and analytics schemas

Features:
    - Pydantic 2.0+ with ConfigDict
    - Field validators and computed properties
    - Enum integration with use_enum_values
    - Comprehensive constraints (ge, gt, le, lt, min_length, max_length, pattern)
    - from_attributes for ORM compatibility
    - validate_assignment for runtime validation
    - Custom validators with cross-field validation
"""

from .base import (
    BaseSchema,
    TimestampMixin,
    ErrorDetail,
    HealthCheck
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
from .profile import (
    UserRole,
    ProfileBase,
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileSettings,
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
from .credits import (
    TransactionType,
    TransactionStatus,
    CreditAccountBase,
    CreditAccountCreate,
    CreditAccountUpdate,
    CreditAccountResponse,
    CreditTransactionBase,
    CreditTransactionCreate,
    CreditTransactionResponse,
    AutoRefillSettings,
)
from .notifications import (
    NotificationType,
    NotificationCategory,
    DigestFrequency,
    NotificationBase,
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationPreferenceBase,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    BulkNotificationAction,
)
from .api_keys import (
    APIKeyStatus,
    APIKeyPermission,
    APIKeyBase,
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyRegenerateRequest,
)
from .usage import (
    UsageMetricBase,
    UsageMetricCreate,
    UsageMetricUpdate,
    UsageMetricResponse,
    UsageSummary,
    UsageTrend,
)

__all__ = [
    # Base schemas
    'BaseSchema',
    'TimestampMixin',
    'ErrorDetail',
    'HealthCheck',
    
    # User schemas
    'UserBase',
    'UserCreate',
    'UserUpdate',
    'UserResponse',
    'UserLogin',
    'TokenResponse',
    'TokenRefresh',
    
    # Profile schemas
    'UserRole',
    'ProfileBase',
    'ProfileCreate',
    'ProfileUpdate',
    'ProfileResponse',
    'ProfileSettings',
    
    # Dataset schemas
    'DatasetStatus',
    'SearchEngine',
    'DatasetBase',
    'DatasetCreate',
    'DatasetUpdate',
    'DatasetResponse',
    'DatasetStats',
    
    # Credit schemas
    'TransactionType',
    'TransactionStatus',
    'CreditAccountBase',
    'CreditAccountCreate',
    'CreditAccountUpdate',
    'CreditAccountResponse',
    'CreditTransactionBase',
    'CreditTransactionCreate',
    'CreditTransactionResponse',
    'AutoRefillSettings',
    
    # Notification schemas
    'NotificationType',
    'NotificationCategory',
    'DigestFrequency',
    'NotificationBase',
    'NotificationCreate',
    'NotificationUpdate',
    'NotificationResponse',
    'NotificationPreferenceBase',
    'NotificationPreferenceUpdate',
    'NotificationPreferenceResponse',
    'BulkNotificationAction',
    
    # API Key schemas
    'APIKeyStatus',
    'APIKeyPermission',
    'APIKeyBase',
    'APIKeyCreate',
    'APIKeyUpdate',
    'APIKeyResponse',
    'APIKeyRegenerateRequest',
    
    # Usage schemas
    'UsageMetricBase',
    'UsageMetricCreate',
    'UsageMetricUpdate',
    'UsageMetricResponse',
    'UsageSummary',
    'UsageTrend',
]
