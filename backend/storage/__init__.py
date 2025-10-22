"""Storage module for PixCrawler backend.

This module provides storage provider implementations and factory functions
for managing file storage across different backends (local, cloud, etc.).

Classes:
    StorageProvider: Protocol defining storage operations interface
    LocalStorageProvider: Local filesystem storage implementation
    AzureBlobStorageProvider: Azure Blob Storage implementation
    StorageSettings: Storage configuration settings

Functions:
    get_storage_provider: Factory function to create storage provider instances

Features:
    - Protocol-based design for flexible storage backends
    - Local filesystem storage with platformdirs
    - Azure Blob Storage with optional dependency
    - Environment-based configuration
    - Comprehensive error handling and logging
"""

from backend.storage.base import StorageProvider
from backend.storage.config import StorageSettings
from backend.storage.factory import get_storage_provider
from backend.storage.local import LocalStorageProvider
from backend.storage.azure_blob import AzureBlobStorageProvider, AZURE_AVAILABLE

__all__ = [
    'StorageProvider',
    'StorageSettings',
    'get_storage_provider',
    'LocalStorageProvider',
    'AzureBlobStorageProvider',
    'AZURE_AVAILABLE'
]
