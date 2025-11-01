"""
Health check endpoints.
"""

from datetime import datetime

from fastapi import APIRouter

from backend.core.config import get_settings
from backend.schemas.base import HealthCheck

router = APIRouter(
    tags=["Health"],
)


@router.get(
    "/",
    response_model=HealthCheck,
    summary="Health Check",
    description="Check the health and status of the PixCrawler API service.",
    response_description="Service health status and metadata",
    operation_id="healthCheck",
    responses={
        200: {
            "description": "Service is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "version": "1.0.0",
                        "environment": "production"
                    }
                }
            }
        }
    },
    tags=["Health"],
    include_in_schema=True,
)
async def health_check() -> HealthCheck:
    """
    Health check endpoint.

    Returns the current status and basic information about the API service.
    This endpoint is used by monitoring systems and load balancers to verify
    service availability.

    **No Authentication Required**

    Returns:
        HealthCheck: Service status, version, and environment information
    """
    settings = get_settings()

    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        environment=settings.environment,
    )
