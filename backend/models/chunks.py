"""
Job chunk models for PixCrawler.

This module defines SQLAlchemy ORM models for tracking individual processing
chunks within crawl jobs, enabling fine-grained progress tracking and
distributed processing.
"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Integer,
    String,
    Text,
    CheckConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from database.models import CrawlJob

__all__ = [
    "JobChunk",
]


class JobChunk(Base, TimestampMixin):
    """
    Job chunk model for tracking individual processing chunks.

    Represents a single chunk of work within a crawl job, enabling
    distributed processing and fine-grained progress tracking.

    Attributes:
        id: Serial primary key
        job_id: Reference to crawl_jobs.id
        chunk_index: Sequential chunk number within the job
        status: Chunk status (pending, processing, completed, failed)
        priority: Processing priority (0-10, higher = more urgent)
        image_range: JSON object with start and end image indices
        error_message: Optional error message if chunk failed
        retry_count: Number of retry attempts
        task_id: Celery task ID for this chunk
        created_at: Timestamp when chunk was created
        updated_at: Timestamp when chunk was last updated
    """

    __tablename__ = "job_chunks"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign key
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chunk identification
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Status and priority
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        server_default="5",
    )

    # Image range tracking
    image_range: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="JSON object with 'start' and 'end' image indices",
    )

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # Task tracking
    task_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Relationships
    job: Mapped["CrawlJob"] = relationship(
        "CrawlJob",
        back_populates="chunks",
        lazy="joined",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="ck_job_chunks_status_valid",
        ),
        CheckConstraint("priority >= 0 AND priority <= 10", name="ck_job_chunks_priority_range"),
        CheckConstraint("retry_count >= 0", name="ck_job_chunks_retry_count_positive"),
        Index("ix_job_chunks_job_id", job_id),
        Index("ix_job_chunks_status", status),
        Index("ix_job_chunks_job_status", job_id, status),
        Index("ix_job_chunks_priority_created", priority, "created_at"),
        Index("ix_job_chunks_task_id", task_id),
    )
