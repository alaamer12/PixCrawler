"""
Project service for business logic.

This module provides the service layer for Project operations,
coordinating between the API and Repository layers.
"""

from typing import List
from uuid import UUID

from fastapi import HTTPException, status

from backend.models import Project
from backend.repositories.project_repository import ProjectRepository
from backend.schemas.project import ProjectCreate, ProjectUpdate

__all__ = ['ProjectService']


class ProjectService:
    """
    Service for Project business logic.

    Handles project creation, updates, retrieval, and deletion.
    """

    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize Project service.

        Args:
            project_repository: Project repository instance
        """
        self.repository = project_repository

    async def get_projects(self, user_id: UUID) -> List[Project]:
        """
        Get all projects for a user.

        Args:
            user_id: User UUID

        Returns:
            List of projects
        """
        return await self.repository.get_by_user(user_id)

    async def get_project(self, project_id: int, user_id: UUID) -> Project:
        """
        Get a specific project by ID.

        Args:
            project_id: Project ID
            user_id: User UUID

        Returns:
            Project instance

        Raises:
            HTTPException: If project not found or access denied
        """
        project = await self.repository.get(project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if project.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this project"
            )

        return project

    async def create_project(self, project_in: ProjectCreate, user_id: UUID) -> Project:
        """
        Create a new project.

        Args:
            project_in: Project creation data
            user_id: User UUID

        Returns:
            Created project
        """
        project_data = project_in.model_dump()
        project_data["user_id"] = user_id

        return await self.repository.create(project_data)

    async def update_project(
        self,
        project_id: int,
        project_in: ProjectUpdate,
        user_id: UUID
    ) -> Project:
        """
        Update an existing project.

        Args:
            project_id: Project ID
            project_in: Project update data
            user_id: User UUID

        Returns:
            Updated project

        Raises:
            HTTPException: If project not found or access denied
        """
        project = await self.get_project(project_id, user_id)

        update_data = project_in.model_dump(exclude_unset=True)
        if not update_data:
            return project

        return await self.repository.update(project_id, update_data)

    async def delete_project(self, project_id: int, user_id: UUID) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project ID
            user_id: User UUID

        Returns:
            True if deleted

        Raises:
            HTTPException: If project not found or access denied
        """
        # Verify ownership first
        await self.get_project(project_id, user_id)

        return await self.repository.delete(project_id)
