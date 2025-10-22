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

from typing import Annotated, Dict, Any, Optional

from fastapi import Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, get_session

__all__ = [
    'CurrentUser',
    'DBSession',
    'UserID',
    'DatasetID',
    'JobID',
    'ProjectID',
    'ImageID',
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
