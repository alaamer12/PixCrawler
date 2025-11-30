"""
SQLAlchemy models synchronized with frontend Drizzle schema.

This module provides SQLAlchemy ORM models that match the frontend Drizzle schema
defined in frontend/lib/db/schema.ts. These models are the backend representation
of the shared Supabase PostgreSQL database.

IMPORTANT: The frontend Drizzle schema is the single source of truth.
Any changes to the database schema should be made in Drizzle first, then
synchronized here.

Tables defined:
- profiles: User profiles (extends Supabase auth.users)
- projects: Project organization
- crawl_jobs: Image crawling tasks with chunk tracking
- images: Crawled image metadata
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
    func,
    UUID as SQLAlchemyUUID,
    CheckConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin

__all__ = [
    'Profile',
    'Project',
    'CrawlJob',
    'Image',
    'ActivityLog',
]


class Profile(Base, TimestampMixin):
    """
    User profile model (extends Supabase auth.users).
    
    Synchronized with frontend/lib/db/schema.ts profiles table.
    
    Attributes:
        id: UUID primary key (references auth.users.id)
        email: User email address (unique)
        full_name: User's full name
        avatar_url: URL to user's avatar image
        role: User role (user, admin)
        onboarding_completed: Whether user completed onboarding
        onboarding_completed_at: Timestamp when onboarding was completed
        created_at: Profile creation timestamp
        updated_at: Profile last update timestamp
    
    Relationships:
        projects: User's projects (one-to-many)
        api_keys: User's API keys (one-to-many)
        credit_account: User's credit account (one-to-one)
        notifications: User's notifications (one-to-many)
        notification_preferences: User's notification preferences (one-to-one)
        usage_metrics: User's usage metrics (one-to-many)
        activity_logs: User's activity logs (one-to-many)
    """
    
    __tablename__ = "profiles"
    
    # Primary key (references auth.users.id)
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        comment="References auth.users.id",
    )
    
    # User information
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Role and status
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user",
        server_default="user",
        index=True,
    )
    
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    
    onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    credit_account: Mapped[Optional["CreditAccount"]] = relationship(
        "CreditAccount",
        back_populates="user",
        uselist=False,
        lazy="joined",
    )
    
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    notification_preferences: Mapped[Optional["NotificationPreference"]] = relationship(
        "NotificationPreference",
        uselist=False,
        lazy="joined",
    )
    
    usage_metrics: Mapped[list["UsageMetric"]] = relationship(
        "UsageMetric",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_profiles_email", "email"),
        Index("ix_profiles_role", "role"),
    )


class Project(Base, TimestampMixin):
    """
    Project model for organizing crawl jobs.
    
    Synchronized with frontend/lib/db/schema.ts projects table.
    
    Attributes:
        id: Serial primary key
        name: Project name
        description: Optional project description
        user_id: Reference to profiles.id
        status: Project status (active, archived, deleted)
        created_at: Project creation timestamp
        updated_at: Project last update timestamp
    
    Relationships:
        user: Project owner (many-to-one)
        crawl_jobs: Project's crawl jobs (one-to-many)
    """
    
    __tablename__ = "projects"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    
    # Project information
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )
    
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


class CrawlJob(Base, TimestampMixin):
    """
    Crawl job model for tracking image crawling tasks.
    
    Synchronized with frontend/lib/db/schema.ts crawl_jobs table.
    Includes chunk tracking for distributed processing.
    
    Attributes:
        id: Serial primary key
        project_id: Reference to projects.id
        name: Job name
        keywords: JSON array of search keywords
        max_images: Maximum number of images to collect
        status: Job status (pending, running, completed, failed, cancelled)
        progress: Progress percentage (0-100)
        total_images: Total images found
        downloaded_images: Number of images downloaded
        valid_images: Number of valid images
        total_chunks: Total number of processing chunks
        active_chunks: Number of currently active chunks
        completed_chunks: Number of completed chunks
        failed_chunks: Number of failed chunks
        task_ids: JSON array of Celery task IDs
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        created_at: Job creation timestamp
        updated_at: Job last update timestamp
    
    Relationships:
        project: Parent project (many-to-one)
        images: Crawled images (one-to-many)
        chunks: Processing chunks (one-to-many)
    """
    
    __tablename__ = "crawl_jobs"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    
    # Foreign key
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Job information
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    
    keywords: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        comment="Array of search keywords",
    )
    
    max_images: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        server_default="1000",
    )
    
    # Status and progress
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )
    
    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    # Image counts
    total_images: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    downloaded_images: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    valid_images: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    # Chunk tracking
    total_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    active_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    completed_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    failed_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    task_ids: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
        comment="Array of Celery task IDs",
    )
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
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


class Image(Base):
    """
    Image model for storing crawled image metadata.
    
    Synchronized with frontend/lib/db/schema.ts images table.
    
    Attributes:
        id: Serial primary key
        crawl_job_id: Reference to crawl_jobs.id
        original_url: Original image URL
        filename: Stored filename
        storage_url: Supabase Storage URL
        width: Image width in pixels
        height: Image height in pixels
        file_size: File size in bytes
        format_: Image format (jpg, png, webp, etc.) - mapped to 'format' column
        hash_: Image hash for duplicate detection - mapped to 'hash' column
        is_valid: Whether image passed validation
        is_duplicate: Whether image is a duplicate
        labels: JSON array of AI-generated labels
        metadata: JSON object with additional metadata
        downloaded_at: Download timestamp
        created_at: Record creation timestamp
    
    Relationships:
        crawl_job: Parent crawl job (many-to-one)
    """
    
    __tablename__ = "images"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    
    # Foreign key
    crawl_job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Image URLs
    original_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    storage_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Supabase Storage URL",
    )
    
    # Image properties
    width: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    height: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="File size in bytes",
    )
    
    format_: Mapped[Optional[str]] = mapped_column(
        "format",
        String(10),
        nullable=True,
    )
    
    # Validation and deduplication
    hash_: Mapped[Optional[str]] = mapped_column(
        "hash",
        String(64),
        nullable=True,
        index=True,
        comment="Hash for duplicate detection",
    )
    
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    
    is_duplicate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    
    # Metadata
    labels: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="AI-generated labels",
    )
    
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional image metadata",
    )
    
    # Timestamps
    downloaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    
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
        Index("ix_images_hash", "hash"),  # Column name in database
    )



class ActivityLog(Base):
    """
    Activity log model for tracking user actions.
    
    Synchronized with frontend/lib/db/schema.ts activity_logs table.
    
    Attributes:
        id: Serial primary key
        user_id: Optional reference to profiles.id
        action: Action description
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        metadata: Additional event metadata (JSON)
        timestamp: Event timestamp
    
    Relationships:
        user: User who performed the action (many-to-one)
    """
    
    __tablename__ = "activity_logs"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    
    # Foreign key (optional for system events)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Event details
    action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    
    # Metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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
