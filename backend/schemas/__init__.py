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
    UserListResponse,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    TokenVerificationResponse,
    ProfileSyncResponse
)
from .profile import (
    UserRole,
    ProfileBase,
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ProfileListResponse,
    ProfileSettings,
)
from .dataset import (
    DatasetStatus,
    SearchEngine,
    DatasetBase,
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetListResponse,
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
    CreditTransactionListResponse,
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
    NotificationListResponse,
    NotificationMarkReadResponse,
    NotificationMarkAllReadResponse,
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
    APIKeyListResponse,
    APIKeyRegenerateRequest,
    APIKeyCreateResponse,
)
from .usage import (
    UsageMetricBase,
    UsageMetricCreate,
    UsageMetricUpdate,
    UsageMetricResponse,
    UsageMetricListResponse,
    UsageSummary,
    UsageTrend,
    UsageTrendListResponse,
)
from .crawl_jobs import (
    CrawlJobStatus,
    CrawlJobCreate,
    CrawlJobUpdate,
    CrawlJobResponse,
    CrawlJobListResponse,
    CrawlJobProgress,
    JobLogEntry,
    JobLogListResponse,
)
from .validation import (
    ValidationLevel,
    ValidationStatus,
    ValidationAnalyzeRequest,
    ValidationBatchRequest,
    ValidationLevelUpdateRequest,
    ValidationAnalyzeResponse,
    ValidationJobResponse,
    ValidationJobListResponse,
    ValidationResultItem,
    ValidationResultsResponse,
    ValidationStatsResponse,
    ValidationLevelUpdateResponse,
)
from .storage import (
    StorageTier,
    StorageUsageResponse,
    FileInfo,
    FileListResponse,
    CleanupRequest,
    CleanupResponse,
    PresignedUrlResponse,
)
from .project import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
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
    'UserListResponse',
    'UserLogin',
    'TokenResponse',
    'TokenRefresh',
    'TokenVerificationResponse',
    'ProfileSyncResponse',
    
    # Profile schemas
    'UserRole',
    'ProfileBase',
    'ProfileCreate',
    'ProfileUpdate',
    'ProfileResponse',
    'ProfileListResponse',
    'ProfileSettings',
    
    # Dataset schemas
    'DatasetStatus',
    'SearchEngine',
    'DatasetBase',
    'DatasetCreate',
    'DatasetUpdate',
    'DatasetResponse',
    'DatasetListResponse',
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
    'CreditTransactionListResponse',
    'AutoRefillSettings',
    
    # Notification schemas
    'NotificationType',
    'NotificationCategory',
    'DigestFrequency',
    'NotificationBase',
    'NotificationCreate',
    'NotificationUpdate',
    'NotificationResponse',
    'NotificationListResponse',
    'NotificationMarkReadResponse',
    'NotificationMarkAllReadResponse',
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
    'APIKeyListResponse',
    'APIKeyRegenerateRequest',
    'APIKeyCreateResponse',
    
    # Usage schemas
    'UsageMetricBase',
    'UsageMetricCreate',
    'UsageMetricUpdate',
    'UsageMetricResponse',
    'UsageMetricListResponse',
    'UsageSummary',
    'UsageTrend',
    'UsageTrendListResponse',
    
    # Crawl Job schemas
    'CrawlJobStatus',
    'CrawlJobCreate',
    'CrawlJobUpdate',
    'CrawlJobResponse',
    'CrawlJobListResponse',
    'CrawlJobProgress',
    'JobLogEntry',
    'JobLogListResponse',
    
    # Validation schemas
    'ValidationLevel',
    'ValidationStatus',
    'ValidationAnalyzeRequest',
    'ValidationBatchRequest',
    'ValidationLevelUpdateRequest',
    'ValidationAnalyzeResponse',
    'ValidationJobResponse',
    'ValidationJobListResponse',
    'ValidationResultItem',
    'ValidationResultsResponse',
    'ValidationStatsResponse',
    'ValidationLevelUpdateResponse',
    
    # Storage schemas
    'StorageTier',
    'StorageUsageResponse',
    'FileInfo',
    'FileListResponse',
    'CleanupRequest',
    'CleanupResponse',
    'PresignedUrlResponse',
    
    # Project schemas
    'ProjectBase',
    'ProjectCreate',
    'ProjectUpdate',
    'ProjectResponse',
    'ProjectListResponse',
]
