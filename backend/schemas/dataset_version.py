from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import Field
from .base import BaseSchema

class DatasetVersionResponse(BaseSchema):
    """
    Schema for dataset version response.
    """
    id: int
    dataset_id: int
    version_number: int
    keywords: List[str]
    search_engines: List[str]
    max_images: int
    crawl_job_id: Optional[int]
    change_summary: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True
