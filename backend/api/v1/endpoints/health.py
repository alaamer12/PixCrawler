"""
Health check endpoints.
"""

from datetime import datetime

from fastapi import APIRouter

from backend.core.config import get_settings
from backend.schemas.base import HealthCheck

router = APIRouter()


@router.get("/", response_model=HealthCheck)
async def health_check() -> HealthCheck:
    """
    Health check endpoint.

    Returns the current status and basic information about the API service.
    """
    settings = get_settings()

    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        environment=settings.environment,
    )
