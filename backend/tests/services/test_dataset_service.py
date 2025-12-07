"""
Unit tests for DatasetService.

Tests business logic for dataset operations including creation,
retrieval, updates, deletion, and statistics.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from fastapi import HTTPException

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import Dataset, CrawlJob
from backend.schemas.dataset import (
    DatasetCreate, DatasetUpdate, DatasetStatus, DatasetResponse
)
from backend.schemas.crawl_jobs import CrawlJobStatus
from backend.services.dataset import DatasetService


def copy_model(model, **updates):
    """Helper to create a copy of a SQLAlchemy model with updates."""
    # Get all mapped columns
    mapper = model.__class__.__mapper__
    data = {}
    for column in mapper.columns:
        if hasattr(model, column.key):
            data[column.key] = getattr(model, column.key)
    
    # Apply updates
    data.update(updates)
    
    # Create new instance
    return model.__class__(**data)


@pytest.fixture
def mock_dataset_repo():
    """Create mock dataset repository."""
    return AsyncMock()


@pytest.fixture
def mock_crawl_job_repo():
    """Create mock crawl job repository."""
    return AsyncMock()


@pytest.fixture
def dataset_service(mock_dataset_repo, mock_crawl_job_repo):
    """Create dataset service with mocked repositories."""
    return DatasetService(mock_dataset_repo, mock_crawl_job_repo)


@pytest.fixture
def sample_dataset():
    """Create sample dataset for testing."""
    dataset = Dataset(
        id=1,
        user_id=uuid4(),
        name="Test Dataset",
        description="Test description",
        status="pending",
        keywords=["cat", "dog"],
        max_images=100,
        search_engines=["google", "bing"],
        crawl_job_id=1
    )
    dataset.created_at = datetime.utcnow()
    dataset.updated_at = datetime.utcnow()
    return dataset


@pytest.fixture
def sample_crawl_job():
    """Create sample crawl job for testing."""
    job = CrawlJob(
        id=1,
        project_id=1,
        name="Test Crawl Job",
        keywords={"keywords": ["cat", "dog"]},
        max_images=100,
        status="pending",
        downloaded_images=0,
        valid_images=0
    )
    job.created_at = datetime.utcnow()
    job.updated_at = datetime.utcnow()
    return job


# ============================================================================
# CREATE DATASET TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_dataset_success(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo,
    sample_dataset,
    sample_crawl_job
):
    """Test successful dataset creation."""
    user_id = uuid4()
    dataset_in = DatasetCreate(
        name="New Dataset",
        description="Description",
        keywords=["cat", "dog"],
        max_images=100,
        search_engines=["google"]
    )
    
    # Mock the crawl job repo to bypass validation
    async def mock_create_crawl_job(crawl_job_data):
        return sample_crawl_job
    
    mock_crawl_job_repo.create = mock_create_crawl_job
    mock_dataset_repo.create.return_value = sample_dataset
    
    result = await dataset_service.create_dataset(dataset_in, user_id)
    
    assert isinstance(result, DatasetResponse)
    assert result.name == sample_dataset.name
    mock_dataset_repo.create.assert_called_once()


# ============================================================================
# GET DATASET TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_dataset_by_id_success(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo,
    sample_dataset,
    sample_crawl_job
):
    """Test successful dataset retrieval."""
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    mock_crawl_job_repo.get_by_id.return_value = sample_crawl_job
    
    result = await dataset_service.get_dataset_by_id(1, sample_dataset.user_id)
    
    assert isinstance(result, DatasetResponse)
    assert result.id == sample_dataset.id
    mock_dataset_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_dataset_by_id_not_found(
    dataset_service,
    mock_dataset_repo
):
    """Test dataset retrieval when dataset doesn't exist."""
    mock_dataset_repo.get_by_id.return_value = None
    
    with pytest.raises(NotFoundError) as exc:
        await dataset_service.get_dataset_by_id(999)
    
    assert "not found" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_get_dataset_by_id_unauthorized(
    dataset_service,
    mock_dataset_repo,
    sample_dataset
):
    """Test dataset retrieval with wrong user."""
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    other_user_id = uuid4()
    
    with pytest.raises(PermissionError):
        await dataset_service.get_dataset_by_id(1, other_user_id)


@pytest.mark.asyncio
async def test_get_dataset_with_progress_calculation(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo,
    sample_dataset,
    sample_crawl_job
):
    """Test dataset retrieval calculates progress correctly."""
    sample_crawl_job.downloaded_images = 50
    sample_crawl_job.valid_images = 45
    sample_dataset.max_images = 100
    sample_dataset.status = "processing"
    
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    mock_crawl_job_repo.get_by_id.return_value = sample_crawl_job
    
    result = await dataset_service.get_dataset_by_id(1, sample_dataset.user_id)
    
    assert result.progress == 50.0
    assert result.images_collected == 45


# ============================================================================
# UPDATE DATASET TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_dataset_success(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo,
    sample_dataset
):
    """Test successful dataset update."""
    dataset_update = DatasetUpdate(name="Updated Name")
    
    # Create updated dataset by modifying the name
    updated_dataset = Dataset(
        id=sample_dataset.id,
        user_id=sample_dataset.user_id,
        name="Updated Name",
        description=sample_dataset.description,
        status=sample_dataset.status,
        keywords=sample_dataset.keywords,
        max_images=sample_dataset.max_images,
        search_engines=sample_dataset.search_engines,
        crawl_job_id=sample_dataset.crawl_job_id
    )
    updated_dataset.created_at = sample_dataset.created_at
    updated_dataset.updated_at = datetime.utcnow()
    
    mock_dataset_repo.get_by_id.side_effect = [sample_dataset, updated_dataset]
    mock_dataset_repo.update.return_value = updated_dataset
    mock_crawl_job_repo.get_by_id.return_value = None
    
    result = await dataset_service.update_dataset(
        1, dataset_update, sample_dataset.user_id
    )
    
    assert result.name == "Updated Name"
    assert result.name == "Updated Name"
    # Verify the update was called with the correct arguments
    # Note: update is called twice, once for the actual update and once for last_accessed_at in get_dataset_by_id
    mock_dataset_repo.update.assert_any_call(1, {"name": "Updated Name"})


@pytest.mark.asyncio
async def test_update_dataset_not_found(
    dataset_service,
    mock_dataset_repo
):
    """Test update when dataset doesn't exist."""
    mock_dataset_repo.get_by_id.return_value = None
    dataset_update = DatasetUpdate(name="Updated")
    
    with pytest.raises(NotFoundError) as exc:
        await dataset_service.update_dataset(999, dataset_update, uuid4())
    
    assert "not found" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_update_dataset_unauthorized(
    dataset_service,
    mock_dataset_repo,
    sample_dataset
):
    """Test update with wrong user."""
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    dataset_update = DatasetUpdate(name="Updated")
    
    with pytest.raises(PermissionError):
        await dataset_service.update_dataset(1, dataset_update, uuid4())


@pytest.mark.asyncio
async def test_update_dataset_while_processing(
    dataset_service,
    mock_dataset_repo,
    sample_dataset
):
    """Test update fails when dataset is processing."""
    sample_dataset.status = "processing"
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    dataset_update = DatasetUpdate(name="Updated")
    
    with pytest.raises(ValidationError) as exc:
        await dataset_service.update_dataset(
            1, dataset_update, sample_dataset.user_id
        )
    
    assert "processed" in str(exc.value).lower()


# ============================================================================
# DELETE DATASET TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_delete_dataset_success(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo,
    sample_dataset
):
    """Test successful dataset deletion."""
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    mock_dataset_repo.delete.return_value = True
    
    await dataset_service.delete_dataset(1, sample_dataset.user_id)
    
    mock_dataset_repo.delete.assert_called_once_with(1)
    mock_crawl_job_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_dataset_not_found(
    dataset_service,
    mock_dataset_repo
):
    """Test delete when dataset doesn't exist."""
    mock_dataset_repo.get_by_id.return_value = None
    
    with pytest.raises(NotFoundError) as exc:
        await dataset_service.delete_dataset(999, uuid4())
    
    assert "not found" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_delete_dataset_unauthorized(
    dataset_service,
    mock_dataset_repo,
    sample_dataset
):
    """Test delete with wrong user."""
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    
    with pytest.raises(PermissionError):
        await dataset_service.delete_dataset(1, uuid4())


# ============================================================================
# CANCEL DATASET TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_cancel_dataset_success(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo,
    sample_dataset
):
    """Test successful dataset cancellation."""
    sample_dataset.status = "processing"
    
    # Create cancelled dataset
    cancelled_dataset = Dataset(
        id=sample_dataset.id,
        user_id=sample_dataset.user_id,
        name=sample_dataset.name,
        description=sample_dataset.description,
        status="cancelled",
        keywords=sample_dataset.keywords,
        max_images=sample_dataset.max_images,
        search_engines=sample_dataset.search_engines,
        crawl_job_id=sample_dataset.crawl_job_id
    )
    cancelled_dataset.created_at = sample_dataset.created_at
    cancelled_dataset.updated_at = datetime.utcnow()
    
    mock_dataset_repo.get_by_id.side_effect = [sample_dataset, cancelled_dataset]
    mock_dataset_repo.update.return_value = cancelled_dataset
    mock_crawl_job_repo.get_by_id.return_value = None
    
    result = await dataset_service.cancel_dataset(1, sample_dataset.user_id)
    
    assert result.status == "cancelled"
    mock_crawl_job_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_dataset_invalid_state(
    dataset_service,
    mock_dataset_repo,
    sample_dataset
):
    """Test cancel fails for completed dataset."""
    sample_dataset.status = "completed"
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    
    with pytest.raises(ValidationError) as exc:
        await dataset_service.cancel_dataset(1, sample_dataset.user_id)
    
    assert "cannot cancel" in str(exc.value).lower()


# ============================================================================
# STATISTICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_dataset_stats_success(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo
):
    """Test successful statistics retrieval."""
    # Mock returns dict with keys that service maps to DatasetStats fields
    mock_dataset_repo.get_stats.return_value = {
        "total": 10,
        "active": 2,  # Maps to processing_datasets
        "completed": 7,
        "failed": 1
    }
    mock_dataset_repo.list.return_value = []
    mock_crawl_job_repo.get_image_stats.return_value = {
        "total_images": 1000
    }
    
    result = await dataset_service.get_dataset_stats()
    
    assert result.total_datasets == 10
    assert result.processing_datasets == 2  # Mapped from "active"
    assert result.completed_datasets == 7
    assert result.failed_datasets == 1
    assert result.total_images == 1000


@pytest.mark.asyncio
async def test_get_dataset_stats_with_user_filter(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo
):
    """Test statistics retrieval filtered by user."""
    user_id = uuid4()
    
    # Create mock datasets properly
    mock_datasets = []
    for i in range(1, 6):
        ds = Dataset(
            id=i,
            user_id=user_id,
            name=f"Dataset {i}",
            status="completed",
            keywords=[],
            max_images=100,
            search_engines=[]
        )
        mock_datasets.append(ds)
    
    mock_dataset_repo.get_stats.return_value = {
        "total": 5,
        "active": 1,  # Maps to processing_datasets
        "completed": 4,
        "failed": 0
    }
    mock_dataset_repo.list.return_value = mock_datasets
    mock_crawl_job_repo.get_image_stats.return_value = {
        "total_images": 500
    }
    
    result = await dataset_service.get_dataset_stats(user_id)
    
    assert result.total_datasets == 5
    assert result.processing_datasets == 1  # Mapped from "active"
    mock_dataset_repo.get_stats.assert_called_once_with(user_id)
    mock_dataset_repo.list.assert_called_once_with(user_id=user_id)


@pytest.mark.asyncio
async def test_get_dataset_stats_all_completed(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo
):
    """Test statistics with all datasets completed."""
    mock_dataset_repo.get_stats.return_value = {
        "total": 10,
        "active": 0,
        "completed": 10,
        "failed": 0
    }
    mock_dataset_repo.list.return_value = []
    mock_crawl_job_repo.get_image_stats.return_value = {
        "total_images": 1000
    }
    
    result = await dataset_service.get_dataset_stats()
    
    assert result.total_datasets == 10
    assert result.processing_datasets == 0
    assert result.completed_datasets == 10
    assert result.total_images == 1000
