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
    "/",
    response_model=ProjectListResponse,
    summary="List Projects",
    description="Retrieve all projects for the authenticated user with metadata.",
    response_description="List of projects with total count",
    operation_id="listProjects",
    responses={
        200: {
            "description": "Successfully retrieved projects",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "name": "My First Project",
                                "description": "A sample project",
                                "created_at": "2024-01-01T00:00:00Z",
                                "updated_at": "2024-01-01T00:00:00Z"
                            }
                        ],
                        "meta": {"total": 1}
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def list_projects(
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    """
    List all projects for the current user.
    
    Retrieves all projects owned by the authenticated user,
    ordered by creation date descending (most recent first).
    
    **Authentication Required:** Bearer token
    
    Args:
        current_user: Current authenticated user (injected)
        service: Project service instance (injected)
        
    Returns:
        ProjectListResponse with list of projects and total count
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if database query fails
    """
    projects = await service.get_projects(current_user["user_id"])
    
    # Transform to response model (handling Pydantic v2 validation)
    project_responses = [ProjectResponse.model_validate(p) for p in projects]
    
    return ProjectListResponse(
        data=project_responses,
        meta={"total": len(projects)}
    )


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project",
    description="Create a new project for organizing crawl jobs and datasets.",
    response_description="Created project with initial configuration",
    operation_id="createProject",
    responses={
        201: {
            "description": "Project created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "My New Project",
                        "description": "Project for cat images",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 422, 500)
    }
)
async def create_project(
    project_in: ProjectCreate,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Create a new project for the current user.
    
    Projects are used to organize related crawl jobs and datasets.
    Each project can contain multiple crawl jobs and helps maintain
    a logical grouping of related work.
    
    **Authentication Required:** Bearer token
    
    Args:
        project_in: Project creation data (name, description)
        current_user: Current authenticated user (injected)
        service: Project service instance (injected)
        
    Returns:
        ProjectResponse with created project information
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 422 if validation fails
        HTTPException: 500 if project creation fails
    """
    project = await service.create_project(project_in, current_user["user_id"])
    return ProjectResponse.model_validate(project)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get Project",
    description="Retrieve detailed information about a specific project.",
    response_description="Project details with metadata",
    operation_id="getProject",
    responses={
        200: {
            "description": "Successfully retrieved project",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "My Project",
                        "description": "Project description",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_project(
    project_id: int,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Get a project by ID.
    
    Retrieves detailed information about a specific project
    including its name, description, and timestamps.
    
    **Authentication Required:** Bearer token
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user (injected)
        service: Project service instance (injected)
        
    Returns:
        ProjectResponse with project details
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 404 if project not found or access denied
        HTTPException: 500 if database query fails
    """
    project = await service.get_project(project_id, current_user["user_id"])
    return ProjectResponse.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update Project",
    description="Update project information such as name or description.",
    response_description="Updated project information",
    operation_id="updateProject",
    responses={
        200: {
            "description": "Project updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Updated Project Name",
                        "description": "Updated description",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-02T00:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 422, 500)
    }
)
async def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """
    Update a project's information.
    
    Allows partial updates to project fields. Only provided
    fields will be updated, others remain unchanged.
    
    **Authentication Required:** Bearer token
    
    Args:
        project_id: Project ID
        project_in: Project update data (name, description)
        current_user: Current authenticated user (injected)
        service: Project service instance (injected)
        
    Returns:
        ProjectResponse with updated project information
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 404 if project not found or access denied
        HTTPException: 422 if validation fails
        HTTPException: 500 if update fails
    """
    project = await service.update_project(project_id, project_in, current_user["user_id"])
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Project",
    description="Permanently delete a project and all associated crawl jobs.",
    response_description="Deletion confirmation",
    operation_id="deleteProject",
    responses={
        200: {
            "description": "Project deleted successfully",
            "content": {
                "application/json": {
                    "example": {"data": None}
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def delete_project(
    project_id: int,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> dict:
    """
    Delete a project permanently.
    
    Deletes the project and all associated crawl jobs.
    This action cannot be undone.
    
    **Warning:** This will delete all crawl jobs associated with this project.
    
    **Authentication Required:** Bearer token
    
    Args:
        project_id: Project ID
        current_user: Current authenticated user (injected)
        service: Project service instance (injected)
        
    Returns:
        Success confirmation with null data
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 404 if project not found or access denied
        HTTPException: 500 if deletion fails
    """
    await service.delete_project(project_id, current_user["user_id"])
    return {"data": None}
