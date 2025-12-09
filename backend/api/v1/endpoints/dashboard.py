"""
Dashboard statistics endpoints.

Provides aggregated statistics for the dashboard overview.
"""

from uuid import UUID

from fastapi import APIRouter

from backend.api.types import CurrentUser, DashboardServiceDep
from backend.api.v1.response_models import get_common_responses

__all__ = ['router']

from models.dashboard import DashboardStats

router = APIRouter(
    tags=["Dashboard"],
    responses=get_common_responses(401, 500),
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




