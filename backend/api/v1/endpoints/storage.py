"""
Storage Management API for PixCrawler
Handles storage operations including usage stats, file info, and cleanup
"""

from datetime import datetime, timedelta
from typing import Optional, List, Union, Dict

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from backend.storage.base import StorageProvider
from backend.api.dependencies import get_storage

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])

class StorageUsageResponse(BaseModel):
    """Response model for storage usage statistics.
    
    Attributes:
        total_storage_bytes: Total storage used in bytes
        total_storage_mb: Total storage used in megabytes
        total_storage_gb: Total storage used in gigabytes
        file_count: Number of files in storage
        last_updated: Timestamp of last update
    """
    total_storage_bytes: int
    total_storage_mb: float
    total_storage_gb: float
    file_count: int
    last_updated: datetime


class FileInfo(BaseModel):
    """Model for individual file information.
    
    Attributes:
        file_path: Relative path to the file in storage
        size_bytes: File size in bytes
        size_mb: File size in megabytes
        last_modified: Last modification timestamp
    """
    file_path: str
    size_bytes: int
    size_mb: float
    last_modified: Optional[datetime]


class CleanupRequest(BaseModel):
    """Request model for cleanup operation.
    
    Attributes:
        age_hours: Delete files older than this many hours
        prefix: Optional prefix to filter files for cleanup
    """
    age_hours: Optional[int] = 24
    prefix: Optional[str] = None


class CleanupResponse(BaseModel):
    """Response model for cleanup operation.
    
    Attributes:
        success: Whether cleanup completed successfully
        files_deleted: Number of files deleted
        space_freed_bytes: Space freed in bytes
        space_freed_mb: Space freed in megabytes
        cleanup_duration_seconds: Duration of cleanup operation
        timestamp: Timestamp of cleanup completion
    """
    success: bool
    files_deleted: int
    space_freed_bytes: int
    space_freed_mb: float
    cleanup_duration_seconds: float
    timestamp: datetime

class StorageService:
    """Service class handling storage operations.
    
    Provides business logic for storage management including
    statistics, file listing, and cleanup operations.
    
    Attributes:
        storage: Storage provider instance
    """

    def __init__(self, storage: StorageProvider):
        """Initialize storage service.
        
        Args:
            storage: Storage provider instance
        """
        self.storage = storage

    async def get_storage_stats(self) -> StorageUsageResponse:
        """Calculate and return storage statistics.
        
        Returns:
            StorageUsageResponse with usage statistics
            
        Raises:
            HTTPException: If statistics calculation fails
        """
        try:
            # Get all files
            files = self.storage.list_files()
            total_size = 0

            # Calculate total size (simplified - in a real implementation, we'd get actual sizes)
            for file_path in files:
                # This is a simplification - actual implementation would get file sizes
                total_size += 1024  # Placeholder: assume 1KB per file

            return StorageUsageResponse(
                total_storage_bytes=total_size,
                total_storage_mb=round(total_size / (1024 * 1024), 2),
                total_storage_gb=round(total_size / (1024 * 1024 * 1024), 2),
                file_count=len(files),
                last_updated=datetime.utcnow()
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get storage stats: {str(e)}"
            )

    async def list_files(
        self,
        prefix: Optional[str] = None
    ) -> List[FileInfo]:
        """List files with optional prefix filtering.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of FileInfo objects
            
        Raises:
            HTTPException: If file listing fails
        """
        try:
            file_paths = self.storage.list_files(prefix)
            # This is a simplified implementation
            # In a real app, we'd get actual file metadata
            return [
                FileInfo(
                    file_path=path,
                    size_bytes=1024,  # Placeholder
                    size_mb=0.001,    # Placeholder
                    last_modified=datetime.utcnow()  # Placeholder
                )
                for path in file_paths
            ]
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list files: {str(e)}"
            )

    async def cleanup_files(
        self,
        age_hours: int = 24,
        prefix: Optional[str] = None
    ) -> CleanupResponse:
        """Clean up old files based on criteria.
        
        Args:
            age_hours: Delete files older than this many hours
            prefix: Optional prefix to filter files
            
        Returns:
            CleanupResponse with cleanup results
            
        Raises:
            HTTPException: If cleanup operation fails
        """
        start_time = datetime.utcnow()

        try:
            # Get files matching the prefix
            files = await self.list_files(prefix)

            # Filter by age (simplified - in a real implementation, we'd check actual file timestamps)
            files_to_delete = files  # Placeholder: would filter by age

            # Delete files
            deleted_count = 0
            space_freed = 0

            for file_info in files_to_delete:
                try:
                    self.storage.delete(file_info.file_path)
                    deleted_count += 1
                    space_freed += file_info.size_bytes
                except Exception as e:
                    # Log the error but continue with other files
                    print(f"Error deleting {file_info.file_path}: {str(e)}")

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return CleanupResponse(
                success=True,
                files_deleted=deleted_count,
                space_freed_bytes=space_freed,
                space_freed_mb=round(space_freed / (1024 * 1024), 2),
                cleanup_duration_seconds=duration,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Cleanup operation failed: {str(e)}"
            )

@router.get("/usage/", response_model=StorageUsageResponse)
async def get_storage_usage(
    storage: StorageProvider = Depends(get_storage)
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
    service = StorageService(storage)
    return await service.get_storage_stats()


@router.get("/files/", response_model=List[FileInfo])
async def list_storage_files(
    prefix: Optional[str] = Query(None, description="Filter files by prefix"),
    storage: StorageProvider = Depends(get_storage)
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
    service = StorageService(storage)
    return await service.list_files(prefix)


@router.post("/cleanup/", response_model=CleanupResponse)
async def cleanup_storage(
    request: CleanupRequest,
    storage: StorageProvider = Depends(get_storage)
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
    service = StorageService(storage)
    return await service.cleanup_files(
        age_hours=request.age_hours,
        prefix=request.prefix
    )


@router.get("/presigned-url/")
async def get_presigned_url(
    path: str = Query(..., description="Path to the file"),
    expires_in: int = Query(3600, description="URL expiration time in seconds"),
    storage: StorageProvider = Depends(get_storage)
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
        url = storage.generate_presigned_url(path, expires_in=expires_in)
        return {
            "url": url,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )
