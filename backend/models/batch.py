from typing import List

from pydantic import BaseModel, Field


class BatchDeleteRequest(BaseModel):
    """Request to delete multiple resources."""
    ids: List[int] = Field(..., description="List of IDs to delete", min_items=1)


class BatchDeleteResponse(BaseModel):
    """Response from batch delete operation."""
    deleted_count: int = Field(..., description="Number of successfully deleted items")
    failed_ids: List[int] = Field(default=[], description="List of IDs that failed to delete")
