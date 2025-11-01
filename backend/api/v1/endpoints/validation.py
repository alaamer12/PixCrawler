"""
Validation service API endpoints.

This module provides API endpoints for image validation services,
including single image analysis, batch validation, results retrieval,
and validation statistics management.
"""

from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.database.connection import get_session
from backend.schemas.validation import (
    ValidationAnalyzeRequest,
    ValidationAnalyzeResponse,
    ValidationBatchRequest,
    ValidationJobResponse,
    ValidationLevelUpdateRequest,
    ValidationLevelUpdateResponse,
    ValidationResultsResponse,
    ValidationStatsResponse,
)
from backend.services.validation import ValidationService

__all__ = ['router']

router = APIRouter()




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
