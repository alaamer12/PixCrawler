"""
Dataset-related Pydantic models and schemas for the PixCrawler backend.

This module provides all dataset-related data models including dataset creation,
processing status tracking, and statistics with comprehensive validation and
type safety for the image dataset generation workflow.

Classes:
    DatasetStatus: Enumeration of dataset processing states
    SearchEngine: Enumeration of supported search engines
    DatasetBase: Base dataset schema with common fields
    DatasetCreate: Schema for creating a new dataset
    DatasetUpdate: Schema for updating dataset information
    DatasetResponse: Schema for dataset response data
    DatasetStats: Schema for dataset statistics

Features:
    - Comprehensive dataset lifecycle management
    - Multi-engine search support
    - Progress tracking and status monitoring
    - Statistical reporting capabilities
"""

from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import Field, HttpUrl, field_validator, model_validator

from .base import BaseSchema, TimestampMixin
from .dataset_version import DatasetVersionResponse

__all__ = [
    'DatasetStatus',
    'SearchEngine',
    'DatasetBase',
    'DatasetCreate',
    'DatasetUpdate',
    'DatasetResponse',
    'DatasetListResponse',
    'DatasetStats',
    'DatasetVersionResponse'
]


class DatasetStatus(str, Enum):
    """
    Dataset processing status enumeration.

    Defines all possible states of a dataset during its lifecycle
    from creation to completion or failure.

    Values:
        PENDING: Dataset created but not yet started
        PROCESSING: Dataset generation in progress
        COMPLETED: Dataset generation completed successfully
        FAILED: Dataset generation failed with errors
        CANCELLED: Dataset generation cancelled by user
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SearchEngine(str, Enum):
    """
    Supported search engines enumeration.

    Defines all search engines available for image collection
    in the dataset generation process.

    Values:
        GOOGLE: Google Images search
        BING: Bing Images search
        BAIDU: Baidu Images search
        DUCKDUCKGO: DuckDuckGo Images search
    """

    GOOGLE = "google"
    BING = "bing"
    BAIDU = "baidu"
    DUCKDUCKGO = "duckduckgo"


class DatasetBase(BaseSchema):
    """
    Base dataset schema with common fields.

    Contains the core dataset attributes that are shared across
    different dataset-related schemas.

    Attributes:
        name: Dataset name with length constraints
        description: Optional dataset description
        keywords: List of search keywords (minimum 1 required)
        max_images: Maximum number of images to collect
        search_engines: List of search engines to use
    """

    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
        description="Dataset name (alphanumeric, spaces, hyphens, underscores only)",
        examples=["My Dataset", "animal_photos", "car-images-2024"]
    )
    description: Optional[str] = Field(
        None, 
        max_length=500,
        description="Dataset description",
        examples=["A collection of animal photos for ML training", None]
    )
    keywords: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=50,
        description="Search keywords",
        examples=[["cats", "dogs"], ["red car", "blue car", "sports car"]]
    )
    max_images: int = Field(
        default=100, 
        ge=1, 
        le=10000,
        description="Maximum number of images to collect",
        examples=[100, 500, 1000]
    )
    search_engines: List[SearchEngine] = Field(
        default=[SearchEngine.GOOGLE],
        min_items=1,
        max_items=4,
        description="Search engines to use",
        examples=[[SearchEngine.GOOGLE], [SearchEngine.GOOGLE, SearchEngine.BING]]
    )

    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate and clean keywords."""
        cleaned = []
        for keyword in v:
            cleaned_keyword = keyword.strip()
            if not cleaned_keyword:
                continue
            if len(cleaned_keyword) < 2:
                raise ValueError(f"Keyword '{cleaned_keyword}' is too short (minimum 2 characters)")
            if len(cleaned_keyword) > 100:
                raise ValueError(f"Keyword '{cleaned_keyword}' is too long (maximum 100 characters)")
            cleaned.append(cleaned_keyword)
        
        if not cleaned:
            raise ValueError("At least one valid keyword is required")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in cleaned:
            if keyword.lower() not in seen:
                seen.add(keyword.lower())
                unique_keywords.append(keyword)
        
        return unique_keywords

    @field_validator('search_engines')
    @classmethod
    def validate_search_engines(cls, v: List[SearchEngine]) -> List[SearchEngine]:
        """Remove duplicate search engines."""
        return list(dict.fromkeys(v))  # Preserves order while removing duplicates


class DatasetCreate(DatasetBase):
    """
    Schema for creating a new dataset.

    Inherits all fields from DatasetBase without additional
    fields for dataset creation requests.
    """
    pass


class DatasetUpdate(BaseSchema):
    """
    Schema for updating dataset information.

    All fields are optional to support partial updates.
    Only metadata fields can be updated, not processing parameters.

    Attributes:
        name: Updated dataset name
        description: Updated dataset description
    """

    name: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100,
        pattern=r'^[a-zA-Z0-9_\-\s]+$',
        description="Updated dataset name",
        examples=["Updated Dataset Name", None]
    )
    description: Optional[str] = Field(
        None, 
        max_length=500,
        description="Updated dataset description",
        examples=["Updated description for the dataset", None]
    )
    keywords: Optional[List[str]] = Field(
        None,
        min_items=1,
        max_items=50,
        description="Updated search keywords",
    )
    search_engines: Optional[List[SearchEngine]] = Field(
        None,
        min_items=1,
        max_items=4,
        description="Updated search engines",
    )
    max_images: Optional[int] = Field(
        None,
        ge=1,
        le=10000,
        description="Updated maximum number of images",
    )

    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> 'DatasetUpdate':
        """Ensure at least one field is provided for update."""
        if not any([self.name, self.description, self.keywords, self.search_engines, self.max_images]):
            raise ValueError("At least one field must be provided for update")
        return self


class DatasetResponse(DatasetBase, TimestampMixin):
    """
    Schema for dataset response data.

    Includes all dataset information returned by the API,
    with processing status and progress tracking.

    Attributes:
        id: Unique dataset identifier
        user_id: Owner user identifier
        status: Current processing status
        progress: Processing progress percentage (0-100)
        images_collected: Number of images successfully collected
        download_url: Download URL when dataset is completed
        error_message: Error message if processing failed
    """

    id: int = Field(
        ..., 
        gt=0,
        description="Dataset ID",
        examples=[1, 42, 1337]
    )
    user_id: UUID = Field(
        ..., 
        description="Owner user ID",
        examples=["a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"]
    )
    status: DatasetStatus = Field(
        ..., 
        description="Processing status",
        examples=[DatasetStatus.PENDING, DatasetStatus.PROCESSING, DatasetStatus.COMPLETED]
    )
    progress: float = Field(
        default=0.0, 
        ge=0.0, 
        le=100.0,
        description="Processing progress percentage",
        examples=[0.0, 45.5, 100.0]
    )
    images_collected: int = Field(
        default=0, 
        ge=0,
        description="Number of images successfully collected",
        examples=[0, 150, 1000]
    )
    download_url: Optional[HttpUrl] = Field(
        None,
        description="Download URL when dataset is completed",
        examples=["https://storage.example.com/datasets/123/download", None]
    )
    error_message: Optional[str] = Field(
        None, 
        max_length=1000,
        description="Error message if processing failed",
        examples=["Network timeout during image download", None]
    )

    @model_validator(mode='after')
    def validate_status_consistency(self) -> 'DatasetResponse':
        """Ensure status and related fields are consistent."""
        if self.status == DatasetStatus.COMPLETED:
            if self.progress != 100.0:
                raise ValueError("Completed datasets must have 100% progress")
            if self.images_collected == 0:
                raise ValueError("Completed datasets should have collected images")
        
        if self.status == DatasetStatus.FAILED and not self.error_message:
            raise ValueError("Failed datasets must have an error message")
            
        if self.status == DatasetStatus.PENDING and self.progress > 0:
            raise ValueError("Pending datasets should have 0% progress")
            
        if self.download_url and self.status != DatasetStatus.COMPLETED:
            raise ValueError("Download URL should only be available for completed datasets")
            
        return self


class DatasetListResponse(BaseSchema):
    """
    Schema for dataset list response.

    Provides a paginated list of datasets with metadata.

    Attributes:
        data: List of dataset responses
        meta: Pagination metadata
    """

    data: List['DatasetResponse'] = Field(
        ...,
        description="List of datasets",
        examples=[[{
            "id": 1,
            "user_id": 1,
            "name": "Animal Photos",
            "description": "Collection of animal images",
            "keywords": ["cat", "dog", "bird"],
            "max_images": 1000,
            "search_engines": ["google", "bing"],
            "status": "completed",
            "progress": 100.0,
            "images_collected": 950,
            "download_url": "https://storage.example.com/datasets/1/download",
            "error_message": None,
            "created_at": "2024-01-27T10:00:00Z",
            "updated_at": "2024-01-27T11:30:00Z"
        }]]
    )
    meta: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 50},
        description="Pagination metadata",
        examples=[{"total": 25, "skip": 0, "limit": 50}]
    )


class DatasetStats(BaseSchema):
    """
    Dataset statistics schema.

    Provides aggregate statistics about datasets in the system
    for dashboard and reporting purposes.

    Attributes:
        total_datasets: Total number of datasets in the system
        completed_datasets: Number of successfully completed datasets
        processing_datasets: Number of currently processing datasets
        failed_datasets: Number of failed datasets
        total_images: Total number of images collected across all datasets
    """

    total_datasets: int = Field(
        ..., 
        ge=0,
        description="Total number of datasets in the system",
        examples=[0, 150, 1000]
    )
    completed_datasets: int = Field(
        ..., 
        ge=0,
        description="Number of successfully completed datasets",
        examples=[0, 120, 800]
    )
    processing_datasets: int = Field(
        ..., 
        ge=0,
        description="Number of currently processing datasets",
        examples=[0, 5, 20]
    )
    failed_datasets: int = Field(
        ..., 
        ge=0,
        description="Number of failed datasets",
        examples=[0, 10, 50]
    )
    total_images: int = Field(
        ..., 
        ge=0,
        description="Total number of images collected across all datasets",
        examples=[0, 50000, 1000000]
    )

    @model_validator(mode='after')
    def validate_stats_consistency(self) -> 'DatasetStats':
        """Ensure statistics are mathematically consistent."""
        calculated_total = self.completed_datasets + self.processing_datasets + self.failed_datasets
        
        # Allow for pending datasets not explicitly counted
        if calculated_total > self.total_datasets:
            raise ValueError(
                f"Sum of status counts ({calculated_total}) cannot exceed total datasets ({self.total_datasets})"
            )
            
        return self
