"""
System metrics schemas for PixCrawler.

This module defines Pydantic schemas for system and application metrics
collection and retrieval.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    'MetricType',
    'MetricName',
    'TimeWindow',
    'SystemMetricBase',
    'SystemMetricCreate',
    'SystemMetricResponse',
    'SystemMetricQuery',
    'SystemStatusResponse',
    'SystemMetricBatchCreate',
]


class MetricType(str, Enum):
    """Types of metrics that can be collected."""
    PROCESSING_TIME = "processing_time"
    SUCCESS_RATE = "success_rate"
    RESOURCE_USAGE = "resource_usage"
    QUEUE_METRICS = "queue_metrics"
    APPLICATION_METRIC = "application_metric"


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


class TimeWindow(str, Enum):
    """Time windows for metric aggregation."""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class SystemMetricBase(BaseModel):
    """Base schema for system metrics."""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )
    
    metric_type: MetricType = Field(
        description="Type of metric",
        examples=[MetricType.PROCESSING_TIME, MetricType.RESOURCE_USAGE],
    )
    
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Metric name",
        examples=["cpu_usage", "download_time"],
    )
    
    value: float = Field(
        description="Metric value",
        examples=[75.5, 1234.56],
    )
    
    unit: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Unit of measurement",
        examples=["percent", "ms", "bytes"],
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata",
        examples=[{"host": "server1", "region": "us-east-1"}],
    )
    
    service: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Service name that generated the metric",
        examples=["backend", "celery-worker", "api"],
    )
    
    description: Optional[str] = Field(
        default=None,
        description="Metric description",
        examples=["CPU usage percentage for the backend service"],
    )


class SystemMetricCreate(SystemMetricBase):
    """Schema for creating a system metric."""
    
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Metric timestamp (defaults to now if not provided)",
    )


class SystemMetricResponse(SystemMetricBase):
    """Schema for system metric responses."""
    
    id: str = Field(description="Metric ID (UUID)")
    timestamp: datetime = Field(description="Metric timestamp")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class SystemMetricQuery(BaseModel):
    """Query parameters for retrieving metrics."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    metric_type: Optional[MetricType] = Field(
        default=None,
        description="Filter by metric type",
    )
    
    name: Optional[str] = Field(
        default=None,
        description="Filter by metric name",
    )
    
    service: Optional[str] = Field(
        default=None,
        description="Filter by service name",
    )
    
    start_time: Optional[datetime] = Field(
        default=None,
        description="Start time for query range",
    )
    
    end_time: Optional[datetime] = Field(
        default=None,
        description="End time for query range",
    )
    
    time_window: TimeWindow = Field(
        default=TimeWindow.DAY,
        description="Time window for aggregation",
    )
    
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results",
    )


class SystemStatusResponse(BaseModel):
    """Schema for system status response."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    status: str = Field(description="System status", examples=["operational"])
    
    cpu: Dict[str, Any] = Field(
        description="CPU metrics",
        examples=[{
            "percent": 45.2,
            "cores": 4,
            "load_avg": [1.2, 1.5, 1.8]
        }],
    )
    
    memory: Dict[str, Any] = Field(
        description="Memory metrics",
        examples=[{
            "total": 8589934592,
            "available": 4294967296,
            "percent": 50.0,
            "used": 4294967296,
            "free": 4294967296
        }],
    )
    
    disk: Dict[str, Any] = Field(
        description="Disk metrics",
        examples=[{
            "total": 107374182400,
            "used": 53687091200,
            "free": 53687091200,
            "percent": 50.0
        }],
    )
    
    process: Dict[str, Any] = Field(
        description="Process metrics",
        examples=[{
            "pid": 12345,
            "memory_info": {"rss": 104857600, "vms": 209715200},
            "cpu_percent": 2.5
        }],
    )


class SystemMetricBatchCreate(BaseModel):
    """Schema for creating multiple metrics in a batch."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    metrics: List[SystemMetricCreate] = Field(
        min_length=1,
        max_length=100,
        description="List of metrics to create",
    )

