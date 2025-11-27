"""
Operational metrics schemas for PixCrawler.

This module defines Pydantic schemas for operational metrics
including processing times, resource usage, and queue depths.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

__all__ = [
    'ProcessingMetricCreate',
    'ProcessingMetricUpdate',
    'ProcessingMetricResponse',
    'ResourceMetricCreate',
    'ResourceMetricResponse',
    'QueueMetricCreate',
    'QueueMetricResponse',
    'MetricsSummary',
    'PerformanceStats',
]


# ============================================================================
# PROCESSING METRICS
# ============================================================================

class ProcessingMetricCreate(BaseModel):
    """Schema for creating processing metrics."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    job_id: Optional[int] = Field(default=None, description="Crawl job ID")
    user_id: Optional[UUID] = Field(default=None, description="User ID")
    operation_type: Literal["download", "validate", "upload", "full_job"] = Field(
        description="Type of operation"
    )
    started_at: datetime = Field(description="Operation start timestamp")
    images_processed: int = Field(default=0, ge=0, description="Number of images processed")
    metadata_: Optional[dict] = Field(default=None, description="Additional metadata")


class ProcessingMetricUpdate(BaseModel):
    """Schema for updating processing metrics."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    duration_ms: Optional[int] = Field(default=None, ge=0, description="Duration in milliseconds")
    status: Optional[Literal["running", "success", "failed", "cancelled"]] = Field(
        default=None, description="Operation status"
    )
    images_processed: Optional[int] = Field(default=None, ge=0)
    images_succeeded: Optional[int] = Field(default=None, ge=0)
    images_failed: Optional[int] = Field(default=None, ge=0)
    error_details: Optional[dict] = Field(default=None, description="Error information")
    metadata_: Optional[dict] = Field(default=None, description="Additional metadata")


class ProcessingMetricResponse(BaseModel):
    """Schema for processing metric responses."""
    
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)
    
    id: UUID = Field(description="Metric ID")
    job_id: Optional[int] = Field(description="Crawl job ID")
    user_id: Optional[UUID] = Field(description="User ID")
    operation_type: str = Field(description="Type of operation")
    started_at: datetime = Field(description="Operation start timestamp")
    completed_at: Optional[datetime] = Field(description="Operation completion timestamp")
    duration_ms: Optional[int] = Field(description="Duration in milliseconds")
    status: str = Field(description="Operation status")
    images_processed: int = Field(description="Images processed count")
    images_succeeded: int = Field(description="Images succeeded count")
    images_failed: int = Field(description="Images failed count")
    error_details: Optional[dict] = Field(description="Error information")
    metadata_: Optional[dict] = Field(description="Additional metadata")
    created_at: datetime = Field(description="Creation timestamp")
    
    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.images_processed == 0:
            return 0.0
        return round((self.images_succeeded / self.images_processed) * 100, 2)
    
    @computed_field
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        if self.images_processed == 0:
            return 0.0
        return round((self.images_failed / self.images_processed) * 100, 2)
    
    @computed_field
    @property
    def avg_processing_time_ms(self) -> Optional[float]:
        """Calculate average processing time per image."""
        if self.duration_ms is None or self.images_processed == 0:
            return None
        return round(self.duration_ms / self.images_processed, 2)


# ============================================================================
# RESOURCE METRICS
# ============================================================================

class ResourceMetricCreate(BaseModel):
    """Schema for creating resource metrics."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    job_id: Optional[int] = Field(default=None, description="Crawl job ID")
    metric_type: Literal["cpu", "memory", "disk", "network"] = Field(
        description="Type of resource metric"
    )
    timestamp: datetime = Field(description="Measurement timestamp")
    value: Decimal = Field(ge=Decimal("0.0"), description="Metric value")
    unit: str = Field(description="Measurement unit (percent, mb, gb, mbps, etc.)")
    hostname: Optional[str] = Field(default=None, description="Server/worker hostname")
    metadata_: Optional[dict] = Field(default=None, description="Additional metadata")


class ResourceMetricResponse(BaseModel):
    """Schema for resource metric responses."""
    
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)
    
    id: UUID = Field(description="Metric ID")
    job_id: Optional[int] = Field(description="Crawl job ID")
    metric_type: str = Field(description="Type of resource metric")
    timestamp: datetime = Field(description="Measurement timestamp")
    value: Decimal = Field(description="Metric value")
    unit: str = Field(description="Measurement unit")
    hostname: Optional[str] = Field(description="Server/worker hostname")
    metadata_: Optional[dict] = Field(description="Additional metadata")
    created_at: datetime = Field(description="Creation timestamp")


# ============================================================================
# QUEUE METRICS
# ============================================================================

class QueueMetricCreate(BaseModel):
    """Schema for creating queue metrics."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    queue_name: str = Field(description="Queue name")
    timestamp: datetime = Field(description="Measurement timestamp")
    pending_tasks: int = Field(default=0, ge=0, description="Tasks waiting in queue")
    active_tasks: int = Field(default=0, ge=0, description="Tasks currently executing")
    reserved_tasks: int = Field(default=0, ge=0, description="Tasks reserved by workers")
    failed_tasks: int = Field(default=0, ge=0, description="Failed tasks in time window")
    worker_count: int = Field(default=0, ge=0, description="Number of active workers")
    avg_wait_time_ms: Optional[int] = Field(
        default=None, ge=0, description="Average task wait time in milliseconds"
    )
    metadata_: Optional[dict] = Field(default=None, description="Additional metadata")


class QueueMetricResponse(BaseModel):
    """Schema for queue metric responses."""
    
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)
    
    id: UUID = Field(description="Metric ID")
    queue_name: str = Field(description="Queue name")
    timestamp: datetime = Field(description="Measurement timestamp")
    pending_tasks: int = Field(description="Tasks waiting in queue")
    active_tasks: int = Field(description="Tasks currently executing")
    reserved_tasks: int = Field(description="Tasks reserved by workers")
    failed_tasks: int = Field(description="Failed tasks in time window")
    worker_count: int = Field(description="Number of active workers")
    avg_wait_time_ms: Optional[int] = Field(description="Average task wait time")
    metadata_: Optional[dict] = Field(description="Additional metadata")
    created_at: datetime = Field(description="Creation timestamp")
    
    @computed_field
    @property
    def total_tasks(self) -> int:
        """Calculate total tasks in queue."""
        return self.pending_tasks + self.active_tasks + self.reserved_tasks
    
    @computed_field
    @property
    def queue_utilization(self) -> float:
        """Calculate queue utilization percentage."""
        if self.worker_count == 0:
            return 0.0
        total = self.active_tasks + self.reserved_tasks
        return round((total / self.worker_count) * 100, 2)


# ============================================================================
# AGGREGATED METRICS
# ============================================================================

class PerformanceStats(BaseModel):
    """Schema for aggregated performance statistics."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    operation_type: str = Field(description="Type of operation")
    total_operations: int = Field(ge=0, description="Total number of operations")
    successful_operations: int = Field(ge=0, description="Successful operations")
    failed_operations: int = Field(ge=0, description="Failed operations")
    avg_duration_ms: float = Field(ge=0.0, description="Average duration in milliseconds")
    min_duration_ms: Optional[int] = Field(description="Minimum duration")
    max_duration_ms: Optional[int] = Field(description="Maximum duration")
    total_images_processed: int = Field(ge=0, description="Total images processed")
    total_images_succeeded: int = Field(ge=0, description="Total images succeeded")
    total_images_failed: int = Field(ge=0, description="Total images failed")
    
    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_operations == 0:
            return 0.0
        return round((self.successful_operations / self.total_operations) * 100, 2)
    
    @computed_field
    @property
    def image_success_rate(self) -> float:
        """Calculate image-level success rate."""
        if self.total_images_processed == 0:
            return 0.0
        return round((self.total_images_succeeded / self.total_images_processed) * 100, 2)


class MetricsSummary(BaseModel):
    """Schema for comprehensive metrics summary."""
    
    model_config = ConfigDict(validate_assignment=True)
    
    # Time range
    start_time: datetime = Field(description="Summary start time")
    end_time: datetime = Field(description="Summary end time")
    
    # Processing metrics
    processing_stats: list[PerformanceStats] = Field(
        default_factory=list, description="Performance statistics by operation type"
    )
    
    # Resource metrics
    avg_cpu_percent: Optional[float] = Field(default=None, description="Average CPU usage")
    avg_memory_mb: Optional[float] = Field(default=None, description="Average memory usage")
    avg_disk_gb: Optional[float] = Field(default=None, description="Average disk usage")
    avg_network_mbps: Optional[float] = Field(default=None, description="Average network usage")
    
    # Queue metrics
    avg_queue_depth: Optional[float] = Field(default=None, description="Average queue depth")
    avg_worker_count: Optional[float] = Field(default=None, description="Average worker count")
    avg_wait_time_ms: Optional[float] = Field(default=None, description="Average wait time")
    
    # Overall statistics
    total_jobs: int = Field(default=0, ge=0, description="Total jobs processed")
    successful_jobs: int = Field(default=0, ge=0, description="Successful jobs")
    failed_jobs: int = Field(default=0, ge=0, description="Failed jobs")
    
    @computed_field
    @property
    def job_success_rate(self) -> float:
        """Calculate overall job success rate."""
        if self.total_jobs == 0:
            return 0.0
        return round((self.successful_jobs / self.total_jobs) * 100, 2)
