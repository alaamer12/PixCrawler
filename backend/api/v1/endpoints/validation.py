"""
Validation service API endpoints.

This module provides API endpoints for image validation services,
including single image analysis, batch validation, results retrieval,
and validation statistics management.
"""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.connection import get_session
from backend.models.base import BaseSchema
from backend.services.validation import ValidationService, ValidationLevel, \
    ValidationStatus

__all__ = ['router']

router = APIRouter()


# Request/Response Models
class ValidationAnalyzeRequest(BaseSchema):
    """Schema for single image validation request."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid'
    }

    image_id: int = Field(
        ...,
        gt=0,
        description="ID of the image to validate",
        examples=[1, 42, 123, 5678]
    )
    validation_level: ValidationLevel = Field(
        default=ValidationLevel.STANDARD,
        description="Level of validation to perform (basic, standard, strict)",
        examples=[ValidationLevel.STANDARD, ValidationLevel.STRICT]
    )


class ValidationBatchRequest(BaseSchema):
    """Schema for batch validation request."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid'
    }

    dataset_id: int = Field(
        ...,
        gt=0,
        description="ID of the dataset to validate",
        examples=[1, 10, 42]
    )
    validation_level: ValidationLevel = Field(
        default=ValidationLevel.STANDARD,
        description="Level of validation to perform (basic, standard, strict)",
        examples=[ValidationLevel.STANDARD, ValidationLevel.STRICT]
    )
    image_ids: Optional[List[int]] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="Optional list of specific image IDs to validate (max 1000)",
        examples=[None, [1, 2, 3, 4, 5]]
    )


class ValidationLevelUpdateRequest(BaseSchema):
    """Schema for updating dataset validation level."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid'
    }

    dataset_id: int = Field(
        ...,
        gt=0,
        description="ID of the dataset",
        examples=[1, 10, 42]
    )
    validation_level: ValidationLevel = Field(
        ...,
        description="New validation level to apply",
        examples=[ValidationLevel.STANDARD, ValidationLevel.STRICT, ValidationLevel.BASIC]
    )


class ValidationAnalyzeResponse(BaseSchema):
    """Schema for single image validation response."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid',
        'use_enum_values': True
    }

    image_id: int = Field(
        ...,
        gt=0,
        description="ID of the validated image",
        examples=[1, 42, 123]
    )
    validation_level: ValidationLevel = Field(
        ...,
        description="Validation level used for analysis",
        examples=[ValidationLevel.STANDARD, ValidationLevel.STRICT]
    )
    is_valid: bool = Field(
        ...,
        description="Whether the image passed validation",
        examples=[True, False]
    )
    quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quality score from 0.0 (worst) to 1.0 (best)",
        examples=[0.95, 0.87, 0.62]
    )
    issues: List[str] = Field(
        ...,
        description="List of validation issues found (empty if valid)",
        examples=[[], ["Low resolution", "Poor lighting"], ["Corrupted file"]]
    )
    metadata: Dict[str, Any] = Field(
        ...,
        description="Additional validation metadata (dimensions, format, etc.)",
        examples=[{"width": 1920, "height": 1080, "format": "jpg"}]
    )
    validated_at: str = Field(
        ...,
        description="ISO 8601 timestamp of validation",
        examples=["2024-01-15T10:30:00Z", "2024-03-20T14:45:30Z"]
    )


class ValidationJobResponse(BaseSchema):
    """Schema for validation job response."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid',
        'use_enum_values': True
    }

    job_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique job identifier (UUID format)",
        examples=["550e8400-e29b-41d4-a716-446655440000", "a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
    )
    dataset_id: int = Field(
        ...,
        gt=0,
        description="Dataset ID being validated",
        examples=[1, 10, 42]
    )
    validation_level: ValidationLevel = Field(
        ...,
        description="Validation level applied to this job",
        examples=[ValidationLevel.STANDARD, ValidationLevel.STRICT]
    )
    total_images: int = Field(
        ...,
        ge=0,
        description="Total number of images to validate in this job",
        examples=[0, 50, 500, 1000]
    )
    status: ValidationStatus = Field(
        ...,
        description="Current job status (pending, processing, completed, failed)",
        examples=[ValidationStatus.PENDING, ValidationStatus.PROCESSING]
    )
    created_at: str = Field(
        ...,
        description="ISO 8601 timestamp of job creation",
        examples=["2024-01-15T10:30:00Z"]
    )


class ValidationResultItem(BaseSchema):
    """Schema for individual validation result."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid'
    }

    image_id: int = Field(
        ...,
        gt=0,
        description="Image ID",
        examples=[1, 42, 123]
    )
    is_valid: bool = Field(
        ...,
        description="Whether the image passed validation",
        examples=[True, False]
    )
    quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quality score from 0.0 to 1.0",
        examples=[0.95, 0.87, 0.62]
    )
    issues: List[str] = Field(
        ...,
        description="List of validation issues found",
        examples=[[], ["Low resolution"], ["Corrupted file", "Invalid format"]]
    )
    validated_at: str = Field(
        ...,
        description="ISO 8601 timestamp of validation",
        examples=["2024-01-15T10:30:00Z"]
    )


class ValidationResultsResponse(BaseSchema):
    """Schema for validation results response."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid',
        'use_enum_values': True
    }

    job_id: str = Field(
        ...,
        min_length=1,
        description="Unique job identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    dataset_id: int = Field(
        ...,
        gt=0,
        description="Dataset ID",
        examples=[1, 10, 42]
    )
    validation_level: ValidationLevel = Field(
        ...,
        description="Validation level used",
        examples=[ValidationLevel.STANDARD]
    )
    status: ValidationStatus = Field(
        ...,
        description="Current job status",
        examples=[ValidationStatus.COMPLETED, ValidationStatus.PROCESSING]
    )
    total_images: int = Field(
        ...,
        ge=0,
        description="Total number of images in job",
        examples=[100, 500, 1000]
    )
    processed_images: int = Field(
        ...,
        ge=0,
        description="Number of images processed so far",
        examples=[50, 100, 500]
    )
    valid_images: int = Field(
        ...,
        ge=0,
        description="Number of images that passed validation",
        examples=[45, 90, 450]
    )
    invalid_images: int = Field(
        ...,
        ge=0,
        description="Number of images that failed validation",
        examples=[5, 10, 50]
    )
    progress: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Progress percentage (0-100)",
        examples=[0.0, 50.5, 100.0]
    )
    created_at: str = Field(
        ...,
        description="ISO 8601 timestamp of job creation",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of last update",
        examples=["2024-01-15T14:45:30Z", None]
    )
    completed_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of job completion",
        examples=["2024-01-15T15:00:00Z", None]
    )
    results: List[ValidationResultItem] = Field(
        ...,
        description="List of individual validation results",
        examples=[[]]
    )


class ValidationStatsResponse(BaseSchema):
    """Schema for dataset validation statistics response."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid'
    }

    dataset_id: int = Field(
        ...,
        gt=0,
        description="Dataset ID",
        examples=[1, 10, 42]
    )
    total_images: int = Field(
        ...,
        ge=0,
        description="Total number of images in dataset",
        examples=[0, 100, 1000, 5000]
    )
    validated_images: int = Field(
        ...,
        ge=0,
        description="Number of images that have been validated",
        examples=[0, 80, 950]
    )
    valid_images: int = Field(
        ...,
        ge=0,
        description="Number of images that passed validation",
        examples=[0, 75, 900]
    )
    invalid_images: int = Field(
        ...,
        ge=0,
        description="Number of images that failed validation",
        examples=[0, 5, 50]
    )
    validation_coverage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of dataset that has been validated (0-100)",
        examples=[0.0, 80.0, 95.0, 100.0]
    )
    average_quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average quality score across all validated images (0.0-1.0)",
        examples=[0.0, 0.85, 0.92]
    )
    total_validation_jobs: int = Field(
        ...,
        ge=0,
        description="Total number of validation jobs run on this dataset",
        examples=[0, 5, 10, 25]
    )


class ValidationLevelUpdateResponse(BaseSchema):
    """Schema for validation level update response."""

    model_config = {
        'str_strip_whitespace': True,
        'validate_assignment': True,
        'extra': 'forbid',
        'use_enum_values': True
    }

    dataset_id: int = Field(
        ...,
        gt=0,
        description="Dataset ID that was updated",
        examples=[1, 10, 42]
    )
    validation_level: ValidationLevel = Field(
        ...,
        description="New validation level applied to dataset",
        examples=[ValidationLevel.STANDARD, ValidationLevel.STRICT]
    )
    updated_at: str = Field(
        ...,
        description="ISO 8601 timestamp of the update",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_by: Optional[int] = Field(
        None,
        gt=0,
        description="User ID who made the update (None if system update)",
        examples=[1, 42, None]
    )


# API Endpoints
@router.post("/analyze/", response_model=ValidationAnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_single_image(
    request: ValidationAnalyzeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ValidationAnalyzeResponse:
    """
    Analyze a single image for quality and content validation.

    Performs comprehensive validation on a single image based on the specified
    validation level. Returns detailed results including quality score and issues.

    Args:
        request: Validation request with image ID and validation level
        current_user: Current authenticated user
        session: Database session

    Returns:
        Validation analysis results

    Raises:
        HTTPException: If image not found or validation fails
    """
    try:
        service = ValidationService(session)

        result = await service.analyze_single_image(
            image_id=request.image_id,
            validation_level=request.validation_level,
            user_id=current_user["user_id"]
        )

        return ValidationAnalyzeResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze image: {str(e)}"
        )


@router.post("/batch/", response_model=ValidationJobResponse, status_code=status.HTTP_201_CREATED)
async def create_batch_validation(
    request: ValidationBatchRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ValidationJobResponse:
    """
    Create a batch validation job for multiple images.

    Creates a new validation job to process multiple images in a dataset.
    The job will be executed in the background and can be monitored using
    the results endpoint.

    Args:
        request: Batch validation request with dataset ID and options
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created validation job information

    Raises:
        HTTPException: If dataset not found or job creation fails
    """
    try:
        service = ValidationService(session)

        job = await service.create_batch_validation_job(
            dataset_id=request.dataset_id,
            validation_level=request.validation_level,
            image_ids=request.image_ids,
            user_id=current_user["user_id"]
        )

        # TODO: Add background task to execute validation job
        # background_tasks.add_task(execute_validation_job, job["job_id"])

        return ValidationJobResponse(**job)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch validation job: {str(e)}"
        )


@router.get("/results/{job_id}/", response_model=ValidationResultsResponse)
async def get_validation_results(
    job_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ValidationResultsResponse:
    """
    Get validation results for a specific job.

    Retrieves detailed results for a validation job, including progress,
    status, and individual image validation results.

    Args:
        job_id: Unique identifier of the validation job
        current_user: Current authenticated user
        session: Database session

    Returns:
        Validation job results and status

    Raises:
        HTTPException: If job not found
    """
    try:
        service = ValidationService(session)

        results = await service.get_validation_results(job_id)

        return ValidationResultsResponse(**results)

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Validation job not found: {job_id}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validation results: {str(e)}"
        )


@router.get("/stats/{dataset_id}/", response_model=ValidationStatsResponse)
async def get_dataset_validation_stats(
    dataset_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ValidationStatsResponse:
    """
    Get validation statistics for a dataset.

    Retrieves comprehensive validation statistics for a dataset, including
    coverage, quality metrics, and job history.

    Args:
        dataset_id: ID of the dataset
        current_user: Current authenticated user
        session: Database session

    Returns:
        Dataset validation statistics

    Raises:
        HTTPException: If dataset not found
    """
    try:
        service = ValidationService(session)

        stats = await service.get_dataset_validation_stats(dataset_id)

        return ValidationStatsResponse(**stats)

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found: {dataset_id}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validation statistics: {str(e)}"
        )


@router.put("/level/", response_model=ValidationLevelUpdateResponse)
async def update_validation_level(
    request: ValidationLevelUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ValidationLevelUpdateResponse:
    """
    Update the validation level for a dataset.

    Changes the default validation level used for new validation jobs
    on the specified dataset.

    Args:
        request: Validation level update request
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated dataset validation level information

    Raises:
        HTTPException: If dataset not found or update fails
    """
    try:
        service = ValidationService(session)

        result = await service.update_dataset_validation_level(
            dataset_id=request.dataset_id,
            validation_level=request.validation_level,
            user_id=current_user["user_id"]
        )

        return ValidationLevelUpdateResponse(**result)

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found: {request.dataset_id}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update validation level: {str(e)}"
        )
