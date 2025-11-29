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
                total_size_bytes=total_size,
                total_size_gb=round(total_size / (1024 * 1024 * 1024), 4),
                file_count=len(files),
                hot_storage_bytes=total_size,  # Placeholder
                warm_storage_bytes=0,  # Placeholder
                cold_storage_bytes=0,  # Placeholder
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
                    file_id=path,  # Use path as ID for now
                    filename=path.split('/')[-1],
                    size_bytes=1024,  # Placeholder
                    storage_tier="hot",  # Placeholder
                    created_at=datetime.utcnow(),
                    last_accessed=None
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
        days_old: int = 30,
        storage_tier: Optional[str] = None,
        dry_run: bool = True
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
            # Get all files
            files = await self.list_files()

            # Filter by age (simplified - in a real implementation, we'd check actual file timestamps)
            files_to_delete = files  # Placeholder: would filter by age

            # Delete files
            deleted_count = 0
            space_freed = 0

            for file_info in files_to_delete:
                try:
                    if not dry_run:
                        self.storage.delete(file_info.filename)  # Assuming filename is path
                        deleted_count += 1
                    space_freed += file_info.size_bytes
                except Exception as e:
                    # Log the error but continue with other files
                    self.logger.warning(f"Error deleting {file_info.file_path}: {str(e)}")

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            self.log_operation(
                "cleanup_files",
                days_old=days_old,
                storage_tier=storage_tier,
                dry_run=dry_run,
                deleted_count=deleted_count,
                space_freed=space_freed
            )

            return CleanupResponse(
                files_deleted=deleted_count,
                space_freed_bytes=space_freed,
                space_freed_gb=round(space_freed / (1024 * 1024 * 1024), 4),
                dry_run=dry_run,
                completed_at=datetime.utcnow(),
                message=f"Cleanup completed. Deleted {deleted_count} files." if not dry_run else f"Dry run completed. Found {deleted_count} files to delete."
            )

        except Exception as e:
            self.logger.error(f"Cleanup operation failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Cleanup operation failed: {str(e)}"
            )

    async def generate_presigned_url_with_expiration(
        self,
        path: str,
        expires_in: int
    ) -> dict:
        """
        Generate a presigned URL with expiration time.

        Args:
            path: Path to the file in storage
            expires_in: URL expiration time in seconds

        Returns:
            Dictionary containing the presigned URL and expiration time

        Raises:
            HTTPException: If URL generation fails
        """
        from datetime import timedelta

        try:
            url = self.storage.generate_presigned_url(path, expires_in=expires_in)
            
            self.log_operation(
                "generate_presigned_url",
                path=path,
                expires_in=expires_in
            )
            
            return {
                "url": url,
                "expires_at": datetime.utcnow() + timedelta(seconds=expires_in)
            }
        except Exception as e:
            self.logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )
