"""Storage provider factory for PixCrawler backend.

This module provides factory functions for creating storage provider instances
with flexible configuration and graceful fallback handling.

Functions:
    get_storage_provider: Create and return configured storage provider

Features:
    - Environment-based provider selection
    - Graceful fallback to local storage
    - Comprehensive error handling and logging
    - Support for multiple storage backends
"""

from functools import lru_cache
from typing import Union

from logging_config import get_logger

from backend.storage.base import StorageProvider
from backend.storage.config import StorageSettings
from backend.storage.local import LocalStorageProvider
from backend.storage.azure_blob import AzureBlobStorageProvider, AZURE_AVAILABLE

__all__ = ['get_storage_provider']

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_storage_provider(settings: StorageSettings = None) -> StorageProvider:
    """Get configured storage provider instance.
    
    Creates and returns a storage provider based on configuration settings.
    Falls back to local storage if the requested provider is unavailable.
    
    Args:
        settings: Storage settings. If None, loads from environment.
        
    Returns:
        Configured storage provider instance
        
    Raises:
        ValueError: If configuration is invalid
    """
    if settings is None:
        settings = StorageSettings()
    
    provider_type = settings.storage_provider.lower()
    
    # Azure Blob Storage
    if provider_type == "azure":
        if not AZURE_AVAILABLE:
            logger.warning(
                "Azure storage requested but azure-storage-blob not installed. "
                "Falling back to local storage."
            )
            return _create_local_provider(settings)
        
        if not settings.azure_connection_string:
            logger.error("Azure provider selected but connection string not provided")
            raise ValueError("azure_connection_string is required for Azure storage")
        
        try:
            logger.info(f"Initializing Azure Blob Storage (container: {settings.azure_container_name})")
            return AzureBlobStorageProvider(
                connection_string=settings.azure_connection_string,
                container_name=settings.azure_container_name,
                max_retries=settings.azure_max_retries
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure storage: {e}. Falling back to local storage.")
            return _create_local_provider(settings)
    
    # Local storage (default)
    return _create_local_provider(settings)


def _create_local_provider(settings: StorageSettings) -> LocalStorageProvider:
    """Create local storage provider instance.
    
    Args:
        settings: Storage settings
        
    Returns:
        LocalStorageProvider instance
    """
    logger.info("Initializing local filesystem storage")
    return LocalStorageProvider(base_directory=settings.local_storage_path)
