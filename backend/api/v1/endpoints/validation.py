"""
Validation service API endpoints.

This module provides API endpoints for image validation services,
including single image analysis, batch validation, results retrieval,
and validation statistics management.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from backend.models.base import BaseSchema, TimestampMixin
from backend.database.connection import get_session
from backend.services.validation import ValidationService, ValidationLevel, ValidationStatus
from backend.api.dependencies import get_current_user

__all__ = ['router']

router = APIRouter()


# Request/Response Models
class ValidationAnalyzeRequest(BaseSchema):
    """Schema for single image validation request."""
    
    image_id: int = Field(..., description="ID of the image to validate")
    validation_level: ValidationLevel = Field(
        default=ValidationLevel.STANDARD,
        description="Level of validation to perform"
    )


class ValidationBatchRequest(BaseSchema):
    """Schema for batch validation request."""
    
    dataset_id: int = Field(..., description="ID of the dataset to validate")
    validation_level: ValidationLevel = Field(
        default=ValidationLevel.STANDARD,
        description="Level of validation to perform"
    )
    image_ids: Optional[List[int]] = Field(
        default=None,
        description="Optional list of specific image IDs to validate"
    )


class ValidationLevelUpdateRequest(BaseSchema):
    """Schema for updating dataset validation level."""
    
    dataset_id: int = Field(..., description="ID of the dataset")
    validation_level: ValidationLevel = Field(..., description="New validation level")


class ValidationAnalyzeResponse(BaseSchema):
    """Schema for single image validation response."""
    
    image_id: int = Field(..., description="ID of the validated image")
    validation_level: ValidationLevel = Field(..., description="Validation level used")
    is_valid: bool = Field(..., description="Whether the image is valid")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score (0-1)")
    issues: List[str] = Field(..., description="List of validation issues found")
    metadata: Dict[str, Any] = Field(..., description="Additional validation metadata")
    validated_at: str = Field(..., description="Validation timestamp")


class ValidationJobResponse(BaseSchema):
    """Schema for validation job response."""
    
    job_id: str = Field(..., description="Unique job identifier")
    dataset_id: int = Field(..., description="Dataset ID")
    validation_level: ValidationLevel = Field(..., description="Validation level")
    total_images: int = Field(..., description="Total number of images to validate")
    status: ValidationStatus = Field(..., description="Current job status")
    created_at: str = Field(..., description="Job creation timestamp")


class ValidationResultItem(BaseSchema):
    """Schema for individual validation result."""
    
    image_id: int = Field(..., description="Image ID")
    is_valid: bool = Field(..., description="Whether the image is valid")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score")
    issues: List[str] = Field(..., description="Validation issues")
    validated_at: str = Field(..., description="Validation timestamp")


class ValidationResultsResponse(BaseSchema):
    """Schema for validation results response."""
    
    job_id: str = Field(..., description="Job ID")
    dataset_id: int = Field(..., description="Dataset ID")
    validation_level: ValidationLevel = Field(..., description="Validation level")
    status: ValidationStatus = Field(..., description="Job status")
    total_images: int = Field(..., description="Total images")
    processed_images: int = Field(..., description="Processed images")
    valid_images: int = Field(..., description="Valid images")
    invalid_images: int = Field(..., description="Invalid images")
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")
    results: List[ValidationResultItem] = Field(..., description="Validation results")


class ValidationStatsResponse(BaseSchema):
    """Schema for dataset validation statistics response."""
    
    dataset_id: int = Field(..., description="Dataset ID")
    total_images: int = Field(..., description="Total images in dataset")
    validated_images: int = Field(..., description="Number of validated images")
    valid_images: int = Field(..., description="Number of valid images")
    invalid_images: int = Field(..., description="Number of invalid images")
    validation_coverage: float = Field(..., ge=0.0, le=100.0, description="Validation coverage percentage")
    average_quality_score: float = Field(..., ge=0.0, le=1.0, description="Average quality score")
    total_validation_jobs: int = Field(..., description="Total validation jobs run")


class ValidationLevelUpdateResponse(BaseSchema):
    """Schema for validation level update response."""
    
    dataset_id: int = Field(..., description="Dataset ID")
    validation_level: ValidationLevel = Field(..., description="Updated validation level")
    updated_at: str = Field(..., description="Update timestamp")
    updated_by: Optional[int] = Field(None, description="User who made the update")


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
