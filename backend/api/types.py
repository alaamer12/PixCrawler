"""
Type aliases for FastAPI route parameters using Annotated.

This module provides reusable type aliases for common FastAPI dependencies,
path parameters, query parameters, and body parameters. Using Annotated with
type aliases improves code reusability, type safety, and IDE support.

Type Aliases:
    CurrentUser: Annotated dependency for current authenticated user
    DBSession: Annotated dependency for async database session
    UserID: Annotated path parameter for user ID
    DatasetID: Annotated path parameter for dataset ID
    JobID: Annotated path parameter for job ID

Best Practices:
    - Use Annotated for all FastAPI parameters (Path, Query, Body, Depends)
    - Create type aliases for frequently used dependencies
    - Add descriptive metadata using Path(), Query(), etc.
    - Improves code reusability and type safety
"""

from typing import Dict, Any, Optional

from fastapi import Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from backend.api.dependencies import (
    get_current_user,
    get_session,
    get_crawl_job_service,
    get_dataset_service,
    get_validation_service,
    get_user_service,
    get_storage_service,
    get_auth_service,
    get_resource_monitor,
    get_metrics_service,
    get_dashboard_service,
)
from backend.services.crawl_job import CrawlJobService
from backend.services.dataset import DatasetService
from backend.services.storage import StorageService
from backend.services.supabase_auth import SupabaseAuthService
from backend.services.user import UserService
from backend.services.validation import ValidationService
from backend.services.resource_monitor import ResourceMonitor
from backend.services.metrics import MetricsService
from backend.services.dashboard import DashboardService

__all__ = [
    # Auth & Session
    'CurrentUser',
    'DBSession',
    # Services
    'CrawlJobServiceDep',
    'DatasetServiceDep',
    'ValidationServiceDep',
    'UserServiceDep',
    'StorageServiceDep',
    'SupabaseAuthServiceDep',
    'ResourceMonitorDep',
    'MetricsServiceDep',
    'DashboardServiceDep',
    # Path Parameters
    'UserID',
    'DatasetID',
    'JobID',
    'ProjectID',
    'ImageID',
    # Query Parameters
    'OptionalQuery',
    'PageQuery',
    'SizeQuery'
]

# ============================================================================
# Dependency Type Aliases
# ============================================================================

CurrentUser = Annotated[
    Dict[str, Any],
    Depends(get_current_user)
]
"""
Current authenticated user dependency.

Automatically injects the authenticated user information from Supabase token.
Raises 401 if authentication fails.

Usage:
    @router.get("/profile")
    async def get_profile(user: CurrentUser):
        return {"user_id": user["user_id"]}
"""

DBSession = Annotated[
    AsyncSession,
    Depends(get_session)
]
"""
Async database session dependency.

Provides an async SQLAlchemy session for database operations.
Automatically handles session lifecycle (commit, rollback, close).

Usage:
    @router.get("/items")
    async def list_items(session: DBSession):
        result = await session.execute(select(Item))
        return result.scalars().all()
"""

# ============================================================================
# Service Type Aliases
# ============================================================================

CrawlJobServiceDep = Annotated[
    CrawlJobService,
    Depends(get_crawl_job_service)
]
"""
CrawlJob service dependency.

Automatically injects CrawlJobService with all required repositories.
Use this instead of manually instantiating the service.

Usage:
    @router.post("/jobs")
    async def create_job(
        job_data: JobCreate,
        service: CrawlJobServiceDep
    ):
        return await service.create_job(...)
"""

DatasetServiceDep = Annotated[
    DatasetService,
    Depends(get_dataset_service)
]
"""
Dataset service dependency.

Automatically injects DatasetService for dataset operations.

Usage:
    @router.post("/datasets")
    async def create_dataset(
        dataset_data: DatasetCreate,
        service: DatasetServiceDep
    ):
        return await service.create_dataset(...)
"""

ValidationServiceDep = Annotated[
    ValidationService,
    Depends(get_validation_service)
]
"""
Validation service dependency.

Automatically injects ValidationService for image validation operations.

Usage:
    @router.post("/validate")
    async def validate_image(
        request: ValidationRequest,
        service: ValidationServiceDep
    ):
        return await service.analyze_single_image(...)
"""

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service)
]
"""
User service dependency.

Automatically injects UserService for user management operations.

Usage:
    @router.get("/users/{user_id}")
    async def get_user(
        user_id: int,
        service: UserServiceDep
    ):
        return await service.get_user_by_id(user_id)
"""

StorageServiceDep = Annotated[
    StorageService,
    Depends(get_storage_service)
]
"""
Storage service dependency.

Automatically injects StorageService for storage operations.

Usage:
    @router.get("/storage/usage")
    async def get_usage(
        service: StorageServiceDep
    ):
        return await service.get_storage_stats()
"""

SupabaseAuthServiceDep = Annotated[
    SupabaseAuthService,
    Depends(get_auth_service)
]
"""
Supabase Auth service dependency.

Automatically injects SupabaseAuthService for authentication operations.

Usage:
    @router.post("/sync-profile")
    async def sync_profile(
        current_user: CurrentUser,
        auth_service: SupabaseAuthServiceDep
    ):
        return await auth_service.sync_user_profile(...)
"""

ResourceMonitorDep = Annotated[
    ResourceMonitor,
    Depends(get_resource_monitor)
]
"""
Resource Monitor dependency.

Automatically injects ResourceMonitor for capacity checking operations.

Usage:
    @router.get("/capacity")
    async def get_capacity(
        monitor: ResourceMonitorDep
    ):
        return await monitor.get_capacity_info()
"""

MetricsServiceDep = Annotated[
    MetricsService,
    Depends(get_metrics_service)
]
"""
Metrics service dependency.

Automatically injects MetricsService for operational metrics operations.

Usage:
    @router.get("/metrics/processing")
    async def get_processing_metrics(
        service: MetricsServiceDep
    ):
        return await service.get_processing_metrics(...)
"""

DashboardServiceDep = Annotated[
    DashboardService,
    Depends(get_dashboard_service)
]
"""
Dashboard service dependency.

Automatically injects DashboardService for dashboard statistics aggregation.

Usage:
    @router.get("/dashboard/stats")
    async def get_dashboard_stats(
        service: DashboardServiceDep
    ):
        return await service.get_dashboard_stats(...)
"""


# ============================================================================
# Path Parameter Type Aliases
# ============================================================================

UserID = Annotated[
    int,
    Path(
        title="User ID",
        description="Unique identifier for the user",
        ge=1,
        examples=[1, 42, 123]
    )
]
"""User ID path parameter with validation (must be >= 1)."""

DatasetID = Annotated[
    int,
    Path(
        title="Dataset ID",
        description="Unique identifier for the dataset",
        ge=1,
        examples=[1, 42, 123]
    )
]
"""Dataset ID path parameter with validation (must be >= 1)."""

JobID = Annotated[
    int,
    Path(
        title="Job ID",
        description="Unique identifier for the crawl job",
        ge=1,
        examples=[1, 42, 123]
    )
]
"""Job ID path parameter with validation (must be >= 1)."""

ProjectID = Annotated[
    int,
    Path(
        title="Project ID",
        description="Unique identifier for the project",
        ge=1,
        examples=[1, 42, 123]
    )
]
"""Project ID path parameter with validation (must be >= 1)."""

ImageID = Annotated[
    int,
    Path(
        title="Image ID",
        description="Unique identifier for the image",
        ge=1,
        examples=[1, 42, 123]
    )
]
"""Image ID path parameter with validation (must be >= 1)."""

# ============================================================================
# Query Parameter Type Aliases
# ============================================================================

OptionalQuery = Annotated[
    Optional[str],
    Query(
        title="Search Query",
        description="Optional search query string",
        max_length=200,
        examples=["cats", "machine learning", None]
    )
]
"""Optional query string parameter for search/filtering."""

PageQuery = Annotated[
    int,
    Query(
        title="Page Number",
        description="Page number for pagination (1-indexed)",
        ge=1,
        le=10000,
        examples=[1, 2, 10]
    )
]
"""Page number query parameter (handled by fastapi-pagination automatically)."""

SizeQuery = Annotated[
    int,
    Query(
        title="Page Size",
        description="Number of items per page",
        ge=1,
        le=100,
        examples=[10, 20, 50]
    )
]
"""Page size query parameter (handled by fastapi-pagination automatically)."""
