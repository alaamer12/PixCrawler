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
from .notifications import Notification, NotificationPreference
from .usage import UsageMetric

# Import core models
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
    # Core models
    'Profile',
    'Project',
    'CrawlJob',
    'Image',
    'ActivityLog',
    # Chunk models
    'JobChunk',
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
]


class Profile(Base, TimestampMixin):
    """
    User profile model (mirrors Drizzle profiles table).

    Extends Supabase auth.users with additional profile information.
    The id field references auth.users.id from Supabase Auth.

    Attributes:
        id: UUID primary key (references auth.users.id)
        email: User email address
        full_name: User's full name
        avatar_url: URL to user's avatar image
        role: User role (default: 'user')
        user_tier: Subscription tier (FREE, PRO, ENTERPRISE)

    Relationships:
        projects: User's projects (one-to-many)
        activity_logs: User's activity logs (one-to-many)
        credit_account: User's credit account (one-to-one)
        api_keys: User's API keys (one-to-many)
    """

    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    user_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="FREE",
        server_default="FREE",
        index=True,
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    credit_account: Mapped[Optional["CreditAccount"]] = relationship(
        "CreditAccount",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Project(Base, TimestampMixin):
    """
    Project model (mirrors Drizzle projects table).

    Projects organize image crawling tasks for users.

    Attributes:
        id: Serial primary key
        name: Project name
        description: Optional project description
        user_id: UUID reference to profiles.id (FK)
        status: Project status (default: 'active')

    Relationships:
        user: Profile owner (many-to-one)
        crawl_jobs: Associated crawl jobs (one-to-many)
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # Relationships
    user: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="projects",
        lazy="joined",
    )
    crawl_jobs: Mapped[list["CrawlJob"]] = relationship(
        "CrawlJob",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
        Index("ix_projects_status", "status"),
    )


class CrawlJob(Base, TimestampMixin, ChunkTrackingMixin):
    """
    Crawl job model with hybrid chunk tracking.

    Attributes:
        id: Serial primary key
        project_id: Reference to projects.id (FK)
        name: Job name
        keywords: JSON array of search keywords
        max_images: Maximum number of images to collect
        status: Job status
        progress: Progress percentage (0-100)
        total_images: Total images found
        downloaded_images: Number of images downloaded
        valid_images: Number of valid images
        started_at: Job start timestamp
        completed_at: Job completion timestamp

    Inherited from ChunkTrackingMixin:
        total_chunks: Total processing chunks
        active_chunks: Currently processing chunks
        completed_chunks: Successfully completed chunks
        failed_chunks: Failed chunks
        task_ids: List of Celery task IDs
        chunk_progress: Property for progress calculation
        is_processing: Property to check if processing
        all_chunks_completed: Property to check completion

    Relationships:
        project: Parent project (many-to-one)
        images: Associated images (one-to-many)
        chunks: Associated job chunks (one-to-many)
    """

    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[dict] = mapped_column(JSONB, nullable=False)
    max_images: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    downloaded_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="crawl_jobs",
        lazy="joined",
    )
    images: Mapped[list["Image"]] = relationship(
        "Image",
        back_populates="crawl_job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    chunks: Mapped[list["JobChunk"]] = relationship(
        "JobChunk",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        Index("ix_crawl_jobs_project_id", "project_id"),
        Index("ix_crawl_jobs_status", "status"),
        Index("ix_crawl_jobs_project_status", "project_id", "status"),
        Index("ix_crawl_jobs_created_at", "created_at"),
    )

    @property
    def is_processing(self) -> bool:
        """Check if job has active chunks."""
        return self.active_chunks > 0

    @property
    def all_chunks_completed(self) -> bool:
        """Check if all chunks are completed."""
        return self.total_chunks > 0 and self.completed_chunks == self.total_chunks


class Image(Base, TimestampMixin):
    """
    Image model (mirrors Drizzle images table).

    Stores metadata for crawled images.

    Attributes:
        id: Serial primary key
        crawl_job_id: Reference to crawl_jobs.id (FK)
        original_url: Original image URL
        filename: Stored filename
        storage_url: Supabase Storage URL
        width: Image width in pixels
        height: Image height in pixels
        file_size: File size in bytes
        format: Image format_ (jpg, png, etc.)

    Relationships:
        crawl_job: Parent crawl job (many-to-one)
    """

    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relationships
    crawl_job: Mapped["CrawlJob"] = relationship(
        "CrawlJob",
        back_populates="images",
        lazy="joined",
    )

    # Indexes
    __table_args__ = (
        Index("ix_images_crawl_job_id", "crawl_job_id"),
        Index("ix_images_created_at", "created_at"),
    )


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
    metadata_: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        back_populates="activity_logs",
        lazy="joined",
    )

    # Indexes
    __table_args__ = (
        Index("ix_activity_logs_user_id", "user_id"),
        Index("ix_activity_logs_timestamp", "timestamp"),
        Index("ix_activity_logs_user_timestamp", "user_id", "timestamp"),
        Index("ix_activity_logs_resource", "resource_type", "resource_id"),
    )
