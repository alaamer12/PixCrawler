"""
Validation schemas for PixCrawler.

This module defines Pydantic schemas for image validation services,
including analysis requests, batch operations, and statistics.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
    'ValidationLevel',
    'ValidationStatus',
    'ValidationAnalyzeRequest',
    'ValidationBatchRequest',
    'ValidationLevelUpdateRequest',
    'ValidationAnalyzeResponse',
    'ValidationJobResponse',
    'ValidationResultItem',
    'ValidationResultsResponse',
    'ValidationStatsResponse',
    'ValidationLevelUpdateResponse',
]


class ValidationLevel(str, Enum):
    """Validation levels."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class ValidationStatus(str, Enum):
    """Validation statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationAnalyzeRequest(BaseModel):
    """Schema for single image validation request."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )
    
    image_id: int = Field(
        gt=0,
        description="ID of the image to validate",
        examples=[1, 42, 123, 5678],
    )
    
    validation_level: ValidationLevel = Field(
        default=ValidationLevel.STANDARD,
        description="Level of validation to perform",
        examples=[ValidationLevel.STANDARD, ValidationLevel.STRICT],
    )


class ValidationBatchRequest(BaseModel):
    """Schema for batch validation request."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )
    
    image_ids: list[int] = Field(
        min_length=1,
        max_length=1000,
        description="List of image IDs to validate",
        examples=[[1, 2, 3], [100, 200, 300]],
    )
    
    validation_level: ValidationLevel = Field(
        default=ValidationLevel.STANDARD,
        description="Level of validation to perform",
    )
    
    @field_validator('image_ids')
    @classmethod
    def validate_image_ids(cls, v: list[int]) -> list[int]:
        """Validate image IDs."""
        if any(id <= 0 for id in v):
            raise ValueError('All image IDs must be positive integers')
        
        # Remove duplicates
        return list(set(v))


class ValidationLevelUpdateRequest(BaseModel):
    """Schema for updating dataset validation level."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
    )
    
    dataset_id: int = Field(
        gt=0,
        description="Dataset ID",
        examples=[1, 42, 123],
    )
    
    validation_level: ValidationLevel = Field(
        description="New validation level",
        examples=[ValidationLevel.STANDARD, ValidationLevel.STRICT],
    )


class ValidationAnalyzeResponse(BaseModel):
    """Schema for single image validation response."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    image_id: int = Field(description="Image ID")
    is_valid: bool = Field(description="Whether image is valid")
    validation_level: ValidationLevel = Field(description="Validation level used")
    checks_passed: int = Field(ge=0, description="Number of checks passed")
    checks_failed: int = Field(ge=0, description="Number of checks failed")
    issues: list[str] = Field(default_factory=list, description="List of issues found")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    validated_at: datetime = Field(description="Validation timestamp")


class ValidationJobResponse(BaseModel):
    """Schema for validation job response."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    job_id: str = Field(description="Job ID")
    status: ValidationStatus = Field(description="Job status")
    total_images: int = Field(ge=0, description="Total images to validate")
    processed_images: int = Field(ge=0, description="Images processed")
    valid_images: int = Field(ge=0, description="Valid images")
    invalid_images: int = Field(ge=0, description="Invalid images")
    validation_level: ValidationLevel = Field(description="Validation level")
    started_at: datetime = Field(description="Start timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Completion timestamp")


class ValidationResultItem(BaseModel):
    """Schema for individual validation result."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    image_id: int = Field(description="Image ID")
    is_valid: bool = Field(description="Whether image is valid")
    checks_passed: int = Field(ge=0, description="Checks passed")
    checks_failed: int = Field(ge=0, description="Checks failed")
    issues: list[str] = Field(default_factory=list, description="Issues found")
    validated_at: datetime = Field(description="Validation timestamp")


class ValidationResultsResponse(BaseModel):
    """Schema for validation results response."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    job_id: str = Field(description="Job ID")
    status: ValidationStatus = Field(description="Job status")
    results: list[ValidationResultItem] = Field(description="Validation results")
    summary: dict[str, Any] = Field(description="Summary statistics")


class ValidationStatsResponse(BaseModel):
    """Schema for dataset validation statistics response."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    dataset_id: int = Field(description="Dataset ID")
    total_images: int = Field(ge=0, description="Total images")
    validated_images: int = Field(ge=0, description="Validated images")
    valid_images: int = Field(ge=0, description="Valid images")
    invalid_images: int = Field(ge=0, description="Invalid images")
    validation_level: ValidationLevel = Field(description="Current validation level")
    last_validated_at: Optional[datetime] = Field(default=None, description="Last validation timestamp")
    common_issues: list[dict[str, Any]] = Field(default_factory=list, description="Common issues")


class ValidationLevelUpdateResponse(BaseModel):
    """Schema for validation level update response."""
    
    model_config = ConfigDict(use_enum_values=True)
    
    dataset_id: int = Field(description="Dataset ID")
    old_level: ValidationLevel = Field(description="Previous validation level")
    new_level: ValidationLevel = Field(description="New validation level")
    updated_at: datetime = Field(description="Update timestamp")
    message: str = Field(description="Success message")
