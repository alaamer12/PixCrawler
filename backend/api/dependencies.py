"""
FastAPI dependencies for authentication and authorization.

This module provides FastAPI dependencies for handling authentication,
authorization, and user context throughout the PixCrawler backend API.

Functions:
    get_current_user: Get current authenticated user from Supabase token
    get_current_user_optional: Get current user or None if not authenticated
    get_supabase_auth_service: Get Supabase authentication service instance
    get_session: Get async database session

Features:
    - Supabase JWT token extraction and verification
    - User context injection into API endpoints
    - Optional authentication support
    - Comprehensive error handling
"""
from typing import AsyncGenerator, Generator, Optional, Dict, Any, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import AuthenticationError
from backend.database.connection import get_session as get_db_session
from backend.services.supabase_auth import SupabaseAuthService
from backend.storage.base import StorageProvider
from backend.storage.factory import get_storage_provider
from backend.repositories import (
    CrawlJobRepository,
    ProjectRepository,
    ImageRepository,
    ActivityLogRepository,
    UserRepository
)
from backend.services.crawl_job import CrawlJobService
from backend.services.dataset import DatasetService
from backend.services.validation import ValidationService
from backend.services.user import UserService
from backend.services.storage import StorageService
from backend.services.metrics import MetricsService

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session.

    FastAPI dependency that provides an async SQLAlchemy session
    for database operations.

    Yields:
        AsyncSession: Async database session
    """
    async for session in get_db_session():
        yield session

# Type alias for dependency injection
# DBSession type re-defined here to avoid circular import, it is re-exported from types.py file
# You should use DBSession type from types.py file in your code
DBSession = Annotated[AsyncSession, Depends(get_session)]

__all__ = [
    # Auth dependencies
    'get_current_user',
    'get_current_user_optional',
    'get_supabase_auth_service',
    # Core dependencies
    'get_session',
    'get_storage',
    'DBSession',
    # Repository factories
    'get_crawl_job_repository',
    'get_project_repository',
    'get_image_repository',
    'get_user_repository',
    'get_activity_log_repository',
    # Service dependencies
    'get_crawl_job_service',
    'get_dataset_service',
    'get_validation_service',
    'get_user_service',
    'get_storage_service',
    'get_auth_service',
    'get_metrics_service',
]

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


def get_supabase_auth_service() -> SupabaseAuthService:
    """
    Get Supabase authentication service instance.

    FastAPI dependency that provides a Supabase authentication
    service instance for use in API endpoints.

    Returns:
        SupabaseAuthService instance
    """
    return SupabaseAuthService()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: SupabaseAuthService = Depends(get_supabase_auth_service)
) -> Dict[str, Any]:
    """
    Get current authenticated user from Supabase token.

    FastAPI dependency that extracts and verifies the Supabase JWT token
    from the Authorization header and returns the authenticated user information.

    Args:
        credentials: HTTP Bearer token credentials
        auth_service: Supabase authentication service

    Returns:
        Authenticated user information

    Raises:
        HTTPException: If authentication fails or token is missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_info = await auth_service.verify_token(credentials.credentials)

        # Get user profile from database
        profile = await auth_service.get_user_profile(user_info["user_id"])

        return {
            **user_info,
            "profile": profile
        }

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: SupabaseAuthService = Depends(get_supabase_auth_service)
) -> Optional[Dict[str, Any]]:
    """
    Get current user or None if not authenticated.

    FastAPI dependency that optionally extracts and verifies the Supabase JWT token.
    Returns None if no token is provided or if authentication fails.

    Args:
        credentials: HTTP Bearer token credentials (optional)
        auth_service: Supabase authentication service

    Returns:
        Authenticated user information or None
    """
    if not credentials:
        return None

    try:
        user_info = await auth_service.verify_token(credentials.credentials)

        # Get user profile from database
        profile = await auth_service.get_user_profile(user_info["user_id"])

        return {
            **user_info,
            "profile": profile
        }

    except Exception:
        # Return None for any authentication errors in optional auth
        return None

def get_storage() -> Generator[StorageProvider, None, None]:
    """
    Dependency that returns the configured storage provider.

    Yields:
        StorageProvider: The configured storage provider instance
    """
    storage = get_storage_provider()
    try:
        yield storage
    finally:
        # Add any cleanup if needed
        pass


# Repository Factory Functions
def get_crawl_job_repository(session: DBSession) -> CrawlJobRepository:
    """Get CrawlJobRepository instance."""
    return CrawlJobRepository(session)


def get_project_repository(session: DBSession) -> ProjectRepository:
    """Get ProjectRepository instance."""
    return ProjectRepository(session)


def get_image_repository(session: DBSession) -> ImageRepository:
    """Get ImageRepository instance."""
    return ImageRepository(session)


def get_user_repository(session: DBSession) -> UserRepository:
    """Get UserRepository instance."""
    return UserRepository(session)


def get_activity_log_repository(session: DBSession) -> ActivityLogRepository:
    """Get ActivityLogRepository instance."""
    return ActivityLogRepository(session)


# Service Dependencies
async def get_crawl_job_service(session: DBSession) -> CrawlJobService:
    """
    Dependency injection for CrawlJobService.

    Creates service with all required repositories.

    Args:
        session: Database session

    Returns:
        CrawlJobService instance
    """
    crawl_job_repo = CrawlJobRepository(session)
    project_repo = ProjectRepository(session)
    image_repo = ImageRepository(session)
    activity_log_repo = ActivityLogRepository(session)

    return CrawlJobService(
        crawl_job_repo=crawl_job_repo,
        project_repo=project_repo,
        image_repo=image_repo,
        activity_log_repo=activity_log_repo
    )


def get_dataset_service() -> DatasetService:
    """
    Dependency injection for DatasetService.

    Returns:
        DatasetService instance
    """
    return DatasetService()


def get_validation_service(session: DBSession) -> ValidationService:
    """
    Dependency injection for ValidationService.

    Args:
        session: Database session

    Returns:
        ValidationService instance
    """
    return ValidationService(session)


def get_user_service() -> UserService:
    """
    Dependency injection for UserService.

    Returns:
        UserService instance
    """
    return UserService()


def get_storage_service(storage: StorageProvider = Depends(get_storage)) -> StorageService:
    """
    Dependency injection for StorageService.

    Args:
        storage: Storage provider instance

    Returns:
        StorageService instance
    """
    return StorageService(storage)


def get_auth_service() -> SupabaseAuthService:
    """
    Dependency injection for SupabaseAuthService.

    Returns:
        SupabaseAuthService instance
    """
    return SupabaseAuthService()


def get_metrics_service(session: DBSession) -> MetricsService:
    """
    Dependency injection for MetricsService.

    Args:
        session: Database session

    Returns:
        MetricsService instance
    """
    return MetricsService(session)
