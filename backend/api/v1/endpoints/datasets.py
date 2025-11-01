"""
Dataset management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from fastapi_pagination import Page

from backend.api.types import CurrentUser, DBSession, DatasetID, DatasetServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.schemas.dataset import DatasetCreate, DatasetResponse, DatasetStats, DatasetUpdate

router = APIRouter(
    tags=["Datasets"],
    responses=get_common_responses(401, 404, 500),
)


@router.post(
    "/",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Dataset",
    description="Create a new dataset with configuration for image collection.",
    response_description="Created dataset with initial configuration",
    operation_id="createDataset",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
    responses={
        201: {
            "description": "Dataset created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Animal Dataset",
                        "status": "pending",
                        "total_images": 0
                    }
                }
            }
        },
        **get_common_responses(401, 422, 429, 500)
    }
)
async def create_dataset(
    dataset_create: DatasetCreate,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> DatasetResponse:
    """
    Create a new dataset generation job.

    **Rate Limit:** 10 requests per minute

    **Authentication Required:** Bearer token

    Args:
        dataset_create: Dataset creation data
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Created dataset information

    Raises:
        HTTPException: If dataset creation fails or rate limit exceeded
    """
    try:
        dataset = await dataset_service.create_dataset(dataset_create, current_user["user_id"])
        return dataset
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/",
    response_model=Page[DatasetResponse],
    summary="List Datasets",
    description="Retrieve a paginated list of datasets for the authenticated user.",
    response_description="Paginated list of datasets",
    operation_id="listDatasets",
    responses={
        200: {
            "description": "Successfully retrieved datasets",
            "content": {
                "application/json": {
                    "example": {
                        "items": [{"id": 1, "name": "Animal Dataset", "status": "completed"}],
                        "total": 5,
                        "page": 1,
                        "size": 50
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def list_datasets(
    current_user: CurrentUser,
    session: DBSession,
    dataset_service: DatasetServiceDep,
) -> Page[DatasetResponse]:
    """
    List datasets with pagination.

    **Query Parameters:**
    - `page` (int): Page number (default: 1)
    - `size` (int): Items per page (default: 50, max: 100)

    **Authentication Required:** Bearer token

    Args:
        current_user: Current authenticated user
        session: Database session
        dataset_service: Dataset service dependency

    Returns:
        Paginated list of datasets
    """
    # TODO: Implement list_datasets in DatasetService with pagination
    raise HTTPException(status_code=501, detail="List datasets not implemented yet")


@router.get(
    "/stats",
    response_model=DatasetStats,
    summary="Get Dataset Statistics",
    description="Retrieve aggregate statistics across all datasets.",
    response_description="Dataset statistics and metrics",
    operation_id="getDatasetStats",
    responses={
        200: {
            "description": "Successfully retrieved statistics",
            "content": {
                "application/json": {
                    "example": {
                        "total_datasets": 10,
                        "total_images": 15000,
                        "active_builds": 2
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def get_dataset_stats(
    dataset_service: DatasetServiceDep,
) -> DatasetStats:
    """
    Get dataset statistics.

    **Authentication Required:** Bearer token

    Args:
        dataset_service: Dataset service dependency

    Returns:
        Dataset statistics
    """
    try:
        stats = await dataset_service.get_dataset_stats()
        return stats
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Dataset statistics not implemented yet")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Get Dataset",
    description="Retrieve detailed information about a specific dataset.",
    response_description="Dataset details with status and configuration",
    operation_id="getDataset",
    responses={
        200: {
            "description": "Successfully retrieved dataset",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Animal Dataset",
                        "status": "completed",
                        "total_images": 1500
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_dataset(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> DatasetResponse:
    """
    Get dataset by ID.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Dataset information

    Raises:
        HTTPException: If dataset not found or access denied
    """
    dataset = await dataset_service.get_dataset_by_id(dataset_id, current_user["user_id"])
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.put(
    "/{dataset_id}",
    response_model=DatasetResponse,
    summary="Update Dataset",
    description="Update dataset configuration and metadata.",
    response_description="Updated dataset information",
    operation_id="updateDataset",
    responses={
        200: {
            "description": "Dataset updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Updated Animal Dataset",
                        "status": "completed"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 422, 500)
    }
)
async def update_dataset(
    dataset_id: DatasetID,
    dataset_update: DatasetUpdate,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> DatasetResponse:
    """
    Update dataset information.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID
        dataset_update: Dataset update data
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Updated dataset information

    Raises:
        HTTPException: If dataset not found, validation fails, or access denied
    """
    try:
        dataset = await dataset_service.update_dataset(dataset_id, dataset_update, current_user["user_id"])
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return dataset
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Dataset",
    description="Permanently delete a dataset and all associated images.",
    response_description="Dataset deleted successfully (no content)",
    operation_id="deleteDataset",
    responses={
        204: {
            "description": "Dataset deleted successfully"
        },
        **get_common_responses(401, 404, 500)
    }
)
async def delete_dataset(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> None:
    """
    Delete dataset.

    **Warning:** This action is permanent and will delete all associated images.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Raises:
        HTTPException: If dataset not found, access denied, or deletion fails
    """
    try:
        result = await dataset_service.delete_dataset(dataset_id, current_user["user_id"])
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{dataset_id}/build",
    response_model=DatasetResponse,
    summary="Start Dataset Build",
    description="Start building/processing a dataset.",
    response_description="Dataset with build status initiated",
    operation_id="startDatasetBuild",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    responses={
        200: {
            "description": "Build started successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Animal Dataset",
                        "status": "building"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 429, 500)
    }
)
async def start_build_job(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> DatasetResponse:
    """
    Start dataset build job.

    **Rate Limit:** 5 requests per minute

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Updated dataset information

    Raises:
        HTTPException: If dataset not found, build start fails, or rate limit exceeded
    """
    # TODO: Implement start_build_job in DatasetService
    raise HTTPException(status_code=501, detail="Start build job not implemented yet")


@router.get(
    "/{dataset_id}/status",
    response_model=DatasetResponse,
    summary="Get Build Status",
    description="Get current build status and progress for a dataset.",
    response_description="Dataset build status and progress",
    operation_id="getDatasetBuildStatus",
    responses={
        200: {
            "description": "Successfully retrieved build status",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "status": "building",
                        "progress": 45,
                        "total_images": 450
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_dataset_status(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> DatasetResponse:
    """
    Get dataset build status.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Dataset build status information

    Raises:
        HTTPException: If dataset not found or access denied
    """
    # TODO: Implement get_build_status in DatasetService
    raise HTTPException(status_code=501, detail="Get build status not implemented yet")


@router.post(
    "/{dataset_id}/download",
    response_model=dict[str, str],
    summary="Generate Download Link",
    description="Generate a temporary download link for a completed dataset.",
    response_description="Download URL with expiration",
    operation_id="generateDatasetDownloadLink",
    responses={
        200: {
            "description": "Download link generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "download_url": "https://storage.example.com/dataset-1.zip?token=abc123",
                        "expires_at": "2024-01-01T12:00:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def generate_download_link(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> dict[str, str]:
    """
    Generate dataset download link.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Download link information with expiration time

    Raises:
        HTTPException: If dataset not found, not completed, or link generation fails
    """
    # TODO: Implement generate_download_link in DatasetService
    raise HTTPException(status_code=501, detail="Generate download link not implemented yet")


@router.post(
    "/{dataset_id}/cancel",
    response_model=DatasetResponse,
    summary="Cancel Dataset Build",
    description="Cancel an ongoing dataset build process.",
    response_description="Dataset with cancelled status",
    operation_id="cancelDatasetBuild",
    responses={
        200: {
            "description": "Build cancelled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Animal Dataset",
                        "status": "cancelled"
                    }
                }
            }
        },
        400: {
            "description": "Dataset cannot be cancelled (wrong status)",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot cancel completed dataset"}
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def cancel_dataset(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> DatasetResponse:
    """
    Cancel dataset processing.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Updated dataset information

    Raises:
        HTTPException: If dataset not found, wrong status, or cancellation fails
    """
    try:
        dataset = await dataset_service.cancel_dataset(dataset_id, current_user["user_id"])
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return dataset
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
