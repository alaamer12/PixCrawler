"""
Storage Management API for PixCrawler
Handles storage operations including usage stats, file info, and cleanup
"""

from datetime import datetime
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.api.types import StorageServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.schemas.storage import (
    CleanupRequest,
    CleanupResponse,
    FileInfo,
    StorageUsageResponse,
)

__all__ = ['router']

router = APIRouter(
    tags=["Storage"],
    responses=get_common_responses(401, 500),
)

@router.get(
    "/usage/",
    response_model=StorageUsageResponse,
    summary="Get Storage Usage",
    description="Retrieve detailed storage usage statistics and metrics.",
    response_description="Storage usage breakdown with file counts and sizes",
    operation_id="getStorageUsage",
    responses={
        200: {
            "description": "Successfully retrieved storage usage",
            "content": {
                "application/json": {
                    "example": {
                        "total_size_bytes": 1073741824,
                        "total_files": 1500,
                        "used_percentage": 45.5,
                        "breakdown": {
                            "images": {"count": 1200, "size_bytes": 858993459},
                            "exports": {"count": 300, "size_bytes": 214748365}
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def get_storage_usage(
    service: StorageServiceDep,
) -> StorageUsageResponse:
    """
    Get storage usage statistics.

    Returns detailed information about storage usage including
    total size, file count, and breakdown by type.

    **Authentication Required:** Bearer token

    Args:
        service: Storage service instance (injected)

    Returns:
        StorageUsageResponse with detailed storage usage information

    Raises:
        HTTPException: If statistics retrieval fails
    """
    return await service.get_storage_stats()


@router.get(
    "/files/",
    response_model=List[FileInfo],
    summary="List Storage Files",
    description="List all files in storage with optional path prefix filtering.",
    response_description="List of files with metadata",
    operation_id="listStorageFiles",
    responses={
        200: {
            "description": "Successfully retrieved file list",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "path": "images/dataset-1/img001.jpg",
                            "size_bytes": 524288,
                            "created_at": "2024-01-01T00:00:00Z",
                            "content_type": "image/jpeg"
                        }
                    ]
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def list_storage_files(
    service: StorageServiceDep,
    prefix: Optional[str] = Query(None, description="Filter files by prefix (e.g., 'images/dataset-1/')"),
) -> List[FileInfo]:
    """
    List files in storage with optional prefix filtering.

    Retrieves a list of all files in storage, optionally filtered
    by a path prefix. Useful for browsing specific directories or datasets.

    **Authentication Required:** Bearer token

    Args:
        service: Storage service instance (injected)
        prefix: Optional prefix to filter files by path

    Returns:
        List of file information objects

    Raises:
        HTTPException: If file listing fails
    """
    return await service.list_files(prefix)


@router.post(
    "/cleanup/",
    response_model=CleanupResponse,
    summary="Cleanup Old Files",
    description="Remove old files from storage based on age threshold.",
    response_description="Cleanup results with deleted file count and freed space",
    operation_id="cleanupOldFiles",
    responses={
        200: {
            "description": "Cleanup completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "deleted_count": 150,
                        "freed_bytes": 157286400,
                        "duration_seconds": 2.5
                    }
                }
            }
        },
        **get_common_responses(401, 422, 500)
    }
)
async def cleanup_old_files(
    request: CleanupRequest,
    service: StorageServiceDep,
) -> CleanupResponse:
    """
    Clean up old files from storage.

    Removes files older than the specified age threshold.
    Useful for managing storage space and removing temporary files.

    **Warning:** This operation is permanent and cannot be undone.

    **Authentication Required:** Bearer token with admin privileges

    Args:
        request: Cleanup configuration (age threshold, prefix filter)
        service: Storage service instance (injected)

    Returns:
        CleanupResponse with count of deleted files and freed space

    Raises:
        HTTPException: If cleanup operation fails
    """
    return await service.cleanup_files(
        age_hours=request.age_hours,
        prefix=request.prefix
    )


@router.get(
    "/presigned-url/",
    summary="Generate Presigned URL",
    description="Create a temporary presigned URL for secure file access.",
    response_description="Presigned URL with expiration timestamp",
    operation_id="generatePresignedUrl",
    responses={
        200: {
            "description": "Presigned URL generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "url": "https://storage.example.com/file.jpg?token=abc123&expires=1234567890",
                        "expires_at": "2024-01-01T01:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_presigned_url(
    service: StorageServiceDep,
    path: str = Query(..., description="Path to the file in storage (e.g., 'images/dataset-1/img001.jpg')"),
    expires_in: int = Query(3600, ge=60, le=86400, description="URL expiration time in seconds (60-86400)"),
) -> Dict[str, Union[str, datetime]]:
    """
    Generate a presigned URL for temporary file access.

    Creates a time-limited URL that allows temporary access to a file
    without requiring authentication. Useful for sharing files or
    allowing temporary downloads.

    **Authentication Required:** Bearer token

    **Expiration Range:** 60 seconds (1 minute) to 86400 seconds (24 hours)

    Args:
        service: Storage service instance (injected)
        path: Path to the file in storage
        expires_in: URL expiration time in seconds (default: 3600 = 1 hour)

    Returns:
        Dictionary containing the presigned URL and expiration time

    Raises:
        HTTPException: If URL generation fails or file doesn't exist (404)
    """
    try:
        url = service.storage.generate_presigned_url(path, expires_in=expires_in)
        return {
            "url": url,
            "expires_at": datetime.utcnow() + datetime.timedelta(seconds=expires_in)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )


# Create a test file "test_{name}"
# Test function [case] def test_{name}()
# Put at least one assert statment
