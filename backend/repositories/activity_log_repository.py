"""
ActivityLog repository for data access operations.

This module provides the repository pattern implementation for ActivityLog model,
handling all database queries and data access logic.

Classes:
    ActivityLogRepository: Repository for ActivityLog CRUD and queries
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ActivityLog
from .base import BaseRepository

__all__ = ['ActivityLogRepository']


class ActivityLogRepository(BaseRepository[ActivityLog]):
    """
    Repository for ActivityLog data access.
    
    Provides database operations for activity logs.
    
    Attributes:
        session: Database session
        model: ActivityLog model class
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize ActivityLog repository.
        
        Args:
            session: Database session
        """
        super().__init__(session, ActivityLog)
    
    async def get_by_user(
        self,
        user_id: UUID,
        limit: int = 50
    ) -> List[ActivityLog]:
        """
        Get activity logs for a user.
        
        Args:
            user_id: User UUID
            limit: Maximum number of logs to return
        
        Returns:
            List of activity logs
        """
        result = await self.session.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50
    ) -> List[ActivityLog]:
        """
        Get activity logs for a specific entity.
        
        Args:
            entity_type: Type of entity (e.g., 'project', 'job')
            entity_id: Entity ID
            limit: Maximum number of logs to return
        
        Returns:
            List of activity logs
        """
        result = await self.session.execute(
            select(ActivityLog)
            .where(
                ActivityLog.entity_type == entity_type,
                ActivityLog.entity_id == entity_id
            )
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
