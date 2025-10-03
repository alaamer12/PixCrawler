"""
Base Pydantic models and common schemas for the PixCrawler backend.

This module provides foundational Pydantic models and schemas that are used
throughout the application for request/response validation, pagination,
error handling, and common data structures.

Classes:
    BaseSchema: Base schema with common configuration
    TimestampMixin: Mixin for models with timestamp fields
    PaginationParams: Pagination parameters for list endpoints
    PaginatedResponse: Generic paginated response wrapper
    ErrorDetail: Error detail schema for structured error responses
    HealthCheck: Health check response schema

Features:
    - Consistent model configuration across all schemas
    - Generic pagination support with type safety
    - Structured error response format
    - Timestamp mixin for audit trails
"""

from datetime import datetime
from typing import Any, Generic, TypeVar, Optional, List, Dict

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    'BaseSchema',
    'TimestampMixin',
    'PaginationParams',
    'PaginatedResponse',
    'ErrorDetail',
    'HealthCheck'
]

DataT = TypeVar("DataT")


class BaseSchema(BaseModel):
    """
    Base schema with common configuration for all Pydantic models.
    
    This class provides consistent configuration settings that should be
    inherited by all other schemas in the application.
    
    Configuration:
        - from_attributes: Allow creation from ORM objects
        - validate_assignment: Validate on field assignment
        - arbitrary_types_allowed: Allow arbitrary types
        - str_strip_whitespace: Strip whitespace from strings
    """
    
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
    )


class TimestampMixin(BaseSchema):
    """
    Mixin for models with timestamp fields.
    
    Provides created_at and updated_at fields for models that need
    audit trail functionality.
    
    Attributes:
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PaginationParams(BaseSchema):
    """
    Pagination parameters for list endpoints.
    
    Provides standard pagination parameters with validation
    for page number and size constraints.
    
    Attributes:
        page: Page number (minimum 1)
        size: Page size (1-100 items)
    """
    
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class PaginatedResponse(BaseSchema, Generic[DataT]):
    """
    Generic paginated response wrapper.
    
    Provides a consistent structure for paginated API responses
    with metadata about the pagination state.
    
    Attributes:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number
        size: Page size used
        pages: Total number of pages
    """
    
    items: List[DataT] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class ErrorDetail(BaseSchema):
    """
    Error detail schema for structured error responses.
    
    Provides a consistent format for API error responses
    with optional additional details.
    
    Attributes:
        type: Error type identifier
        message: Human-readable error message
        details: Optional additional error details
    """
    
    type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class HealthCheck(BaseSchema):
    """
    Health check response schema.
    
    Provides information about the service health status
    and basic service metadata.
    
    Attributes:
        status: Service status indicator
        timestamp: Check timestamp
        version: API version
        environment: Environment name
    """
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")
