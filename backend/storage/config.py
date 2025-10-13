"""Storage configuration models for PixCrawler backend.

This module provides Pydantic settings models for storage configuration,
supporting multiple storage providers with comprehensive validation.

Classes:
    StorageSettings: Storage provider configuration settings

Features:
    - Environment-based configuration with .env support
    - Type-safe configuration with Pydantic v2 validation
    - Support for local and Azure Blob storage
    - Comprehensive field validation and examples
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ['StorageSettings']


class StorageSettings(BaseSettings):
    """Storage provider configuration settings.
    
    Configuration for storage backends including local filesystem
    and Azure Blob Storage, with environment variable support.
    
    Attributes:
        storage_provider: Storage provider type (local or azure)
        local_storage_path: Base directory for local storage
        azure_connection_string: Azure Storage connection string
        azure_container_name: Azure Blob container name
        azure_max_retries: Maximum retry attempts for Azure operations
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="STORAGE_",  # Now reads STORAGE_PROVIDER, STORAGE_LOCAL_STORAGE_PATH
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        str_strip_whitespace=True
    )

    # Provider selection
    storage_provider: str = Field(
        default="local",
        pattern=r'^(local|azure)$',
        description="Storage provider type",
        examples=["local", "azure"]
    )

    # Local storage settings
    local_storage_path: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Base directory for local storage (uses platformdirs if not set)",
        examples=["./storage", "/var/lib/pixcrawler/storage", "C:\\ProgramData\\PixCrawler\\storage"]
    )

    # Azure Blob Storage settings
    azure_connection_string: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Azure Storage connection string",
        examples=["DefaultEndpointsProtocol=https;AccountName=..."]
    )
    azure_container_name: str = Field(
        default="pixcrawler-storage",
        min_length=3,
        max_length=63,
        pattern=r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$',
        description="Azure Blob container name (lowercase, alphanumeric, hyphens)",
        examples=["pixcrawler-storage", "images-prod", "dev-storage"]
    )
    azure_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts for Azure operations",
        examples=[3, 5, 10]
    )

    @field_validator('storage_provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate storage provider is supported."""
        v = v.lower()
        if v not in ('local', 'azure'):
            raise ValueError("storage_provider must be 'local' or 'azure'")
        return v

    @field_validator('azure_connection_string')
    @classmethod
    def validate_azure_connection(cls, v: Optional[str], info) -> Optional[str]:
        """Validate Azure connection string when Azure provider is selected."""
        if info.data.get('storage_provider') == 'azure' and not v:
            raise ValueError("azure_connection_string is required when using Azure provider")
        return v

    @field_validator('local_storage_path')
    @classmethod
    def validate_local_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize local storage path."""
        if v:
            path = Path(v)
            # Ensure path is absolute or make it absolute
            if not path.is_absolute():
                path = path.resolve()
            return str(path)
        return v
