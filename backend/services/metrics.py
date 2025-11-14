"""
Metrics service for collecting and retrieving system and application metrics.

This module provides services for tracking system metrics like CPU usage,
memory usage, processing times, and queue metrics.
"""

import psutil
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError
from backend.models.metrics import SystemMetric
from backend.schemas.metrics import (
    SystemMetricCreate,
    SystemMetricResponse,
    SystemMetricQuery,
    SystemStatusResponse,
    MetricType,
)
from .base import BaseService

__all__ = [
    'MetricsService',
]


class MetricsService(BaseService):
    """
    Service for collecting and retrieving system metrics.
    
    Provides functionality for creating, querying, and aggregating
    system and application metrics.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize metrics service with database session.
        
        Args:
            session: Async database session
        """
        super().__init__()
        self.session = session
    
    async def create_metric(self, metric_data: SystemMetricCreate) -> SystemMetricResponse:
        """
        Create a new metric entry.
        
        Args:
            metric_data: Metric creation data
            
        Returns:
            Created metric response
        """
        self.log_operation("create_metric", name=metric_data.name, type=metric_data.metric_type)
        
        db_metric = SystemMetric(
            metric_type=metric_data.metric_type.value,
            name=metric_data.name,
            value=metric_data.value,
            unit=metric_data.unit,
            metadata_=metric_data.metadata or {},
            service=metric_data.service,
            description=metric_data.description,
            timestamp=metric_data.timestamp or datetime.utcnow(),
        )
        
        self.session.add(db_metric)
        await self.session.commit()
        await self.session.refresh(db_metric)
        
        return SystemMetricResponse.model_validate(db_metric)
    
    async def create_metrics_batch(
        self,
        metrics: List[SystemMetricCreate]
    ) -> List[SystemMetricResponse]:
        """
        Create multiple metric entries in a single transaction.
        
        Args:
            metrics: List of metric creation data
            
        Returns:
            List of created metric responses
        """
        self.log_operation("create_metrics_batch", count=len(metrics))
        
        db_metrics = []
        for metric_data in metrics:
            db_metric = SystemMetric(
                metric_type=metric_data.metric_type.value,
                name=metric_data.name,
                value=metric_data.value,
                unit=metric_data.unit,
                metadata_=metric_data.metadata or {},
                service=metric_data.service,
                description=metric_data.description,
                timestamp=metric_data.timestamp or datetime.utcnow(),
            )
            db_metrics.append(db_metric)
            self.session.add(db_metric)
        
        await self.session.commit()
        
        # Refresh all metrics
        for db_metric in db_metrics:
            await self.session.refresh(db_metric)
        
        return [SystemMetricResponse.model_validate(m) for m in db_metrics]
    
    async def get_metric_by_id(self, metric_id: UUID) -> Optional[SystemMetricResponse]:
        """
        Get a metric by ID.
        
        Args:
            metric_id: Metric ID
            
        Returns:
            Metric response or None if not found
        """
        result = await self.session.get(SystemMetric, metric_id)
        if not result:
            return None
        return SystemMetricResponse.model_validate(result)
    
    async def get_metrics(self, query: SystemMetricQuery) -> List[SystemMetricResponse]:
        """
        Retrieve metrics based on query parameters.
        
        Args:
            query: Query parameters
            
        Returns:
            List of metric responses
        """
        self.log_operation(
            "get_metrics",
            type=query.metric_type,
            name=query.name,
            service=query.service,
        )
        
        stmt = select(SystemMetric)
        conditions = []
        
        if query.metric_type:
            conditions.append(SystemMetric.metric_type == query.metric_type.value)
        
        if query.name:
            conditions.append(SystemMetric.name == query.name)
        
        if query.service:
            conditions.append(SystemMetric.service == query.service)
        
        if query.start_time:
            conditions.append(SystemMetric.timestamp >= query.start_time)
        
        if query.end_time:
            conditions.append(SystemMetric.timestamp <= query.end_time)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Order by timestamp descending
        stmt = stmt.order_by(SystemMetric.timestamp.desc())
        
        # Limit results
        stmt = stmt.limit(query.limit)
        
        result = await self.session.execute(stmt)
        metrics = result.scalars().all()
        
        return [SystemMetricResponse.model_validate(m) for m in metrics]
    
    async def collect_system_metrics(
        self,
        service_name: str = "backend"
    ) -> List[SystemMetricResponse]:
        """
        Collect and store current system metrics (CPU, memory, disk usage).
        
        Args:
            service_name: Name of the service to associate with the metrics
            
        Returns:
            List of collected metric responses
        """
        self.log_operation("collect_system_metrics", service=service_name)
        
        metrics = []
        timestamp = datetime.utcnow()
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(SystemMetricCreate(
                metric_type=MetricType.RESOURCE_USAGE,
                name="cpu_usage",
                value=float(cpu_percent),
                unit="percent",
                service=service_name,
                description="CPU usage percentage",
                timestamp=timestamp,
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics.append(SystemMetricCreate(
                metric_type=MetricType.RESOURCE_USAGE,
                name="memory_usage",
                value=float(memory.percent),
                unit="percent",
                service=service_name,
                description="Memory usage percentage",
                metadata={
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "free": memory.free,
                },
                timestamp=timestamp,
            ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics.append(SystemMetricCreate(
                metric_type=MetricType.RESOURCE_USAGE,
                name="disk_usage",
                value=float(disk.percent),
                unit="percent",
                service=service_name,
                description="Disk usage percentage",
                metadata={
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                },
                timestamp=timestamp,
            ))
            
            # Process metrics
            process = psutil.Process()
            metrics.append(SystemMetricCreate(
                metric_type=MetricType.RESOURCE_USAGE,
                name="process_memory",
                value=float(process.memory_info().rss),
                unit="bytes",
                service=service_name,
                description="Process memory usage (RSS)",
                timestamp=timestamp,
            ))
            
            metrics.append(SystemMetricCreate(
                metric_type=MetricType.RESOURCE_USAGE,
                name="process_cpu",
                value=float(process.cpu_percent(interval=0.1)),
                unit="percent",
                service=service_name,
                description="Process CPU usage percentage",
                timestamp=timestamp,
            ))
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            raise
        
        return await self.create_metrics_batch(metrics)
    
    async def get_system_status(self) -> SystemStatusResponse:
        """
        Get current system status and resource usage.
        
        Returns:
            System status response with current metrics
        """
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = None
            if hasattr(psutil, 'getloadavg'):
                try:
                    load_avg = list(psutil.getloadavg())
                except (OSError, AttributeError):
                    pass
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            
            # Get process metrics
            process = psutil.Process()
            memory_info = process.memory_info()
            process_cpu = process.cpu_percent(interval=0.1)
            
            return SystemStatusResponse(
                status="operational",
                cpu={
                    "percent": cpu_percent,
                    "cores": cpu_count,
                    "load_avg": load_avg,
                },
                memory={
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free,
                },
                disk={
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent,
                },
                process={
                    "pid": process.pid,
                    "memory_info": {
                        "rss": memory_info.rss,
                        "vms": memory_info.vms,
                    },
                    "cpu_percent": process_cpu,
                },
            )
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            raise

