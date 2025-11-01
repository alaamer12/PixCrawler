"""
Base models and mixins for PixCrawler ORM.

This module provides base classes and common mixins for all
SQLAlchemy models in the application.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

__all__ = [
    'Base',
    'TimestampMixin',
]


class Base(DeclarativeBase):
    """
    Base class for all database models.
    
    Provides common functionality and configuration for all models.
    Uses SQLAlchemy 2.0 declarative style with Mapped annotations.
    """
    
    # Type annotation map for common types
    type_annotation_map = {}


class TimestampMixin:
    """
    Mixin for models with timestamp fields.
    
    Provides created_at and updated_at fields that automatically
    track record creation and modification times.
    
    Attributes:
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when record was created",
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp when record was last updated",
    )
