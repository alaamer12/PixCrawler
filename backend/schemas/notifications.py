"""
Notification schemas for PixCrawler.

This module defines Pydantic schemas for notification system validation,
including notifications and user preferences.
"""

from datetime import datetime, time
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
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
]


class NotificationType(str, Enum):
    """Notification types."""
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class NotificationCategory(str, Enum):
    """Notification categories."""
    CRAWL_JOB = "crawl_job"
    PAYMENT = "payment"
    SYSTEM = "system"
    SECURITY = "security"
    DATASET = "dataset"
    PROJECT = "project"


class DigestFrequency(str, Enum):
    """Notification digest frequencies."""
    REALTIME = "realtime"
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"


class NotificationBase(BaseModel):
    """Base schema for notifications."""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )
    
    title: str = Field(
        min_length=1,
        max_length=255,
        description="Notification title",
        examples=["Crawl job completed", "Payment received"],
    )
    
    message: str = Field(
        min_length=1,
        max_length=5000,
        description="Notification message",
        examples=["Your crawl job 'Animals Dataset' has completed successfully."],
    )
    
    type: NotificationType = Field(
        description="Notification type",
        examples=["success", "info"],
    )
    
    category: Optional[NotificationCategory] = Field(
        default=None,
        description="Notification category",
        examples=["crawl_job", "payment"],
    )
    
    icon: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Lucide icon name",
        examples=["check-circle", "alert-triangle"],
    )
    
    color: Optional[str] = Field(
        default=None,
        max_length=20,
        pattern=r'^#[0-9A-Fa-f]{6}$|^[a-z-]+$',
        description="Display color (hex or CSS name)",
        examples=["#10b981", "green"],
    )
    
    action_url: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Action URL",
        examples=["/dashboard/projects/123", "/dashboard/billing"],
    )
    
    action_label: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Action button label",
        examples=["View Project", "Update Payment"],
    )
    
    metadata_: Optional[dict] = Field(
        default=None,
        alias="metadata",
        description="Additional notification data",
    )


class NotificationCreate(NotificationBase):
    """Schema for creating notifications."""
    
    user_id: UUID = Field(description="User ID")


class NotificationUpdate(BaseModel):
    """Schema for updating notifications."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    is_read: bool = Field(description="Mark as read/unread")


class NotificationResponse(NotificationBase):
    """Schema for notification responses."""
    
    id: int = Field(description="Notification ID")
    user_id: UUID = Field(description="User ID")
    is_read: bool = Field(description="Read status")
    read_at: Optional[datetime] = Field(default=None, description="Read timestamp")
    created_at: datetime = Field(description="Creation timestamp")


class NotificationListResponse(BaseModel):
    """Schema for notification list responses."""
    
    model_config = ConfigDict(from_attributes=True)
    
    data: list[NotificationResponse] = Field(
        description="List of notifications",
        examples=[[{
            "id": 1,
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "title": "Crawl Job Completed",
            "message": "Your crawl job 'Animals Dataset' has completed successfully.",
            "type": "success",
            "category": "crawl_job",
            "icon": "check-circle",
            "color": "#10b981",
            "action_url": "/dashboard/projects/123",
            "action_label": "View Project",
            "is_read": False,
            "read_at": None,
            "created_at": "2024-01-27T10:00:00Z",
            "metadata": {}
        }]]
    )
    
    meta: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 50},
        description="Pagination metadata",
        examples=[{"total": 10, "skip": 0, "limit": 50}]
    )


class NotificationMarkReadResponse(BaseModel):
    """Schema for mark as read response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    data: dict = Field(
        description="Updated notification status",
        examples=[{"id": 1, "is_read": True}]
    )


class NotificationMarkAllReadResponse(BaseModel):
    """Schema for mark all as read response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    data: dict = Field(
        description="Bulk update result",
        examples=[{"success": True, "count": 5}]
    )


class BulkNotificationAction(BaseModel):
    """Schema for bulk notification actions."""
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    notification_ids: Optional[list[int]] = Field(
        default=None,
        description="Specific notification IDs (if None, applies to all)",
    )
    
    mark_as_read: Optional[bool] = Field(
        default=None,
        description="Mark as read",
    )
    
    delete: Optional[bool] = Field(
        default=None,
        description="Delete notifications",
    )
    
    filter_read: Optional[bool] = Field(
        default=None,
        description="Filter by read status",
    )


class NotificationPreferenceBase(BaseModel):
    """Base schema for notification preferences."""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        use_enum_values=True,
    )
    
    # Channel preferences
    email_enabled: bool = Field(default=True, description="Email notifications")
    push_enabled: bool = Field(default=False, description="Push notifications")
    sms_enabled: bool = Field(default=False, description="SMS notifications")
    
    # Category preferences
    crawl_jobs_enabled: bool = Field(default=True, description="Crawl job notifications")
    datasets_enabled: bool = Field(default=True, description="Dataset notifications")
    billing_enabled: bool = Field(default=True, description="Billing notifications")
    security_enabled: bool = Field(default=True, description="Security notifications")
    marketing_enabled: bool = Field(default=False, description="Marketing notifications")
    product_updates_enabled: bool = Field(default=True, description="Product update notifications")
    
    # Frequency settings
    digest_frequency: DigestFrequency = Field(
        default=DigestFrequency.DAILY,
        description="Notification digest frequency",
    )
    
    quiet_hours_start: Optional[time] = Field(
        default=None,
        description="Quiet hours start time",
        examples=["22:00:00"],
    )
    
    quiet_hours_end: Optional[time] = Field(
        default=None,
        description="Quiet hours end time",
        examples=["08:00:00"],
    )
    
    @field_validator('quiet_hours_end')
    @classmethod
    def validate_quiet_hours(cls, v: Optional[time], info) -> Optional[time]:
        """Ensure quiet hours end is after start if both are set."""
        if v is not None and 'quiet_hours_start' in info.data:
            start = info.data['quiet_hours_start']
            if start is not None and v == start:
                raise ValueError('quiet_hours_end must be different from quiet_hours_start')
        return v


class NotificationPreferenceUpdate(NotificationPreferenceBase):
    """Schema for updating notification preferences."""
    pass


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """Schema for notification preference responses."""
    
    id: UUID = Field(description="Preference ID")
    user_id: UUID = Field(description="User ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
