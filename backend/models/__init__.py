"""
SQLAlchemy database models for PixCrawler.

This module provides comprehensive SQLAlchemy ORM models for the PixCrawler
backend, synchronized with the Drizzle schema in the frontend.

IMPORTANT: These models must be kept in sync with the Drizzle schema in
frontend/lib/db/schema.ts. The Drizzle schema is the source of truth.

Model Categories:
    - Core: Profile, Project, CrawlJob, Image, ActivityLog
    - Credits: CreditAccount, CreditTransaction
    - Notifications: Notification, NotificationPreference
    - API: APIKey
    - Usage: UsageMetric

Features:
    - SQLAlchemy 2.0 with Mapped annotations
    - Full type safety with mypy support
    - Advanced constraints and indexes
    - Relationship management with cascade behaviors
    - PostgreSQL-specific features (JSONB, UUID)
    - Supabase auth integration
"""

from .base import Base, TimestampMixin
from .api_keys import APIKey
from .chunks import JobChunk
from .credits import CreditAccount, CreditTransaction
from .dataset import Dataset
from .notifications import Notification, NotificationPreference
from .usage import UsageMetric
from .metrics import ProcessingMetric, ResourceMetric, QueueMetric
from .workflow import WorkflowStatus, TaskStatus, WorkflowState, WorkflowTask

# Import core models from database.models (synchronized with Drizzle schema)
from backend.database.models import Profile, Project, CrawlJob, Image, ActivityLog

__all__ = [
    # Base classes
    'Base',
    'TimestampMixin',
    # Core models (from database.models - synchronized with Drizzle)
    'Profile',
    'Project',
    'CrawlJob',
    'Image',
    'ActivityLog',
    'Dataset',
    # Chunk models
    'JobChunk',
    # Workflow models
    'WorkflowStatus',
    'TaskStatus',
    'WorkflowState',
    'WorkflowTask',
    # Credit models
    'CreditAccount',
    'CreditTransaction',
    # Notification models
    'Notification',
    'NotificationPreference',
    # API models
    'APIKey',
    # Usage models
    'UsageMetric',
    # Metrics models
    'ProcessingMetric',
    'ResourceMetric',
    'QueueMetric',
]
