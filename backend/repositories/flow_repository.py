"""
Flow repository for simple crawl operations.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.flow import Flow
from backend.repositories.base import BaseRepository


class FlowRepository(BaseRepository[Flow]):
    """Repository for Flow operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Flow)
    
    async def get_by_flow_id(self, flow_id: str) -> Optional[Flow]:
        """Get flow by flow_id."""
        result = await self.session.execute(
            select(Flow).where(Flow.flow_id == flow_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_status(self, status: str) -> List[Flow]:
        """Get flows by status."""
        result = await self.session.execute(
            select(Flow).where(Flow.status == status).order_by(Flow.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_active_flows(self) -> List[Flow]:
        """Get all active (running/pending) flows."""
        result = await self.session.execute(
            select(Flow).where(Flow.status.in_(["pending", "running"])).order_by(Flow.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def update_progress(
        self,
        flow_id: str,
        progress: int,
        downloaded_images: int,
        validated_images: int = 0
    ) -> Optional[Flow]:
        """Update flow progress."""
        flow = await self.get_by_flow_id(flow_id)
        if flow:
            flow.progress = progress
            flow.downloaded_images = downloaded_images
            flow.validated_images = validated_images
            await self.session.commit()
            await self.session.refresh(flow)
        return flow
    
    async def update_task_counts(
        self,
        flow_id: str,
        completed_tasks: int,
        failed_tasks: int
    ) -> Optional[Flow]:
        """Update task completion counts."""
        flow = await self.get_by_flow_id(flow_id)
        if flow:
            flow.completed_tasks = completed_tasks
            flow.failed_tasks = failed_tasks
            
            # Update overall progress based on task completion
            if flow.total_tasks > 0:
                flow.progress = int((completed_tasks + failed_tasks) / flow.total_tasks * 100)
            
            await self.session.commit()
            await self.session.refresh(flow)
        return flow
    
    async def mark_completed(self, flow_id: str, status: str = "completed") -> Optional[Flow]:
        """Mark flow as completed."""
        from datetime import datetime
        
        flow = await self.get_by_flow_id(flow_id)
        if flow:
            flow.status = status
            flow.progress = 100 if status == "completed" else flow.progress
            flow.completed_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(flow)
        return flow
    
    async def mark_failed(self, flow_id: str, error_message: str) -> Optional[Flow]:
        """Mark flow as failed with error message."""
        from datetime import datetime
        
        flow = await self.get_by_flow_id(flow_id)
        if flow:
            flow.status = "failed"
            flow.error_message = error_message
            flow.completed_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(flow)
        return flow