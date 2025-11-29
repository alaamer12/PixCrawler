"""
Job orchestration service for managing dataset build workflows.

This module provides the JobOrchestrator class for orchestrating complex
multi-step workflows with Celery integration, state persistence, and recovery.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Coroutine
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import WorkflowState, WorkflowTask, CrawlJob
from backend.repositories import (
    WorkflowStateRepository,
    WorkflowTaskRepository,
    CrawlJobRepository,
)
from backend.schemas.workflow import (
    WorkflowStateCreate,
    WorkflowTaskCreate,
    WorkflowProgressUpdate,
)
from backend.services.base import BaseService
from utility.logging_config import get_logger

logger = get_logger(__name__)

__all__ = ['JobOrchestrator', 'WorkflowStep', 'WorkflowDefinition']


class WorkflowStep:
    """
    Represents a single step in a workflow.

    Attributes:
        name: Step name
        task_type: Type of task (e.g., 'download', 'validate')
        handler: Async function to execute
        max_retries: Maximum retry attempts
        dependencies: List of step indices this step depends on
        timeout: Timeout in seconds
        estimated_duration: Estimated duration in seconds
    """

    def __init__(
        self,
        name: str,
        task_type: str,
        handler: Callable[..., Coroutine],
        max_retries: int = 3,
        dependencies: Optional[List[int]] = None,
        timeout: Optional[int] = None,
        estimated_duration: Optional[int] = None,
    ):
        self.name = name
        self.task_type = task_type
        self.handler = handler
        self.max_retries = max_retries
        self.dependencies = dependencies or []
        self.timeout = timeout
        self.estimated_duration = estimated_duration


class WorkflowDefinition:
    """
    Defines a complete workflow with multiple steps.

    Attributes:
        name: Workflow name
        steps: List of WorkflowStep objects
        max_recovery_attempts: Maximum recovery attempts
    """

    def __init__(
        self,
        name: str,
        steps: List[WorkflowStep],
        max_recovery_attempts: int = 3,
    ):
        self.name = name
        self.steps = steps
        self.max_recovery_attempts = max_recovery_attempts

    def validate(self) -> None:
        """
        Validate workflow definition.

        Raises:
            ValidationError: If workflow is invalid
        """
        if not self.steps:
            raise ValidationError("Workflow must have at least one step")

        # Validate dependencies
        for i, step in enumerate(self.steps):
            for dep in step.dependencies:
                if dep >= len(self.steps) or dep < 0:
                    raise ValidationError(
                        f"Step {i} has invalid dependency: {dep}"
                    )
                if dep >= i:
                    raise ValidationError(
                        f"Step {i} has forward dependency: {dep}"
                    )


class JobOrchestrator(BaseService):
    """
    Orchestrates complex multi-step workflows for dataset builds.

    Manages workflow execution, state persistence, task dispatching,
    progress tracking, and error recovery.

    Attributes:
        workflow_repo: WorkflowState repository
        task_repo: WorkflowTask repository
        job_repo: CrawlJob repository
    """

    def __init__(
        self,
        workflow_repo: WorkflowStateRepository,
        task_repo: WorkflowTaskRepository,
        job_repo: CrawlJobRepository,
    ):
        """
        Initialize JobOrchestrator.

        Args:
            workflow_repo: WorkflowState repository
            task_repo: WorkflowTask repository
            job_repo: CrawlJob repository
        """
        super().__init__()
        self.workflow_repo = workflow_repo
        self.task_repo = task_repo
        self.job_repo = job_repo

    async def create_workflow(
        self,
        job_id: int,
        workflow_def: WorkflowDefinition,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkflowState:
        """
        Create a new workflow for a job.

        Args:
            job_id: Job ID
            workflow_def: Workflow definition
            metadata: Optional workflow metadata

        Returns:
            Created WorkflowState

        Raises:
            NotFoundError: If job not found
            ValidationError: If workflow definition is invalid
        """
        # Validate workflow
        workflow_def.validate()

        # Verify job exists
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(f"Job not found: {job_id}")

        # Create workflow state
        workflow_data = {
            "job_id": job_id,
            "total_steps": len(workflow_def.steps),
            "status": "pending",
            "current_step": 0,
            "progress": 0,
            "metadata": metadata or {},
            "max_recovery_attempts": workflow_def.max_recovery_attempts,
        }

        workflow = await self.workflow_repo.create(**workflow_data)

        # Create workflow tasks
        for i, step in enumerate(workflow_def.steps):
            task_data = {
                "workflow_id": workflow.id,
                "task_name": step.name,
                "task_type": step.task_type,
                "step_index": i,
                "max_retries": step.max_retries,
                "dependencies": step.dependencies,
                "estimated_duration": step.estimated_duration,
                "status": "pending",
            }
            await self.task_repo.create(**task_data)

        self.log_operation(
            "create_workflow",
            job_id=job_id,
            total_steps=len(workflow_def.steps),
        )

        return workflow

    async def get_workflow(self, workflow_id: int) -> Optional[WorkflowState]:
        """
        Get workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            WorkflowState or None if not found
        """
        return await self.workflow_repo.get_by_id(workflow_id)

    async def get_workflow_by_job(self, job_id: int) -> Optional[WorkflowState]:
        """
        Get workflow by job ID.

        Args:
            job_id: Job ID

        Returns:
            WorkflowState or None if not found
        """
        return await self.workflow_repo.get_by_job_id(job_id)

    async def start_workflow(self, workflow_id: int) -> WorkflowState:
        """
        Start workflow execution.

        Args:
            workflow_id: Workflow ID

        Returns:
            Updated WorkflowState

        Raises:
            NotFoundError: If workflow not found
            ValidationError: If workflow cannot be started
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow not found: {workflow_id}")

        if workflow.status != "pending":
            raise ValidationError(
                f"Cannot start workflow in {workflow.status} state"
            )

        updated = await self.workflow_repo.update(
            workflow,
            status="running",
            started_at=datetime.utcnow(),
        )

        self.log_operation("start_workflow", workflow_id=workflow_id)
        return updated

    async def execute_workflow(
        self,
        workflow_id: int,
        workflow_def: WorkflowDefinition,
    ) -> WorkflowState:
        """
        Execute workflow with all steps.

        Args:
            workflow_id: Workflow ID
            workflow_def: Workflow definition with handlers

        Returns:
            Completed WorkflowState

        Raises:
            NotFoundError: If workflow not found
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow not found: {workflow_id}")

        try:
            # Start workflow
            workflow = await self.start_workflow(workflow_id)

            # Execute steps
            for i, step in enumerate(workflow_def.steps):
                # Check dependencies
                if not await self._check_dependencies(workflow_id, step.dependencies):
                    logger.warning(
                        f"Skipping step {i} due to failed dependencies"
                    )
                    continue

                # Get or create task
                tasks = await self.task_repo.get_by_workflow(workflow_id)
                task = tasks[i] if i < len(tasks) else None

                if not task:
                    raise NotFoundError(f"Task not found for step {i}")

                # Execute task with retries
                result = await self._execute_task_with_retries(
                    task, step, workflow_id
                )

                # Update workflow progress
                progress = int(((i + 1) / len(workflow_def.steps)) * 100)
                await self.workflow_repo.update_progress(
                    workflow_id,
                    current_step=i + 1,
                    progress=progress,
                )

            # Mark workflow as completed
            workflow = await self.workflow_repo.mark_completed(workflow_id)
            self.log_operation("execute_workflow_completed", workflow_id=workflow_id)

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            await self.workflow_repo.mark_failed(workflow_id, str(e))
            raise

        return workflow

    async def _execute_task_with_retries(
        self,
        task: WorkflowTask,
        step: WorkflowStep,
        workflow_id: int,
    ) -> Dict[str, Any]:
        """
        Execute a task with retry logic.

        Args:
            task: WorkflowTask to execute
            step: WorkflowStep definition
            workflow_id: Workflow ID

        Returns:
            Task result

        Raises:
            Exception: If task fails after all retries
        """
        last_error = None

        for attempt in range(task.max_retries + 1):
            try:
                # Mark task as running
                await self.task_repo.update(
                    task,
                    status="running",
                    started_at=datetime.utcnow(),
                )

                # Execute handler with timeout
                if step.timeout:
                    result = await asyncio.wait_for(
                        step.handler(),
                        timeout=step.timeout,
                    )
                else:
                    result = await step.handler()

                # Mark task as completed
                await self.task_repo.mark_completed(task.id, result or {})

                self.log_operation(
                    "task_completed",
                    task_id=task.id,
                    task_name=step.name,
                    attempt=attempt + 1,
                )

                return result or {}

            except asyncio.TimeoutError as e:
                last_error = f"Task timeout after {step.timeout}s"
                logger.warning(
                    f"Task {step.name} timed out (attempt {attempt + 1}/{task.max_retries + 1})"
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Task {step.name} failed (attempt {attempt + 1}/{task.max_retries + 1}): {str(e)}"
                )

            # Retry if attempts remaining
            if attempt < task.max_retries:
                await self.task_repo.mark_retrying(task.id)
                # Exponential backoff: 2^attempt seconds
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
            else:
                # Mark task as failed
                await self.task_repo.mark_failed(task.id, last_error or "Unknown error")
                raise Exception(f"Task {step.name} failed after {task.max_retries + 1} attempts: {last_error}")

    async def _check_dependencies(
        self,
        workflow_id: int,
        dependencies: List[int],
    ) -> bool:
        """
        Check if all dependencies are completed.

        Args:
            workflow_id: Workflow ID
            dependencies: List of task indices to check

        Returns:
            True if all dependencies are completed, False otherwise
        """
        if not dependencies:
            return True

        tasks = await self.task_repo.get_by_workflow(workflow_id)

        for dep_idx in dependencies:
            if dep_idx >= len(tasks):
                return False
            if tasks[dep_idx].status != "completed":
                return False

        return True

    async def pause_workflow(self, workflow_id: int) -> WorkflowState:
        """
        Pause workflow execution.

        Args:
            workflow_id: Workflow ID

        Returns:
            Updated WorkflowState

        Raises:
            NotFoundError: If workflow not found
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow not found: {workflow_id}")

        updated = await self.workflow_repo.update(workflow, status="paused")
        self.log_operation("pause_workflow", workflow_id=workflow_id)
        return updated

    async def cancel_workflow(self, workflow_id: int) -> WorkflowState:
        """
        Cancel workflow execution.

        Args:
            workflow_id: Workflow ID

        Returns:
            Updated WorkflowState

        Raises:
            NotFoundError: If workflow not found
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow not found: {workflow_id}")

        updated = await self.workflow_repo.update(
            workflow,
            status="cancelled",
            completed_at=datetime.utcnow(),
        )

        self.log_operation("cancel_workflow", workflow_id=workflow_id)
        return updated

    async def recover_workflow(
        self,
        workflow_id: int,
        from_step: int,
    ) -> WorkflowState:
        """
        Recover workflow from a specific step.

        Args:
            workflow_id: Workflow ID
            from_step: Step index to recover from

        Returns:
            Updated WorkflowState

        Raises:
            NotFoundError: If workflow not found
            ValidationError: If workflow cannot be recovered
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow not found: {workflow_id}")

        if not workflow.can_recover:
            raise ValidationError(
                f"Workflow cannot be recovered (attempts: {workflow.recovery_attempts}/{workflow.max_recovery_attempts})"
            )

        # Reset tasks from recovery point
        tasks = await self.task_repo.get_by_workflow(workflow_id)
        for i, task in enumerate(tasks):
            if i >= from_step:
                await self.task_repo.update(
                    task,
                    status="pending",
                    retry_count=0,
                    error_message=None,
                )

        # Update workflow
        updated = await self.workflow_repo.increment_recovery_attempts(workflow_id)
        await self.workflow_repo.update(
            updated,
            current_step=from_step,
            progress=int((from_step / len(tasks)) * 100),
        )

        self.log_operation(
            "recover_workflow",
            workflow_id=workflow_id,
            from_step=from_step,
        )

        return updated

    async def get_workflow_progress(self, workflow_id: int) -> Dict[str, Any]:
        """
        Get detailed workflow progress.

        Args:
            workflow_id: Workflow ID

        Returns:
            Progress information

        Raises:
            NotFoundError: If workflow not found
        """
        workflow = await self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow not found: {workflow_id}")

        tasks = await self.task_repo.get_by_workflow(workflow_id)

        completed_tasks = sum(1 for t in tasks if t.status == "completed")
        failed_tasks = sum(1 for t in tasks if t.status == "failed")
        running_tasks = sum(1 for t in tasks if t.status == "running")

        return {
            "workflow_id": workflow.id,
            "job_id": workflow.job_id,
            "status": workflow.status,
            "progress": workflow.progress,
            "current_step": workflow.current_step,
            "total_steps": workflow.total_steps,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "running_tasks": running_tasks,
            "total_tasks": len(tasks),
            "recovery_attempts": workflow.recovery_attempts,
            "max_recovery_attempts": workflow.max_recovery_attempts,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "tasks": [
                {
                    "id": t.id,
                    "name": t.task_name,
                    "type": t.task_type,
                    "status": t.status,
                    "retry_count": t.retry_count,
                    "error_message": t.error_message,
                }
                for t in tasks
            ],
        }

    async def get_active_workflows(self) -> List[WorkflowState]:
        """
        Get all active workflows.

        Returns:
            List of active workflows
        """
        return await self.workflow_repo.get_active_workflows()

    async def get_failed_workflows(self) -> List[WorkflowState]:
        """
        Get all failed workflows.

        Returns:
            List of failed workflows
        """
        return await self.workflow_repo.get_failed_workflows()

    async def get_recoverable_workflows(self) -> List[WorkflowState]:
        """
        Get all recoverable workflows.

        Returns:
            List of recoverable workflows
        """
        return await self.workflow_repo.get_recoverable_workflows()
