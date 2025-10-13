"""Storage provider protocol for PixCrawler backend.

This module defines the storage provider protocol that all storage implementations
must follow, enabling flexible storage backends (local, cloud, etc.).

Protocols:
    StorageProvider: Protocol defining storage operations interface

Features:
    - Protocol-based design for better type checking
    - Support for multiple storage backends
    - Consistent interface for file operations
    - Presigned URL generation support
"""

from pathlib import Path
from typing import Protocol, List, Optional, Union

__all__ = ['StorageProvider']


class StorageProvider(Protocol):
    """Protocol for storage provider implementations.
    
    All storage providers must implement these methods to provide
    consistent file storage operations across different backends.
    
    Methods:
        upload: Upload a file to storage
        download: Download a file from storage
        delete: Delete a file from storage
        list_files: List files with optional prefix filter
        generate_presigned_url: Generate temporary access URL
    """

    def upload(self, file_path: Union[str, Path], destination_path: str) -> None:
        """Upload a file to storage.
        
        Args:
            file_path: Path to the local file to upload
            destination_path: Destination path in storage
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            IOError: If upload fails
        """
        ...

    def download(self, file_path: str, destination_path: Union[str, Path]) -> None:
        """Download a file from storage.
        
        Args:
            file_path: Path to the file in storage
            destination_path: Local destination path
            
        Raises:
            FileNotFoundError: If file doesn't exist in storage
            IOError: If download fails
        """
        ...

    def delete(self, file_path: str) -> None:
        """Delete a file from storage.
        
        Args:
            file_path: Path to the file in storage
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If deletion fails
        """
        ...

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """List files in storage with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file paths in storage
            
        Raises:
            IOError: If listing fails
        """
        ...

    def generate_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate a presigned URL for temporary file access.
        
        Args:
            file_path: Path to the file in storage
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If URL generation fails
        """
        ...
