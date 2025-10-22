"""Enhanced storage configuration with Archive Tier support for PixCrawler.

This module extends PixCrawler's storage configuration to include
archive tier settings for cost optimization.

Classes:
    StorageSettings: Enhanced storage configuration with archive tier options

Features:
    - All existing PixCrawler storage settings
    - Archive tier configuration
    - Default tier selection
    - Rehydration priority settings
    - Backward compatible with existing code
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ['StorageSettings']


class StorageSettings(BaseSettings):
    """Enhanced storage provider configuration with Archive Tier support.
    
    Extends PixCrawler's storage configuration to include archive tier
    settings for cost-effective long-term storage.
    
    Attributes:
        storage_provider: Storage provider type (local or azure)
        local_storage_path: Base directory for local storage
        azure_connection_string: Azure Storage connection string
        azure_container_name: Azure Blob container name
        azure_max_retries: Maximum retry attempts for Azure operations
        
        # Archive Tier Settings (NEW)
        azure_enable_archive_tier: Enable archive tier features
        azure_default_tier: Default tier for uploads (hot, cool, archive)
        azure_rehydrate_priority: Default rehydration priority (standard, high)
    
    Cost Optimization:
        - Hot tier: $0.018/GB/month (baseline)
        - Cool tier: $0.010/GB/month (44% savings)
        - Archive tier: $0.001/GB/month (94% savings!)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="STORAGE_",
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
        examples=["./storage", "/var/lib/pixcrawler/storage"]
    )

    # Azure Blob Storage settings (existing)
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

    # Archive Tier Settings (NEW)
    azure_enable_archive_tier: bool = Field(
        default=True,
        description="Enable archive tier features for cost optimization",
        examples=[True, False]
    )
    azure_default_tier: str = Field(
        default="hot",
        pattern=r'^(hot|cool|archive)$',
        description="Default access tier for uploads (hot/cool/archive)",
        examples=["hot", "cool", "archive"]
    )
    azure_rehydrate_priority: str = Field(
        default="standard",
        pattern=r'^(standard|high)$',
        description="Default rehydration priority (standard: 15h, high: <1h)",
        examples=["standard", "high"]
    )

    # Lifecycle Policy Settings (NEW)
    azure_lifecycle_enabled: bool = Field(
        default=False,
        description="Enable automatic lifecycle management",
        examples=[True, False]
    )
    azure_lifecycle_cool_after_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Move to Cool tier after N days (optional)",
        examples=[30, 60, 90]
    )
    azure_lifecycle_archive_after_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Move to Archive tier after N days (optional)",
        examples=[90, 180, 365]
    )
    azure_lifecycle_delete_after_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Delete after N days (optional)",
        examples=[365, 2555, 3650]
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
            if not path.is_absolute():
                path = path.resolve()
            return str(path)
        return v

    @field_validator('azure_default_tier')
    @classmethod
    def validate_default_tier(cls, v: str) -> str:
        """Validate default tier value."""
        v = v.lower()
        if v not in ('hot', 'cool', 'archive'):
            raise ValueError("azure_default_tier must be 'hot', 'cool', or 'archive'")
        return v

    @field_validator('azure_rehydrate_priority')
    @classmethod
    def validate_rehydrate_priority(cls, v: str) -> str:
        """Validate rehydration priority value."""
        v = v.lower()
        if v not in ('standard', 'high'):
            raise ValueError("azure_rehydrate_priority must be 'standard' or 'high'")
        return v

    @field_validator('azure_lifecycle_archive_after_days')
    @classmethod
    def validate_archive_days(cls, v: Optional[int], info) -> Optional[int]:
        """Validate archive days is greater than cool days."""
        if v is not None:
            cool_days = info.data.get('azure_lifecycle_cool_after_days')
            if cool_days is not None and v <= cool_days:
                raise ValueError(
                    "azure_lifecycle_archive_after_days must be greater than "
                    "azure_lifecycle_cool_after_days"
                )
        return v

    @field_validator('azure_lifecycle_delete_after_days')
    @classmethod
    def validate_delete_days(cls, v: Optional[int], info) -> Optional[int]:
        """Validate delete days is greater than archive days."""
        if v is not None:
            archive_days = info.data.get('azure_lifecycle_archive_after_days')
            if archive_days is not None and v <= archive_days:
                raise ValueError(
                    "azure_lifecycle_delete_after_days must be greater than "
                    "azure_lifecycle_archive_after_days"
                )
        return v

    def get_tier_enum(self):
        """Get AccessTier enum from string value."""
        from azure_blob_archive import AccessTier
        tier_map = {
            'hot': AccessTier.HOT,
            'cool': AccessTier.COOL,
            'archive': AccessTier.ARCHIVE
        }
        return tier_map[self.azure_default_tier.lower()]

    def get_priority_enum(self):
        """Get RehydratePriority enum from string value."""
        from azure_blob_archive import RehydratePriority
        priority_map = {
            'standard': RehydratePriority.STANDARD,
            'high': RehydratePriority.HIGH
        }
        return priority_map[self.azure_rehydrate_priority.lower()]
