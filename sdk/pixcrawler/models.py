"""
PixCrawler SDK Models

This module defines shared Pydantic models for the SDK.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict

class Image(BaseModel):
    """Represents a downloaded image."""
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = None
    filename: str
    path: Path
    url: Optional[str] = None
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    format: str
    hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class JobStatus(BaseModel):
    """Status of a background job."""
    job_id: str
    status: str
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class CrawlRequest(BaseModel):
    """Request model for a crawl operation."""
    keyword: str
    max_images: int = 100
    engines: List[str] = Field(default_factory=lambda: ["google", "bing"])
    use_variations: bool = True
    min_width: Optional[int] = None
    min_height: Optional[int] = None
