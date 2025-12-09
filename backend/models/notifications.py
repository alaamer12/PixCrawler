"""
Notification models for PixCrawler.

This module defines SQLAlchemy ORM models for the notification system,
including notifications and user preferences.
"""

from datetime import datetime, time
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    Time,
    func,
    UUID as SQLAlchemyUUID,
    CheckConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

__all__ = [
    'Notification',
    'NotificationPreference',
]


class Notification(Base):
    """
    Notification model for user alerts and messages.
    
    Stores all user notifications with support for actions,
    categorization, and read/unread tracking.
    
    Attributes:
        id: Serial primary key
        user_id: Reference to profiles.id
        title: Notification title
        message: Notification message body
        type: Notification type (success, info, warning, error)
        category: Notification category (crawl_job, payment, system, security)
        icon: Lucide icon name
        color: Display color
        action_url: Optional action URL
        action_label: Optional action button label
        is_read: Read status
        read_at: Timestamp when marked as read
        metadata_: Additional notification data (JSON)
        created_at: Creation timestamp
    """
    
    __tablename__ = "notifications"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    
    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Content
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    # Classification
    type_: Mapped[str] = mapped_column(
        "type",
        String(50),
        nullable=False,
        index=True,
    )
    
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    
    # Display properties
    icon: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    color: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Action
    action_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    action_label: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    # Status
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )
    
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Additional data
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "\"type\" IN ('success', 'info', 'warning', 'error')",
            name="ck_notifications_type_valid",
        ),
        CheckConstraint(
            "category IN ('crawl_job', 'payment', 'system', 'security', 'dataset', 'project') OR category IS NULL",
            name="ck_notifications_category_valid",
        ),
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_type", "type"),
        Index("ix_notifications_category", "category"),
        Index("ix_notifications_created_at", "created_at", postgresql_using="btree", postgresql_ops={"created_at": "DESC"}),
        Index("ix_notifications_user_unread", "user_id", "is_read", postgresql_where="is_read = false"),
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )
    
    @property
    def type(self) -> str:
        """Property accessor for type field to support Pydantic serialization."""
        return self.type_
    
    @type.setter
    def type(self, value: str) -> None:
        """Property setter for type field."""
        self.type_ = value


class NotificationPreference(Base, TimestampMixin):
    """
    Notification preference model for user settings.
    
    Stores user preferences for notification channels,
    categories, and delivery frequency.
    
    Attributes:
        id: UUID primary key
        user_id: Reference to profiles.id (unique)
        email_enabled: Email notifications enabled
        push_enabled: Push notifications enabled
        sms_enabled: SMS notifications enabled
        crawl_jobs_enabled: Crawl job notifications enabled
        datasets_enabled: Dataset notifications enabled
        billing_enabled: Billing notifications enabled
        security_enabled: Security notifications enabled
        marketing_enabled: Marketing notifications enabled
        product_updates_enabled: Product update notifications enabled
        digest_frequency: Notification digest frequency
        quiet_hours_start: Quiet hours start time
        quiet_hours_end: Quiet hours end time
    """
    
    __tablename__ = "notification_preferences"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Channel preferences
    email_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    
    push_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    
    sms_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    
    # Category preferences
    crawl_jobs_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    
    datasets_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    
    billing_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    
    security_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    
    marketing_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    
    product_updates_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    
    # Frequency settings
    digest_frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="daily",
        server_default="daily",
    )
    
    quiet_hours_start: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
    )
    
    quiet_hours_end: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "digest_frequency IN ('realtime', 'daily', 'weekly', 'never')",
            name="ck_notification_preferences_digest_frequency_valid",
        ),
        Index("ix_notification_preferences_user_id", "user_id"),
    )
