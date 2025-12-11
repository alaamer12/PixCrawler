"""
Main API router for v1 endpoints.

This module aggregates all v1 API endpoints and provides a unified router
with consistent configuration, error handling, and OpenAPI documentation.
"""

from fastapi import APIRouter
from starlette.responses import JSONResponse

from backend.api.v1.response_models import get_common_responses
from .endpoints import auth, crawl_jobs, datasets, exports, health, storage, users, validation, projects, notifications, metrics, credits, api_keys, activity, dashboard, batch, policies, simple_flow

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

# Projects - Project management
api_router.include_router(
    projects.router,
    prefix="/projects",
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

# Notifications - User notifications
api_router.include_router(
    notifications.router,
    prefix="/notifications",
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

# Metrics - Operational metrics and monitoring
api_router.include_router(
    metrics.router,
    include_in_schema=True,
)

# Credits - Credit and billing management
api_router.include_router(
    credits.router,
    prefix="/credits",
    include_in_schema=True,
)

# API Keys - API key management
api_router.include_router(
    api_keys.router,
    prefix="/api-keys",
    include_in_schema=True,
)

# Activity Logs - User activity tracking
api_router.include_router(
    activity.router,
    prefix="/activity",
    include_in_schema=True,
)

# Dashboard - Dashboard statistics
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    include_in_schema=True,
)

# Batch Operations
api_router.include_router(
    batch.router,
    prefix="/batch",
    include_in_schema=True,
)

# Policies - Dataset lifecycle policies
api_router.include_router(
    policies.router,
    prefix="/policies",
    include_in_schema=True,
)

# Simple Flow - Standalone flow system (no database dependencies)
api_router.include_router(
    simple_flow.router,
    include_in_schema=True,
)
