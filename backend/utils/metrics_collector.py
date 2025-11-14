"""
Metrics collection utilities for tracking operational metrics.

This module provides utilities for collecting metrics during processing,
including context managers for timing operations and helpers for tracking
success rates and queue depths.
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.metrics import (
    SystemMetricCreate,
    MetricType,
)
from backend.services.metrics import MetricsService

__all__ = [
    'MetricsCollector',
    'track_processing_time',
    'track_success_rate',
    'track_queue_depth',
]


class MetricsCollector:
    """
    Utility class for collecting operational metrics.
    
    Provides methods for tracking processing times, success rates,
    resource usage, and queue depths during job execution.
    """
    
    def __init__(self, session: AsyncSession, service_name: str = "backend") -> None:
        """
        Initialize metrics collector.
        
        Args:
            session: Database session for storing metrics
            service_name: Name of the service collecting metrics
        """
        self.session = session
        self.service_name = service_name
        self.metrics_service = MetricsService(session)
        self._pending_metrics: List[SystemMetricCreate] = []
    
    async def record_processing_time(
        self,
        operation: str,
        duration_seconds: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record processing time for an operation.
        
        Args:
            operation: Operation name (e.g., "download", "validate", "upload")
            duration_seconds: Duration in seconds
            metadata: Additional metadata
        """
        metric = SystemMetricCreate(
            metric_type=MetricType.PROCESSING_TIME,
            name=f"{operation}_time",
            value=duration_seconds,
            unit="seconds",
            service=self.service_name,
            description=f"Processing time for {operation} operation",
            metadata=metadata or {},
        )
        self._pending_metrics.append(metric)
    
    async def record_success_rate(
        self,
        operation: str,
        success_count: int,
        total_count: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record success rate for an operation.
        
        Args:
            operation: Operation name (e.g., "download", "validate", "upload")
            success_count: Number of successful operations
            total_count: Total number of operations
            metadata: Additional metadata
        """
        if total_count == 0:
            return
        
        success_rate = (success_count / total_count) * 100.0
        
        metric = SystemMetricCreate(
            metric_type=MetricType.SUCCESS_RATE,
            name=f"{operation}_success",
            value=success_rate,
            unit="percent",
            service=self.service_name,
            description=f"Success rate for {operation} operation",
            metadata={
                **(metadata or {}),
                "success_count": success_count,
                "total_count": total_count,
            },
        )
        self._pending_metrics.append(metric)
    
    async def record_queue_depth(
        self,
        queue_name: str,
        depth: int,
        wait_time_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record queue depth and wait time.
        
        Args:
            queue_name: Name of the queue
            depth: Current queue depth
            wait_time_seconds: Average wait time in seconds (optional)
            metadata: Additional metadata
        """
        metric_data = {
            **(metadata or {}),
            "queue_name": queue_name,
        }
        
        # Record queue depth
        depth_metric = SystemMetricCreate(
            metric_type=MetricType.QUEUE_METRICS,
            name="queue_depth",
            value=float(depth),
            unit="count",
            service=self.service_name,
            description=f"Queue depth for {queue_name}",
            metadata=metric_data,
        )
        self._pending_metrics.append(depth_metric)
        
        # Record wait time if provided
        if wait_time_seconds is not None:
            wait_metric = SystemMetricCreate(
                metric_type=MetricType.QUEUE_METRICS,
                name="queue_wait_time",
                value=wait_time_seconds,
                unit="seconds",
                service=self.service_name,
                description=f"Queue wait time for {queue_name}",
                metadata=metric_data,
            )
            self._pending_metrics.append(wait_metric)
    
    @asynccontextmanager
    async def track_operation(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for tracking operation processing time.
        
        Usage:
            async with collector.track_operation("download", {"job_id": 123}):
                # Perform download operation
                pass
        """
        start_time = time.time()
        success = False
        
        try:
            yield
            success = True
        finally:
            duration = time.time() - start_time
            await self.record_processing_time(
                operation=operation,
                duration_seconds=duration,
                metadata={
                    **(metadata or {}),
                    "success": success,
                },
            )
    
    async def flush(self) -> None:
        """
        Flush all pending metrics to the database.
        
        This should be called periodically or at the end of operations
        to ensure all metrics are persisted.
        """
        if not self._pending_metrics:
            return
        
        try:
            await self.metrics_service.create_metrics_batch(self._pending_metrics)
            self._pending_metrics.clear()
        except Exception as e:
            # Log error but don't fail the operation
            # Metrics collection should not break the main workflow
            print(f"Error flushing metrics: {e}")


@asynccontextmanager
async def track_processing_time(
    session: AsyncSession,
    operation: str,
    service_name: str = "backend",
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Context manager for tracking processing time of an operation.
    
    Usage:
        async with track_processing_time(session, "download", metadata={"job_id": 123}):
            # Perform download operation
            pass
    """
    collector = MetricsCollector(session, service_name)
    async with collector.track_operation(operation, metadata):
        yield collector


async def track_success_rate(
    session: AsyncSession,
    operation: str,
    success_count: int,
    total_count: int,
    service_name: str = "backend",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Track success rate for an operation.
    
    Args:
        session: Database session
        operation: Operation name
        success_count: Number of successful operations
        total_count: Total number of operations
        service_name: Service name
        metadata: Additional metadata
    """
    collector = MetricsCollector(session, service_name)
    await collector.record_success_rate(operation, success_count, total_count, metadata)
    await collector.flush()


async def track_queue_depth(
    session: AsyncSession,
    queue_name: str,
    depth: int,
    wait_time_seconds: Optional[float] = None,
    service_name: str = "backend",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Track queue depth and wait time.
    
    Args:
        session: Database session
        queue_name: Queue name
        depth: Queue depth
        wait_time_seconds: Average wait time
        service_name: Service name
        metadata: Additional metadata
    """
    collector = MetricsCollector(session, service_name)
    await collector.record_queue_depth(queue_name, depth, wait_time_seconds, metadata)
    await collector.flush()

