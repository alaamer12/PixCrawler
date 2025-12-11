"""
Notification repository for data access operations.

This module provides the repository pattern implementation for Notification model,
handling all database queries and data access logic.
"""

from typing import List
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Notification
from .base import BaseRepository

__all__ = ['NotificationRepository']


# noinspection PyTypeChecker
class NotificationRepository(BaseRepository[Notification]):
    """
    Repository for Notification data access.

    Provides database operations for notifications including CRUD,
    marking as read, and user-specific filtering.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize Notification repository.

        Args:
            session: Database session
        """
        super().__init__(session, Notification)

    async def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Get notifications for a specific user.

        Args:
            user_id: User UUID
            skip: Pagination skip
            limit: Pagination limit
            unread_only: Filter by unread status

        Returns:
            List of notifications
        """
        query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            query = query.where(Notification.is_read == False)

        query = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User UUID

        Returns:
            Count of unread notifications
        """
        # Note: In a real implementation, we might want to use func.count()
        # But for now, we can reuse the query logic or implement a specific count query
        from sqlalchemy import func
        query = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        result = await self.session.execute(query)
        return result.scalar_one()

    async def count_by_user(self, user_id: UUID, unread_only: bool = False) -> int:
        """
        Get total count of notifications for a user.

        Args:
            user_id: User UUID
            unread_only: Filter by unread status

        Returns:
            Total count of notifications
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.where(Notification.is_read == False)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def mark_as_read(self, notification_id: int, user_id: UUID) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification ID
            user_id: User UUID (for security check)

        Returns:
            True if updated, False otherwise
        """
        from datetime import datetime

        query = (
            update(Notification)
            .where(Notification.id == notification_id, Notification.user_id == user_id)
            .values(is_read=True, read_at=datetime.utcnow())
            .execution_options(synchronize_session=False)
        )

        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0 if result.rawcount else 0

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User UUID

        Returns:
            Number of notifications updated
        """
        from datetime import datetime

        query = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=datetime.utcnow())
            .execution_options(synchronize_session=False)
        )

        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0 if result.rawcount else 0
