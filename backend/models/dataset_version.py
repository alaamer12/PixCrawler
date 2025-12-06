"""
Dataset Version model for PixCrawler backend.

This module provides the DatasetVersion SQLAlchemy model for tracking
changes to dataset configurations and metadata over time.
"""

from typing import Optional, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import (
    Integer,
    ForeignKey,
    String,
    Text,
    Index,
    DateTime,
    func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UUID as SQLAlchemyUUID

from .base import Base

__all__ = ['DatasetVersion']


class DatasetVersion(Base):
    """
    Dataset Version model for history tracking.
    
    Represents a snapshot of a dataset's configuration at a specific point in time.
    Created whenever influential parameters (keywords, search engines) change.
    
    Attributes:
        id: Serial primary key
        dataset_id: Reference to parent dataset (FK)
        version_number: Incremental version number for this dataset
        crawl_job_id: Reference to the crawl job executed for this version
        keywords: Snapshot of search keywords
        search_engines: Snapshot of used search engines
        max_images: Snapshot of max images setting
        change_summary: Description of what caused this version creation
        created_at: Version creation timestamp
        created_by: User who triggered the version creation
        
    Relationships:
        dataset: Parent dataset (many-to-one)
        crawl_job: Associated crawl job (one-to-one)
        creator: User who created this version (many-to-one)
    """
    
    __tablename__ = "dataset_versions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Configuration Snapshot
    keywords: Mapped[list] = mapped_column(JSONB, nullable=False)
    search_engines: Mapped[list] = mapped_column(JSONB, nullable=False)
    max_images: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Execution Context
    crawl_job_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Metadata
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Relationships
    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        back_populates="versions"
    )
    crawl_job: Mapped[Optional["CrawlJob"]] = relationship(
        "CrawlJob",
        foreign_keys=[crawl_job_id],
        lazy="joined"
    )
    creator: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        foreign_keys=[created_by],
        lazy="joined"
    )

    __table_args__ = (
        Index("ix_dataset_versions_dataset_version", "dataset_id", "version_number", unique=True),
    )
