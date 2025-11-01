"""
Dataset management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from fastapi_pagination import Page

from backend.api.types import CurrentUser, DBSession, DatasetID
from backend.schemas.dataset import DatasetCreate, DatasetResponse, DatasetStats, DatasetUpdate
from backend.services.dataset import DatasetService

router = APIRouter(prefix="/api/v1/datasets")


@router.post(
    "/",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def create_dataset(
    dataset_create: DatasetCreate,
    current_user: CurrentUser,
    dataset_service: DatasetService = Depends(),
) -> DatasetResponse:
    """
    Create a new dataset generation job.

    Args:
        dataset_create: Dataset creation data
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Created dataset information

    Raises:
        HTTPException: If dataset creation fails
    """
    try:
        dataset = await dataset_service.create_dataset(dataset_create, current_user["user_id"])
        return dataset
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=Page[DatasetResponse])
async def list_datasets(
    current_user: CurrentUser,
    session: DBSession,
    dataset_service: DatasetService = Depends(),
) -> Page[DatasetResponse]:
    """
    List datasets with pagination.

    Pagination is handled automatically by fastapi-pagination.
    Query parameters: page (default=1), size (default=50)

    Args:
        current_user: Current authenticated user
        session: Database session
        dataset_service: Dataset service dependency

    Returns:
        Paginated list of datasets
    """
    # TODO: Implement list_datasets in DatasetService with pagination
    raise HTTPException(status_code=501, detail="List datasets not implemented yet")


@router.get("/stats", response_model=DatasetStats)
async def get_dataset_stats(
    dataset_service: DatasetService = Depends(),
) -> DatasetStats:
    """
    Get dataset statistics.

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


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetService = Depends(),
) -> DatasetResponse:
    """
    Get dataset by ID.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Dataset information

    Raises:
        HTTPException: If dataset not found
    """
    dataset = await dataset_service.get_dataset_by_id(dataset_id, current_user["user_id"])
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
    dataset_id: DatasetID,
    dataset_update: DatasetUpdate,
    current_user: CurrentUser,
    dataset_service: DatasetService = Depends(),
) -> DatasetResponse:
    """
    Update dataset information.

    Args:
        dataset_id: Dataset ID
        dataset_update: Dataset update data
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Updated dataset information

    Raises:
        HTTPException: If dataset not found or update fails
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


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetService = Depends(),
) -> None:
    """
    Delete dataset.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Raises:
        HTTPException: If dataset not found or deletion fails
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
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def start_build_job(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetService = Depends(),
) -> DatasetResponse:
    """
    Start dataset build job.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Updated dataset information

    Raises:
        HTTPException: If dataset not found or build start fails
    """
    # TODO: Implement start_build_job in DatasetService
    raise HTTPException(status_code=501, detail="Start build job not implemented yet")


@router.get("/{dataset_id}/status", response_model=DatasetResponse)
async def get_dataset_status(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetService = Depends(),
) -> DatasetResponse:
    """
    Get dataset build status.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Dataset build status information

    Raises:
        HTTPException: If dataset not found
    """
    # TODO: Implement get_build_status in DatasetService
    raise HTTPException(status_code=501, detail="Get build status not implemented yet")


@router.post("/{dataset_id}/download", response_model=dict[str, str])
async def generate_download_link(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetService = Depends(),
) -> dict[str, str]:
    """
    Generate dataset download link.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Download link information

    Raises:
        HTTPException: If dataset not found or link generation fails
    """
    # TODO: Implement generate_download_link in DatasetService
    raise HTTPException(status_code=501, detail="Generate download link not implemented yet")


@router.post("/{dataset_id}/cancel", response_model=DatasetResponse)
async def cancel_dataset(
    dataset_id: DatasetID,
    current_user: CurrentUser,
    dataset_service: DatasetService = Depends(),
) -> DatasetResponse:
    """
    Cancel dataset processing.

    Args:
        dataset_id: Dataset ID
        current_user: Current authenticated user
        dataset_service: Dataset service dependency

    Returns:
        Updated dataset information

    Raises:
        HTTPException: If dataset not found or cancellation fails
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
