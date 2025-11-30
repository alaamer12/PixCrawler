"""
SQLAlchemy database models for PixCrawler.

This module provides comprehensive SQLAlchemy ORM models for the PixCrawler
backend, synchronized with the Drizzle schema in the frontend.

IMPORTANT: These models must be kept in sync with the Drizzle schema in
frontend/lib/db/schema.ts. The Drizzle schema is the source of truth.

Model Categories:
    - Core: Profile, Project, CrawlJob, Image, ActivityLog
    - Credits: CreditAccount, CreditTransaction
    - Notifications: Notification, NotificationPreference
    - API: APIKey
    - Usage: UsageMetric

Features:
    - SQLAlchemy 2.0 with Mapped annotations
    - Full type safety with mypy support
    - Advanced constraints and indexes
    - Relationship management with cascade behaviors
    - PostgreSQL-specific features (JSONB, UUID)
    - Supabase auth integration
"""

from .base import Base, TimestampMixin
from .api_keys import APIKey
from .chunks import JobChunk
from .credits import CreditAccount, CreditTransaction
from .dataset import Dataset
from .notifications import Notification, NotificationPreference
from .usage import UsageMetric
from .metrics import ProcessingMetric, ResourceMetric, QueueMetric
from .workflow import WorkflowStatus, TaskStatus, WorkflowState, WorkflowTask

# Import core models from database.models (synchronized with Drizzle schema)
from backend.database.models import Profile, Project, CrawlJob, Image

# Import for mixins
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text, func, UUID as SQLAlchemyUUID, CheckConstraint, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, declared_attr, relationship


class ChunkTrackingMixin:
    """
    Mixin for hybrid chunk tracking in processing jobs.

    Provides fields and methods for tracking Celery task chunks
    without needing a separate chunk table.

    Attributes:
        total_chunks: Total number of processing chunks
        active_chunks: Currently processing chunks
        completed_chunks: Successfully completed chunks
        failed_chunks: Failed chunks
        task_ids: List of Celery task IDs for status queries
    """

    @declared_attr
    def total_chunks(cls) -> Mapped[int]:
        return mapped_column(Integer, nullable=False, default=0)

    @declared_attr
    def active_chunks(cls) -> Mapped[int]:
        return mapped_column(Integer, nullable=False, default=0)

    @declared_attr
    def completed_chunks(cls) -> Mapped[int]:
        return mapped_column(Integer, nullable=False, default=0)

    @declared_attr
    def failed_chunks(cls) -> Mapped[int]:
        return mapped_column(Integer, nullable=False, default=0)

    @declared_attr
    def task_ids(cls) -> Mapped[list]:
        return mapped_column(JSONB, nullable=False, default=list)

    @property
    def chunk_progress(self) -> float:
        """Calculate chunk completion progress (0-100)."""
        if self.total_chunks == 0:
            return 0.0
        return (self.completed_chunks / self.total_chunks) * 100

    @property
    def is_processing(self) -> bool:
        """Check if job has active chunks."""
        return self.active_chunks > 0

    @property
    def all_chunks_completed(self) -> bool:
        """Check if all chunks are completed."""
        return self.total_chunks > 0 and self.completed_chunks == self.total_chunks

__all__ = [
    # Base classes
    'Base',
    'TimestampMixin',
    'ChunkTrackingMixin',
    # Core models (from database.models - synchronized with Drizzle)
    'Profile',
    'Project',
    'CrawlJob',
    'Image',
    'ActivityLog',
    'Dataset',
    # Chunk models
    'JobChunk',
    # Workflow models
    'WorkflowStatus',
    'TaskStatus',
    'WorkflowState',
    'WorkflowTask',
    # Credit models
    'CreditAccount',
    'CreditTransaction',
    # Notification models
    'Notification',
    'NotificationPreference',
    # API models
    'APIKey',
    # Usage models
    'UsageMetric',
    # Metrics models
    'ProcessingMetric',
    'ResourceMetric',
    'QueueMetric',
]


class ActivityLog(Base):
    """
    Activity log model (mirrors Drizzle activityLogs table).

    Tracks user actions and system events.

    Attributes:
        id: Serial primary key
        user_id: Optional reference to profiles.id (FK)
        action: Action description
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        metadata_: Additional event metadata (JSON)
        timestamp: Event timestamp

    Relationships:
        user: User who performed the action (many-to-one)
    """

    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        lazy="joined",
    )

    # Indexes
    __table_args__ = (
        Index("ix_activity_logs_user_id", "user_id"),
        Index("ix_activity_logs_timestamp", "timestamp"),
        Index("ix_activity_logs_user_timestamp", "user_id", "timestamp"),
        Index("ix_activity_logs_resource", "resource_type", "resource_id"),
    )
