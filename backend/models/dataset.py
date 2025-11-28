"""
Dataset model for PixCrawler backend.

This module provides the Dataset SQLAlchemy model for managing
image dataset generation jobs and their metadata.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID as SQLAlchemyUUID

from .base import Base, TimestampMixin

__all__ = ['Dataset']


class Dataset(Base, TimestampMixin):
    """
    Dataset model for image collection jobs.
    
    Represents a dataset generation job that collects images based on
    keywords and search engines. Each dataset is associated with a
    CrawlJob that performs the actual image collection.
    
    Attributes:
        id: Serial primary key
        user_id: UUID reference to profiles.id (FK)
        name: Dataset name
        description: Optional dataset description
        keywords: JSON array of search keywords
        max_images: Maximum number of images to collect
        search_engines: JSON array of search engines to use
        status: Dataset status (pending, processing, completed, failed, cancelled)
        progress: Progress percentage (0-100)
        images_collected: Number of images successfully collected
        crawl_job_id: Reference to associated crawl_jobs.id (FK)
        download_url: URL for downloading completed dataset
        error_message: Error message if processing failed
        
    Relationships:
        user: Profile owner (many-to-one)
        crawl_job: Associated crawl job (one-to-one)
    """
    
    __tablename__ = "datasets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False)
    max_images: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
    )
    search_engines: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    progress: Mapped[float] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    images_collected: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    crawl_job_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    download_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped["Profile"] = relationship(
        "Profile",
        foreign_keys=[user_id],
        lazy="joined",
    )
    crawl_job: Mapped[Optional["CrawlJob"]] = relationship(
        "CrawlJob",
        foreign_keys=[crawl_job_id],
        lazy="joined",
    )
    
    # Indexes and constraints
    __table_args__ = (
        Index("ix_datasets_user_id", "user_id"),
        Index("ix_datasets_status", "status"),
        Index("ix_datasets_user_status", "user_id", "status"),
        Index("ix_datasets_created_at", "created_at"),
        CheckConstraint(
            "progress >= 0 AND progress <= 100",
            name="ck_datasets_progress_range"
        ),
        CheckConstraint(
            "images_collected >= 0",
            name="ck_datasets_images_collected_positive"
        ),
        CheckConstraint(
            "max_images > 0",
            name="ck_datasets_max_images_positive"
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')",
            name="ck_datasets_status_valid"
        ),
    )
