"""
SQLAlchemy database models synchronized with Drizzle schema.

This module provides SQLAlchemy models that mirror the Drizzle schema defined
in the frontend. These models are used by the FastAPI backend to interact with
the shared Supabase PostgreSQL database.

IMPORTANT: These models must be kept in sync with the Drizzle schema in
frontend/lib/db/schema.ts. The Drizzle schema is the source of truth.

Classes:
    Base: Base class for all database models
    TimestampMixin: Mixin for models with timestamp fields
    Profile: User profile model (mirrors Drizzle profiles table)
    Project: Project model (mirrors Drizzle projects table)
    CrawlJob: Crawl job model (mirrors Drizzle crawlJobs table)
    Image: Image model (mirrors Drizzle images table)
    ActivityLog: Activity log model (mirrors Drizzle activityLogs table)

Features:
    - Direct mapping to Supabase PostgreSQL tables
    - Synchronized with frontend Drizzle schema
    - Support for UUID primary keys (Supabase auth integration)
    - JSON field support for complex data structures
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text, func, UUID as SQLAlchemyUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = [
    'Base',
    'TimestampMixin',
    'Profile',
    'Project',
    'CrawlJob',
    'Image',
    'ActivityLog'
]


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class TimestampMixin:
    """
    Mixin for models with timestamp fields.

    Provides created_at and updated_at fields that match the
    Drizzle schema timestamp pattern.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


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
    """

    __tablename__ = "profiles"

    id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")


class Project(Base, TimestampMixin):
    """
    Project model (mirrors Drizzle projects table).

    Projects organize image crawling tasks for users.

    Attributes:
        id: Serial primary key
        name: Project name
        description: Optional project description
        user_id: UUID reference to profiles.id
        status: Project status (default: 'active')
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class CrawlJob(Base, TimestampMixin):
    """
    Crawl job model (mirrors Drizzle crawlJobs table).

    Represents individual image crawling tasks within projects.

    Attributes:
        id: Serial primary key
        project_id: Reference to projects.id
        name: Job name
        keywords: JSON array of search keywords
        max_images: Maximum number of images to collect
        status: Job status (default: 'pending')
        progress: Progress percentage (0-100)
        total_images: Total images found
        downloaded_images: Number of images downloaded
        valid_images: Number of valid images
        started_at: Job start timestamp
        completed_at: Job completion timestamp
    """

    __tablename__ = "crawl_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[dict] = mapped_column(JSONB, nullable=False)
    max_images: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    downloaded_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),
                                                           nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True),
                                                             nullable=True)


class Image(Base):
    """
    Image model (mirrors Drizzle images table).

    Stores metadata for crawled images.

    Attributes:
        id: Serial primary key
        crawl_job_id: Reference to crawl_jobs.id
        original_url: Original image URL
        filename: Stored filename
        storage_url: Supabase Storage URL
        width: Image width in pixels
        height: Image height in pixels
        file_size: File size in bytes
        format: Image format (jpg, png, etc.)
    """

    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_job_id: Mapped[int] = mapped_column(Integer, nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)


class ActivityLog(Base):
    """
    Activity log model (mirrors Drizzle activityLogs table).

    Tracks user actions and system events.

    Attributes:
        id: Serial primary key
        user_id: Optional reference to profiles.id
        action: Action description
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        metadata: Additional event metadata (JSON)
        timestamp: Event timestamp
    """

    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(SQLAlchemyUUID(as_uuid=True),
                                                    nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
