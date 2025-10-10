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

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
        - extra: Forbid extra fields for strict validation
        - use_enum_values: Use enum values in serialization
    """

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        extra='forbid',
        use_enum_values=True,
        validate_default=True
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

    created_at: datetime = Field(
        ..., 
        description="Creation timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: datetime = Field(
        ..., 
        description="Last update timestamp",
        examples=["2024-01-15T14:45:30Z"]
    )

    @model_validator(mode='after')
    def validate_timestamps(self) -> 'TimestampMixin':
        """Ensure updated_at is not before created_at."""
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be before created_at")
        return self


class PaginationParams(BaseSchema):
    """
    Pagination parameters for list endpoints.

    Provides standard pagination parameters with validation
    for page number and size constraints.

    Attributes:
        page: Page number (minimum 1)
        size: Page size (1-100 items)
    """

    page: int = Field(
        default=1, 
        ge=1, 
        le=10000,
        description="Page number",
        examples=[1, 2, 10]
    )
    size: int = Field(
        default=20, 
        ge=1, 
        le=100, 
        description="Page size",
        examples=[10, 20, 50, 100]
    )

    @field_validator('page', 'size')
    @classmethod
    def validate_positive_integers(cls, v: int) -> int:
        """Ensure pagination parameters are positive."""
        if v <= 0:
            raise ValueError("Pagination parameters must be positive")
        return v


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

    items: List[DataT] = Field(
        ..., 
        description="List of items",
        examples=[[]]
    )
    total: int = Field(
        ..., 
        ge=0,
        description="Total number of items",
        examples=[0, 150, 1000]
    )
    page: int = Field(
        ..., 
        ge=1,
        description="Current page number",
        examples=[1, 2, 5]
    )
    size: int = Field(
        ..., 
        ge=1, 
        le=100,
        description="Page size",
        examples=[10, 20, 50]
    )
    pages: int = Field(
        ..., 
        ge=0,
        description="Total number of pages",
        examples=[0, 8, 20]
    )

    @model_validator(mode='after')
    def validate_pagination_consistency(self) -> 'PaginatedResponse[DataT]':
        """Ensure pagination metadata is consistent."""
        if self.total == 0:
            if self.pages != 0 or len(self.items) != 0:
                raise ValueError("Empty result should have 0 pages and no items")
        else:
            expected_pages = (self.total + self.size - 1) // self.size
            if self.pages != expected_pages:
                raise ValueError(f"Pages count {self.pages} doesn't match expected {expected_pages}")
            
            if self.page > self.pages:
                raise ValueError(f"Current page {self.page} exceeds total pages {self.pages}")
                
        return self


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

    type: str = Field(
        ..., 
        min_length=1,
        max_length=100,
        description="Error type identifier",
        examples=["validation_error", "not_found", "permission_denied"]
    )
    message: str = Field(
        ..., 
        min_length=1,
        max_length=500,
        description="Human-readable error message",
        examples=["Invalid input data", "Resource not found", "Access denied"]
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details",
        examples=[{"field": "email", "code": "invalid_format"}]
    )

    @field_validator('type', 'message')
    @classmethod
    def validate_non_empty_strings(cls, v: str) -> str:
        """Ensure error strings are not empty after stripping."""
        if not v.strip():
            raise ValueError("Error type and message cannot be empty")
        return v.strip()


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

    status: str = Field(
        ..., 
        pattern=r'^(healthy|unhealthy|degraded)$',
        description="Service status indicator",
        examples=["healthy", "unhealthy", "degraded"]
    )
    timestamp: datetime = Field(
        ..., 
        description="Check timestamp",
        examples=["2024-01-15T10:30:00Z"]
    )
    version: str = Field(
        ..., 
        min_length=1,
        max_length=20,
        pattern=r'^\d+\.\d+\.\d+$',
        description="API version",
        examples=["1.0.0", "2.1.3"]
    )
    environment: str = Field(
        ..., 
        min_length=1,
        max_length=20,
        description="Environment name",
        examples=["development", "staging", "production"]
    )

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        valid_environments = {"development", "staging", "production", "test"}
        if v.lower() not in valid_environments:
            raise ValueError(f"Environment must be one of: {', '.join(valid_environments)}")
        return v.lower()
