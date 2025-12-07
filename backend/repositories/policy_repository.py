"""
Repositories for dataset lifecycle policies.
"""

from typing import List, Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.policy import ArchivalPolicy, CleanupPolicy, PolicyExecutionLog
from .base import BaseRepository


class ArchivalPolicyRepository(BaseRepository[ArchivalPolicy]):
    """Repository for archival policies."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ArchivalPolicy)

    async def get_active_policies(self) -> Sequence[ArchivalPolicy]:
        """Get all active archival policies."""
        query = select(ArchivalPolicy).where(ArchivalPolicy.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[ArchivalPolicy]:
        """Get policy by name."""
        query = select(ArchivalPolicy).where(ArchivalPolicy.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class CleanupPolicyRepository(BaseRepository[CleanupPolicy]):
    """Repository for cleanup policies."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, CleanupPolicy)

    async def get_active_policies(self) -> Sequence[CleanupPolicy]:
        """Get all active cleanup policies."""
        query = select(CleanupPolicy).where(CleanupPolicy.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[CleanupPolicy]:
        """Get policy by name."""
        query = select(CleanupPolicy).where(CleanupPolicy.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class PolicyExecutionLogRepository(BaseRepository[PolicyExecutionLog]):
    """Repository for policy execution logs."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PolicyExecutionLog)

    async def get_by_dataset(self, dataset_id: int) -> Sequence[PolicyExecutionLog]:
        """Get logs for a specific dataset."""
        query = select(PolicyExecutionLog).where(
            PolicyExecutionLog.dataset_id == dataset_id
        ).order_by(PolicyExecutionLog.executed_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
