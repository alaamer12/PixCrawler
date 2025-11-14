"""
System metrics models for PixCrawler.

This module defines SQLAlchemy ORM models for tracking system and application
metrics like CPU usage, memory usage, processing times, and queue metrics.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
    Index,
    Enum as SQLEnum,
    UUID as SQLAlchemyUUID,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin

__all__ = [
    'MetricType',
    'MetricName',
    'SystemMetric',
]


class MetricType(str):
    """Types of metrics that can be collected."""
    PROCESSING_TIME = "processing_time"
    SUCCESS_RATE = "success_rate"
    RESOURCE_USAGE = "resource_usage"
    QUEUE_METRICS = "queue_metrics"
    APPLICATION_METRIC = "application_metric"


class MetricName(str):
    """Specific metric names."""
    # Processing times
    DOWNLOAD_TIME = "download_time"
    VALIDATION_TIME = "validation_time"
    UPLOAD_TIME = "upload_time"
    TOTAL_PROCESSING_TIME = "total_processing_time"
    
    # Success rates
    DOWNLOAD_SUCCESS = "download_success"
    VALIDATION_SUCCESS = "validation_success"
    UPLOAD_SUCCESS = "upload_success"
    
    # Resource usage
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    
    # Queue metrics
    QUEUE_DEPTH = "queue_depth"
    QUEUE_WAIT_TIME = "queue_wait_time"


class SystemMetric(Base, TimestampMixin):
    """
    System metric model for tracking application and system metrics.
    
    Stores metrics for processing times, success rates, resource usage,
    and queue metrics with metadata and service association.
    
    Attributes:
        id: UUID primary key
        timestamp: Metric timestamp
        metric_type: Type of metric (processing_time, success_rate, etc.)
        name: Specific metric name
        value: Metric value (float)
        unit: Unit of measurement (optional)
        metadata_: Additional metadata (JSONB)
        service: Service name that generated the metric (optional)
        description: Metric description (optional)
    """
    
    __tablename__ = "system_metrics"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    
    # Metric timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Metric type
    metric_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    
    # Metric name
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    
    # Metric value
    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    
    # Unit of measurement
    unit: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    
    # Metadata
    metadata_: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
    )
    
    # Service name
    service: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_system_metrics_timestamp_type", "timestamp", "metric_type"),
        Index("ix_system_metrics_service_name", "service", "name"),
        Index("ix_system_metrics_timestamp_name", "timestamp", "name"),
    )

