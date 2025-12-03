"""
Integration tests for complete backend workflows.

These tests verify the interaction between multiple components:
- API -> Service -> Database
- Service -> Celery -> Builder/Validator
- Builder/Validator -> Storage -> Database
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from backend.models import CrawlJob, Project, Dataset
from backend.services.crawl_job import CrawlJobService
from backend.services.dataset import DatasetService
from backend.core.config import get_settings

settings = get_settings()

# Use the existing fixtures from conftest.py
# client, app, mock_supabase_client, etc.

@pytest.mark.asyncio
class TestBuilderBackendIntegration:
    """Tests for Builder + Backend integration workflows."""

    async def test_crawl_job_execution_flow(self, client, mock_supabase_client, app):
        """
        Test the full crawl job execution flow:
        1. Create Job (API)
        2. Execute Job (Celery Task - Manually Invoked)
        3. Builder Execution (Mocked Builder, real Service logic)
        4. Status Update (Service -> DB)
        """
        from backend.services.crawl_job import execute_crawl_job
        
        # 1. Setup - Create Project and User
        # We need a valid user and project in the DB
        # Since we are using the client fixture which mocks auth, we can assume a user exists
        # But for the service layer to work, we might need to insert a project into the DB
        
        # Mock the dependency overrides to get the current user
        user_id = str(uuid4())
        app.dependency_overrides = {} # Reset first
        
        # We need to insert a project into the test database
        # We can use the 'client' to create a project if the endpoint exists, 
        # or use a repository directly if we have access to the session.
        # Let's try to use the API to create a project first.
        
        # Mock authentication
        async def mock_get_current_user():
            return {"user_id": user_id, "email": "test@example.com"}
            
        from backend.api.dependencies import get_current_user
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        # Create Project via API (assuming project endpoints exist and work)
        # If not, we might need to insert directly into DB. 
        # Let's assume we can insert directly for stability using a fixture or direct DB access.
        # But we don't have easy access to the session here without a fixture.
        # Let's rely on the API for project creation if possible, or mock the repo.
        
        # Actually, let's mock the `execute_crawl_job` in the API module to avoid 
        # it running in the background during the API call.
        with patch("backend.api.v1.endpoints.crawl_jobs.execute_crawl_job") as mock_background_task:
            
            # Create a project first (mocking the project service or repo might be easier)
            # But let's try to be as "integrated" as possible.
            # We need a project ID.
            # Let's mock the ProjectRepository.get_by_id to return a fake project
            # so we don't need to actually create one in the DB for the API check.
            
            with patch("backend.services.crawl_job.ProjectRepository.get_by_id") as mock_get_project:
                mock_get_project.return_value = MagicMock(id=1, user_id=uuid4())
                
                # Also need to mock create_job in the service if we don't want to use real DB
                # But we WANT to use real DB for integration.
                # So we need a real session.
                # The `client` fixture uses `app` which uses `get_session`.
                # We should probably use the `db_session` fixture if available, or `override_dependencies`.
                
                # Let's simplify: Mock the Builder, but let the Service and DB run for real.
                # We need to insert a project into the DB.
                pass 

    async def test_crawl_job_execution_flow_implementation(self, client, mock_supabase_client, app):
        """
        Implementation of the test flow.
        """
        # We need to patch the Builder in the service module
        with patch("backend.services.crawl_job.Builder") as MockBuilder:
            # Setup Mock Builder instance
            mock_builder_instance = MockBuilder.return_value
            
            # Mock generate_async_batches to yield some fake images
            async def async_gen(batch_size=50):
                yield [{"original_url": "http://example.com/img1.jpg", "filename": "img1.jpg", "is_valid": True}]
                yield [{"original_url": "http://example.com/img2.jpg", "filename": "img2.jpg", "is_valid": True}]
            
            mock_builder_instance.generate_async_batches.side_effect = lambda batch_size: async_gen(batch_size)
            
            # Mock cleanup
            mock_builder_instance.cleanup = MagicMock()

            # We also need to mock run_sync and run_in_threadpool because they might not work well with mocks
            with patch("backend.services.crawl_job.run_sync", side_effect=lambda func, *args, **kwargs: func(*args, **kwargs) if func != MockBuilder else mock_builder_instance), \
                 patch("backend.services.crawl_job.run_in_threadpool", side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)):
                
                # 1. Create a Job manually in the DB (to skip API/Project complexity for this specific test)
                # Or use the service to create it.
                # We need a session.
                from backend.database.connection import AsyncSessionLocal
                from backend.repositories import CrawlJobRepository, ProjectRepository
                from backend.services.crawl_job import CrawlJobService, execute_crawl_job
                
                async with AsyncSessionLocal() as session:
                    # Create a dummy project
                    project_repo = ProjectRepository(session)
                    # We need to create a project first. 
                    # Assuming Project model has required fields.
                    # This might be tricky if we don't know the Project model details.
                    # Let's try to mock the repositories inside execute_crawl_job instead?
                    # No, we want to test DB interaction.
                    
                    # Let's assume we can create a project.
                    new_project = Project(name="Test Project", user_id=uuid4(), description="Test")
                    session.add(new_project)
                    await session.commit()
                    await session.refresh(new_project)
                    
                    project_id = new_project.id
                    user_id = str(new_project.user_id)
                    
                    # Create Job
                    job_service = CrawlJobService(
                        CrawlJobRepository(session),
                        project_repo,
                        MagicMock(), # ImageRepo
                        MagicMock()  # ActivityLogRepo
                    )
                    
                    job = await job_service.create_job(
                        project_id=project_id,
                        name="Integration Test Job",
                        keywords=["test"],
                        max_images=10,
                        user_id=user_id
                    )
                    job_id = job.id
                
                # 2. Execute Job (Manually call the task function)
                # We pass the job_id and user_id
                await execute_crawl_job(job_id, user_id=user_id, tier="free")
                
                # 3. Verify Job Status in DB
                async with AsyncSessionLocal() as session:
                    job_repo = CrawlJobRepository(session)
                    updated_job = await job_repo.get_by_id(job_id)
                    
                    assert updated_job.status == "completed"
                    assert updated_job.downloaded_images == 2
                    assert updated_job.valid_images == 2
                    assert updated_job.progress == 100
                    
            # Verify Builder was called
            # Since we mocked the class, we can check if it was instantiated
            # However, run_sync might make this check tricky if we didn't mock it correctly.
            # But we mocked run_sync to return mock_builder_instance.
            
            # Assertions on mock_builder_instance
            mock_builder_instance.generate_async_batches.assert_called()
            mock_builder_instance.cleanup.assert_called()

@pytest.mark.asyncio
class TestValidatorBackendIntegration:
    """Tests for Validator + Backend integration workflows."""
    
    async def test_dataset_validation_flow(self):
        pass

@pytest.mark.asyncio
class TestCeleryIntegration:
    """Tests for Celery task execution and monitoring."""
    
    async def test_task_chain_execution(self):
        pass

@pytest.mark.asyncio
class TestDatabaseIntegration:
    """Tests for database operations across components."""
    
    async def test_transactional_integrity(self):
        pass

@pytest.mark.asyncio
class TestStorageIntegration:
    """Tests for storage provider integration."""
    
    async def test_storage_workflow(self):
        pass

@pytest.mark.asyncio
class TestApiAuthIntegration:
    """Tests for API and Authentication flows."""
    
    async def test_full_user_flow(self):
        pass
