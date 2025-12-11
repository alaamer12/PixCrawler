"""
Flow model for simple crawl operations.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base, TimestampMixin


class Flow(Base, TimestampMixin):
    """
    Simple flow model for crawl operations.
    
    This is a simplified alternative to the complex CrawlJob model.
    """
    
    __tablename__ = "simple_flows"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Flow identification
    flow_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    # Basic info
    keywords: Mapped[List[str]] = mapped_column(JSON)
    max_images: Mapped[int] = mapped_column(Integer, default=50)
    engines: Mapped[List[str]] = mapped_column(JSON, default=["duckduckgo"])
    
    # Status tracking
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    
    # Results
    downloaded_images: Mapped[int] = mapped_column(Integer, default=0)
    validated_images: Mapped[int] = mapped_column(Integer, default=0)
    failed_images: Mapped[int] = mapped_column(Integer, default=0)
    
    # Task tracking
    task_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    
    # Paths and output
    output_path: Mapped[str] = mapped_column(String(500))
    output_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Flow(id={self.id}, flow_id='{self.flow_id}', status='{self.status}')>"