"""Local filesystem storage provider for PixCrawler backend.

This module implements local filesystem storage using modern Python patterns
with pathlib, platformdirs, and proper error handling.

Classes:
    LocalStorageProvider: Local filesystem storage implementation

Features:
    - Uses pathlib.Path for cross-platform compatibility
    - Uses platformdirs for proper base directory location
    - Comprehensive error handling and logging
    - Safe file operations with proper validation
"""

import shutil
import time
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import quote

from platformdirs import user_data_dir
from utility.logging_config import get_logger

__all__ = ['LocalStorageProvider']

logger = get_logger(__name__)


class LocalStorageProvider:
    """Local filesystem storage provider.

    Implements storage operations using the local filesystem with
    modern Python patterns and proper error handling.

    Attributes:
        base_directory: Base directory for storage operations
    """

    def __init__(self, base_directory: Optional[Union[str, Path]] = None) -> None:
        """Initialize local storage provider.

        Args:
            base_directory: Base directory for storage. If None, uses
                platformdirs to determine appropriate location.
        """
        if base_directory is None:
            # Use platformdirs for proper cross-platform data directory
            base_directory = Path(user_data_dir("pixcrawler", "pixcrawler")) / "storage"
        else:
            base_directory = Path(base_directory)

        # Resolve to absolute path to ensure path validation works correctly
        self.base_directory = base_directory.resolve()
        self.base_directory.mkdir(parents=True, exist_ok=True)

        logger.info(f"Local storage initialized at: {self.base_directory}")

    def _full_path(self, file_path: str) -> Path:
        """Get full path for a file in storage.

        Args:
            file_path: Relative file path

        Returns:
            Full absolute path

        Raises:
            ValueError: If path attempts directory traversal
        """
        full_path = (self.base_directory / file_path).resolve()

        # Security: Ensure path is within base_directory
        try:
            full_path.relative_to(self.base_directory)
        except ValueError:
            raise ValueError(f"Invalid file path: {file_path} (directory traversal detected)")

        return full_path

    def upload(self, file_path: Union[str, Path], destination_path: str) -> None:
        """Upload a file to local storage.

        Args:
            file_path: Path to the local file to upload
            destination_path: Destination path in storage

        Raises:
            FileNotFoundError: If source file doesn't exist
            IOError: If upload fails
        """
        source = Path(file_path)

        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")

        if not source.is_file():
            raise ValueError(f"Source path is not a file: {file_path}")

        try:
            destination = self._full_path(destination_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            logger.debug(f"Uploaded file: {file_path} -> {destination_path}")
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise IOError(f"Upload failed: {e}") from e

    def download(self, file_path: str, destination_path: Union[str, Path]) -> None:
        """Download a file from local storage.

        Args:
            file_path: Path to the file in storage
            destination_path: Local destination path

        Raises:
            FileNotFoundError: If file doesn't exist in storage
            IOError: If download fails
        """
        try:
            source = self._full_path(file_path)

            if not source.exists():
                raise FileNotFoundError(f"File not found in storage: {file_path}")

            destination = Path(destination_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            logger.debug(f"Downloaded file: {file_path} -> {destination_path}")
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            raise IOError(f"Download failed: {e}") from e

    def delete(self, file_path: str) -> None:
        """Delete a file from local storage.

        Args:
            file_path: Path to the file in storage

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If deletion fails
        """
        try:
            full_path = self._full_path(file_path)

            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            full_path.unlink()
            logger.debug(f"Deleted file: {file_path}")
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise IOError(f"Deletion failed: {e}") from e

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """List files in local storage with optional prefix filter.

        Args:
            prefix: Optional prefix to filter files

        Returns:
            List of relative file paths

        Raises:
            IOError: If listing fails
        """
        try:
            files = []

            for file_path in self.base_directory.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(self.base_directory)
                    relative_str = str(relative_path).replace("\\", "/")

                    if prefix is None or relative_str.startswith(prefix):
                        files.append(relative_str)

            logger.debug(f"Listed {len(files)} files with prefix: {prefix}")
            return sorted(files)
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            raise IOError(f"Listing failed: {e}") from e

    def generate_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for local file access.

        Note: For local storage, this generates a file:// URL with expiration
        metadata. In production, consider using a web server to serve files.

        Args:
            file_path: Path to the file in storage
            expires_in: URL expiration time in seconds

        Returns:
            File URL with expiration metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If URL generation fails
        """
        try:
            full_path = self._full_path(file_path)

            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            timestamp = int(time.time())
            expires_at = timestamp + expires_in

            # For local storage, return file:// URL with metadata
            url = f"file://{quote(str(full_path))}?expires_at={expires_at}"
            logger.debug(f"Generated presigned URL for: {file_path}")
            return url
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {file_path}: {e}")
            raise IOError(f"URL generation failed: {e}") from e
