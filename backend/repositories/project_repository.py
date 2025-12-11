"""
Project repository for data access operations.

This module provides the repository pattern implementation for Project model,
handling all database queries and data access logic.

Classes:
    ProjectRepository: Repository for Project CRUD and queries
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Project
from .base import BaseRepository

__all__ = ['ProjectRepository']


# noinspection PyTypeChecker
class ProjectRepository(BaseRepository[Project]):
    """
    Repository for Project data access.

    Provides database operations for projects including CRUD
    and user-specific filtering.

    Attributes:
        session: Database session
        model: Project model class
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize Project repository.

        Args:
            session: Database session
        """
        super().__init__(session, Project)

    async def get_by_user(self, user_id: UUID) -> List[Project]:
        """
        Get all projects for a specific user.

        Args:
            user_id: User UUID

        Returns:
            List of projects
        """
        result = await self.session.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: str, user_id: Optional[UUID] = None) -> List[Project]:
        """
        Get projects by status, optionally filtered by user.

        Args:
            status: Project status
            user_id: Optional user UUID filter

        Returns:
            List of projects
        """
        query = select(Project).where(Project.status == status)

        if user_id:
            query = query.where(Project.user_id == user_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_projects(self, user_id: UUID) -> List[Project]:
        """
        Get all active projects for a user.

        Args:
            user_id: User UUID

        Returns:
            List of active projects
        """
        return await self.get_by_status("active", user_id)
