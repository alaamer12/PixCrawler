"""
Workflow repository for data access operations.

This module provides the repository pattern implementation for workflow models,
handling all database queries and data access logic for workflow state and tasks.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import WorkflowState, WorkflowTask
from .base import BaseRepository

__all__ = ['WorkflowStateRepository', 'WorkflowTaskRepository']


# noinspection PyTypeChecker
class WorkflowStateRepository(BaseRepository[WorkflowState]):
    """
    Repository for WorkflowState data access.

    Provides database operations for workflow states including CRUD,
    filtering, and progress tracking.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize WorkflowState repository.

        Args:
            session: Database session
        """
        super().__init__(session, WorkflowState)

    async def get_by_job_id(self, job_id: int) -> Optional[WorkflowState]:
        """
        Get workflow state by job ID.

        Args:
            job_id: Job ID

        Returns:
            WorkflowState or None if not found
        """
        result = await self.session.execute(
            select(WorkflowState).where(WorkflowState.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_active_workflows(self) -> List[WorkflowState]:
        """
        Get all active workflows.

        Returns:
            List of active workflows
        """
        result = await self.session.execute(
            select(WorkflowState).where(
                WorkflowState.status.in_(["running", "recovering"])
            )
        )
        return list(result.scalars().all())

    async def get_failed_workflows(self) -> List[WorkflowState]:
        """
        Get all failed workflows.

        Returns:
            List of failed workflows
        """
        result = await self.session.execute(
            select(WorkflowState).where(WorkflowState.status == "failed")
        )
        return list(result.scalars().all())

    async def get_recoverable_workflows(self) -> List[WorkflowState]:
        """
        Get workflows that can be recovered.

        Returns:
            List of recoverable workflows
        """
        result = await self.session.execute(
            select(WorkflowState).where(
                and_(
                    WorkflowState.status == "failed",
                    WorkflowState.recovery_attempts < WorkflowState.max_recovery_attempts
                )
            )
        )
        return list(result.scalars().all())

    async def update_progress(
        self,
        workflow_id: int,
        current_step: int,
        progress: int,
        metadata: Optional[dict] = None
    ) -> Optional[WorkflowState]:
        """
        Update workflow progress.

        Args:
            workflow_id: Workflow ID
            current_step: Current step index
            progress: Progress percentage (0-100)
            metadata: Optional metadata update

        Returns:
            Updated workflow or None if not found
        """
        workflow = await self.get_by_id(workflow_id)
        if not workflow:
            return None

        update_data = {
            'current_step': current_step,
            'progress': progress,
            'last_checkpoint': datetime.utcnow()
        }

        if metadata:
            # Merge metadata
            current_metadata = workflow.metadata or {}
            current_metadata.update(metadata)
            update_data['metadata'] = current_metadata

        return await self.update(workflow, **update_data)

    async def mark_completed(
        self,
        workflow_id: int
    ) -> Optional[WorkflowState]:
        """
        Mark workflow as completed.

        Args:
            workflow_id: Workflow ID

        Returns:
            Updated workflow or None if not found
        """
        workflow = await self.get_by_id(workflow_id)
        if not workflow:
            return None

        return await self.update(
            workflow,
            status="completed",
            progress=100,
            completed_at=datetime.utcnow()
        )

    async def mark_failed(
        self,
        workflow_id: int,
        error_message: str
    ) -> Optional[WorkflowState]:
        """
        Mark workflow as failed.

        Args:
            workflow_id: Workflow ID
            error_message: Error message

        Returns:
            Updated workflow or None if not found
        """
        workflow = await self.get_by_id(workflow_id)
        if not workflow:
            return None

        return await self.update(
            workflow,
            status="failed",
            error_message=error_message,
            completed_at=datetime.utcnow()
        )

    async def increment_recovery_attempts(
        self,
        workflow_id: int
    ) -> Optional[WorkflowState]:
        """
        Increment recovery attempts counter.

        Args:
            workflow_id: Workflow ID

        Returns:
            Updated workflow or None if not found
        """
        workflow = await self.get_by_id(workflow_id)
        if not workflow:
            return None

        return await self.update(
            workflow,
            recovery_attempts=workflow.recovery_attempts + 1,
            status="recovering"
        )


class WorkflowTaskRepository(BaseRepository[WorkflowTask]):
    """
    Repository for WorkflowTask data access.

    Provides database operations for workflow tasks including CRUD,
    filtering, and status management.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize WorkflowTask repository.

        Args:
            session: Database session
        """
        super().__init__(session, WorkflowTask)

    async def get_by_workflow(self, workflow_id: int) -> List[WorkflowTask]:
        """
        Get all tasks for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of tasks
        """
        result = await self.session.execute(
            select(WorkflowTask)
            .where(WorkflowTask.workflow_id == workflow_id)
            .order_by(WorkflowTask.step_index)
        )
        return list(result.scalars().all())

    async def get_by_status(self, workflow_id: int, status: str) -> List[WorkflowTask]:
        """
        Get tasks by status for a workflow.

        Args:
            workflow_id: Workflow ID
            status: Task status

        Returns:
            List of tasks
        """
        result = await self.session.execute(
            select(WorkflowTask).where(
                and_(
                    WorkflowTask.workflow_id == workflow_id,
                    WorkflowTask.status == status
                )
            )
        )
        return list(result.scalars().all())

    async def get_pending_tasks(self, workflow_id: int) -> List[WorkflowTask]:
        """
        Get pending tasks for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of pending tasks
        """
        return await self.get_by_status(workflow_id, "pending")

    async def get_failed_tasks(self, workflow_id: int) -> List[WorkflowTask]:
        """
        Get failed tasks for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of failed tasks
        """
        return await self.get_by_status(workflow_id, "failed")

    async def get_retryable_tasks(self, workflow_id: int) -> List[WorkflowTask]:
        """
        Get tasks that can be retried.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of retryable tasks
        """
        result = await self.session.execute(
            select(WorkflowTask).where(
                and_(
                    WorkflowTask.workflow_id == workflow_id,
                    WorkflowTask.status == "failed",
                    WorkflowTask.retry_count < WorkflowTask.max_retries
                )
            )
        )
        return list(result.scalars().all())

    async def mark_completed(
        self,
        task_id: int,
        result: dict
    ) -> Optional[WorkflowTask]:
        """
        Mark task as completed.

        Args:
            task_id: Task ID
            result: Task result data

        Returns:
            Updated task or None if not found
        """
        task = await self.get_by_id(task_id)
        if not task:
            return None

        return await self.update(
            task,
            status="completed",
            result=result,
            completed_at=datetime.utcnow()
        )

    async def mark_failed(
        self,
        task_id: int,
        error_message: str
    ) -> Optional[WorkflowTask]:
        """
        Mark task as failed.

        Args:
            task_id: Task ID
            error_message: Error message

        Returns:
            Updated task or None if not found
        """
        task = await self.get_by_id(task_id)
        if not task:
            return None

        return await self.update(
            task,
            status="failed",
            error_message=error_message,
            completed_at=datetime.utcnow()
        )

    async def mark_retrying(
        self,
        task_id: int
    ) -> Optional[WorkflowTask]:
        """
        Mark task as retrying.

        Args:
            task_id: Task ID

        Returns:
            Updated task or None if not found
        """
        task = await self.get_by_id(task_id)
        if not task:
            return None

        return await self.update(
            task,
            status="retrying",
            retry_count=task.retry_count + 1
        )

    async def set_celery_task_id(
        self,
        task_id: int,
        celery_task_id: str
    ) -> Optional[WorkflowTask]:
        """
        Set Celery task ID for a workflow task.

        Args:
            task_id: Task ID
            celery_task_id: Celery task ID

        Returns:
            Updated task or None if not found
        """
        task = await self.get_by_id(task_id)
        if not task:
            return None

        return await self.update(
            task,
            celery_task_id=celery_task_id,
            status="queued"
        )

    async def get_by_celery_task_id(self, celery_task_id: str) -> Optional[WorkflowTask]:
        """
        Get task by Celery task ID.

        Args:
            celery_task_id: Celery task ID

        Returns:
            WorkflowTask or None if not found
        """
        result = await self.session.execute(
            select(WorkflowTask).where(WorkflowTask.celery_task_id == celery_task_id)
        )
        return result.scalar_one_or_none()
