"""
Crawl job management endpoints.

This module provides API endpoints for managing image crawling jobs,
including creation, status monitoring, and execution control.
"""

from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from fastapi_pagination import Page

from backend.api.types import CurrentUser, JobID, CrawlJobServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.core.exceptions import ValidationError, NotFoundError
from backend.models import CrawlJob
from backend.schemas.crawl_jobs import (
    CrawlJobCreate,
    CrawlJobProgress,
    CrawlJobResponse,
    JobLogEntry,
)
from backend.services.crawl_job import execute_crawl_job

__all__ = ['router']

router = APIRouter(
    tags=["Crawl Jobs"],
    responses=get_common_responses(401, 404, 500),
)

@router.get(
    "/",
    response_model=Page[CrawlJobResponse],
    summary="List Crawl Jobs",
    description="Retrieve a paginated list of crawl jobs for the authenticated user.",
    response_description="Paginated list of crawl jobs with status and progress",
    operation_id="listCrawlJobs",
    responses={
        200: {
            "description": "Successfully retrieved crawl jobs",
            "content": {
                "application/json": {
                    "example": {
                        "items": [{"id": 1, "name": "Cat Images", "status": "running", "progress": 45}],
                        "total": 10,
                        "page": 1,
                        "size": 50
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def list_crawl_jobs(
    current_user: CurrentUser,
    service: CrawlJobServiceDep,
) -> Page[CrawlJobResponse]:
    """
    List crawl jobs for the current user with pagination.

    Jobs are filtered by projects owned by the current user.

    **Query Parameters:**
    - `page` (int): Page number (default: 1)
    - `size` (int): Items per page (default: 50, max: 100)

    **Authentication Required:** Bearer token

    Args:
        current_user: Current authenticated user
        service: CrawlJob service (injected)

    Returns:
        Paginated list of crawl jobs
    """
    try:
        # Delegate to service layer
        return await service.list_jobs(user_id=current_user["user_id"])

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list crawl jobs: {str(e)}",
        )


@router.post(
    "/",
    response_model=CrawlJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Crawl Job",
    description="Create a new image crawling job and start execution in background.",
    response_description="Created crawl job with initial status",
    operation_id="createCrawlJob",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
    responses={
        201: {
            "description": "Crawl job created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Cat Images",
                        "keywords": ["cats", "kittens"],
                        "status": "pending",
                        "progress": 0
                    }
                }
            }
        },
        **get_common_responses(401, 422, 429, 500)
    }
)
async def create_crawl_job(
    job_create: CrawlJobCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: CrawlJobServiceDep,
) -> CrawlJobResponse:
    """
    Create a new crawl job.

    Creates a new image crawling job and starts execution in the background.
    The job will process images using the PixCrawler builder.

    **Rate Limit:** 10 requests per minute

    **Authentication Required:** Bearer token

    Args:
        job_create: Crawl job creation data
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        service: CrawlJob service (injected)

    Returns:
        Created crawl job information

    Raises:
        HTTPException: If job creation fails or rate limit exceeded
    """
    try:
        job = await service.create_job(
            project_id=job_create.project_id,
            name=job_create.name,
            keywords=job_create.keywords,
            max_images=job_create.max_images,
            user_id=current_user["user_id"]
        )

        # Start job execution in background
        background_tasks.add_task(execute_crawl_job, job.id)

        # Use service method to convert to response
        return service.to_response(job)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create crawl job: {str(e)}"
        )


@router.get(
    "/{job_id}",
    response_model=CrawlJobResponse,
    summary="Get Crawl Job",
    description="Retrieve detailed information about a specific crawl job.",
    response_description="Crawl job details with current status and progress",
    operation_id="getCrawlJob",
    responses={
        200: {
            "description": "Successfully retrieved crawl job",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Cat Images",
                        "status": "running",
                        "progress": 65,
                        "total_images": 650,
                        "downloaded_images": 650,
                        "valid_images": 612
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_crawl_job(
    job_id: JobID,
    current_user: CurrentUser,
    service: CrawlJobServiceDep,
) -> CrawlJobResponse:
    """
    Get crawl job by ID.

    Retrieves detailed information about a specific crawl job,
    including current status, progress, and image statistics.

    **Authentication Required:** Bearer token

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        service: CrawlJob service (injected)

    Returns:
        Crawl job information

    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        # Service handles ownership verification
        job = await service.get_job_with_ownership_check(
            job_id=job_id,
            user_id=current_user["user_id"]
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        # Use service method to convert to response
        return service.to_response(job)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve crawl job: {str(e)}"
        )


@router.post(
    "/{job_id}/cancel",
    summary="Cancel Crawl Job",
    description="Cancel a running or pending crawl job.",
    response_description="Cancellation confirmation message",
    operation_id="cancelCrawlJob",
    responses={
        200: {
            "description": "Job cancelled successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Crawl job cancelled successfully"}
                }
            }
        },
        400: {
            "description": "Job cannot be cancelled (wrong status)",
            "content": {
                "application/json": {
                    "example": {"detail": "Cannot cancel job with status: completed"}
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def cancel_crawl_job(
    job_id: JobID,
    current_user: CurrentUser,
    service: CrawlJobServiceDep,
) -> dict[str, str]:
    """
    Cancel a running crawl job.

    Attempts to cancel a crawl job that is currently running or pending.
    Completed or failed jobs cannot be cancelled.

    **Authentication Required:** Bearer token

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        service: CrawlJob service (injected)

    Returns:
        Success message

    Raises:
        HTTPException: If job not found, wrong status, or cancellation fails
    """
    try:
        # Call the service cancel_job method
        await service.cancel_job(
            job_id=job_id,
            user_id=current_user["user_id"]
        )

        return {"message": "Crawl job cancelled successfully"}

    except ValidationError as e:
        # Job status doesn't allow cancellation
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawl job not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel crawl job: {str(e)}"
        )


@router.post(
    "/{job_id}/retry",
    response_model=CrawlJobResponse,
    summary="Retry Failed Job",
    description="Retry a failed or cancelled crawl job from the beginning.",
    response_description="Updated job with reset progress",
    operation_id="retryCrawlJob",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
    responses={
        200: {
            "description": "Job retry initiated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Cat Images",
                        "status": "pending",
                        "progress": 0,
                        "total_images": 0
                    }
                }
            }
        },
        400: {
            "description": "Job cannot be retried (wrong status)",
            "content": {
                "application/json": {
                    "example": {"detail": "Only failed or cancelled jobs can be retried (current: running)"}
                }
            }
        },
        **get_common_responses(401, 404, 429, 500)
    }
)
async def retry_crawl_job(
    job_id: JobID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    service: CrawlJobServiceDep,
) -> CrawlJobResponse:
    """
    Retry a failed or cancelled crawl job.

    Resets job progress and schedules execution in the background.
    Only failed or cancelled jobs can be retried.

    **Rate Limit:** 5 requests per minute

    **Authentication Required:** Bearer token

    Args:
        job_id: Crawl job ID
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        service: CrawlJob service (injected)

    Returns:
        Updated crawl job information

    Raises:
        HTTPException: If job not found, wrong status, or retry fails
    """
    try:
        # Service handles ownership check, status validation, and reset
        job = await service.retry_job(
            job_id=job_id,
            user_id=current_user["user_id"]
        )

        # Requeue execution
        background_tasks.add_task(execute_crawl_job, job.id)

        # Use service method to convert to response
        return service.to_response(job)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawl job not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry crawl job: {str(e)}"
        )


@router.get(
    "/{job_id}/logs",
    response_model=List[JobLogEntry],
    summary="Get Job Logs",
    description="Retrieve activity logs for a specific crawl job.",
    response_description="List of job activity log entries",
    operation_id="getCrawlJobLogs",
    responses={
        200: {
            "description": "Successfully retrieved job logs",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "action": "Job started",
                            "timestamp": "2024-01-01T10:00:00Z",
                            "metadata": {"images_target": 1000}
                        },
                        {
                            "action": "Images downloaded",
                            "timestamp": "2024-01-01T10:05:00Z",
                            "metadata": {"count": 250}
                        }
                    ]
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_crawl_job_logs(
    job_id: JobID,
    current_user: CurrentUser,
    service: CrawlJobServiceDep,
) -> List[JobLogEntry]:
    """
    Get activity logs for a crawl job.

    Returns activity entries associated with the job, ordered by timestamp descending.
    Useful for debugging and monitoring job execution.

    **Authentication Required:** Bearer token

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        service: CrawlJob service (injected)

    Returns:
        List of job log entries

    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        # Service handles ownership verification and log retrieval
        logs = await service.get_job_logs(
            job_id=job_id,
            user_id=current_user["user_id"]
        )

        return logs

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crawl job not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve crawl job logs: {str(e)}"
        )


@router.get(
    "/{job_id}/progress",
    response_model=CrawlJobProgress,
    summary="Get Job Progress",
    description="Get real-time progress updates for a running crawl job.",
    response_description="Current job progress with status and metrics",
    operation_id="getCrawlJobProgress",
    responses={
        200: {
            "description": "Successfully retrieved job progress",
            "content": {
                "application/json": {
                    "example": {
                        "status": "running",
                        "progress": 75,
                        "total_images": 750,
                        "downloaded_images": 750,
                        "valid_images": 705,
                        "started_at": "2024-01-01T10:00:00Z",
                        "updated_at": "2024-01-01T10:15:00Z"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def get_crawl_job_progress(
    job_id: JobID,
    current_user: CurrentUser,
    service: CrawlJobServiceDep,
) -> CrawlJobProgress:
    """
    Get real-time progress for a crawl job.

    Returns status and progress metrics for monitoring job execution.
    Useful for polling or displaying progress bars in the UI.

    **Authentication Required:** Bearer token

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        service: CrawlJob service (injected)

    Returns:
        CrawlJobProgress containing status and counters

    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        # Service handles ownership verification
        job = await service.get_job_with_ownership_check(
            job_id=job_id,
            user_id=current_user["user_id"]
        )

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        return CrawlJobProgress(
            status=job.status,
            progress=job.progress,
            total_images=job.total_images,
            downloaded_images=job.downloaded_images,
            valid_images=job.valid_images,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            updated_at=job.updated_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve crawl job progress: {str(e)}"
        )
