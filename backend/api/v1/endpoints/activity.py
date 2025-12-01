"""
Activity log API endpoints.

This module provides API endpoints for activity log management,
including listing and filtering user activity logs.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_session, get_current_user
from backend.api.types import CurrentUser
from backend.api.v1.response_models import get_common_responses
from backend.schemas.activity import (
    ActivityLogResponse,
    ActivityLogListResponse,
)
from backend.services.activity import ActivityLogService

__all__ = ['router']

router = APIRouter(
    tags=["Activity Logs"],
    responses=get_common_responses(401, 500),
)


def get_activity_service(session: AsyncSession = Depends(get_session)) -> ActivityLogService:
    """
    Dependency injection for ActivityLogService.
    
    Args:
        session: Database session (injected by FastAPI)
        
    Returns:
        ActivityLogService instance
    """
    return ActivityLogService(session)


@router.get(
    "/",
    response_model=ActivityLogListResponse,
    summary="List Activity Logs",
    description="Retrieve a paginated list of activity logs for the authenticated user with optional filtering.",
    response_description="Paginated list of activity logs",
    operation_id="listActivityLogs",
    responses={
        200: {
            "description": "Successfully retrieved activity logs",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                                "action": "Created project 'Animals Dataset'",
                                "resource_type": "project",
                                "resource_id": "1",
                                "metadata": {
                                    "project_name": "Animals Dataset",
                                    "description": "Dataset for animal classification"
                                },
                                "timestamp": "2024-01-27T10:00:00Z"
                            },
                            {
                                "id": 2,
                                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                                "action": "Started crawl job",
                                "resource_type": "crawl_job",
                                "resource_id": "5",
                                "metadata": {
                                    "job_name": "Cat Images",
                                    "keywords": ["cats", "kittens"],
                                    "max_images": 1000
                                },
                                "timestamp": "2024-01-27T10:05:00Z"
                            }
                        ],
                        "meta": {
                            "total": 25,
                            "skip": 0,
                            "limit": 50
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def list_activity_logs(
    current_user: CurrentUser,
    service: ActivityLogService = Depends(get_activity_service),
    skip: int = Query(0, ge=0, description="Number of items to skip for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return (max: 100)"),
    resource_type: Optional[str] = Query(
        None,
        description="Filter by resource type (project, crawl_job, dataset, api_key, etc.)"
    ),
) -> ActivityLogListResponse:
    """
    List activity logs for the current user.
    
    Returns a paginated list of all user actions including:
    - Project creation/updates/deletion
    - Crawl job operations
    - Dataset operations
    - API key management
    - Credit transactions
    - And more
    
    Activity logs provide an audit trail of all user actions
    for debugging, compliance, and user transparency.
    
    **Query Parameters:**
    - `skip` (int): Pagination offset (default: 0)
    - `limit` (int): Items per page (default: 50, max: 100)
    - `resource_type` (str): Filter by resource type (optional)
    
    **Authentication Required:** Bearer token
    
    Args:
        current_user: Current authenticated user (injected)
        service: Activity log service instance (injected)
        skip: Number of items to skip
        limit: Maximum items to return
        resource_type: Resource type filter
        
    Returns:
        Paginated list of activity logs
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if query fails
    """
    try:
        user_id = UUID(current_user["user_id"])
        logs, total = await service.list_logs(
            user_id=user_id,
            skip=skip,
            limit=limit,
            resource_type=resource_type,
        )
        
        # Transform to response model
        data = [ActivityLogResponse.model_validate(log) for log in logs]
        
        return ActivityLogListResponse(
            data=data,
            meta={"total": total, "skip": skip, "limit": limit}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve activity logs: {str(e)}"
        )
