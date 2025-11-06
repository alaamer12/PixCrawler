"""
Metrics data models and schemas.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base, TimestampMixin


class MetricType(str, Enum):
    """Types of metrics that can be collected."""
    PROCESSING_TIME = "processing_time"
    SUCCESS_RATE = "success_rate"
    RESOURCE_USAGE = "resource_usage"
    QUEUE_METRICS = "queue_metrics"


class MetricName(str, Enum):
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


class Metric(TimestampMixin, Base):
    """
    Database model for storing metrics data.
    """
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_type = Column(SQLEnum(MetricType), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    metadata_ = Column("metadata", JSONB, default={}, nullable=True)
    service = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)


# Pydantic models for API requests/responses
class MetricBase(BaseModel):
    """Base model for metric data."""
    metric_type: MetricType
    name: str
    value: float
    unit: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    service: Optional[str] = None
    description: Optional[str] = None


class MetricCreate(MetricBase):
    """Schema for creating a new metric entry."""
    pass


class MetricResponse(MetricBase):
    """Schema for returning metric data."""
    id: int
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TimeWindow(str, Enum):
    """Time windows for metric aggregation."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class MetricQuery(BaseModel):
    """Query parameters for retrieving metrics."""
    metric_type: Optional[MetricType] = None
    name: Optional[str] = None
    service: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    time_window: TimeWindow = TimeWindow.DAY
