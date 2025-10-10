"""
Dependency injection for the PixCrawler API
"""
from typing import Generator
from fastapi import Depends
from .storage.factory import get_storage_provider
from .storage.base import StorageProvider

def get_storage() -> Generator[StorageProvider, None, None]:
    """
    Dependency that returns the configured storage provider.
    
    Yields:
        StorageProvider: The configured storage provider instance
    """
    storage = get_storage_provider()
    try:
        yield storage
    finally:
        # Add any cleanup if needed
        pass
