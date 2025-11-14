"""
Job schemas for PixCrawler (ValidationJob and ExportJob).

This module defines Pydantic schemas for validation and export jobs,
including creation, updates, and responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field

__all__ = [
    'ValidationJobStatus',
    'ValidationJobCreate',
    'ValidationJobUpdate',
    'ValidationJobResponse',
    'ExportJobStatus',
    'ExportJobFormat',
    'ExportJobCreate',
    'ExportJobUpdate',
    'ExportJobResponse',
]


class ValidationJobStatus(str, Enum):
    """Validation job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationJobCreate(BaseModel):
    """Schema for creating a validation job."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )
    
    crawl_job_id: int = Field(
        gt=0,
        description="Crawl job ID to validate",
        examples=[1, 42, 123],
    )
    
    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
        description="Validation job name",
        examples=["Image Validation", "quality_check"],
    )
    
    validation_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Validation rules configuration",
        examples=[
            {"min_width": 100, "min_height": 100},
            {"formats": ["jpg", "png"], "max_size_mb": 10},
        ],
    )


class ValidationJobUpdate(BaseModel):
    """Schema for updating validation job."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
    )
    
    status: Optional[ValidationJobStatus] = Field(
        default=None,
        description="Job status",
    )


class ValidationJobResponse(BaseModel):
    """Schema for validation job response."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )
    
    id: int = Field(description="Validation job ID")
    crawl_job_id: int = Field(description="Crawl job ID")
    name: str = Field(description="Job name")
    status: str = Field(description="Job status")
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    total_images: int = Field(ge=0, description="Total images to validate")
    validated_images: int = Field(ge=0, description="Validated images")
    invalid_images: int = Field(ge=0, description="Invalid images")
    validation_rules: dict[str, Any] = Field(description="Validation rules")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    @computed_field
    @property
    def success_rate(self) -> Optional[float]:
        """Calculate validation success rate."""
        if self.total_images == 0:
            return None
        return round((self.validated_images / self.total_images) * 100, 2)
    
    @computed_field
    @property
    def is_running(self) -> bool:
        """Check if job is running."""
        return self.status == "running"
    
    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status in ("completed", "failed")


class ExportJobStatus(str, Enum):
    """Export job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportJobFormat(str, Enum):
    """Supported export formats."""
    ZIP = "zip"
    TAR = "tar"
    TAR_GZ = "tar.gz"
    CSV = "csv"
    JSON = "json"


class ExportJobCreate(BaseModel):
    """Schema for creating an export job."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )
    
    crawl_job_id: int = Field(
        gt=0,
        description="Crawl job ID to export",
        examples=[1, 42, 123],
    )
    
    name: str = Field(
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
        description="Export job name",
        examples=["Export Dataset", "backup_images"],
    )
    
    format: ExportJobFormat = Field(
        default=ExportJobFormat.ZIP,
        description="Export format",
        examples=["zip", "tar.gz", "csv"],
    )
    
    export_options: dict[str, Any] = Field(
        default_factory=dict,
        description="Export-specific options",
        examples=[
            {"include_metadata": True, "compress": True},
            {"delimiter": ",", "include_urls": True},
        ],
    )


class ExportJobUpdate(BaseModel):
    """Schema for updating export job."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
    )
    
    status: Optional[ExportJobStatus] = Field(
        default=None,
        description="Job status",
    )


class ExportJobResponse(BaseModel):
    """Schema for export job response."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )
    
    id: int = Field(description="Export job ID")
    crawl_job_id: int = Field(description="Crawl job ID")
    user_id: UUID = Field(description="User ID")
    name: str = Field(description="Job name")
    status: str = Field(description="Job status")
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    format: str = Field(description="Export format")
    total_images: int = Field(ge=0, description="Total images to export")
    exported_images: int = Field(ge=0, description="Exported images")
    file_size: Optional[int] = Field(default=None, ge=0, description="File size in bytes")
    download_url: Optional[str] = Field(default=None, description="Download URL")
    export_options: dict[str, Any] = Field(description="Export options")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Download expiration")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    @computed_field
    @property
    def success_rate(self) -> Optional[float]:
        """Calculate export success rate."""
        if self.total_images == 0:
            return None
        return round((self.exported_images / self.total_images) * 100, 2)
    
    @computed_field
    @property
    def is_running(self) -> bool:
        """Check if job is running."""
        return self.status == "running"
    
    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status in ("completed", "failed")
    
    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if download link is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at
