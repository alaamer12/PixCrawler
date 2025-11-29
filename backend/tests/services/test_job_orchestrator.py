"""
Tests for JobOrchestrator service.

Comprehensive test suite covering workflow creation, execution,
error handling, and recovery.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from backend.models import WorkflowState, WorkflowTask, CrawlJob
from backend.repositories import (
    WorkflowStateRepository,
    WorkflowTaskRepository,
    CrawlJobRepository,
)
from backend.services.job_orchestrator import (
    JobOrchestrator,
    WorkflowStep,
    WorkflowDefinition,
)
from backend.core.exceptions import NotFoundError, ValidationError


@pytest.fixture
def mock_workflow_repo():
    """Mock WorkflowStateRepository."""
    return AsyncMock(spec=WorkflowStateRepository)


@pytest.fixture
def mock_task_repo():
    """Mock WorkflowTaskRepository."""
    return AsyncMock(spec=WorkflowTaskRepository)


@pytest.fixture
def mock_job_repo():
    """Mock CrawlJobRepository."""
    return AsyncMock(spec=CrawlJobRepository)


@pytest.fixture
def orchestrator(mock_workflow_repo, mock_task_repo, mock_job_repo):
    """Create JobOrchestrator instance."""
    return JobOrchestrator(mock_workflow_repo, mock_task_repo, mock_job_repo)


@pytest.fixture
def sample_workflow_def():
    """Create sample workflow definition."""
    async def step1_handler():
        return {"status": "success"}

    async def step2_handler():
        return {"status": "success"}

    steps = [
        WorkflowStep(
            name="Download Images",
            task_type="download",
            handler=step1_handler,
            max_retries=3,
            estimated_duration=300,
        ),
        WorkflowStep(
            name="Validate Images",
            task_type="validate",
            handler=step2_handler,
            max_retries=2,
            dependencies=[0],
            estimated_duration=200,
        ),
    ]

    return WorkflowDefinition(
        name="Dataset Build Workflow",
        steps=steps,
        max_recovery_attempts=3,
    )


class TestWorkflowDefinition:
    """Tests for WorkflowDefinition."""

    def test_workflow_validation_success(self, sample_workflow_def):
        """Test valid workflow passes validation."""
        sample_workflow_def.validate()  # Should not raise

    def test_workflow_validation_empty_steps(self):
        """Test workflow with no steps fails validation."""
        workflow = WorkflowDefinition(
            name="Empty Workflow",
            steps=[],
        )

        with pytest.raises(ValidationError):
            workflow.validate()

    def test_workflow_validation_invalid_dependency(self):
        """Test workflow with invalid dependency fails validation."""
        async def handler():
            return {}

        steps = [
            WorkflowStep(
                name="Step 1",
                task_type="test",
                handler=handler,
                dependencies=[5],  # Invalid: index out of range
            ),
        ]

        workflow = WorkflowDefinition(name="Invalid Workflow", steps=steps)

        with pytest.raises(ValidationError):
            workflow.validate()

    def test_workflow_validation_forward_dependency(self):
        """Test workflow with forward dependency fails validation."""
        async def handler():
            return {}

        steps = [
            WorkflowStep(
                name="Step 1",
                task_type="test",
                handler=handler,
                dependencies=[1],  # Invalid: forward dependency
            ),
            WorkflowStep(
                name="Step 2",
                task_type="test",
                handler=handler,
            ),
        ]

        workflow = WorkflowDefinition(name="Invalid Workflow", steps=steps)

        with pytest.raises(ValidationError):
            workflow.validate()


class TestJobOrchestrator:
    """Tests for JobOrchestrator."""

    @pytest.mark.asyncio
    async def test_create_workflow_success(
        self, orchestrator, mock_job_repo, mock_workflow_repo, mock_task_repo, sample_workflow_def
    ):
        """Test successful workflow creation."""
        job_id = 1
        job = MagicMock(spec=CrawlJob)
        job.id = job_id

        workflow = MagicMock(spec=WorkflowState)
        workflow.id = 1

        mock_job_repo.get_by_id.return_value = job
        mock_workflow_repo.create.return_value = workflow
        mock_task_repo.create.return_value = MagicMock(spec=WorkflowTask)

        result = await orchestrator.create_workflow(
            job_id, sample_workflow_def, {"key": "value"}
        )

        assert result.id == 1
        mock_job_repo.get_by_id.assert_called_once_with(job_id)
        mock_workflow_repo.create.assert_called_once()
        assert mock_task_repo.create.call_count == 2  # Two steps

    @pytest.mark.asyncio
    async def test_create_workflow_job_not_found(
        self, orchestrator, mock_job_repo, sample_workflow_def
    ):
        """Test workflow creation fails when job not found."""
        mock_job_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await orchestrator.create_workflow(999, sample_workflow_def)

    @pytest.mark.asyncio
    async def test_create_workflow_invalid_definition(
        self, orchestrator, mock_job_repo
    ):
        """Test workflow creation fails with invalid definition."""
        job = MagicMock(spec=CrawlJob)
        mock_job_repo.get_by_id.return_value = job

        workflow = WorkflowDefinition(name="Invalid", steps=[])

        with pytest.raises(ValidationError):
            await orchestrator.create_workflow(1, workflow)

    @pytest.mark.asyncio
    async def test_get_workflow(self, orchestrator, mock_workflow_repo):
        """Test getting workflow by ID."""
        workflow = MagicMock(spec=WorkflowState)
        mock_workflow_repo.get_by_id.return_value = workflow

        result = await orchestrator.get_workflow(1)

        assert result == workflow
        mock_workflow_repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_workflow_by_job(self, orchestrator, mock_workflow_repo):
        """Test getting workflow by job ID."""
        workflow = MagicMock(spec=WorkflowState)
        mock_workflow_repo.get_by_job_id.return_value = workflow

        result = await orchestrator.get_workflow_by_job(1)

        assert result == workflow
        mock_workflow_repo.get_by_job_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_start_workflow_success(self, orchestrator, mock_workflow_repo):
        """Test successful workflow start."""
        workflow = MagicMock(spec=WorkflowState)
        workflow.status = "pending"

        updated_workflow = MagicMock(spec=WorkflowState)
        updated_workflow.status = "running"

        mock_workflow_repo.get_by_id.return_value = workflow
        mock_workflow_repo.update.return_value = updated_workflow

        result = await orchestrator.start_workflow(1)

        assert result.status == "running"
        mock_workflow_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_workflow_not_found(self, orchestrator, mock_workflow_repo):
        """Test start workflow fails when not found."""
        mock_workflow_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await orchestrator.start_workflow(999)

    @pytest.mark.asyncio
    async def test_start_workflow_invalid_state(self, orchestrator, mock_workflow_repo):
        """Test start workflow fails when not in pending state."""
        workflow = MagicMock(spec=WorkflowState)
        workflow.status = "running"

        mock_workflow_repo.get_by_id.return_value = workflow

        with pytest.raises(ValidationError):
            await orchestrator.start_workflow(1)

    @pytest.mark.asyncio
    async def test_pause_workflow(self, orchestrator, mock_workflow_repo):
        """Test pausing workflow."""
        workflow = MagicMock(spec=WorkflowState)
        paused_workflow = MagicMock(spec=WorkflowState)
        paused_workflow.status = "paused"

        mock_workflow_repo.get_by_id.return_value = workflow
        mock_workflow_repo.update.return_value = paused_workflow

        result = await orchestrator.pause_workflow(1)

        assert result.status == "paused"

    @pytest.mark.asyncio
    async def test_cancel_workflow(self, orchestrator, mock_workflow_repo):
        """Test cancelling workflow."""
        workflow = MagicMock(spec=WorkflowState)
        cancelled_workflow = MagicMock(spec=WorkflowState)
        cancelled_workflow.status = "cancelled"

        mock_workflow_repo.get_by_id.return_value = workflow
        mock_workflow_repo.update.return_value = cancelled_workflow

        result = await orchestrator.cancel_workflow(1)

        assert result.status == "cancelled"

    @pytest.mark.asyncio
    async def test_recover_workflow_success(self, orchestrator, mock_workflow_repo, mock_task_repo):
        """Test successful workflow recovery."""
        workflow = MagicMock(spec=WorkflowState)
        workflow.can_recover = True
        workflow.recovery_attempts = 0
        workflow.max_recovery_attempts = 3

        task1 = MagicMock(spec=WorkflowTask)
        task2 = MagicMock(spec=WorkflowTask)

        recovered_workflow = MagicMock(spec=WorkflowState)

        mock_workflow_repo.get_by_id.return_value = workflow
        mock_task_repo.get_by_workflow.return_value = [task1, task2]
        mock_workflow_repo.increment_recovery_attempts.return_value = recovered_workflow
        mock_workflow_repo.update.return_value = recovered_workflow

        result = await orchestrator.recover_workflow(1, from_step=1)

        assert result == recovered_workflow
        mock_workflow_repo.increment_recovery_attempts.assert_called_once()

    @pytest.mark.asyncio
    async def test_recover_workflow_max_attempts_exceeded(
        self, orchestrator, mock_workflow_repo
    ):
        """Test recovery fails when max attempts exceeded."""
        workflow = MagicMock(spec=WorkflowState)
        workflow.can_recover = False

        mock_workflow_repo.get_by_id.return_value = workflow

        with pytest.raises(ValidationError):
            await orchestrator.recover_workflow(1, from_step=0)

    @pytest.mark.asyncio
    async def test_get_workflow_progress(self, orchestrator, mock_workflow_repo, mock_task_repo):
        """Test getting workflow progress."""
        workflow = MagicMock(spec=WorkflowState)
        workflow.id = 1
        workflow.job_id = 1
        workflow.status = "running"
        workflow.progress = 50
        workflow.current_step = 1
        workflow.total_steps = 2
        workflow.recovery_attempts = 0
        workflow.max_recovery_attempts = 3

        task1 = MagicMock(spec=WorkflowTask)
        task1.id = 1
        task1.task_name = "Step 1"
        task1.task_type = "download"
        task1.status = "completed"
        task1.retry_count = 0
        task1.error_message = None

        task2 = MagicMock(spec=WorkflowTask)
        task2.id = 2
        task2.task_name = "Step 2"
        task2.task_type = "validate"
        task2.status = "running"
        task2.retry_count = 0
        task2.error_message = None

        mock_workflow_repo.get_by_id.return_value = workflow
        mock_task_repo.get_by_workflow.return_value = [task1, task2]

        result = await orchestrator.get_workflow_progress(1)

        assert result["workflow_id"] == 1
        assert result["progress"] == 50
        assert result["completed_tasks"] == 1
        assert result["running_tasks"] == 1
        assert len(result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_get_active_workflows(self, orchestrator, mock_workflow_repo):
        """Test getting active workflows."""
        workflows = [MagicMock(spec=WorkflowState), MagicMock(spec=WorkflowState)]
        mock_workflow_repo.get_active_workflows.return_value = workflows

        result = await orchestrator.get_active_workflows()

        assert len(result) == 2
        mock_workflow_repo.get_active_workflows.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_failed_workflows(self, orchestrator, mock_workflow_repo):
        """Test getting failed workflows."""
        workflows = [MagicMock(spec=WorkflowState)]
        mock_workflow_repo.get_failed_workflows.return_value = workflows

        result = await orchestrator.get_failed_workflows()

        assert len(result) == 1
        mock_workflow_repo.get_failed_workflows.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recoverable_workflows(self, orchestrator, mock_workflow_repo):
        """Test getting recoverable workflows."""
        workflows = [MagicMock(spec=WorkflowState)]
        mock_workflow_repo.get_recoverable_workflows.return_value = workflows

        result = await orchestrator.get_recoverable_workflows()

        assert len(result) == 1
        mock_workflow_repo.get_recoverable_workflows.assert_called_once()
