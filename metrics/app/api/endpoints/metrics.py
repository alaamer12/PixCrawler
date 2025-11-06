"""
API endpoints for metrics collection and retrieval.
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.metrics import (
    MetricResponse, MetricCreate, MetricQuery, TimeWindow, MetricType
)
from app.services.metrics_service import MetricsService

router = APIRouter()


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    """Dependency for getting the metrics service."""
    return MetricsService(db)


@router.post("/", response_model=MetricResponse, status_code=status.HTTP_201_CREATED)
async def create_metric(
    metric: MetricCreate,
    metrics_service: MetricsService = Depends(get_metrics_service)
) -> MetricResponse:
    """Create a new metric entry."""
    return await metrics_service.create_metric(metric)


@router.get("/", response_model=List[MetricResponse])
async def get_metrics(
    metric_type: Optional[MetricType] = None,
    name: Optional[str] = None,
    service: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    time_window: TimeWindow = TimeWindow.DAY,
    metrics_service: MetricsService = Depends(get_metrics_service)
) -> List[MetricResponse]:
    """Retrieve metrics based on query parameters."""
    query = MetricQuery(
        metric_type=metric_type,
        name=name,
        service=service,
        start_time=start_time,
        end_time=end_time,
        time_window=time_window
    )
    return await metrics_service.get_metrics(query)


@router.get("/{metric_id}", response_model=MetricResponse)
async def get_metric(
    metric_id: int,
    metrics_service: MetricsService = Depends(get_metrics_service)
) -> MetricResponse:
    """Retrieve a specific metric by ID."""
    metric = await metrics_service.get_metric_by_id(metric_id)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Metric with ID {metric_id} not found"
        )
    return metric


@router.post("/batch", response_model=List[MetricResponse], status_code=status.HTTP_201_CREATED)
async def create_metrics_batch(
    metrics: List[MetricCreate],
    metrics_service: MetricsService = Depends(get_metrics_service)
) -> List[MetricResponse]:
    """Create multiple metric entries in a single request."""
    results = []
    for metric in metrics:
        result = await metrics_service.create_metric(metric)
        results.append(result)
    return results
