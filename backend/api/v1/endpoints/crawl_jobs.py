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
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, get_session
from backend.api.types import CurrentUser, DBSession, JobID
from backend.models import ActivityLog, CrawlJob, Project
from backend.schemas.crawl_jobs import (
    CrawlJobCreate,
    CrawlJobProgress,
    CrawlJobResponse,
    JobLogEntry,
)
from backend.services.crawl_job import CrawlJobService, execute_crawl_job

__all__ = ['router']

router = APIRouter()

@router.get("/", response_model=Page[CrawlJobResponse])
async def list_crawl_jobs(
    current_user: CurrentUser,
    session: DBSession,
) -> Page[CrawlJobResponse]:
    """
    List crawl jobs for the current user with pagination.

    Jobs are filtered by projects owned by the current user.
    Pagination is handled automatically by fastapi-pagination.
    Query parameters: page (default=1), size (default=50)

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
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def create_crawl_job(
    job_create: CrawlJobCreate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    session: DBSession,
) -> CrawlJobResponse:
    """
    Create a new crawl job.

    Creates a new image crawling job and optionally starts it immediately.
    The job will be executed in the background using the PixCrawler builder.

    Args:
        job_create: Crawl job creation data
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        session: Database session

    Returns:
        Created crawl job information

    Raises:
        HTTPException: If job creation fails
    """
    try:
        service = CrawlJobService(session)

        job = await service.create_job(
            project_id=job_create.project_id,
            name=job_create.name,
            keywords=job_create.keywords,
            max_images=job_create.max_images,
            search_engine=job_create.search_engine,
            config=job_create.config,
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


@router.get("/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_job(
    job_id: JobID,
    current_user: CurrentUser,
    session: DBSession,
) -> CrawlJobResponse:
    """
    Get crawl job by ID.

    Retrieves detailed information about a specific crawl job,
    including current status and progress.

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        Crawl job information

    Raises:
        HTTPException: If job not found
    """
    try:
        service = CrawlJobService(session)
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


@router.post("/{job_id}/cancel")
async def cancel_crawl_job(
    job_id: JobID,
    current_user: CurrentUser,
    session: DBSession,
) -> dict[str, str]:
    """
    Cancel a running crawl job.

    Attempts to cancel a crawl job that is currently running or pending.

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If job not found or cannot be cancelled
    """
    try:
        service = CrawlJobService(session)
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

        await service.update_job(job_id, "cancelled")

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
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def retry_crawl_job(
    job_id: JobID,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    session: DBSession,
) -> CrawlJobResponse:
    """
    Retry a failed or cancelled crawl job.

    Resets job progress and schedules execution in the background.

    Args:
        job_id: Crawl job ID
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        session: Database session

    Returns:
        Updated crawl job information

    Raises:
        HTTPException: If job not found, not owned by user, or cannot be retried
    """
    try:
        service = CrawlJobService(session)
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


@router.get("/{job_id}/logs", response_model=List[JobLogEntry])
async def get_crawl_job_logs(
    job_id: JobID,
    current_user: CurrentUser,
    session: DBSession,
) -> List[JobLogEntry]:
    """
    Get activity logs for a crawl job.

    Returns activity entries associated with the job, ordered by timestamp desc.

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        List of job log entries

    Raises:
        HTTPException: If job not found or not owned by user
    """
    try:
        # Verify job exists and ownership
        service = CrawlJobService(session)
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


@router.get("/{job_id}/progress", response_model=CrawlJobProgress)
async def get_crawl_job_progress(
    job_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CrawlJobProgress:
    """
    Get real-time progress for a crawl job.

    Returns status and progress metrics, ensuring the job belongs to the user.

    Args:
        job_id: Crawl job ID
        current_user: Current authenticated user
        session: Database session

    Returns:
        CrawlJobProgress containing status and counters

    Raises:
        HTTPException: If job not found or not owned by user
    """
    try:
        service = CrawlJobService(session)
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
