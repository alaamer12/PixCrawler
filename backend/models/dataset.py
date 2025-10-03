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

from pydantic import Field, HttpUrl

from .base import BaseSchema, TimestampMixin

__all__ = [
    'DatasetStatus',
    'SearchEngine',
    'DatasetBase',
    'DatasetCreate',
    'DatasetUpdate',
    'DatasetResponse',
    'DatasetStats'
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
    
    name: str = Field(..., min_length=1, max_length=100, description="Dataset name")
    description: Optional[str] = Field(None, max_length=500, description="Dataset description")
    keywords: List[str] = Field(..., min_items=1, description="Search keywords")
    max_images: int = Field(default=100, ge=1, le=10000, description="Maximum number of images")
    search_engines: List[SearchEngine] = Field(
        default=[SearchEngine.GOOGLE],
        description="Search engines to use"
    )


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
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Dataset name")
    description: Optional[str] = Field(None, max_length=500, description="Dataset description")


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
    
    id: int = Field(..., description="Dataset ID")
    user_id: int = Field(..., description="Owner user ID")
    status: DatasetStatus = Field(..., description="Processing status")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Processing progress percentage")
    images_collected: int = Field(default=0, description="Number of images collected")
    download_url: Optional[HttpUrl] = Field(None, description="Download URL when completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")


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
    
    total_datasets: int = Field(..., description="Total number of datasets")
    completed_datasets: int = Field(..., description="Number of completed datasets")
    processing_datasets: int = Field(..., description="Number of processing datasets")
    failed_datasets: int = Field(..., description="Number of failed datasets")
    total_images: int = Field(..., description="Total number of images collected")
