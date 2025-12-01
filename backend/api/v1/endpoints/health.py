"""
Health check endpoints with comprehensive system checks.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from backend.core.config import get_settings
from backend.core.database import get_db
from backend.schemas.base import HealthCheck
from celery_core.app import celery_app
from utility.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    tags=["Health"],
)


async def check_database_health(db: AsyncSession) -> Dict[str, Any]:
    """
    Check database connection health.
    
    Args:
        db: Database session
        
    Returns:
        Database health status
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()
        return {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }


async def check_redis_health(redis_url: str) -> Dict[str, Any]:
    """
    Check Redis connection health.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        Redis health status
    """
    try:
        redis_client = await redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        await redis_client.ping()
        await redis_client.close()
        return {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }


def check_celery_health() -> Dict[str, Any]:
    """
    Check Celery worker health.
    
    Returns:
        Celery health status
    """
    try:
        # Get active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            worker_count = len(active_workers)
            return {
                "status": "healthy",
                "message": f"{worker_count} worker(s) active",
                "workers": list(active_workers.keys())
            }
        else:
            return {
                "status": "degraded",
                "message": "No active workers found"
            }
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Celery check failed: {str(e)}"
        }


@router.get(
    "/",
    response_model=HealthCheck,
    summary="Basic Health Check",
    description="Check the basic health and status of the PixCrawler API service.",
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
    Basic health check endpoint.

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


@router.get(
    "/detailed",
    summary="Detailed Health Check",
    description="Comprehensive health check including database, Redis, and Celery workers.",
    response_description="Detailed health status of all system components",
    operation_id="detailedHealthCheck",
    responses={
        200: {
            "description": "Detailed health status",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2024-01-01T00:00:00Z",
                        "version": "1.0.0",
                        "environment": "production",
                        "components": {
                            "database": {
                                "status": "healthy",
                                "message": "Database connection successful"
                            },
                            "redis_cache": {
                                "status": "healthy",
                                "message": "Redis connection successful"
                            },
                            "redis_limiter": {
                                "status": "healthy",
                                "message": "Redis connection successful"
                            },
                            "celery": {
                                "status": "healthy",
                                "message": "2 worker(s) active",
                                "workers": ["worker1@hostname", "worker2@hostname"]
                            }
                        }
                    }
                }
            }
        }
    },
    tags=["Health"],
    include_in_schema=True,
)
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check endpoint.

    Performs comprehensive health checks on all system components:
    - Database connection
    - Redis cache connection
    - Redis rate limiter connection
    - Celery worker availability

    **No Authentication Required**

    Returns:
        Dict: Detailed health status of all components
    """
    settings = get_settings()
    
    # Initialize response
    response = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "environment": settings.environment,
        "components": {}
    }
    
    # Check database
    db_health = await check_database_health(db)
    response["components"]["database"] = db_health
    if db_health["status"] != "healthy":
        response["status"] = "unhealthy"
    
    # Check Redis cache (if enabled)
    if settings.cache.enabled:
        cache_health = await check_redis_health(settings.cache.get_redis_url())
        response["components"]["redis_cache"] = cache_health
        if cache_health["status"] == "unhealthy":
            response["status"] = "degraded" if response["status"] == "healthy" else "unhealthy"
    else:
        response["components"]["redis_cache"] = {
            "status": "disabled",
            "message": "Cache is disabled"
        }
    
    # Check Redis rate limiter (if enabled)
    if settings.rate_limit.enabled:
        limiter_health = await check_redis_health(settings.rate_limit.get_redis_url())
        response["components"]["redis_limiter"] = limiter_health
        if limiter_health["status"] == "unhealthy":
            response["status"] = "degraded" if response["status"] == "healthy" else "unhealthy"
    else:
        response["components"]["redis_limiter"] = {
            "status": "disabled",
            "message": "Rate limiting is disabled"
        }
    
    # Check Celery workers
    celery_health = check_celery_health()
    response["components"]["celery"] = celery_health
    if celery_health["status"] == "unhealthy":
        response["status"] = "degraded" if response["status"] == "healthy" else "unhealthy"
    
    return response