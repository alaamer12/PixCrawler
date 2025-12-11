"""
Flow schemas for the streamlined crawl flow.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class FlowRequest(BaseModel):
    """Request schema for flow crawl."""
    
    keywords: List[str] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="Keywords to search for (1-10 keywords)"
    )
    max_images: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum images to download (1-500)"
    )
    engines: List[str] = Field(
        default=["duckduckgo"],
        description="Search engines to use"
    )
    output_name: Optional[str] = Field(
        default=None,
        description="Custom name for the output directory"
    )


class FlowResponse(BaseModel):
    """Response schema for flow crawl."""
    
    flow_id: str = Field(..., description="Unique flow identifier")
    status: str = Field(..., description="Flow status")
    keywords: List[str] = Field(..., description="Keywords being crawled")
    max_images: int = Field(..., description="Maximum images to download")
    engines: List[str] = Field(..., description="Search engines used")
    output_path: str = Field(..., description="Output directory path")
    task_ids: List[str] = Field(..., description="Celery task IDs")
    message: str = Field(..., description="Status message")


class FlowStatus(BaseModel):
    """Status schema for flow crawl."""
    
    flow_id: str = Field(..., description="Flow identifier")
    status: str = Field(..., description="Current status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    downloaded_images: int = Field(..., description="Number of images downloaded")
    validated_images: int = Field(..., description="Number of images validated")
    total_tasks: int = Field(..., description="Total number of tasks")
    completed_tasks: int = Field(..., description="Completed tasks")
    failed_tasks: int = Field(..., description="Failed tasks")
    output_path: str = Field(..., description="Output directory path")
    started_at: Optional[str] = Field(None, description="Start timestamp")
    completed_at: Optional[str] = Field(None, description="Completion timestamp")


class FlowResult(BaseModel):
    """Final result schema for flow crawl."""
    
    flow_id: str = Field(..., description="Flow identifier")
    status: str = Field(..., description="Final status")
    total_downloaded: int = Field(..., description="Total images downloaded")
    total_validated: int = Field(..., description="Total images validated")
    total_failed: int = Field(..., description="Total failed downloads")
    output_path: str = Field(..., description="Output directory path")
    file_list: List[str] = Field(..., description="List of downloaded files")
    processing_time: float = Field(..., description="Total processing time in seconds")
    engines_used: List[str] = Field(..., description="Search engines used")
    keywords_processed: List[str] = Field(..., description="Keywords processed")