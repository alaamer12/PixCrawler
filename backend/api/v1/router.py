"""
Main API router for v1 endpoints.

This module aggregates all v1 API endpoints and provides a unified router
with consistent configuration, error handling, and OpenAPI documentation.
"""

from fastapi import APIRouter
from starlette.responses import JSONResponse

from backend.api.v1.response_models import get_common_responses
from .endpoints import auth, crawl_jobs, datasets, exports, health, storage, users, validation

__all__ = ['api_router']

# Main v1 API Router with comprehensive configuration
api_router = APIRouter(
    prefix="/api/v1",
    responses=get_common_responses(500),
    default_response_class=JSONResponse,
    redirect_slashes=True,
    include_in_schema=True,
)

# Health Check - Public endpoint (no auth required)
api_router.include_router(
    health.router,
    prefix="/health",
    include_in_schema=True,
)

# Authentication - User authentication and profile management
api_router.include_router(
    auth.router,
    prefix="/auth",
    include_in_schema=True,
)

# Users - User account management (admin)
api_router.include_router(
    users.router,
    prefix="/users",
    include_in_schema=True,
)

# Datasets - Dataset creation and management
api_router.include_router(
    datasets.router,
    prefix="/datasets",
    include_in_schema=True,
)

# Crawl Jobs - Image crawling job management
api_router.include_router(
    crawl_jobs.router,
    prefix="/jobs",
    include_in_schema=True,
)

# Storage - Storage management and file operations
api_router.include_router(
    storage.router,
    prefix="/storage",
    include_in_schema=True,
)

# Exports - Dataset export in various formats
api_router.include_router(
    exports.router,
    prefix="/exports",
    include_in_schema=True,
)

# Validation - Image validation services
api_router.include_router(
    validation.router,
    prefix="/validation",
    include_in_schema=True,
)
