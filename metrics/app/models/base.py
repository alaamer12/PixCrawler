"""
Base model for SQLAlchemy models.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import Column, DateTime

Base = declarative_base()

class TimestampMixin:
    """Mixin that adds timestamp fields to models."""
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
