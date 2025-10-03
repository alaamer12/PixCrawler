"""
Dataset-related Pydantic models and schemas.
"""

from enum import Enum
from typing import Optional

from pydantic import Field, HttpUrl

from .base import BaseSchema, TimestampMixin


class DatasetStatus(str, Enum):
    """Dataset processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SearchEngine(str, Enum):
    """Supported search engines."""

    GOOGLE = "google"
    BING = "bing"
    BAIDU = "baidu"
    DUCKDUCKGO = "duckduckgo"


class DatasetBase(BaseSchema):
    """Base dataset schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Dataset name")
    description: Optional[str] = Field(None, max_length=500,
                                       description="Dataset description")
    keywords: list[str] = Field(..., min_items=1, description="Search keywords")
    max_images: int = Field(default=100, ge=1, le=10000,
                            description="Maximum number of images")
    search_engines: list[SearchEngine] = Field(
        default=[SearchEngine.GOOGLE],
        description="Search engines to use"
    )


class DatasetCreate(DatasetBase):
    """Schema for creating a new dataset."""
    pass


class DatasetUpdate(BaseSchema):
    """Schema for updating dataset information."""

    name: Optional[str] = Field(None, min_length=1, max_length=100,
                                description="Dataset name")
    description: Optional[str] = Field(None, max_length=500,
                                       description="Dataset description")


class DatasetResponse(DatasetBase, TimestampMixin):
    """Schema for dataset response data."""

    id: int = Field(..., description="Dataset ID")
    user_id: int = Field(..., description="Owner user ID")
    status: DatasetStatus = Field(..., description="Processing status")
    progress: float = Field(default=0.0, ge=0.0, le=100.0,
                            description="Processing progress percentage")
    images_collected: int = Field(default=0, description="Number of images collected")
    download_url: Optional[HttpUrl] = Field(None,
                                            description="Download URL when completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        from_attributes = True


class DatasetStats(BaseSchema):
    """Dataset statistics schema."""

    total_datasets: int = Field(..., description="Total number of datasets")
    completed_datasets: int = Field(..., description="Number of completed datasets")
    processing_datasets: int = Field(..., description="Number of processing datasets")
    failed_datasets: int = Field(..., description="Number of failed datasets")
    total_images: int = Field(..., description="Total number of images collected")
