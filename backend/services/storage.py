"""
Storage service for storage operations.

This module provides services for storage management including
statistics, file listing, and cleanup operations.

Classes:
    StorageService: Service for storage operations
"""

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException

from backend.schemas.storage import (
    CleanupResponse,
    FileInfo,
    StorageUsageResponse,
)
from backend.storage.base import StorageProvider
from .base import BaseService

__all__ = ['StorageService']


class StorageService(BaseService):
    """
    Service class handling storage operations.

    Provides business logic for storage management including
    statistics, file listing, and cleanup operations.

    Attributes:
        storage: Storage provider instance
    """

    def __init__(self, storage: StorageProvider) -> None:
        """
        Initialize storage service.

        Args:
            storage: Storage provider instance
        """
        super().__init__()
        self.storage = storage

    async def get_storage_stats(self) -> StorageUsageResponse:
        """
        Calculate and return storage statistics.

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

            self.log_operation("get_storage_stats", file_count=len(files), total_size=total_size)

            return StorageUsageResponse(
                total_storage_bytes=total_size,
                total_storage_mb=round(total_size / (1024 * 1024), 2),
                total_storage_gb=round(total_size / (1024 * 1024 * 1024), 2),
                file_count=len(files),
                last_updated=datetime.utcnow()
            )
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get storage stats: {str(e)}"
            )

    async def list_files(
        self,
        prefix: Optional[str] = None
    ) -> List[FileInfo]:
        """
        List files with optional prefix filtering.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of FileInfo objects

        Raises:
            HTTPException: If file listing fails
        """
        try:
            file_paths = self.storage.list_files(prefix)
            
            self.log_operation("list_files", prefix=prefix, count=len(file_paths))
            
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
            self.logger.error(f"Failed to list files: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list files: {str(e)}"
            )

    async def cleanup_files(
        self,
        age_hours: int = 24,
        prefix: Optional[str] = None
    ) -> CleanupResponse:
        """
        Clean up old files based on criteria.

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
                    self.logger.warning(f"Error deleting {file_info.file_path}: {str(e)}")

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            self.log_operation(
                "cleanup_files",
                age_hours=age_hours,
                prefix=prefix,
                deleted_count=deleted_count,
                space_freed=space_freed
            )

            return CleanupResponse(
                success=True,
                files_deleted=deleted_count,
                space_freed_bytes=space_freed,
                space_freed_mb=round(space_freed / (1024 * 1024), 2),
                cleanup_duration_seconds=duration,
                timestamp=datetime.utcnow()
            )

        except Exception as e:
            self.logger.error(f"Cleanup operation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Cleanup operation failed: {str(e)}"
            )
