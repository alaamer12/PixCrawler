"""
Metrics collection service for operational monitoring.

This module provides services for collecting, storing, and querying
operational metrics including processing times, resource usage, and queue depths.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

import psutil

from backend.repositories import (
    ProcessingMetricRepository,
    ResourceMetricRepository,
    QueueMetricRepository,
)
from backend.schemas.metrics import (
    ProcessingMetricCreate,
    ProcessingMetricUpdate,
    ProcessingMetricResponse,
    ResourceMetricResponse,
    QueueMetricCreate,
    QueueMetricResponse,
    MetricsSummary,
    PerformanceStats,
)
from .base import BaseService

__all__ = [
    'MetricsService',
]


class MetricsService(BaseService):
    """
    Service for managing operational metrics.

    Provides functionality for collecting, storing, and querying metrics
    related to processing performance, resource usage, and queue status.

    Attributes:
        processing_repo: ProcessingMetric repository
        resource_repo: ResourceMetric repository
        queue_repo: QueueMetric repository
        session: Optional database session
    """

    def __init__(
        self,
        processing_repo: ProcessingMetricRepository,
        resource_repo: ResourceMetricRepository,
        queue_repo: QueueMetricRepository
    ) -> None:
        """
        Initialize metrics service with repositories.

        Args:
            processing_repo: ProcessingMetric repository
            resource_repo: ResourceMetric repository
            queue_repo: QueueMetric repository
        """
        super().__init__()
        self.processing_repo = processing_repo
        self.resource_repo = resource_repo
        self.queue_repo = queue_repo

    # ========================================================================
    # PROCESSING METRICS
    # ========================================================================

    async def start_processing_metric(
        self,
        operation_type: str,
        job_id: Optional[int] = None,
        user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingMetricResponse:
        """
        Start tracking a processing operation.

        Args:
            operation_type: Type of operation (download, validate, upload, full_job)
            job_id: Optional crawl job ID
            user_id: Optional user ID
            metadata: Optional additional metadata

        Returns:
            Created processing metric
        """
        self.log_operation(
            "start_processing_metric",
            operation_type=operation_type,
            job_id=job_id,
            user_id=str(user_id) if user_id else None
        )

        metric_data = ProcessingMetricCreate(
            job_id=job_id,
            user_id=user_id,
            operation_type=operation_type,
            started_at=datetime.utcnow(),
            metadata_=metadata or {}
        )

        metric = await self.processing_repo.create(**metric_data.model_dump())
        return ProcessingMetricResponse.model_validate(metric)

    async def complete_processing_metric(
        self,
        metric_id: UUID,
        status: str,
        images_processed: int = 0,
        images_succeeded: int = 0,
        images_failed: int = 0,
        error_details: Optional[Dict[str, Any]] = None
    ) -> ProcessingMetricResponse:
        """
        Complete a processing operation and update metrics.

        Args:
            metric_id: Processing metric ID
            status: Final status (success, failed, cancelled)
            images_processed: Number of images processed
            images_succeeded: Number of successful images
            images_failed: Number of failed images
            error_details: Optional error information

        Returns:
            Updated processing metric
        """
        self.log_operation(
            "complete_processing_metric",
            metric_id=str(metric_id),
            status=status,
            images_processed=images_processed
        )

        # Get the metric
        metric = await self.processing_repo.get_by_id(metric_id)
        if not metric:
            raise ValueError(f"Processing metric {metric_id} not found")

        # Calculate duration
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - metric.started_at).total_seconds() * 1000)

        # Update the metric
        update_data = ProcessingMetricUpdate(
            completed_at=completed_at,
            duration_ms=duration_ms,
            status=status,
            images_processed=images_processed,
            images_succeeded=images_succeeded,
            images_failed=images_failed,
            error_details=error_details
        )

        updated_metric = await self.processing_repo.update(
            metric,
            **update_data.model_dump(exclude_none=True)
        )
        return ProcessingMetricResponse.model_validate(updated_metric)

    async def get_processing_metrics(
        self,
        job_id: Optional[int] = None,
        user_id: Optional[UUID] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        operation_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ProcessingMetricResponse]:
        """
        Get processing metrics with optional filters.

        Args:
            job_id: Optional filter by job ID
            user_id: Optional filter by user ID
            start_time: Optional start of time range
            end_time: Optional end of time range
            operation_type: Optional filter by operation type
            status: Optional filter by status
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of processing metrics
        """
        if job_id:
            metrics = await self.processing_repo.get_by_job_id(job_id, limit, offset)
        elif user_id:
            metrics = await self.processing_repo.get_by_user_id(user_id, limit, offset)
        elif start_time and end_time:
            metrics = await self.processing_repo.get_by_time_range(
                start_time, end_time, operation_type, status, limit, offset
            )
        else:
            # Default to last 24 hours
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)
            metrics = await self.processing_repo.get_by_time_range(
                start_time, end_time, operation_type, status, limit, offset
            )

        return [ProcessingMetricResponse.model_validate(m) for m in metrics]

    # ========================================================================
    # RESOURCE METRICS
    # ========================================================================

    async def collect_resource_metrics(
        self,
        job_id: Optional[int] = None,
        hostname: Optional[str] = None
    ) -> List[ResourceMetricResponse]:
        """
        Collect current system resource metrics.

        Args:
            job_id: Optional job ID to associate metrics with
            hostname: Optional hostname (defaults to current host)

        Returns:
            List of collected resource metrics
        """
        self.log_operation("collect_resource_metrics", job_id=job_id, hostname=hostname)

        timestamp = datetime.utcnow()
        collected_metrics = []

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_metric = await self.resource_repo.create(
                job_id=job_id,
                metric_type="cpu",
                timestamp=timestamp,
                value=Decimal(str(cpu_percent)),
                unit="percent",
                hostname=hostname
            )
            collected_metrics.append(ResourceMetricResponse.model_validate(cpu_metric))

            # Memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / (1024 * 1024)
            memory_metric = await self.resource_repo.create(
                job_id=job_id,
                metric_type="memory",
                timestamp=timestamp,
                value=Decimal(str(round(memory_mb, 2))),
                unit="mb",
                hostname=hostname,
                metadata_={
                    "total_mb": round(memory.total / (1024 * 1024), 2),
                    "percent": memory.percent
                }
            )
            collected_metrics.append(ResourceMetricResponse.model_validate(memory_metric))

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_gb = disk.used / (1024 * 1024 * 1024)
            disk_metric = await self.resource_repo.create(
                job_id=job_id,
                metric_type="disk",
                timestamp=timestamp,
                value=Decimal(str(round(disk_gb, 2))),
                unit="gb",
                hostname=hostname,
                metadata_={
                    "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                    "percent": disk.percent
                }
            )
            collected_metrics.append(ResourceMetricResponse.model_validate(disk_metric))

            # Network I/O (if available)
            try:
                net_io = psutil.net_io_counters()
                # Convert bytes to MB
                bytes_sent_mb = net_io.bytes_sent / (1024 * 1024)
                bytes_recv_mb = net_io.bytes_recv / (1024 * 1024)

                network_metric = await self.resource_repo.create(
                    job_id=job_id,
                    metric_type="network",
                    timestamp=timestamp,
                    value=Decimal(str(round(bytes_sent_mb + bytes_recv_mb, 2))),
                    unit="mb",
                    hostname=hostname,
                    metadata_={
                        "bytes_sent_mb": round(bytes_sent_mb, 2),
                        "bytes_recv_mb": round(bytes_recv_mb, 2),
                        "packets_sent": net_io.packets_sent,
                        "packets_recv": net_io.packets_recv
                    }
                )
                collected_metrics.append(ResourceMetricResponse.model_validate(network_metric))
            except Exception as e:
                self.logger.warning(f"Failed to collect network metrics: {e}")

        except Exception as e:
            self.logger.error(f"Error collecting resource metrics: {e}")
            raise

        return collected_metrics

    async def get_resource_metrics(
        self,
        job_id: Optional[int] = None,
        metric_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        hostname: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ResourceMetricResponse]:
        """
        Get resource metrics with optional filters.

        Args:
            job_id: Optional filter by job ID
            metric_type: Optional filter by metric type
            start_time: Optional start of time range
            end_time: Optional end of time range
            hostname: Optional filter by hostname
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of resource metrics
        """
        if job_id:
            metrics = await self.resource_repo.get_by_job_id(job_id, metric_type, limit, offset)
        elif start_time and end_time:
            metrics = await self.resource_repo.get_by_time_range(
                start_time, end_time, metric_type, hostname, limit, offset
            )
        else:
            # Default to last 24 hours
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)
            metrics = await self.resource_repo.get_by_time_range(
                start_time, end_time, metric_type, hostname, limit, offset
            )

        return [ResourceMetricResponse.model_validate(m) for m in metrics]

    # ========================================================================
    # QUEUE METRICS
    # ========================================================================

    async def collect_queue_metrics(
        self,
        queue_name: str,
        pending_tasks: int,
        active_tasks: int,
        reserved_tasks: int = 0,
        failed_tasks: int = 0,
        worker_count: int = 0,
        avg_wait_time_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QueueMetricResponse:
        """
        Collect queue depth and status metrics.

        Args:
            queue_name: Name of the queue
            pending_tasks: Number of pending tasks
            active_tasks: Number of active tasks
            reserved_tasks: Number of reserved tasks
            failed_tasks: Number of failed tasks
            worker_count: Number of active workers
            avg_wait_time_ms: Average task wait time
            metadata: Optional additional metadata

        Returns:
            Created queue metric
        """
        self.log_operation(
            "collect_queue_metrics",
            queue_name=queue_name,
            pending=pending_tasks,
            active=active_tasks,
            workers=worker_count
        )

        metric_data = QueueMetricCreate(
            queue_name=queue_name,
            timestamp=datetime.utcnow(),
            pending_tasks=pending_tasks,
            active_tasks=active_tasks,
            reserved_tasks=reserved_tasks,
            failed_tasks=failed_tasks,
            worker_count=worker_count,
            avg_wait_time_ms=avg_wait_time_ms,
            metadata_=metadata or {}
        )

        metric = await self.queue_repo.create(**metric_data.model_dump())
        return QueueMetricResponse.model_validate(metric)

    async def get_queue_metrics(
        self,
        queue_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[QueueMetricResponse]:
        """
        Get queue metrics with optional filters.

        Args:
            queue_name: Optional filter by queue name
            start_time: Optional start of time range
            end_time: Optional end of time range
            limit: Maximum number of records
            offset: Number of records to skip

        Returns:
            List of queue metrics
        """
        if queue_name and not start_time:
            metrics = await self.queue_repo.get_by_queue_name(queue_name, limit, offset)
        elif start_time and end_time:
            metrics = await self.queue_repo.get_by_time_range(
                start_time, end_time, queue_name, limit, offset
            )
        else:
            # Default to last 24 hours
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=1)
            metrics = await self.queue_repo.get_by_time_range(
                start_time, end_time, queue_name, limit, offset
            )

        return [QueueMetricResponse.model_validate(m) for m in metrics]

    async def get_latest_queue_status(self, queue_name: str) -> Optional[QueueMetricResponse]:
        """
        Get the latest status for a specific queue.

        Args:
            queue_name: Queue name

        Returns:
            Latest queue metric or None
        """
        metric = await self.queue_repo.get_latest_by_queue(queue_name)
        return QueueMetricResponse.model_validate(metric) if metric else None

    # ========================================================================
    # AGGREGATED METRICS
    # ========================================================================

    async def get_metrics_summary(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> MetricsSummary:
        """
        Get comprehensive metrics summary for a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Comprehensive metrics summary
        """
        self.log_operation(
            "get_metrics_summary",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )

        # Get processing stats for each operation type
        operation_types = ["download", "validate", "upload", "full_job"]
        processing_stats = []

        for op_type in operation_types:
            stats = await self.processing_repo.get_aggregated_stats(
                start_time, end_time, op_type
            )
            if stats['total_operations'] > 0:
                processing_stats.append(
                    PerformanceStats(
                        operation_type=op_type,
                        **stats
                    )
                )

        # Get resource averages
        avg_cpu = await self.resource_repo.get_average_by_type(start_time, end_time, "cpu")
        avg_memory = await self.resource_repo.get_average_by_type(start_time, end_time, "memory")
        avg_disk = await self.resource_repo.get_average_by_type(start_time, end_time, "disk")
        avg_network = await self.resource_repo.get_average_by_type(start_time, end_time, "network")

        # Get queue averages
        avg_queue_depth = await self.queue_repo.get_average_queue_depth(start_time, end_time)

        # Calculate job statistics from full_job operations
        full_job_stats = await self.processing_repo.get_aggregated_stats(
            start_time, end_time, "full_job"
        )

        return MetricsSummary(
            start_time=start_time,
            end_time=end_time,
            processing_stats=processing_stats,
            avg_cpu_percent=avg_cpu,
            avg_memory_mb=avg_memory,
            avg_disk_gb=avg_disk,
            avg_network_mbps=avg_network,
            avg_queue_depth=avg_queue_depth,
            total_jobs=full_job_stats['total_operations'],
            successful_jobs=full_job_stats['successful_operations'],
            failed_jobs=full_job_stats['failed_operations']
        )
