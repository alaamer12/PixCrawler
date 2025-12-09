"""
Operational metrics models for PixCrawler.

This module defines SQLAlchemy ORM models for tracking operational metrics
including processing times, success rates, resource usage, and queue depths.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Integer,
    Numeric,
    String,
    func,
    UUID as SQLAlchemyUUID,
    CheckConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

__all__ = [
    'ProcessingMetric',
    'ResourceMetric',
    'QueueMetric',
]


class ProcessingMetric(Base):
    """
    Processing metrics model for tracking job execution performance.
    
    Stores detailed metrics for each processing operation including
    download, validation, and upload times, along with success/failure counts.
    
    Attributes:
        id: UUID primary key
        job_id: Reference to crawl_jobs.id (optional)
        user_id: Reference to profiles.id (optional)
        operation_type: Type of operation (download, validate, upload, full_job)
        started_at: Operation start timestamp
        completed_at: Operation completion timestamp
        duration_ms: Operation duration in milliseconds
        status: Operation status (success, failed, cancelled)
        images_processed: Number of images processed
        images_succeeded: Number of successful images
        images_failed: Number of failed images
        error_details: JSON object with error information
        metadata_: Additional operation metadata (JSON)
        created_at: Creation timestamp
    """
    
    __tablename__ = "processing_metrics"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign keys (optional for aggregated metrics)
    job_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    user_id: Mapped[Optional[UUID]] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Operation details
    operation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type: download, validate, upload, full_job",
    )
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Duration in milliseconds",
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="running",
        index=True,
        comment="Status: running, success, failed, cancelled",
    )
    
    # Processing counts
    images_processed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    images_succeeded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    images_failed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    # Error tracking
    error_details: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Error information and stack traces",
    )
    
    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional operation metadata",
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("images_processed >= 0", name="ck_processing_metrics_images_processed_positive"),
        CheckConstraint("images_succeeded >= 0", name="ck_processing_metrics_images_succeeded_positive"),
        CheckConstraint("images_failed >= 0", name="ck_processing_metrics_images_failed_positive"),
        CheckConstraint("duration_ms >= 0", name="ck_processing_metrics_duration_positive"),
        Index("ix_processing_metrics_job_id", "job_id"),
        Index("ix_processing_metrics_user_id", "user_id"),
        Index("ix_processing_metrics_operation_type", "operation_type"),
        Index("ix_processing_metrics_status", "status"),
        Index("ix_processing_metrics_started_at", "started_at"),
        Index("ix_processing_metrics_created_at", "created_at"),
        Index("ix_processing_metrics_operation_status", "operation_type", "status"),
    )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.images_processed == 0:
            return 0.0
        return round((self.images_succeeded / self.images_processed) * 100, 2)
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.images_processed == 0:
            return 0.0
        return round((self.images_failed / self.images_processed) * 100, 2)


class ResourceMetric(Base):
    """
    Resource usage metrics model for tracking system resources.
    
    Stores resource consumption metrics including CPU, memory, disk usage,
    and network bandwidth for monitoring system health.
    
    Attributes:
        id: UUID primary key
        job_id: Reference to crawl_jobs.id (optional)
        metric_type: Type of resource (cpu, memory, disk, network)
        timestamp: Measurement timestamp
        value: Metric value
        unit: Measurement unit (percent, mb, gb, etc.)
        hostname: Server/worker hostname
        metadata_: Additional resource metadata (JSON)
        created_at: Creation timestamp
    """
    
    __tablename__ = "resource_metrics"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign key (optional)
    job_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("crawl_jobs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    
    # Resource details
    metric_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type: cpu, memory, disk, network",
    )
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    
    value: Mapped[Decimal] = mapped_column(
        Numeric(15, 4),
        nullable=False,
        comment="Metric value",
    )
    
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Unit: percent, mb, gb, mbps, etc.",
    )
    
    hostname: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Server/worker hostname",
    )
    
    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional resource metadata",
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("value >= 0", name="ck_resource_metrics_value_positive"),
        Index("ix_resource_metrics_job_id", "job_id"),
        Index("ix_resource_metrics_metric_type", "metric_type"),
        Index("ix_resource_metrics_timestamp", "timestamp"),
        Index("ix_resource_metrics_hostname", "hostname"),
        Index("ix_resource_metrics_type_timestamp", "metric_type", "timestamp"),
    )


class QueueMetric(Base):
    """
    Queue depth metrics model for tracking task queue status.
    
    Stores queue depth and task distribution metrics for monitoring
    the Celery task queue and worker status.
    
    Attributes:
        id: UUID primary key
        queue_name: Name of the queue
        timestamp: Measurement timestamp
        pending_tasks: Number of pending tasks
        active_tasks: Number of active tasks
        reserved_tasks: Number of reserved tasks
        failed_tasks: Number of failed tasks (in time window)
        worker_count: Number of active workers
        avg_wait_time_ms: Average task wait time in milliseconds
        metadata_: Additional queue metadata (JSON)
        created_at: Creation timestamp
    """
    
    __tablename__ = "queue_metrics"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    
    # Queue details
    queue_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Queue name (e.g., celery, crawl_jobs)",
    )
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    
    # Queue depths
    pending_tasks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Tasks waiting in queue",
    )
    
    active_tasks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Tasks currently executing",
    )
    
    reserved_tasks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Tasks reserved by workers",
    )
    
    failed_tasks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Failed tasks in time window",
    )
    
    # Worker status
    worker_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of active workers",
    )
    
    # Performance metrics
    avg_wait_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Average task wait time in milliseconds",
    )
    
    # Additional metadata
    metadata_: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional queue metadata",
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("pending_tasks >= 0", name="ck_queue_metrics_pending_positive"),
        CheckConstraint("active_tasks >= 0", name="ck_queue_metrics_active_positive"),
        CheckConstraint("reserved_tasks >= 0", name="ck_queue_metrics_reserved_positive"),
        CheckConstraint("failed_tasks >= 0", name="ck_queue_metrics_failed_positive"),
        CheckConstraint("worker_count >= 0", name="ck_queue_metrics_workers_positive"),
        CheckConstraint("avg_wait_time_ms >= 0", name="ck_queue_metrics_wait_time_positive"),
        Index("ix_queue_metrics_queue_name", "queue_name"),
        Index("ix_queue_metrics_timestamp", "timestamp"),
        Index("ix_queue_metrics_queue_timestamp", "queue_name", "timestamp"),
    )
    
    @property
    def total_tasks(self) -> int:
        """Calculate total tasks in queue."""
        return self.pending_tasks + self.active_tasks + self.reserved_tasks
    
    @property
    def queue_utilization(self) -> float:
        """Calculate queue utilization percentage."""
        if self.worker_count == 0:
            return 0.0
        total = self.active_tasks + self.reserved_tasks
        return round((total / self.worker_count) * 100, 2)
