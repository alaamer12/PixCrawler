"""
Metrics endpoints for system and application metrics collection and retrieval.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import DBSession, get_metrics_service
from backend.schemas.metrics import (
    SystemMetricCreate,
    SystemMetricResponse,
    SystemMetricQuery,
    SystemStatusResponse,
    SystemMetricBatchCreate,
    MetricType,
    TimeWindow,
)
from backend.services.metrics import MetricsService
from backend.utils.queue_metrics import track_celery_queue_metrics

router = APIRouter()


@router.post(
    "/",
    response_model=SystemMetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a metric",
    description="Create a new system or application metric entry",
)
async def create_metric(
    metric: SystemMetricCreate,
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> SystemMetricResponse:
    """
    Create a new metric entry.
    
    Args:
        metric: Metric creation data
        metrics_service: Metrics service instance
        
    Returns:
        Created metric response
    """
    return await metrics_service.create_metric(metric)


@router.post(
    "/batch",
    response_model=List[SystemMetricResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create metrics batch",
    description="Create multiple metric entries in a single request",
)
async def create_metrics_batch(
    batch: SystemMetricBatchCreate,
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> List[SystemMetricResponse]:
    """
    Create multiple metric entries in a single request.
    
    Args:
        batch: Batch of metrics to create
        metrics_service: Metrics service instance
        
    Returns:
        List of created metric responses
    """
    return await metrics_service.create_metrics_batch(batch.metrics)


@router.get(
    "/",
    response_model=List[SystemMetricResponse],
    summary="Get metrics",
    description="Retrieve metrics based on query parameters",
)
async def get_metrics(
    metric_type: Optional[MetricType] = None,
    name: Optional[str] = None,
    service: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    time_window: TimeWindow = TimeWindow.DAY,
    limit: int = 100,
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> List[SystemMetricResponse]:
    """
    Retrieve metrics based on query parameters.
    
    Args:
        metric_type: Filter by metric type
        name: Filter by metric name
        service: Filter by service name
        start_time: Start time for query range
        end_time: End time for query range
        time_window: Time window for aggregation
        limit: Maximum number of results (1-1000)
        metrics_service: Metrics service instance
        
    Returns:
        List of metric responses
    """
    query = SystemMetricQuery(
        metric_type=metric_type,
        name=name,
        service=service,
        start_time=start_time,
        end_time=end_time,
        time_window=time_window,
        limit=limit,
    )
    return await metrics_service.get_metrics(query)


@router.get(
    "/{metric_id}",
    response_model=SystemMetricResponse,
    summary="Get metric by ID",
    description="Retrieve a specific metric by its ID",
)
async def get_metric(
    metric_id: UUID,
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> SystemMetricResponse:
    """
    Retrieve a specific metric by ID.
    
    Args:
        metric_id: Metric ID
        metrics_service: Metrics service instance
        
    Returns:
        Metric response
        
    Raises:
        HTTPException: If metric not found
    """
    metric = await metrics_service.get_metric_by_id(metric_id)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric with ID {metric_id} not found",
        )
    return metric


@router.post(
    "/collect",
    response_model=List[SystemMetricResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Collect system metrics",
    description="Collect and store current system metrics (CPU, memory, disk usage)",
)
async def collect_system_metrics(
    service_name: str = "backend",
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> List[SystemMetricResponse]:
    """
    Collect and store current system metrics (CPU, memory, disk usage).
    
    Args:
        service_name: Name of the service to associate with the metrics
        metrics_service: Metrics service instance
        
    Returns:
        List of collected metric responses
    """
    return await metrics_service.collect_system_metrics(service_name=service_name)


@router.get(
    "/system/status",
    response_model=SystemStatusResponse,
    summary="Get system status",
    description="Get current system status and resource usage",
)
async def get_system_status(
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> SystemStatusResponse:
    """
    Get current system status and resource usage.
    
    Args:
        metrics_service: Metrics service instance
        
    Returns:
        System status response with current metrics
    """
    return await metrics_service.get_system_status()


@router.post(
    "/queues/track",
    response_model=List[SystemMetricResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Track queue metrics",
    description="Track Celery queue depth and wait times",
)
async def track_queue_metrics(
    queue_name: str = "celery",
    session: DBSession = None,
) -> List[SystemMetricResponse]:
    """
    Track queue depth and wait times for Celery queues.
    
    Args:
        queue_name: Name of the queue to track
        session: Database session (injected via dependency)
        
    Returns:
        List of created metric responses
    """
    await track_celery_queue_metrics(
        session=session,
        queue_name=queue_name,
        service_name="backend",
    )
    
    # Return empty list for now - the metrics are stored
    return []

