"""
Metrics API endpoints for operational monitoring.

This module provides REST API endpoints for accessing operational metrics
including processing times, resource usage, and queue depths.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status

from backend.api.dependencies import get_current_user, get_metrics_service
from backend.api.types import MetricsServiceDep
from backend.schemas.metrics import (
    ProcessingMetricResponse,
    ResourceMetricResponse,
    QueueMetricResponse,
    MetricsSummary,
)

__all__ = ['router']

router = APIRouter(prefix="/metrics", tags=["metrics"])


# ============================================================================
# PROCESSING METRICS ENDPOINTS
# ============================================================================

@router.get(
    "/processing",
    response_model=List[ProcessingMetricResponse],
    summary="Get processing metrics",
    description="Retrieve processing metrics with optional filters for job, user, time range, and operation type"
)
async def get_processing_metrics(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    start_time: Optional[datetime] = Query(None, description="Start of time range (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End of time range (ISO 8601)"),
    operation_type: Optional[str] = Query(
        None,
        description="Filter by operation type",
        regex="^(download|validate|upload|full_job)$"
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status",
        regex="^(running|success|failed|cancelled)$"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(get_current_user),
    service: MetricsServiceDep
) -> List[ProcessingMetricResponse]:
    """
    Get processing metrics with optional filters.
    
    Returns metrics for processing operations including download, validate,
    upload, and full job execution times and success rates.
    """
    try:
        metrics = await service.get_processing_metrics(
            job_id=job_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            operation_type=operation_type,
            status=status,
            limit=limit,
            offset=offset
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve processing metrics: {str(e)}"
        )


# ============================================================================
# RESOURCE METRICS ENDPOINTS
# ============================================================================

@router.get(
    "/resources",
    response_model=List[ResourceMetricResponse],
    summary="Get resource metrics",
    description="Retrieve system resource usage metrics including CPU, memory, disk, and network"
)
async def get_resource_metrics(
    job_id: Optional[int] = Query(None, description="Filter by job ID"),
    metric_type: Optional[str] = Query(
        None,
        description="Filter by metric type",
        regex="^(cpu|memory|disk|network)$"
    ),
    start_time: Optional[datetime] = Query(None, description="Start of time range (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End of time range (ISO 8601)"),
    hostname: Optional[str] = Query(None, description="Filter by hostname"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(get_current_user),
    service: MetricsServiceDep
) -> List[ResourceMetricResponse]:
    """
    Get resource usage metrics.
    
    Returns metrics for system resource consumption including CPU percentage,
    memory usage (MB), disk usage (GB), and network I/O (MB).
    """
    try:
        metrics = await service.get_resource_metrics(
            job_id=job_id,
            metric_type=metric_type,
            start_time=start_time,
            end_time=end_time,
            hostname=hostname,
            limit=limit,
            offset=offset
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resource metrics: {str(e)}"
        )


@router.post(
    "/resources/collect",
    response_model=List[ResourceMetricResponse],
    summary="Collect current resource metrics",
    description="Trigger collection of current system resource metrics",
    status_code=status.HTTP_201_CREATED
)
async def collect_resource_metrics(
    job_id: Optional[int] = Query(None, description="Associate metrics with job ID"),
    hostname: Optional[str] = Query(None, description="Hostname for metrics"),
    current_user: dict = Depends(get_current_user),
    service: MetricsServiceDep
) -> List[ResourceMetricResponse]:
    """
    Collect current system resource metrics.
    
    Triggers immediate collection of CPU, memory, disk, and network metrics.
    """
    try:
        metrics = await service.collect_resource_metrics(
            job_id=job_id,
            hostname=hostname
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect resource metrics: {str(e)}"
        )


# ============================================================================
# QUEUE METRICS ENDPOINTS
# ============================================================================

@router.get(
    "/queue",
    response_model=List[QueueMetricResponse],
    summary="Get queue metrics",
    description="Retrieve task queue depth and status metrics"
)
async def get_queue_metrics(
    queue_name: Optional[str] = Query(None, description="Filter by queue name"),
    start_time: Optional[datetime] = Query(None, description="Start of time range (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End of time range (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: dict = Depends(get_current_user),
    service: MetricsServiceDep
) -> List[QueueMetricResponse]:
    """
    Get queue depth and status metrics.
    
    Returns metrics for task queue including pending, active, and reserved
    task counts, worker count, and average wait times.
    """
    try:
        metrics = await service.get_queue_metrics(
            queue_name=queue_name,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve queue metrics: {str(e)}"
        )


@router.get(
    "/queue/{queue_name}/latest",
    response_model=QueueMetricResponse,
    summary="Get latest queue status",
    description="Retrieve the most recent status for a specific queue"
)
async def get_latest_queue_status(
    queue_name: str,
    current_user: dict = Depends(get_current_user),
    service: MetricsServiceDep
) -> QueueMetricResponse:
    """
    Get the latest status for a specific queue.
    
    Returns the most recent queue metric snapshot including current
    task counts and worker status.
    """
    try:
        metric = await service.get_latest_queue_status(queue_name)
        if not metric:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No metrics found for queue: {queue_name}"
            )
        return metric
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve queue status: {str(e)}"
        )


# ============================================================================
# SUMMARY ENDPOINTS
# ============================================================================

@router.get(
    "/summary",
    response_model=MetricsSummary,
    summary="Get metrics summary",
    description="Retrieve comprehensive metrics summary with aggregated statistics"
)
async def get_metrics_summary(
    start_time: Optional[datetime] = Query(
        None,
        description="Start of time range (ISO 8601). Defaults to 24 hours ago"
    ),
    end_time: Optional[datetime] = Query(
        None,
        description="End of time range (ISO 8601). Defaults to now"
    ),
    current_user: dict = Depends(get_current_user),
    service: MetricsServiceDep
) -> MetricsSummary:
    """
    Get comprehensive metrics summary.
    
    Returns aggregated statistics for processing performance, resource usage,
    and queue status over the specified time range. Defaults to last 24 hours.
    
    Includes:
    - Processing statistics by operation type
    - Average resource usage (CPU, memory, disk, network)
    - Queue depth and worker statistics
    - Overall job success rates
    """
    try:
        # Default to last 24 hours if not specified
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=1)
        
        # Validate time range
        if start_time >= end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_time must be before end_time"
            )
        
        # Limit time range to 30 days
        max_range = timedelta(days=30)
        if (end_time - start_time) > max_range:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time range cannot exceed 30 days"
            )
        
        summary = await service.get_metrics_summary(start_time, end_time)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate metrics summary: {str(e)}"
        )
