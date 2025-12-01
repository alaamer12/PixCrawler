"""
Batch operations endpoints.

Provides endpoints for bulk operations on multiple resources.
"""

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.api.types import CurrentUser
from backend.api.v1.response_models import get_common_responses
from backend.services.project import ProjectService
from backend.api.v1.endpoints.projects import get_project_service
from fastapi import Depends

__all__ = ['router']

router = APIRouter(
    tags=["Batch Operations"],
    responses=get_common_responses(401, 500),
)


class BatchDeleteRequest(BaseModel):
    """Request to delete multiple resources."""
    ids: List[int] = Field(..., description="List of IDs to delete", min_items=1)


class BatchDeleteResponse(BaseModel):
    """Response from batch delete operation."""
    deleted_count: int = Field(..., description="Number of successfully deleted items")
    failed_ids: List[int] = Field(default=[], description="List of IDs that failed to delete")


@router.post(
    "/projects/batch-delete",
    response_model=BatchDeleteResponse,
    summary="Batch Delete Projects",
    description="Delete multiple projects in a single operation.",
    operation_id="batchDeleteProjects",
)
async def batch_delete_projects(
    request: BatchDeleteRequest,
    current_user: CurrentUser,
    service: ProjectService = Depends(get_project_service),
) -> BatchDeleteResponse:
    """
    Delete multiple projects in a single operation.
    
    Iterates through the provided list of project IDs and attempts to delete each one.
    Returns the count of successfully deleted projects and a list of IDs that failed.
    
    **Authentication Required:** Bearer token
    
    Args:
        request: Batch delete request containing list of project IDs
        current_user: Current authenticated user (injected)
        service: Project service instance (injected)
        
    Returns:
        BatchDeleteResponse with success count and failed IDs
    """
    deleted_count = 0
    failed_ids = []
    user_id = current_user["user_id"]
    
    for project_id in request.ids:
        try:
            await service.delete_project(project_id, user_id)
            deleted_count += 1
        except Exception:
            # Log error if needed, but continue with other items
            failed_ids.append(project_id)
    
    return BatchDeleteResponse(
        deleted_count=deleted_count,
        failed_ids=failed_ids,
    )
