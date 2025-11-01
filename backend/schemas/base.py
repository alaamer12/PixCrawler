"""
Base Pydantic models and common schemas for the PixCrawler backend.

This module provides foundational Pydantic models and schemas that are used
throughout the application for request/response validation, error handling,
and common data structures.

Classes:
    BaseSchema: Base schema with common configuration
    TimestampMixin: Mixin for models with timestamp fields
    ErrorDetail: Error detail schema for structured error responses
    HealthCheck: Health check response schema

Features:
    - Consistent model configuration across all schemas
    - Structured error response format
    - Timestamp mixin for audit trails

Note:
    Pagination is now handled by fastapi-pagination library.
    Use Page[Model] from fastapi_pagination instead of PaginatedResponse.
"""

from datetime import datetime
from typing import Any, Optional, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = [
    'BaseSchema',
    'TimestampMixin',
    'ErrorDetail',
    'HealthCheck'
]


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
