"""
Tests for CrawlJobRepository task management methods.

This module tests the task management methods added to CrawlJobRepository
for Celery integration, including task ID tracking, job completion, and
failure handling.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.crawl_job_repository import CrawlJobRepository
from backend.database.models import CrawlJob, Project, Profile


@pytest.fixture
async def test_profile(session: AsyncSession):
    """Create a test user profile."""
    from uuid import uuid4
    profile = Profile(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        role="user"
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


@pytest.fixture
async def test_project(session: AsyncSession, test_profile: Profile):
    """Create a test project."""
    project = Project(
        name="Test Project",
        user_id=test_profile.id,
        status="active"
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


@pytest.fixture
async def test_job(session: AsyncSession, test_project: Project):
    """Create a test crawl job."""
    job = CrawlJob(
        project_id=test_project.id,
        name="Test Job",
        keywords=["test", "keyword"],
        max_images=100,
        status="pending",
        progress=0,
        total_chunks=10,
        active_chunks=0,
        completed_chunks=0,
        failed_chunks=0,
        task_ids=[]
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


@pytest.fixture
def repository(session: AsyncSession):
    """Create a CrawlJobRepository instance."""
    return CrawlJobRepository(session)


class TestAddTaskId:
    """Tests for add_task_id method."""
    
    async def test_add_task_id_to_empty_list(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test adding a task ID to an empty task_ids list."""
        task_id = "task_123"
        
        updated_job = await repository.add_task_id(test_job.id, task_id)
        
        assert updated_job is not None
        assert task_id in updated_job.task_ids
        assert len(updated_job.task_ids) == 1
    
    async def test_add_multiple_task_ids(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test adding multiple task IDs."""
        task_ids = ["task_1", "task_2", "task_3"]
        
        for task_id in task_ids:
            await repository.add_task_id(test_job.id, task_id)
        
        updated_job = await repository.get_by_id(test_job.id)
        assert updated_job is not None
        assert len(updated_job.task_ids) == 3
        for task_id in task_ids:
            assert task_id in updated_job.task_ids
    
    async def test_add_duplicate_task_id(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test that duplicate task IDs are not added."""
        task_id = "task_duplicate"
        
        await repository.add_task_id(test_job.id, task_id)
        await repository.add_task_id(test_job.id, task_id)
        
        updated_job = await repository.get_by_id(test_job.id)
        assert updated_job is not None
        assert len(updated_job.task_ids) == 1
        assert task_id in updated_job.task_ids
    
    async def test_add_task_id_nonexistent_job(
        self,
        repository: CrawlJobRepository
    ):
        """Test adding task ID to non-existent job returns None."""
        result = await repository.add_task_id(99999, "task_123")
        assert result is None


class TestMarkCompleted:
    """Tests for mark_completed method."""
    
    async def test_mark_completed_sets_status(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test that mark_completed sets status to 'completed'."""
        updated_job = await repository.mark_completed(test_job.id)
        
        assert updated_job is not None
        assert updated_job.status == "completed"
    
    async def test_mark_completed_sets_progress_to_100(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test that mark_completed sets progress to 100."""
        updated_job = await repository.mark_completed(test_job.id)
        
        assert updated_job is not None
        assert updated_job.progress == 100
    
    async def test_mark_completed_sets_timestamp(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test that mark_completed sets completed_at timestamp."""
        before = datetime.utcnow()
        updated_job = await repository.mark_completed(test_job.id)
        after = datetime.utcnow()
        
        assert updated_job is not None
        assert updated_job.completed_at is not None
        assert before <= updated_job.completed_at <= after
    
    async def test_mark_completed_nonexistent_job(
        self,
        repository: CrawlJobRepository
    ):
        """Test marking non-existent job as completed returns None."""
        result = await repository.mark_completed(99999)
        assert result is None


class TestMarkFailed:
    """Tests for mark_failed method."""
    
    async def test_mark_failed_sets_status(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test that mark_failed sets status to 'failed'."""
        error_msg = "Test error message"
        updated_job = await repository.mark_failed(test_job.id, error_msg)
        
        assert updated_job is not None
        assert updated_job.status == "failed"
    
    async def test_mark_failed_sets_timestamp(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test that mark_failed sets completed_at timestamp."""
        error_msg = "Test error message"
        before = datetime.utcnow()
        updated_job = await repository.mark_failed(test_job.id, error_msg)
        after = datetime.utcnow()
        
        assert updated_job is not None
        assert updated_job.completed_at is not None
        assert before <= updated_job.completed_at <= after
    
    async def test_mark_failed_nonexistent_job(
        self,
        repository: CrawlJobRepository
    ):
        """Test marking non-existent job as failed returns None."""
        result = await repository.mark_failed(99999, "error")
        assert result is None


class TestGetActiveTasks:
    """Tests for get_active_tasks method."""
    
    async def test_get_active_tasks_empty_list(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test getting active tasks from job with no tasks."""
        task_ids = await repository.get_active_tasks(test_job.id)
        
        assert task_ids == []
    
    async def test_get_active_tasks_with_tasks(
        self,
        repository: CrawlJobRepository,
        test_job: CrawlJob
    ):
        """Test getting active tasks from job with tasks."""
        expected_tasks = ["task_1", "task_2", "task_3"]
        
        for task_id in expected_tasks:
            await repository.add_task_id(test_job.id, task_id)
        
        task_ids = await repository.get_active_tasks(test_job.id)
        
        assert len(task_ids) == 3
        assert set(task_ids) == set(expected_tasks)
    
    async def test_get_active_tasks_nonexistent_job(
        self,
        repository: CrawlJobRepository
    ):
        """Test getting active tasks from non-existent job returns empty list."""
        task_ids = await repository.get_active_tasks(99999)
        assert task_ids == []
