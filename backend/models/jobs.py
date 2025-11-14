"""
Job models for PixCrawler (ValidationJob and ExportJob).

This module provides SQLAlchemy ORM models for validation and export jobs,
extending the core crawl job functionality with specialized processing.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text, func, ForeignKey, Index
from sqlalchemy import UUID as SQLAlchemyUUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

__all__ = [
    'ValidationJob',
    'ExportJob',
]


class ValidationJob(Base, TimestampMixin):
    """
    Validation job model for image validation tasks.

    Tracks validation jobs that process and validate images from crawl jobs.

    Attributes:
        id: Serial primary key
        crawl_job_id: Reference to crawl_jobs.id (FK)
        name: Validation job name
        status: Job status (pending, running, completed, failed)
        progress: Progress percentage (0-100)
        total_images: Total images to validate
        validated_images: Number of validated images
        invalid_images: Number of invalid images
        validation_rules: JSON object with validation rules
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        error_message: Error message if failed
        crawl_job: Many-to-one relationship to CrawlJob
    """

    __tablename__ = "validation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validated_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    invalid_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    validation_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_validation_job_status", "status"),
        Index("ix_validation_job_crawl_job_id", "crawl_job_id"),
    )


class ExportJob(Base, TimestampMixin):
    """
    Export job model for dataset export tasks.

    Tracks export jobs that package and export validated images.

    Attributes:
        id: Serial primary key
        crawl_job_id: Reference to crawl_jobs.id (FK)
        user_id: Reference to profiles.id (FK)
        name: Export job name
        status: Job status (pending, running, completed, failed)
        progress: Progress percentage (0-100)
        format: Export format (zip, tar, csv, etc.)
        total_images: Total images to export
        exported_images: Number of exported images
        file_size: Size of exported file in bytes
        download_url: URL to download exported file
        export_options: JSON object with export options
        started_at: Job start timestamp
        completed_at: Job completion timestamp
        expires_at: Timestamp when download link expires
        error_message: Error message if failed
        user: Many-to-one relationship to Profile
    """

    __tablename__ = "export_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="zip")
    total_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    exported_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    export_options: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_export_job_status", "status"),
        Index("ix_export_job_user_id", "user_id"),
        Index("ix_export_job_crawl_job_id", "crawl_job_id"),
    )
