"""
Dashboard statistics endpoints.

Provides aggregated statistics for the dashboard overview.
"""

from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.api.types import CurrentUser, DashboardServiceDep
from backend.api.v1.response_models import get_common_responses

__all__ = ['router']

router = APIRouter(
    tags=["Dashboard"],
    responses=get_common_responses(401, 500),
)


class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    
    total_projects: int = Field(
        ...,
        description="Total number of projects owned by the user",
        ge=0,
        examples=[12]
    )
    active_jobs: int = Field(
        ...,
        description="Number of currently active (pending or running) jobs",
        ge=0,
        examples=[3]
    )
    total_datasets: int = Field(
        ...,
        description="Total number of datasets across all projects",
        ge=0,
        examples=[45]
    )
    total_images: int = Field(
        ...,
        description="Total number of images collected",
        ge=0,
        examples=[125000]
    )
    storage_used: str = Field(
        ...,
        description="Total storage used in human-readable format",
        examples=["12.5 GB"]
    )
    processing_speed: str = Field(
        ...,
        description="Average processing speed in images per minute",
        examples=["150/min"]
    )
    credits_remaining: int = Field(
        default=0,
        description="Remaining credits in user account",
        ge=0,
        examples=[5000]
    )


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Get Dashboard Statistics",
    description="Retrieve aggregated statistics for the dashboard overview.",
    response_description="Dashboard statistics including projects, jobs, images, and storage",
    operation_id="getDashboardStats",
    responses={
        200: {
            "description": "Successfully retrieved dashboard statistics",
            "content": {
                "application/json": {
                    "example": {
                        "total_projects": 12,
                        "active_jobs": 3,
                        "total_datasets": 45,
                        "total_images": 125000,
                        "storage_used": "12.5 GB",
                        "processing_speed": "150/min",
                        "credits_remaining": 5000
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def get_dashboard_stats(
    current_user: CurrentUser,
    service: DashboardServiceDep,
) -> DashboardStats:
    """
    Get dashboard statistics for the current user.
    
    Aggregates data from multiple tables to provide overview metrics
    including project count, active jobs, total images, and storage usage.
    
    **Authentication Required:** Bearer token
    
    Args:
        current_user: Current authenticated user (injected)
        service: Dashboard service instance (injected)
        
    Returns:
        Dashboard statistics
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if query fails
    """
    # Get user ID
    user_id = UUID(current_user["user_id"])
    
    # Get statistics
    stats = await service.get_dashboard_stats(user_id)
    
    return DashboardStats(**stats)




