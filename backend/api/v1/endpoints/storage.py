"""
Storage Management API for PixCrawler
Handles storage operations including usage stats, file info, and cleanup
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.types import StorageServiceDep
from backend.schemas.storage import (
    CleanupRequest,
    CleanupResponse,
    FileInfo,
    StorageUsageResponse,
)
from backend.storage.base import StorageProvider

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])

@router.get("/usage/", response_model=StorageUsageResponse)
async def get_storage_usage(
    service: StorageServiceDep,
):
    """Get storage usage statistics.

    Retrieves comprehensive storage usage information including
    total size, file count, and last update timestamp.

    Args:
        storage: Storage provider instance (injected)

    Returns:
        StorageUsageResponse with detailed storage usage information

    Raises:
        HTTPException: If statistics retrieval fails
    """
    return await service.get_storage_stats()


@router.get("/files/", response_model=List[FileInfo])
async def list_storage_files(
    service: StorageServiceDep,
    prefix: Optional[str] = Query(None, description="Filter files by prefix"),
) -> List[FileInfo]:
    """List files in storage with optional prefix filtering.

    Retrieves a list of all files in storage, optionally filtered
    by a path prefix.

    Args:
        prefix: Optional prefix to filter files by path
        storage: Storage provider instance (injected)

    Returns:
        List of FileInfo objects containing file metadata

    Raises:
        HTTPException: If file listing fails
    """
    return await service.list_files(prefix)


@router.post("/cleanup/", response_model=CleanupResponse)
async def cleanup_storage(
    request: CleanupRequest,
    service: StorageServiceDep,
) -> CleanupResponse:
    """Clean up old files based on specified criteria.

    Deletes files from storage based on age and optional prefix filter,
    freeing up storage space.

    Args:
        request: Cleanup configuration including age threshold and prefix
        storage: Storage provider instance (injected)

    Returns:
        CleanupResponse with cleanup operation results

    Raises:
        HTTPException: If cleanup operation fails
    """
    return await service.cleanup_files(
        age_hours=request.age_hours,
        prefix=request.prefix
    )


@router.get("/presigned-url/")
async def get_presigned_url(
    service: StorageServiceDep,
    path: str = Query(..., description="Path to the file"),
    expires_in: int = Query(3600, description="URL expiration time in seconds"),
) -> Dict[str, Union[str, datetime]]:
    """Generate a presigned URL for temporary file access.

    Creates a time-limited URL that allows temporary access to a file
    without requiring authentication.

    Args:
        path: Path to the file in storage
        expires_in: URL expiration time in seconds (default: 3600)
        storage: Storage provider instance (injected)

    Returns:
        Dictionary containing the presigned URL and expiration timestamp

    Raises:
        HTTPException: If URL generation fails or file not found
    """
    try:
        url = service.storage.generate_presigned_url(path, expires_in=expires_in)
        return {
            "url": url,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )


# Create a test file "test_{name}"
# Test function [case] def test_{name}()
# Put at least one assert statment
