"""
Crawl job management endpoints.

This module provides API endpoints for managing image crawling jobs,
including creation, status monitoring, and execution control.
"""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select

from backend.api.types import CurrentUser, DBSession, JobID, CrawlJobServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.models import ActivityLog, Project
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
    session: DBSession,
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
        session: Database session

    Returns:
        Paginated list of crawl jobs
    """
    try:
        # Build query for user's crawl jobs
        query = (
            select(CrawlJob)
            .join(Project, Project.id == CrawlJob.project_id)
            .where(Project.user_id == uuid.UUID(current_user["user_id"]))
            .order_by(CrawlJob.created_at.desc())
        )

        # Use fastapi-pagination's paginate function
        return await paginate(session, query)

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

        return CrawlJobResponse(
            id=job.id,
            project_id=job.project_id,
            name=job.name,
            keywords=job.keywords,
            max_images=job.max_images,
            search_engine="duckduckgo",  # Default, not stored in DB
            status=job.status,
            progress=job.progress,
            total_images=job.total_images,
            downloaded_images=job.downloaded_images,
            valid_images=job.valid_images,
            config={},  # Default empty config
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )

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
    session: DBSession,
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
        session: Database session (for ownership check)
        service: CrawlJob service (injected)

    Returns:
        Crawl job information

    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        job = await service.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        # Ensure the job belongs to the current user via its project
        owner_query = (
            select(Project.user_id)
            .where(Project.id == job.project_id)
        )
        owner_result = await session.execute(owner_query)
        owner_id = owner_result.scalar_one_or_none()
        if str(owner_id) != str(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        return CrawlJobResponse(
            id=job.id,
            project_id=job.project_id,
            name=job.name,
            keywords=job.keywords,
            max_images=job.max_images,
            search_engine="duckduckgo",  # Default, not stored in DB
            status=job.status,
            progress=job.progress,
            total_images=job.total_images,
            downloaded_images=job.downloaded_images,
            valid_images=job.valid_images,
            config={},  # Default empty config
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )

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
        job = await service.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        if job.status not in ["pending", "running"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status: {job.status}"
            )

        # TODO: Implement cancel logic in service
        # await service.cancel_job(job_id)

        return {"message": "Crawl job cancelled successfully"}

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
    session: DBSession,
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
        session: Database session (for ownership check)
        service: CrawlJob service (injected)

    Returns:
        Updated crawl job information

    Raises:
        HTTPException: If job not found, wrong status, or retry fails
    """
    try:
        job = await service.get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        # Ensure ownership
        owner_query = (
            select(Project.user_id)
            .where(Project.id == job.project_id)
        )
        owner_result = await session.execute(owner_query)
        owner_id = owner_result.scalar_one_or_none()
        if str(owner_id) != str(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        if job.status not in ["failed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only failed or cancelled jobs can be retried (current: {job.status})"
            )

        # Reset job state
        job.status = "pending"
        job.progress = 0
        job.total_images = 0
        job.downloaded_images = 0
        job.valid_images = 0
        job.started_at = None
        job.completed_at = None

        await session.commit()
        await session.refresh(job)

        # Requeue execution
        background_tasks.add_task(execute_crawl_job, job.id)

        return CrawlJobResponse(
            id=job.id,
            project_id=job.project_id,
            name=job.name,
            keywords=job.keywords,
            max_images=job.max_images,
            search_engine="duckduckgo",  # Default, not stored in DB
            status=job.status,
            progress=job.progress,
            total_images=job.total_images,
            downloaded_images=job.downloaded_images,
            valid_images=job.valid_images,
            config={},  # Default empty config
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
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
    session: DBSession,
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
        session: Database session (for log queries)
        service: CrawlJob service (injected)

    Returns:
        List of job log entries

    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        # Verify job exists and ownership
        job = await service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        owner_query = select(Project.user_id).where(Project.id == job.project_id)
        owner_result = await session.execute(owner_query)
        owner_id = owner_result.scalar_one_or_none()
        if str(owner_id) != str(current_user["user_id"]):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        # Query activity logs for this job
        logs_query = (
            select(ActivityLog)
            .where(
                ActivityLog.resource_type == "crawl_job",
                ActivityLog.resource_id == str(job_id),
            )
            .order_by(ActivityLog.timestamp.desc())
        )
        logs_result = await session.execute(logs_query)
        logs: List[ActivityLog] = list(logs_result.scalars().all())

        return [
            JobLogEntry(
                action=log.action,
                timestamp=log.timestamp.isoformat(),
                metadata=log.metadata_,
            )
            for log in logs
        ]

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
    session: DBSession,
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
        session: Database session (for ownership check)
        service: CrawlJob service (injected)

    Returns:
        CrawlJobProgress containing status and counters

    Raises:
        HTTPException: If job not found or access denied
    """
    try:
        job = await service.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )

        # Ensure ownership
        owner_query = select(Project.user_id).where(Project.id == job.project_id)
        owner_result = await session.execute(owner_query)
        owner_id = owner_result.scalar_one_or_none()
        if str(owner_id) != str(current_user["user_id"]):
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
