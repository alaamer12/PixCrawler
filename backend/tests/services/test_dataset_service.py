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

from backend.models import Dataset, CrawlJob
from backend.schemas.dataset import (
    DatasetCreate, DatasetUpdate, DatasetStatus, DatasetResponse
)
from backend.schemas.crawl_jobs import CrawlJobStatus
from backend.services.dataset import DatasetService


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
    return Dataset(
        id=1,
        user_id=uuid4(),
        name="Test Dataset",
        description="Test description",
        status=DatasetStatus.PENDING,
        keywords=["cat", "dog"],
        max_images=100,
        search_engines=["google", "bing"],
        crawl_job_id=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_crawl_job():
    """Create sample crawl job for testing."""
    return CrawlJob(
        id=1,
        name="Test Crawl Job",
        keywords=["cat", "dog"],
        max_images=100,
        sources=["google", "bing"],
        status=CrawlJobStatus.PENDING,
        downloaded_images=0,
        valid_images=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


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
    
    mock_crawl_job_repo.create.return_value = sample_crawl_job
    mock_dataset_repo.create.return_value = sample_dataset
    
    result = await dataset_service.create_dataset(dataset_in, user_id)
    
    assert isinstance(result, DatasetResponse)
    assert result.name == sample_dataset.name
    mock_crawl_job_repo.create.assert_called_once()
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
    
    with pytest.raises(Exception) as exc:
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
    updated_dataset = Dataset(**{**sample_dataset.__dict__, "name": "Updated Name"})
    
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    mock_dataset_repo.update.return_value = updated_dataset
    mock_crawl_job_repo.get_by_id.return_value = None
    
    result = await dataset_service.update_dataset(
        1, dataset_update, sample_dataset.user_id
    )
    
    assert result.name == "Updated Name"
    mock_dataset_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_dataset_not_found(
    dataset_service,
    mock_dataset_repo
):
    """Test update when dataset doesn't exist."""
    mock_dataset_repo.get_by_id.return_value = None
    dataset_update = DatasetUpdate(name="Updated")
    
    with pytest.raises(Exception) as exc:
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
    sample_dataset.status = DatasetStatus.PROCESSING
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    dataset_update = DatasetUpdate(name="Updated")
    
    with pytest.raises(Exception) as exc:
        await dataset_service.update_dataset(
            1, dataset_update, sample_dataset.user_id
        )
    
    assert "processing" in str(exc.value).lower()


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
    
    with pytest.raises(Exception) as exc:
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
    sample_dataset.status = DatasetStatus.PROCESSING
    cancelled_dataset = Dataset(**{**sample_dataset.__dict__, "status": DatasetStatus.CANCELLED})
    
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    mock_dataset_repo.update.return_value = cancelled_dataset
    mock_crawl_job_repo.get_by_id.return_value = None
    
    result = await dataset_service.cancel_dataset(1, sample_dataset.user_id)
    
    assert result.status == DatasetStatus.CANCELLED
    mock_crawl_job_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_dataset_invalid_state(
    dataset_service,
    mock_dataset_repo,
    sample_dataset
):
    """Test cancel fails for completed dataset."""
    sample_dataset.status = DatasetStatus.COMPLETED
    mock_dataset_repo.get_by_id.return_value = sample_dataset
    
    with pytest.raises(Exception) as exc:
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
    mock_dataset_repo.get_stats.return_value = {
        "total": 10,
        "active": 2,
        "completed": 7,
        "failed": 1
    }
    mock_dataset_repo.list.return_value = [
        Dataset(id=i, user_id=uuid4(), name=f"Dataset {i}")
        for i in range(1, 11)
    ]
    mock_crawl_job_repo.get_image_stats.return_value = {
        "total_images": 1000
    }
    
    result = await dataset_service.get_dataset_stats()
    
    assert result.total_datasets == 10
    assert result.active_datasets == 2
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
    
    mock_dataset_repo.get_stats.return_value = {
        "total": 5,
        "active": 1,
        "completed": 4,
        "failed": 0
    }
    mock_dataset_repo.list.return_value = [
        Dataset(id=i, user_id=user_id, name=f"Dataset {i}")
        for i in range(1, 6)
    ]
    mock_crawl_job_repo.get_image_stats.return_value = {
        "total_images": 500
    }
    
    result = await dataset_service.get_dataset_stats(user_id)
    
    assert result.total_datasets == 5
    mock_dataset_repo.get_stats.assert_called_once_with(user_id)
    mock_dataset_repo.list.assert_called_once_with(user_id=user_id)


@pytest.mark.asyncio
async def test_get_dataset_stats_calculates_average(
    dataset_service,
    mock_dataset_repo,
    mock_crawl_job_repo
):
    """Test statistics calculates average images per dataset."""
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
    
    assert result.average_images_per_dataset == 100.0
