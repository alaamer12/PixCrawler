"""
Storage schemas for PixCrawler.

This module defines Pydantic schemas for storage management,
including usage statistics, file operations, and cleanup.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
    'StorageTier',
    'StorageUsageResponse',
    'FileInfo',
    'FileListResponse',
    'CleanupRequest',
    'CleanupResponse',
    'PresignedUrlResponse',
]


class StorageTier(str, Enum):
    """Storage tiers."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class StorageUsageResponse(BaseModel):
    """Response model for storage usage statistics."""
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
    )
    
    total_size_bytes: int = Field(
        ge=0,
        description="Total storage used in bytes",
        examples=[1073741824, 5368709120],
    )
    
    total_size_gb: float = Field(
        ge=0.0,
        description="Total storage used in GB",
        examples=[1.0, 5.0, 10.5],
    )
    
    file_count: int = Field(
        ge=0,
        description="Total number of files",
        examples=[100, 1000, 5000],
    )
    
    hot_storage_bytes: int = Field(
        ge=0,
        description="Hot tier storage in bytes",
    )
    
    warm_storage_bytes: int = Field(
        ge=0,
        description="Warm tier storage in bytes",
    )
    
    cold_storage_bytes: int = Field(
        ge=0,
        description="Cold tier storage in bytes",
    )
    
    last_updated: datetime = Field(
        description="Last update timestamp",
    )


class FileInfo(BaseModel):
    """Model for individual file information."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )
    
    file_id: str = Field(
        description="File ID",
        examples=["abc123", "xyz789"],
    )
    
    filename: str = Field(
        min_length=1,
        max_length=255,
        description="File name",
        examples=["image_001.jpg", "dataset_export.zip"],
    )
    
    size_bytes: int = Field(
        ge=0,
        description="File size in bytes",
    )
    
    storage_tier: StorageTier = Field(
        description="Storage tier",
        examples=[StorageTier.HOT, StorageTier.WARM],
    )
    
    created_at: datetime = Field(
        description="Creation timestamp",
    )
    
    last_accessed: Optional[datetime] = Field(
        default=None,
        description="Last access timestamp",
    )


class CleanupRequest(BaseModel):
    """Request model for cleanup operation."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )
    
    days_old: int = Field(
        gt=0,
        le=365,
        description="Delete files older than this many days",
        examples=[30, 60, 90],
    )
    
    storage_tier: Optional[StorageTier] = Field(
        default=None,
        description="Specific storage tier to clean (optional)",
    )
    
    dry_run: bool = Field(
        default=True,
        description="If true, only simulate cleanup without deleting",
    )
    
    @field_validator('days_old')
    @classmethod
    def validate_days_old(cls, v: int) -> int:
        """Validate days_old is reasonable."""
        if v < 7:
            raise ValueError('days_old must be at least 7 to prevent accidental deletion')
        return v


class FileListResponse(BaseModel):
    """Response model for file list."""
    
    model_config = ConfigDict(from_attributes=True)
    
    data: list[FileInfo] = Field(
        description="List of files",
        examples=[[{
            "file_id": "abc123",
            "filename": "image_001.jpg",
            "size_bytes": 1048576,
            "storage_tier": "hot",
            "created_at": "2024-01-27T10:00:00Z",
            "last_accessed": "2024-01-27T12:00:00Z"
        }]]
    )
    
    meta: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 50},
        description="Pagination metadata",
        examples=[{"total": 100, "skip": 0, "limit": 50}]
    )


class CleanupResponse(BaseModel):
    """Response model for cleanup operation."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    files_deleted: int = Field(
        ge=0,
        description="Number of files deleted",
    )
    
    space_freed_bytes: int = Field(
        ge=0,
        description="Space freed in bytes",
    )
    
    space_freed_gb: float = Field(
        ge=0.0,
        description="Space freed in GB",
    )
    
    dry_run: bool = Field(
        description="Whether this was a dry run",
    )
    
    completed_at: datetime = Field(
        description="Completion timestamp",
    )
    
    message: str = Field(
        description="Result message",
        examples=["Cleanup completed successfully", "Dry run completed - no files deleted"],
    )


class PresignedUrlResponse(BaseModel):
    """Response model for presigned URL generation."""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )
    
    url: str = Field(
        min_length=1,
        description="Presigned URL for temporary file access",
        examples=[
            "https://storage.example.com/file.jpg?token=abc123&expires=1234567890",
            "https://pixcrawler.blob.core.windows.net/datasets/file.zip?sig=xyz789"
        ]
    )
    
    expires_at: datetime = Field(
        description="URL expiration timestamp",
        examples=["2024-01-27T13:00:00Z", "2024-01-28T10:00:00Z"]
    )
