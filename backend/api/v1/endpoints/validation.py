"""Validation service API endpoints.

This module provides API endpoints for image validation services,
including single image analysis, batch validation, results retrieval,
and validation statistics management."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, status as http_status

from backend.api.types import CurrentUser, ValidationServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.core.exceptions import NotFoundError
from backend.schemas.validation import (
    ValidationAnalyzeRequest,
    ValidationAnalyzeResponse,
    ValidationBatchRequest,
    ValidationJobResponse,
    ValidationLevelUpdateRequest,
    ValidationLevelUpdateResponse,
    ValidationRequest,
    ValidationResponse,
    ValidationResultsResponse,
    ValidationStatsResponse,
)

__all__ = ['router']

router = APIRouter(
    tags=["Validation"],
    responses=get_common_responses(401, 404, 500),
)


# API Endpoints
@router.post(
    "/analyze/",
    response_model=ValidationAnalyzeResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Analyze Single Image",
    description="Perform quality and content validation on a single image.",
    response_description="Validation analysis results with quality score",
    operation_id="analyzeSingleImage",
    responses={
        200: {
            "description": "Image analyzed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "image_id": 1,
                        "quality_score": 0.85,
                        "is_valid": True,
                        "issues": []
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def analyze_single_image(
    request: ValidationAnalyzeRequest,
    current_user: CurrentUser,
    service: ValidationServiceDep,
) -> ValidationAnalyzeResponse:
    """
    Analyze a single image for quality and content validation.

    Performs comprehensive validation based on the specified validation level.
    Returns quality score, validity status, and any detected issues.

    **Authentication Required:** Bearer token

    Args:
        request: Validation request with image ID and validation level
        current_user: Current authenticated user
        service: Validation service

    Returns:
        Validation analysis results

    Raises:
        HTTPException: If image not found or validation fails
    """
    try:
        result = await service.analyze_single_image(
            image_id=request.image_id,
            validation_level=request.validation_level,
            user_id=current_user["user_id"]
        )

        return ValidationAnalyzeResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze image: {str(e)}"
        )


@router.post(
    "/batch/",
    response_model=ValidationJobResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create Batch Validation",
    description="Create a batch validation job for multiple images.",
    response_description="Created validation job with status",
    operation_id="createBatchValidation",
    responses={
        201: {
            "description": "Validation job created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "val-123",
                        "status": "pending",
                        "total_images": 100
                    }
                }
            }
        },
        **get_common_responses(401, 404, 422, 500)
    }
)
async def create_batch_validation(
    request: ValidationBatchRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: ValidationServiceDep,
) -> ValidationJobResponse:
    """
    Create a batch validation job for multiple images.

    Creates a validation job to process multiple images in the background.
    Monitor progress using the results endpoint.

    **Authentication Required:** Bearer token

    Args:
        request: Batch validation request with dataset ID and options
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        service: Validation service (injected)

    Returns:
        Created validation job information

    Raises:
        HTTPException: If dataset not found or job creation fails
    """
    try:
        # Use injected service instead of creating new instance
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
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch validation job: {str(e)}"
        )


@router.post(
    "/job/{job_id}/",
    response_model=ValidationResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Validate Job Images",
    description="Validate all images in a crawl job.",
    response_description="Validation job started with task IDs",
    operation_id="validateJobImages",
    responses={
        200: {
            "description": "Validation started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": 123,
                        "images_count": 100,
                        "validation_level": "standard",
                        "task_ids": ["task_123_0", "task_123_1"],
                        "message": "Validation started for 100 images"
                    }
                }
            }
        },
        **get_common_responses(401, 403, 404, 422, 500)
    }
)
async def validate_job_images(
    job_id: int,
    request: ValidationRequest,
    current_user: CurrentUser,
    service: ValidationServiceDep,
) -> ValidationResponse:
    """
    Validate all images in a crawl job.

    Retrieves all images for the specified job and dispatches validation
    tasks via Celery based on the requested validation level.

    **Authentication Required:** Bearer token

    Args:
        job_id: ID of the crawl job
        request: Validation request with level
        current_user: Current authenticated user
        service: Validation service

    Returns:
        Validation job information with task IDs

    Raises:
        HTTPException: If job not found, no images, or validation fails
    """
    try:
        result = await service.validate_job_images(
            job_id=job_id,
            validation_level=request.level,
            user_id=current_user["user_id"]
        )

        return ValidationResponse(**result)

    except NotFoundError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start validation: {str(e)}"
        )


@router.get(
    "/results/{job_id}/",
    response_model=ValidationResultsResponse,
    summary="Get Validation Results",
    description="Retrieve results for a specific validation job.",
    response_description="Validation job results with progress and status",
    operation_id="getValidationResults",
    responses={
        200: {
            "description": "Successfully retrieved validation results",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "val-123",
                        "status": "completed",
                        "progress": 100,
                        "valid_images": 85,
                        "invalid_images": 15
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_validation_results(
    job_id: str,
    current_user: CurrentUser,
    service: ValidationServiceDep,
) -> ValidationResultsResponse:
    """
    Get validation results for a specific job.

    Retrieves detailed results including progress, status,
    and individual image validation results.

    **Authentication Required:** Bearer token

    Args:
        job_id: Unique identifier of the validation job
        current_user: Current authenticated user
        service: Validation service

    Returns:
        Validation job results and status

    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        results = await service.get_validation_results(job_id)

        return ValidationResultsResponse(**results)

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Validation job not found: {job_id}"
            )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validation results: {str(e)}"
        )


@router.get(
    "/stats/{dataset_id}/",
    response_model=ValidationStatsResponse,
    summary="Get Dataset Validation Stats",
    description="Retrieve validation statistics for a dataset.",
    response_description="Dataset validation statistics and metrics",
    operation_id="getDatasetValidationStats",
    responses={
        200: {
            "description": "Successfully retrieved validation statistics",
            "content": {
                "application/json": {
                    "example": {
                        "dataset_id": 1,
                        "total_images": 1000,
                        "validated_images": 950,
                        "average_quality_score": 0.87
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_dataset_validation_stats(
    dataset_id: int,
    current_user: CurrentUser,
    service: ValidationServiceDep,
) -> ValidationStatsResponse:
    """
    Get validation statistics for a dataset.

    Retrieves comprehensive validation statistics including
    coverage, quality metrics, and job history.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: ID of the dataset
        current_user: Current authenticated user
        service: Validation service

    Returns:
        Dataset validation statistics

    Raises:
        HTTPException: If dataset not found or access denied
    """
    try:
        stats = await service.get_dataset_validation_stats(dataset_id)

        return ValidationStatsResponse(**stats)

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found: {dataset_id}"
            )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validation statistics: {str(e)}"
        )


@router.put(
    "/level/",
    response_model=ValidationLevelUpdateResponse,
    summary="Update Validation Level",
    description="Update the default validation level for a dataset.",
    response_description="Updated validation level configuration",
    operation_id="updateValidationLevel",
    responses={
        200: {
            "description": "Validation level updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "dataset_id": 1,
                        "validation_level": "strict",
                        "updated_at": "2024-01-01T12:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 422, 500)
    }
)
async def update_validation_level(
    request: ValidationLevelUpdateRequest,
    current_user: CurrentUser,
    service: ValidationServiceDep,
) -> ValidationLevelUpdateResponse:
    """
    Update the validation level for a dataset.

    Changes the default validation level used for new validation jobs
    on the specified dataset.

    **Authentication Required:** Bearer token

    Args:
        request: Validation level update request
        current_user: Current authenticated user
        service: Validation service

    Returns:
        Updated dataset validation level information

    Raises:
        HTTPException: If dataset not found, validation fails, or access denied
    """
    try:
        result = await service.update_dataset_validation_level(
            dataset_id=request.dataset_id,
            validation_level=request.validation_level,
            user_id=current_user["user_id"]
        )

        return ValidationLevelUpdateResponse(**result)

    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found: {request.dataset_id}"
            )
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update validation level: {str(e)}"
        )
