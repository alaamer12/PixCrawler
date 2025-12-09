"""
Metrics repository for database operations.

This module provides repository classes for managing operational metrics
in the database, including processing, resource, and queue metrics.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ProcessingMetric, ResourceMetric, QueueMetric
from .base import BaseRepository

__all__ = [
    'ProcessingMetricRepository',
    'ResourceMetricRepository',
    'QueueMetricRepository',
]


# noinspection PyTypeChecker
class ProcessingMetricRepository(BaseRepository[ProcessingMetric]):
    """Repository for processing metrics operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with session."""
        super().__init__(session, ProcessingMetric)

    async def get_by_job_id(
        self,
        job_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[ProcessingMetric]:
        """
        Get processing metrics for a specific job.

        Args:
            job_id: Crawl job ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of processing metrics
        """
        stmt = (
            select(ProcessingMetric)
            .where(ProcessingMetric.job_id == job_id)
            .order_by(desc(ProcessingMetric.started_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_user_id(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[ProcessingMetric]:
        """
        Get processing metrics for a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of processing metrics
        """
        stmt = (
            select(ProcessingMetric)
            .where(ProcessingMetric.user_id == user_id)
            .order_by(desc(ProcessingMetric.started_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        operation_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[ProcessingMetric]:
        """
        Get processing metrics within a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range
            operation_type: Optional filter by operation type
            status: Optional filter by status
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of processing metrics
        """
        conditions = [
            ProcessingMetric.started_at >= start_time,
            ProcessingMetric.started_at <= end_time,
        ]

        if operation_type:
            conditions.append(ProcessingMetric.operation_type == operation_type)

        if status:
            conditions.append(ProcessingMetric.status == status)

        stmt = (
            select(ProcessingMetric)
            .where(and_(*conditions))
            .order_by(desc(ProcessingMetric.started_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_aggregated_stats(
        self,
        start_time: datetime,
        end_time: datetime,
        operation_type: Optional[str] = None
    ) -> dict:
        """
        Get aggregated statistics for processing metrics.

        Args:
            start_time: Start of time range
            end_time: End of time range
            operation_type: Optional filter by operation type

        Returns:
            Dictionary with aggregated statistics
        """
        conditions = [
            ProcessingMetric.started_at >= start_time,
            ProcessingMetric.started_at <= end_time,
        ]

        if operation_type:
            conditions.append(ProcessingMetric.operation_type == operation_type)

        stmt = select(
            func.count(ProcessingMetric.id).label('total_operations'),
            func.count(ProcessingMetric.id).filter(
                ProcessingMetric.status == 'success'
            ).label('successful_operations'),
            func.count(ProcessingMetric.id).filter(
                ProcessingMetric.status == 'failed'
            ).label('failed_operations'),
            func.avg(ProcessingMetric.duration_ms).label('avg_duration_ms'),
            func.min(ProcessingMetric.duration_ms).label('min_duration_ms'),
            func.max(ProcessingMetric.duration_ms).label('max_duration_ms'),
            func.sum(ProcessingMetric.images_processed).label('total_images_processed'),
            func.sum(ProcessingMetric.images_succeeded).label('total_images_succeeded'),
            func.sum(ProcessingMetric.images_failed).label('total_images_failed'),
        ).where(and_(*conditions))

        result = await self.session.execute(stmt)
        row = result.first()

        if not row:
            return {
                'total_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'avg_duration_ms': 0.0,
                'min_duration_ms': None,
                'max_duration_ms': None,
                'total_images_processed': 0,
                'total_images_succeeded': 0,
                'total_images_failed': 0,
            }

        return {
            'total_operations': row.total_operations or 0,
            'successful_operations': row.successful_operations or 0,
            'failed_operations': row.failed_operations or 0,
            'avg_duration_ms': float(row.avg_duration_ms or 0.0),
            'min_duration_ms': row.min_duration_ms,
            'max_duration_ms': row.max_duration_ms,
            'total_images_processed': row.total_images_processed or 0,
            'total_images_succeeded': row.total_images_succeeded or 0,
            'total_images_failed': row.total_images_failed or 0,
        }


class ResourceMetricRepository(BaseRepository[ResourceMetric]):
    """Repository for resource metrics operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with session."""
        super().__init__(session, ResourceMetric)

    async def get_by_job_id(
        self,
        job_id: int,
        metric_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ResourceMetric]:
        """
        Get resource metrics for a specific job.

        Args:
            job_id: Crawl job ID
            metric_type: Optional filter by metric type
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of resource metrics
        """
        conditions = [ResourceMetric.job_id == job_id]

        if metric_type:
            conditions.append(ResourceMetric.metric_type == metric_type)

        stmt = (
            select(ResourceMetric)
            .where(and_(*conditions))
            .order_by(desc(ResourceMetric.timestamp))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        metric_type: Optional[str] = None,
        hostname: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[ResourceMetric]:
        """
        Get resource metrics within a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range
            metric_type: Optional filter by metric type
            hostname: Optional filter by hostname
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of resource metrics
        """
        conditions = [
            ResourceMetric.timestamp >= start_time,
            ResourceMetric.timestamp <= end_time,
        ]

        if metric_type:
            conditions.append(ResourceMetric.metric_type == metric_type)

        if hostname:
            conditions.append(ResourceMetric.hostname == hostname)

        stmt = (
            select(ResourceMetric)
            .where(and_(*conditions))
            .order_by(desc(ResourceMetric.timestamp))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_average_by_type(
        self,
        start_time: datetime,
        end_time: datetime,
        metric_type: str
    ) -> Optional[float]:
        """
        Get average value for a specific metric type.

        Args:
            start_time: Start of time range
            end_time: End of time range
            metric_type: Metric type to average

        Returns:
            Average value or None
        """
        stmt = select(
            func.avg(ResourceMetric.value)
        ).where(
            and_(
                ResourceMetric.timestamp >= start_time,
                ResourceMetric.timestamp <= end_time,
                ResourceMetric.metric_type == metric_type,
            )
        )
        result = await self.session.execute(stmt)
        avg_value = result.scalar()
        return float(avg_value) if avg_value is not None else None


class QueueMetricRepository(BaseRepository[QueueMetric]):
    """Repository for queue metrics operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with session."""
        super().__init__(session, QueueMetric)

    async def get_by_queue_name(
        self,
        queue_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[QueueMetric]:
        """
        Get queue metrics for a specific queue.

        Args:
            queue_name: Queue name
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of queue metrics
        """
        stmt = (
            select(QueueMetric)
            .where(QueueMetric.queue_name == queue_name)
            .order_by(desc(QueueMetric.timestamp))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        queue_name: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[QueueMetric]:
        """
        Get queue metrics within a time range.

        Args:
            start_time: Start of time range
            end_time: End of time range
            queue_name: Optional filter by queue name
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of queue metrics
        """
        conditions = [
            QueueMetric.timestamp >= start_time,
            QueueMetric.timestamp <= end_time,
        ]

        if queue_name:
            conditions.append(QueueMetric.queue_name == queue_name)

        stmt = (
            select(QueueMetric)
            .where(and_(*conditions))
            .order_by(desc(QueueMetric.timestamp))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_queue(self, queue_name: str) -> Optional[QueueMetric]:
        """
        Get the latest metric for a specific queue.

        Args:
            queue_name: Queue name

        Returns:
            Latest queue metric or None
        """
        stmt = (
            select(QueueMetric)
            .where(QueueMetric.queue_name == queue_name)
            .order_by(desc(QueueMetric.timestamp))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_average_queue_depth(
        self,
        start_time: datetime,
        end_time: datetime,
        queue_name: Optional[str] = None
    ) -> Optional[float]:
        """
        Get average queue depth (total tasks).

        Args:
            start_time: Start of time range
            end_time: End of time range
            queue_name: Optional filter by queue name

        Returns:
            Average queue depth or None
        """
        conditions = [
            QueueMetric.timestamp >= start_time,
            QueueMetric.timestamp <= end_time,
        ]

        if queue_name:
            conditions.append(QueueMetric.queue_name == queue_name)

        stmt = select(
            func.avg(
                QueueMetric.pending_tasks +
                QueueMetric.active_tasks +
                QueueMetric.reserved_tasks
            )
        ).where(and_(*conditions))

        result = await self.session.execute(stmt)
        avg_depth = result.scalar()
        return float(avg_depth) if avg_depth is not None else None
