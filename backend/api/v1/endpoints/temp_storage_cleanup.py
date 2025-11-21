"""
API endpoints for temporary storage cleanup operations.

This module provides REST API endpoints for managing and triggering
temporary storage cleanup operations manually or retrieving cleanup statistics.

Endpoints:
    GET /cleanup/stats - Get current storage and cleanup statistics
    POST /cleanup/emergency - Trigger emergency cleanup manually
    POST /cleanup/orphaned - Trigger orphaned files cleanup
    POST /cleanup/crash/{job_id} - Trigger crash recovery cleanup for specific job
    POST /cleanup/scheduled - Trigger scheduled cleanup manually
    GET /cleanup/history - Get cleanup operation history

Features:
    - Manual cleanup triggers for all scenarios
    - Real-time storage statistics
    - Cleanup operation history and monitoring
    - Integration with Celery background tasks
    - Comprehensive error handling and validation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.api.dependencies import get_session, DBSession
from backend.services.temp_storage_cleanup import TempStorageCleanupService
from backend.tasks.temp_storage_cleanup import (
    task_emergency_cleanup,
    task_cleanup_orphaned_files,
    task_cleanup_after_crash,
    task_scheduled_cleanup,
    task_get_storage_stats
)
from backend.storage.factory import get_storage_provider
from backend.core.exceptions import PixCrawlerException
from utility.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Temp Storage Cleanup"])

__all__ = ['router']


# Request/Response Models

class CleanupStatsResponse(BaseModel):
    """Response model for cleanup statistics."""
    success: bool
    storage_usage_percent: float
    emergency_threshold: float
    temp_files_count: int
    temp_files_size_bytes: int
    active_jobs_count: int
    failed_jobs_count: int
    orphaned_files_count: int
    orphaned_files_size_bytes: int
    cleanup_needed: bool
    message: str


class CleanupOperationResponse(BaseModel):
    """Response model for cleanup operations."""
    success: bool
    task_id: str
    message: str
    trigger_type: str
    estimated_duration_minutes: Optional[int] = None


class CleanupResultResponse(BaseModel):
    """Response model for completed cleanup operations."""
    success: bool
    stats: Dict[str, Any]
    message: str
    duration_seconds: float
    files_deleted: int
    bytes_freed: int
    storage_before_percent: float
    storage_after_percent: float
    errors: List[str] = Field(default_factory=list)


class OrphanedFilesCleanupRequest(BaseModel):
    """Request model for orphaned files cleanup."""
    max_age_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=168,
        description="Maximum age in hours for files to be considered orphaned"
    )


class CrashRecoveryCleanupRequest(BaseModel):
    """Request model for crash recovery cleanup."""
    job_id: Optional[int] = Field(
        default=None,
        description="Specific job ID to clean up. If None, cleans all failed jobs."
    )


# Helper Functions

async def get_cleanup_service(session: DBSession) -> TempStorageCleanupService:
    """Get configured cleanup service instance."""
    storage_provider = get_storage_provider()
    return TempStorageCleanupService(
        storage_provider=storage_provider,
        session=session
    )


# API Endpoints

@router.get(
    "/stats",
    response_model=CleanupStatsResponse,
    summary="Get Storage Statistics",
    description="Get current temporary storage usage statistics and cleanup status"
)
async def get_cleanup_stats(
    session: DBSession = Depends(get_session)
) -> CleanupStatsResponse:
    """
    Get current storage and cleanup statistics.
    
    Returns comprehensive information about:
    - Current storage usage percentage
    - Number of temporary files and their total size
    - Active and failed job counts
    - Orphaned files detection
    - Whether cleanup is needed
    """
    try:
        logger.info("Getting temp storage cleanup statistics")
        
        # Try to get stats via Celery task first (non-blocking)
        try:
            task_result = task_get_storage_stats.delay()
            result = task_result.get(timeout=10)  # 10 second timeout
            
            if result.get("success"):
                stats = result["stats"]
                return CleanupStatsResponse(
                    success=True,
                    storage_usage_percent=stats.get("storage_usage_percent", 0.0),
                    emergency_threshold=stats.get("emergency_threshold", 95.0),
                    temp_files_count=stats.get("temp_files_count", 0),
                    temp_files_size_bytes=stats.get("temp_files_size_bytes", 0),
                    active_jobs_count=stats.get("active_jobs_count", 0),
                    failed_jobs_count=stats.get("failed_jobs_count", 0),
                    orphaned_files_count=stats.get("orphaned_files_count", 0),
                    orphaned_files_size_bytes=stats.get("orphaned_files_size_bytes", 0),
                    cleanup_needed=stats.get("cleanup_needed", False),
                    message="Storage statistics retrieved successfully"
                )
        except Exception as e:
            logger.warning(f"Celery task failed, falling back to direct call: {e}")
        
        # Fallback to direct service call
        cleanup_service = await get_cleanup_service(session)
        stats = await cleanup_service.get_storage_stats()
        
        return CleanupStatsResponse(
            success=True,
            storage_usage_percent=stats.get("storage_usage_percent", 0.0),
            emergency_threshold=stats.get("emergency_threshold", 95.0),
            temp_files_count=stats.get("temp_files_count", 0),
            temp_files_size_bytes=stats.get("temp_files_size_bytes", 0),
            active_jobs_count=stats.get("active_jobs_count", 0),
            failed_jobs_count=stats.get("failed_jobs_count", 0),
            orphaned_files_count=stats.get("orphaned_files_count", 0),
            orphaned_files_size_bytes=stats.get("orphaned_files_size_bytes", 0),
            cleanup_needed=stats.get("cleanup_needed", False),
            message="Storage statistics retrieved successfully (direct)"
        )
        
    except Exception as e:
        logger.error(f"Failed to get cleanup stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cleanup statistics: {str(e)}"
        )


@router.post(
    "/emergency",
    response_model=CleanupOperationResponse,
    summary="Trigger Emergency Cleanup",
    description="Manually trigger emergency cleanup when storage usage is critical"
)
async def trigger_emergency_cleanup() -> CleanupOperationResponse:
    """
    Trigger emergency cleanup manually.
    
    This endpoint immediately starts an emergency cleanup task to free up
    storage space when usage exceeds the emergency threshold.
    """
    try:
        logger.warning("Manual emergency cleanup triggered via API")
        
        # Start emergency cleanup task
        task_result = task_emergency_cleanup.delay()
        
        return CleanupOperationResponse(
            success=True,
            task_id=task_result.id,
            message="Emergency cleanup task started successfully",
            trigger_type="manual_emergency",
            estimated_duration_minutes=30
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger emergency cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger emergency cleanup: {str(e)}"
        )


@router.post(
    "/orphaned",
    response_model=CleanupOperationResponse,
    summary="Trigger Orphaned Files Cleanup",
    description="Manually trigger cleanup of orphaned temporary files"
)
async def trigger_orphaned_cleanup(
    request: OrphanedFilesCleanupRequest = OrphanedFilesCleanupRequest()
) -> CleanupOperationResponse:
    """
    Trigger orphaned files cleanup manually.
    
    This endpoint starts a cleanup task to remove temporary files that are
    no longer associated with active jobs or are older than the specified age.
    """
    try:
        logger.info(f"Manual orphaned files cleanup triggered via API (max_age_hours: {request.max_age_hours})")
        
        # Start orphaned files cleanup task
        task_result = task_cleanup_orphaned_files.delay(max_age_hours=request.max_age_hours)
        
        return CleanupOperationResponse(
            success=True,
            task_id=task_result.id,
            message=f"Orphaned files cleanup task started (max age: {request.max_age_hours or 'default'} hours)",
            trigger_type="manual_orphaned",
            estimated_duration_minutes=15
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger orphaned cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger orphaned cleanup: {str(e)}"
        )


@router.post(
    "/crash/{job_id}",
    response_model=CleanupOperationResponse,
    summary="Trigger Crash Recovery Cleanup",
    description="Manually trigger cleanup for a specific failed job or all failed jobs"
)
async def trigger_crash_recovery_cleanup(
    job_id: Optional[int] = Path(None, description="Job ID to clean up. Use 0 for all failed jobs")
) -> CleanupOperationResponse:
    """
    Trigger crash recovery cleanup manually.
    
    This endpoint starts a cleanup task to remove temporary files from
    failed, cancelled, or crashed jobs.
    """
    try:
        # Convert 0 to None for "all failed jobs"
        actual_job_id = job_id if job_id and job_id > 0 else None
        
        logger.info(f"Manual crash recovery cleanup triggered via API for job {actual_job_id or 'all failed jobs'}")
        
        # Start crash recovery cleanup task
        task_result = task_cleanup_after_crash.delay(job_id=actual_job_id)
        
        job_desc = f"job {actual_job_id}" if actual_job_id else "all failed jobs"
        
        return CleanupOperationResponse(
            success=True,
            task_id=task_result.id,
            message=f"Crash recovery cleanup task started for {job_desc}",
            trigger_type="manual_crash_recovery",
            estimated_duration_minutes=10
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger crash recovery cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger crash recovery cleanup: {str(e)}"
        )


@router.post(
    "/scheduled",
    response_model=CleanupOperationResponse,
    summary="Trigger Scheduled Cleanup",
    description="Manually trigger the scheduled cleanup routine"
)
async def trigger_scheduled_cleanup() -> CleanupOperationResponse:
    """
    Trigger scheduled cleanup manually.
    
    This endpoint starts the same cleanup routine that runs automatically
    on a schedule, performing comprehensive cleanup of all temporary files.
    """
    try:
        logger.info("Manual scheduled cleanup triggered via API")
        
        # Start scheduled cleanup task
        task_result = task_scheduled_cleanup.delay()
        
        return CleanupOperationResponse(
            success=True,
            task_id=task_result.id,
            message="Scheduled cleanup task started successfully",
            trigger_type="manual_scheduled",
            estimated_duration_minutes=20
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger scheduled cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger scheduled cleanup: {str(e)}"
        )


@router.get(
    "/task/{task_id}/status",
    summary="Get Cleanup Task Status",
    description="Get the status and results of a cleanup task"
)
async def get_cleanup_task_status(
    task_id: str = Path(..., description="Celery task ID")
) -> Dict[str, Any]:
    """
    Get the status and results of a cleanup task.
    
    This endpoint allows monitoring the progress and results of
    cleanup tasks that were started via the API.
    """
    try:
        from celery_core.app import get_celery_app
        
        celery_app = get_celery_app()
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            return {
                "task_id": task_id,
                "state": "PENDING",
                "message": "Task is waiting to be processed"
            }
        elif task_result.state == 'PROGRESS':
            return {
                "task_id": task_id,
                "state": "PROGRESS",
                "message": "Task is currently running",
                "progress": task_result.info
            }
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            return {
                "task_id": task_id,
                "state": "SUCCESS",
                "result": result,
                "message": result.get("message", "Task completed successfully")
            }
        elif task_result.state == 'FAILURE':
            return {
                "task_id": task_id,
                "state": "FAILURE",
                "error": str(task_result.info),
                "message": f"Task failed: {task_result.info}"
            }
        else:
            return {
                "task_id": task_id,
                "state": task_result.state,
                "info": task_result.info,
                "message": f"Task state: {task_result.state}"
            }
            
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get(
    "/health",
    summary="Cleanup Service Health Check",
    description="Check the health status of the temp storage cleanup service"
)
async def cleanup_service_health_check(
    session: DBSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Health check for the temp storage cleanup service.
    
    Returns information about service availability, configuration,
    and current operational status.
    """
    try:
        cleanup_service = await get_cleanup_service(session)
        
        # Get basic stats to verify service is working
        stats = await cleanup_service.get_storage_stats()
        
        # Check if emergency cleanup is needed
        cleanup_needed = stats.get("cleanup_needed", False)
        storage_usage = stats.get("storage_usage_percent", 0.0)
        emergency_threshold = stats.get("emergency_threshold", 95.0)
        
        health_status = "healthy"
        if storage_usage >= emergency_threshold:
            health_status = "critical"
        elif storage_usage >= emergency_threshold - 10:
            health_status = "warning"
        
        return {
            "service": "temp_storage_cleanup",
            "status": health_status,
            "storage_usage_percent": storage_usage,
            "emergency_threshold": emergency_threshold,
            "cleanup_needed": cleanup_needed,
            "temp_files_count": stats.get("temp_files_count", 0),
            "orphaned_files_count": stats.get("orphaned_files_count", 0),
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Service is {health_status}"
        }
        
    except Exception as e:
        logger.error(f"Cleanup service health check failed: {e}")
        return {
            "service": "temp_storage_cleanup",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Service health check failed: {e}"
        }
