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
from backend.services.resource_monitor import ResourceMonitor
from backend.services.metrics import MetricsService
from backend.services.dashboard import DashboardService
from backend.services.policy import PolicyService
from backend.repositories import ProjectRepository, DatasetRepository
from backend.repositories.policy_repository import (
    ArchivalPolicyRepository,
    CleanupPolicyRepository,
    PolicyExecutionLogRepository
)


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
    'require_admin',
    'require_role',
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
    'get_resource_monitor',
    'get_metrics_service',
    'get_dashboard_service',
    'get_policy_service',
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


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require admin role for endpoint access.

    FastAPI dependency that verifies the current user has admin privileges.
    Raises 403 Forbidden if the user is not an admin.

    Args:
        current_user: Current authenticated user (injected)

    Returns:
        Current user information if admin

    Raises:
        HTTPException: 403 if user is not an admin

    Usage:
        @router.post("/admin/action")
        async def admin_action(admin_user: Annotated[Dict[str, Any], Depends(require_admin)]):
            # Only admins can access this endpoint
            pass
    """
    from backend.core.exceptions import AuthorizationError
    
    # Check if user has admin role
    profile = current_user.get("profile", {})
    role = profile.get("role", "user")
    
    if role not in ["admin", "superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def require_role(
    required_role: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Require specific role for endpoint access.

    FastAPI dependency factory that verifies the current user has the specified role.
    Raises 403 Forbidden if the user doesn't have the required role.

    Args:
        required_role: Role name required (e.g., "admin", "superuser", "user")
        current_user: Current authenticated user (injected)

    Returns:
        Current user information if role matches

    Raises:
        HTTPException: 403 if user doesn't have required role

    Usage:
        @router.post("/moderator/action")
        async def moderator_action(
            user: Annotated[Dict[str, Any], Depends(lambda: require_role("moderator"))]
        ):
            # Only moderators can access this endpoint
            pass
    """
    from backend.core.exceptions import AuthorizationError
    
    # Check if user has required role
    profile = current_user.get("profile", {})
    user_role = profile.get("role", "user")
    
    # Define role hierarchy
    role_hierarchy = {
        "superuser": 3,
        "admin": 2,
        "moderator": 1,
        "user": 0
    }
    
    required_level = role_hierarchy.get(required_role, 0)
    user_level = role_hierarchy.get(user_role, 0)
    
    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{required_role}' or higher required"
        )
    
    return current_user

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


# ============================================================================
# Service Factory Functions
# ============================================================================
# Pattern: get_service(session: DBSession) -> Service
# - Create repository instances from session
# - Inject repositories into service constructor
# - Service receives repositories, NOT session
# ============================================================================

def get_crawl_job_service(session: DBSession) -> CrawlJobService:
    """
    Dependency injection for CrawlJobService.

    Creates service with all required repositories following the pattern:
    get_service(session) -> Service where service receives repositories.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        CrawlJobService instance with injected repositories
    """
    # Create repository instances
    crawl_job_repo = CrawlJobRepository(session)
    project_repo = ProjectRepository(session)
    image_repo = ImageRepository(session)
    activity_log_repo = ActivityLogRepository(session)

    # Inject repositories into service
    return CrawlJobService(
        crawl_job_repo=crawl_job_repo,
        project_repo=project_repo,
        image_repo=image_repo,
        activity_log_repo=activity_log_repo
    )


def get_dataset_service(session: DBSession) -> DatasetService:
    """
    Dependency injection for DatasetService.

    Creates service with all required repositories following the pattern:
    get_service(session) -> Service where service receives repositories.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        DatasetService instance with injected repositories
    """
    from backend.repositories import DatasetRepository

    # Create repository instances
    dataset_repo = DatasetRepository(session)
    crawl_job_repo = CrawlJobRepository(session)

    # Inject repositories into service
    return DatasetService(
        dataset_repository=dataset_repo,
        crawl_job_repository=crawl_job_repo
    )


def get_validation_service(session: DBSession) -> ValidationService:
    """
    Dependency injection for ValidationService.

    Creates service with all required repositories following the pattern:
    get_service(session) -> Service where service receives repositories.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        ValidationService instance with injected repositories
    """
    from backend.repositories import DatasetRepository

    # Create repository instances
    image_repo = ImageRepository(session)
    dataset_repo = DatasetRepository(session)

    # Inject repositories into service
    return ValidationService(
        image_repo=image_repo,
        dataset_repo=dataset_repo
    )


def get_user_service(session: DBSession) -> UserService:
    """
    Dependency injection for UserService.

    Creates service with all required repositories following the pattern:
    get_service(session) -> Service where service receives repositories.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        UserService instance with injected repositories
    """
    # Create repository instance
    user_repo = UserRepository(session)

    # Inject repository into service
    return UserService(user_repository=user_repo)


def get_storage_service(storage: StorageProvider = Depends(get_storage)) -> StorageService:
    """
    Dependency injection for StorageService.

    Creates service with storage provider following the pattern:
    get_service(storage) -> Service where service receives storage provider.

    Args:
        storage: Storage provider instance (injected by FastAPI)

    Returns:
        StorageService instance with injected storage provider
    """
    # Inject storage provider into service
    return StorageService(storage)


def get_auth_service() -> SupabaseAuthService:
    """
    Dependency injection for SupabaseAuthService.

    Creates service instance. This service doesn't require repositories
    as it interacts directly with Supabase API.

    Returns:
        SupabaseAuthService instance
    """
    return SupabaseAuthService()


def get_resource_monitor(session: DBSession) -> ResourceMonitor:
    """
    Dependency injection for ResourceMonitor.

    Creates resource monitor with required repository following the pattern:
    get_monitor(session) -> Monitor where monitor receives repositories.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        ResourceMonitor instance with injected repositories
    """
    # Create repository instance
    crawl_job_repo = CrawlJobRepository(session)

    # Inject repository into monitor
    return ResourceMonitor(crawl_job_repo=crawl_job_repo)


def get_metrics_service(session: DBSession) -> MetricsService:
    """
    Dependency injection for MetricsService.

    Creates service with all required repositories following the pattern:
    get_service(session) -> Service where service receives repositories.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        MetricsService instance with injected repositories
    """
    from backend.repositories import (
        ProcessingMetricRepository,
        ResourceMetricRepository,
        QueueMetricRepository,
    )

    # Create repository instances
    processing_repo = ProcessingMetricRepository(session)
    resource_repo = ResourceMetricRepository(session)
    queue_repo = QueueMetricRepository(session)

    # Inject repositories into service
    return MetricsService(
        processing_repo=processing_repo,
        resource_repo=resource_repo,
        queue_repo=queue_repo
    )


def get_dashboard_service(session: DBSession) -> DashboardService:
    """
    Dependency injection for DashboardService.

    Creates service with all required repositories following the pattern:
    get_service(session) -> Service where service receives repositories.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        DashboardService instance with injected repositories
    """
    # Create repository instances
    project_repo = ProjectRepository(session)
    crawl_job_repo = CrawlJobRepository(session)
    image_repo = ImageRepository(session)

    # Inject repositories into service
    return DashboardService(
        project_repo=project_repo,
        crawl_job_repo=crawl_job_repo,
        image_repo=image_repo
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


def get_api_key_service(session: AsyncSession = Depends(get_session)) -> APIKeyService:
    """
    Dependency injection for APIKeyService.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        APIKeyService instance
    """
    return APIKeyService(session)


def get_credit_service(session: AsyncSession = Depends(get_session)) -> CreditService:
    """
    Dependency injection for CreditService.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        CreditService instance
    """
    return CreditService(session)


def get_project_service(session: AsyncSession = Depends(get_session)) -> ProjectService:
    """
    Dependency injection for ProjectService.

    Creates service with required repository following the pattern:
    get_service(session) -> Service where service receives repository.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        ProjectService instance with injected repository
    """
    # Create repository instance
    repository = ProjectRepository(session)

    # Inject repository into service
    return ProjectService(repository)


def get_policy_service(session: DBSession) -> PolicyService:
    """
    Dependency injection for PolicyService.

    Creates service with all required repositories following the pattern:
    get_service(session) -> Service where service receives repositories.

    Args:
        session: Database session (injected by FastAPI)

    Returns:
        PolicyService instance with injected repositories
    """
    # Create repository instances
    archival_repo = ArchivalPolicyRepository(session)
    cleanup_repo = CleanupPolicyRepository(session)
    execution_log_repo = PolicyExecutionLogRepository(session)

    # Inject repositories into service
    return PolicyService(
        archival_repo=archival_repo,
        cleanup_repo=cleanup_repo,
        execution_log_repo=execution_log_repo
    )
