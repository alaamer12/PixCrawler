"""
Project API endpoints.

This module provides the API endpoints for Project management.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, get_session
from backend.api.types import CurrentUser
from backend.api.v1.response_models import get_common_responses
from backend.repositories.project_repository import ProjectRepository
from backend.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from backend.services.project import ProjectService

__all__ = ['router']

router = APIRouter(
    tags=["Projects"],
    responses=get_common_responses(401, 403, 404, 500),
)


async def get_project_service(session = Depends(get_session)) -> ProjectService:
    """Dependency to get ProjectService instance."""
    repository = ProjectRepository(session)
    return ProjectService(repository)


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List Projects",
    description="Get all projects for the current user.",
)
async def list_projects(
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    """
    List all projects.
    
    Args:
        current_user: Current authenticated user
        service: Project service
        
    Returns:
        List of projects
    """
    projects = await service.get_projects(current_user["user_id"])
    
    # Transform to response model (handling Pydantic v2 validation)
    project_responses = [ProjectResponse.model_validate(p) for p in projects]
    
    return ProjectListResponse(
        data=project_responses,
        meta={"total": len(projects)}
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project",
    description="Create a new project.",
)
async def create_project(
    project_in: ProjectCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Create a new project.
    
    Args:
        project_in: Project creation data
        current_user: Current authenticated user
        service: Project service
        
    Returns:
        Created project
    """
    project = await service.create_project(project_in, current_user["user_id"])
    return ProjectResponse.model_validate(project)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get Project",
    description="Get a specific project by ID.",
)
async def get_project(
    project_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Get a project by ID.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        service: Project service
        
    Returns:
        Project details
    """
    project = await service.get_project(project_id, current_user["user_id"])
    return ProjectResponse.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update Project",
    description="Update an existing project.",
)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Update a project.
    
    Args:
        project_id: Project ID
        project_in: Project update data
        current_user: Current authenticated user
        service: Project service
        
    Returns:
        Updated project
    """
    project = await service.update_project(project_id, project_in, current_user["user_id"])
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Project",
    description="Delete a project.",
)
async def delete_project(
    project_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> dict:
    """
    Delete a project.
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user
        service: Project service
        
    Returns:
        Success message
    """
    await service.delete_project(project_id, current_user["user_id"])
    return {"data": None}
