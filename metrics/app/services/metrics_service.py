"""
Metrics service for collecting and retrieving system and application metrics.
"""
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException

from app.database import SessionLocal, get_db
from app.models.metrics import (
    Metric, MetricType, MetricName, MetricCreate, 
    MetricResponse, MetricQuery, TimeWindow
)


class MetricsService:
    """Service for collecting and retrieving metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_metric(self, metric_data: MetricCreate) -> MetricResponse:
        """Create a new metric entry."""
        db_metric = Metric(
            metric_type=metric_data.metric_type,
            name=metric_data.name,
            value=metric_data.value,
            unit=metric_data.unit,
            metadata_=metric_data.metadata or {},
            service=metric_data.service,
            description=metric_data.description,
            timestamp=datetime.utcnow()
        )
        
        self.db.add(db_metric)
        self.db.commit()
        self.db.refresh(db_metric)
        
        return MetricResponse.from_orm(db_metric)
    
    async def get_metrics(self, query: MetricQuery) -> List[MetricResponse]:
        """Retrieve metrics based on query parameters."""
        query = self.db.query(Metric)
        
        # Apply filters
        if query.metric_type:
            query = query.filter(Metric.metric_type == query.metric_type)
        if query.name:
            query = query.filter(Metric.name == query.name)
        if query.service:
            query = query.filter(Metric.service == query.service)
        if query.start_time:
            query = query.filter(Metric.timestamp >= query.start_time)
        if query.end_time:
            query = query.filter(Metric.timestamp <= query.end_time)
        
        # Apply time window grouping if needed
        if query.time_window:
            # This is a simplified example - in a real app, you'd use SQL window functions
            # or materialized views for efficient time-based aggregation
            pass
            
        metrics = query.order_by(Metric.timestamp.desc()).all()
        return [MetricResponse.from_orm(metric) for metric in metrics]
    
    async def get_metric_by_id(self, metric_id: int) -> Optional[MetricResponse]:
        """Retrieve a single metric by ID."""
        metric = self.db.query(Metric).filter(Metric.id == metric_id).first()
        if not metric:
            return None
        return MetricResponse.from_orm(metric)
    
    async def collect_system_metrics(self, service_name: str = "system") -> List[MetricResponse]:
        """Collect system-level metrics (CPU, memory, disk, etc.)."""
        metrics = []
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(await self.create_metric(
            MetricCreate(
                metric_type=MetricType.RESOURCE_USAGE,
                name=MetricName.CPU_USAGE,
                value=cpu_percent,
                unit="percent",
                service=service_name,
                description="System CPU usage percentage"
            )
        ))
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics.append(await self.create_metric(
            MetricCreate(
                metric_type=MetricType.RESOURCE_USAGE,
                name=MetricName.MEMORY_USAGE,
                value=memory.percent,
                unit="percent",
                service=service_name,
                description="System memory usage percentage"
            )
        ))
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        metrics.append(await self.create_metric(
            MetricCreate(
                metric_type=MetricType.RESOURCE_USAGE,
                name=MetricName.DISK_USAGE,
                value=disk.percent,
                unit="percent",
                service=service_name,
                description="Root disk usage percentage"
            )
        ))
        
        return metrics
    
    @contextmanager
    def track_processing_time(
        self, 
        metric_name: str, 
        service: str,
        **metadata
    ) -> Generator[None, None, None]:
        """Context manager to track processing time of a block of code.
        
        Example:
            with metrics_service.track_processing_time("process_data", "data_processor"):
                # Code to be timed
                process_data()
        """
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
            self.db.add(Metric(
                metric_type=MetricType.PROCESSING_TIME,
                name=metric_name,
                value=elapsed,
                unit="ms",
                service=service,
                metadata_=metadata,
                timestamp=datetime.utcnow()
            ))
            self.db.commit()
    
    async def track_success(
        self, 
        success: bool, 
        operation: str,
        service: str,
        **metadata
    ) -> MetricResponse:
        """Track success/failure of an operation."""
        return await self.create_metric(
            MetricCreate(
                metric_type=MetricType.SUCCESS_RATE,
                name=operation,
                value=1.0 if success else 0.0,
                unit="boolean",
                service=service,
                metadata=metadata,
                description=f"Success status of {operation} operation"
            )
        )
    
    async def track_queue_metrics(
        self,
        queue_name: str,
        depth: int,
        wait_time: Optional[float] = None,
        service: str = "queue_service",
        **metadata
    ) -> List[MetricResponse]:
        """Track queue metrics (depth and wait time)."""
        metrics = []
        
        # Track queue depth
        metrics.append(await self.create_metric(
            MetricCreate(
                metric_type=MetricType.QUEUE_METRICS,
                name=f"{queue_name}.{MetricName.QUEUE_DEPTH}",
                value=depth,
                unit="items",
                service=service,
                metadata=metadata,
                description=f"Current depth of {queue_name} queue"
            )
        ))
        
        # Track wait time if provided
        if wait_time is not None:
            metrics.append(await self.create_metric(
                MetricCreate(
                    metric_type=MetricType.QUEUE_METRICS,
                    name=f"{queue_name}.{MetricName.QUEUE_WAIT_TIME}",
                    value=wait_time,
                    unit="seconds",
                    service=service,
                    metadata=metadata,
                    description=f"Average wait time in {queue_name} queue"
                )
            ))
        
        return metrics
