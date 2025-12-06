import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import UUID

from backend.services.dataset import DatasetService
from backend.models import Dataset, DatasetVersion, CrawlJob
from backend.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetStatus
from backend.core.exceptions import NotFoundError, ValidationError

@pytest.fixture
def dataset_service(db_session):
    return DatasetService(db_session)

@pytest.mark.asyncio
async def test_create_dataset_creates_initial_version(dataset_service, db_session):
    # Mocking repositories
    dataset_service.dataset_repo.create = AsyncMock()
    dataset_service.dataset_repo.create_version = AsyncMock()
    dataset_service.crawl_job_repo.create = AsyncMock()
    
    # Setup return values
    mock_dataset = Dataset(id=1, name="Test", status="pending", created_at=datetime.now())
    dataset_service.dataset_repo.create.return_value = mock_dataset
    
    mock_crawl_job = CrawlJob(id=100)
    dataset_service.crawl_job_repo.create.return_value = mock_crawl_job
    
    # Execute
    data = DatasetCreate(
        name="Test",
        keywords=["cat"],
        search_engines=["google"],
        max_images=10
    )
    await dataset_service.create_dataset(data, user_id=1)
    
    # Verify initial version creation
    dataset_service.dataset_repo.create_version.assert_called_once()
    call_args = dataset_service.dataset_repo.create_version.call_args[0][0]
    assert call_args["version_number"] == 1
    assert call_args["dataset_id"] == 1
    assert call_args["crawl_job_id"] == 100
    assert call_args["max_images"] == 10

@pytest.mark.asyncio
async def test_update_dataset_creates_new_version_on_config_change(dataset_service, db_session):
    # Mock repositories
    dataset_service.dataset_repo.get_by_id = AsyncMock()
    dataset_service.dataset_repo.get_versions = AsyncMock()
    dataset_service.dataset_repo.update = AsyncMock()
    dataset_service.dataset_repo.create_version = AsyncMock()
    dataset_service.crawl_job_repo.create = AsyncMock()
    
    # Setup existing dataset
    mock_dataset = Dataset(
        id=1, 
        user_id=1,
        name="Test", 
        keywords=["cat"],
        search_engines=["google"],
        max_images=10,
        status="completed",
        crawl_job_id=100
    )
    dataset_service.dataset_repo.get_by_id.return_value = mock_dataset
    
    # Setup existing versions
    dataset_service.dataset_repo.get_versions.return_value = [
        DatasetVersion(version_number=1)
    ]
    
    # Setup new crawl job
    mock_new_crawl_job = CrawlJob(id=101)
    dataset_service.crawl_job_repo.create.return_value = mock_new_crawl_job
    
    dataset_service.dataset_repo.update.return_value = mock_dataset
    dataset_service.get_dataset_by_id = AsyncMock() # Mock return

    # Execute update (config change: max_images 10 -> 20)
    update_data = DatasetUpdate(
        max_images=20,
        name="Test Updated" # Valid because at least one field provided
    )
    
    await dataset_service.update_dataset(dataset_id=1, dataset_update=update_data, user_id=1)
    
    # Verify new version creation
    dataset_service.dataset_repo.create_version.assert_called_once()
    call_args = dataset_service.dataset_repo.create_version.call_args[0][0]
    assert call_args["version_number"] == 2
    assert call_args["max_images"] == 20
    assert call_args["crawl_job_id"] == 101

@pytest.mark.asyncio
async def test_rollback_dataset(dataset_service, db_session):
    # Mock repositories and methods
    dataset_service.get_dataset_version = AsyncMock()
    dataset_service.update_dataset = AsyncMock()
    
    # Setup target version
    mock_version = DatasetVersion(
        version_number=1,
        keywords=["old_keyword"],
        search_engines=["bing"],
        max_images=50
    )
    dataset_service.get_dataset_version.return_value = mock_version
    
    # Execute
    await dataset_service.rollback_dataset(dataset_id=1, version_number=1, user_id=1)
    
    # Verify update called with config from version 1
    dataset_service.update_dataset.assert_called_once()
    call_args = dataset_service.update_dataset.call_args
    update_obj = call_args[0][1] # 2nd arg is dataset_update
    
    assert update_obj.keywords == ["old_keyword"]
    assert update_obj.max_images == 50
    assert "Rollback to v1" in update_obj.name
