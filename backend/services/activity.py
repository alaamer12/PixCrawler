"""
Activity log service for PixCrawler.

This module provides business logic for activity log management,
including listing and filtering activity logs.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ActivityLog
from .base import BaseService

__all__ = ['ActivityLogService']


# noinspection PyTypeChecker
class ActivityLogService(BaseService):
    """
    Service for managing activity logs.

    Handles activity log retrieval and filtering.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize activity log service.

        Args:
            session: Database session
        """
        super().__init__()
        self.session = session

    async def list_logs(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        resource_type: Optional[str] = None,
    ) -> tuple[list[ActivityLog], int]:
        """
        List activity logs for user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            resource_type: Filter by resource type

        Returns:
            Tuple of (logs list, total count)
        """
        # Build query
        query = select(ActivityLog).where(ActivityLog.user_id == user_id)

        if resource_type:
            query = query.where(ActivityLog.resource_type == resource_type)

        # Get total count
        count_query = select(func.count()).select_from(ActivityLog).where(
            ActivityLog.user_id == user_id
        )
        if resource_type:
            count_query = count_query.where(ActivityLog.resource_type == resource_type)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results
        query = query.order_by(ActivityLog.timestamp.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        logs = result.scalars().all()

        return list(logs), total

    async def create_log(
        self,
        user_id: UUID,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ActivityLog:
        """
        Create an activity log entry.

        Args:
            user_id: User ID
            action: Action description
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            metadata: Additional event metadata

        Returns:
            Created activity log
        """
        log = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_=metadata,
        )

        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)

        self.log_operation(
            "create_activity_log",
            user_id=str(user_id),
            action=action,
        )

        return log
