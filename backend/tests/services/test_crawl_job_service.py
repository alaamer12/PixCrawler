"""
Unit tests for CrawlJobService.

Tests business logic for crawl job management including creation,
progress tracking, status updates, and cancellation.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import make_transient

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import CrawlJob, Project, Image
from backend.services.crawl_job import CrawlJobService, RateLimiter, RateLimitExceeded


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
def mock_crawl_job_repo():
    """Create mock crawl job repository."""
    return AsyncMock()


@pytest.fixture
def mock_project_repo():
    """Create mock project repository."""
    return AsyncMock()


@pytest.fixture
def mock_image_repo():
    """Create mock image repository."""
    return AsyncMock()


@pytest.fixture
def mock_activity_log_repo():
    """Create mock activity log repository."""
    return AsyncMock()


@pytest.fixture
def mock_dataset_repo():
    """Create mock dataset repository."""
    return AsyncMock()


@pytest.fixture
def crawl_job_service(
    mock_crawl_job_repo,
    mock_project_repo,
    mock_image_repo,
    mock_activity_log_repo,
    mock_dataset_repo
):
    """Create crawl job service with mocked repositories."""
    return CrawlJobService(
        crawl_job_repo=mock_crawl_job_repo,
        project_repo=mock_project_repo,
        image_repo=mock_image_repo,
        activity_log_repo=mock_activity_log_repo,
        dataset_repo=mock_dataset_repo
    )


@pytest.fixture
def sample_project():
    """Create sample project for testing."""
    return Project(
        id=1,
        user_id=uuid4(),
        name="Test Project",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_crawl_job():
    """Create sample crawl job for testing."""
    return CrawlJob(
        id=1,
        dataset_id=1,
        name="Test Crawl Job",
        keywords={"keywords": ["cat", "dog"]},
        max_images=100,
        status="pending",
        progress=0,
        downloaded_images=0,
        valid_images=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


# ============================================================================
# RATE LIMITER TESTS
# ============================================================================

def test_rate_limiter_invalid_tier():
    """Test rate limiter with invalid tier."""
    with pytest.raises(ValueError) as exc:
        RateLimiter.check_concurrency("user123", "invalid_tier")
    
    assert "invalid tier" in str(exc.value).lower()


@patch('backend.services.crawl_job.celery_app.control.inspect')
def test_rate_limiter_free_tier_limit_exceeded(mock_inspect):
    """Test rate limiter for free tier when limit is exceeded."""
    # Mock inspector to return 1 active job for the user
    mock_inspector = mock_inspect.return_value
    mock_inspector.active.return_value = {
        'worker1': [{
            'name': 'backend.tasks.execute_crawl_job',
            'kwargs': {'user_id': 'user123'}
        }]
    }
    mock_inspector.reserved.return_value = {}
    
    with pytest.raises(RateLimitExceeded) as exc:
        RateLimiter.check_concurrency("user123", "free")
    
    assert exc.value.tier == "free"
    assert exc.value.active_jobs == 1
    assert exc.value.limit == 1


@patch('backend.services.crawl_job.celery_app.control.inspect')
def test_rate_limiter_pro_tier_within_limit(mock_inspect):
    """Test rate limiter for pro tier within limit."""
    # Mock inspector to return 2 active jobs for the user
    mock_inspector = mock_inspect.return_value
    mock_inspector.active.return_value = {
        'worker1': [{
            'name': 'backend.tasks.execute_crawl_job',
            'kwargs': {'user_id': 'user123'}
        }],
        'worker2': [{
            'name': 'backend.tasks.execute_crawl_job',
            'kwargs': {'user_id': 'user123'}
        }]
    }
    mock_inspector.reserved.return_value = {}
    
    # Should not raise exception (pro tier allows 3 concurrent jobs)
    RateLimiter.check_concurrency("user123", "pro")


# ============================================================================
# CREATE JOB TESTS
# ============================================================================

@pytest.mark.asyncio
@patch('backend.services.crawl_job.RateLimiter.check_concurrency')
async def test_create_job_success(
    mock_rate_limiter,
    crawl_job_service,
    mock_project_repo,
    mock_crawl_job_repo,
    mock_activity_log_repo,
    sample_project,
    sample_crawl_job
):
    """Test successful job creation."""
    # Mock dataset repository to return a dataset (since service checks dataset existence)
    from backend.models.dataset import Dataset
    mock_dataset = Dataset(id=1, name="Test Dataset", user_id=uuid4())
    crawl_job_service.dataset_repo.get_by_id.return_value = mock_dataset
    mock_crawl_job_repo.create.return_value = sample_crawl_job
    
    result = await crawl_job_service.create_job(
        dataset_id=1,
        name="Test Job",
        keywords=["cat", "dog"],
        max_images=100,
        user_id=str(uuid4()),
        tier="free"
    )
    
    assert result.name == "Test Crawl Job"
    mock_rate_limiter.assert_called_once()
    mock_crawl_job_repo.create.assert_called_once()
    mock_activity_log_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_job_project_not_found(
    crawl_job_service,
    mock_project_repo
):
    """Test job creation when project doesn't exist."""
    mock_project_repo.get_by_id.return_value = None
    
    with pytest.raises(NotFoundError) as exc:
        await crawl_job_service.create_job(
            project_id=999,
            name="Test Job",
            keywords=["cat"],
            max_images=100
        )
    
    assert "project not found" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_create_job_empty_keywords(
    crawl_job_service,
    mock_project_repo,
    sample_project
):
    """Test job creation with empty keywords."""
    mock_project_repo.get_by_id.return_value = sample_project
    
    with pytest.raises(ValidationError) as exc:
        await crawl_job_service.create_job(
            project_id=1,
            name="Test Job",
            keywords=[],
            max_images=100
        )
    
    assert "keywords" in str(exc.value).lower()


@pytest.mark.asyncio
@patch('backend.services.crawl_job.RateLimiter.check_concurrency')
async def test_create_job_rate_limit_exceeded(
    mock_rate_limiter,
    crawl_job_service,
    mock_project_repo,
    sample_project
):
    """Test job creation when rate limit is exceeded."""
    mock_project_repo.get_by_id.return_value = sample_project
    mock_rate_limiter.side_effect = RateLimitExceeded("free", 1, 1)
    
    with pytest.raises(RateLimitExceeded):
        await crawl_job_service.create_job(
            project_id=1,
            name="Test Job",
            keywords=["cat"],
            max_images=100,
            user_id=str(uuid4()),
            tier="free"
        )


# ============================================================================
# GET JOB TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_job_success(
    crawl_job_service,
    mock_crawl_job_repo,
    sample_crawl_job
):
    """Test successful job retrieval."""
    mock_crawl_job_repo.get_by_id.return_value = sample_crawl_job
    
    result = await crawl_job_service.get_job(1)
    
    assert result.id == 1
    mock_crawl_job_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_job_not_found(
    crawl_job_service,
    mock_crawl_job_repo
):
    """Test job retrieval when job doesn't exist."""
    mock_crawl_job_repo.get_by_id.return_value = None
    
    result = await crawl_job_service.get_job(999)
    
    assert result is None


# ============================================================================
# UPDATE PROGRESS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_job_progress(
    crawl_job_service,
    mock_crawl_job_repo,
    sample_crawl_job
):
    """Test updating job progress."""
    updated_job = copy_model(sample_crawl_job, progress=50)
    mock_crawl_job_repo.update.return_value = updated_job
    
    with patch('backend.services.crawl_job.get_supabase_client', return_value=None):
        result = await crawl_job_service.update_job_progress(
            job_id=1,
            progress=50,
            downloaded_images=50,
            valid_images=45
        )
    
    assert result.progress == 50
    mock_crawl_job_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_job_progress_bounds(
    crawl_job_service,
    mock_crawl_job_repo,
    sample_crawl_job
):
    """Test progress is clamped to 0-100 range."""
    updated_job = copy_model(sample_crawl_job, progress=100)
    mock_crawl_job_repo.update.return_value = updated_job
    
    # Test upper bound
    with patch('backend.services.crawl_job.get_supabase_client', return_value=None):
        result = await crawl_job_service.update_job_progress(
            job_id=1,
            progress=150,  # Should be clamped to 100
            downloaded_images=100
        )
    
    # Verify the update was called with clamped value
    call_args = mock_crawl_job_repo.update.call_args
    assert call_args[1]['progress'] == 100


# ============================================================================
# UPDATE STATUS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_job_status_success(
    crawl_job_service,
    mock_crawl_job_repo,
    sample_crawl_job
):
    """Test successful status update."""
    updated_job = copy_model(sample_crawl_job, status="completed")
    mock_crawl_job_repo.update.return_value = updated_job
    
    with patch('backend.services.crawl_job.get_supabase_client', return_value=None):
        result = await crawl_job_service.update_job_status(
            job_id=1,
            status="completed"
        )
    
    assert result.status == "completed"
    mock_crawl_job_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_job_status_with_error(
    crawl_job_service,
    mock_crawl_job_repo,
    sample_crawl_job
):
    """Test status update with error message."""
    # Note: CrawlJob model doesn't have an 'error' field, 
    # but the service passes it to the repository update method.
    # The repository is mocked, so we just verify the service behavior.
    updated_job = copy_model(
        sample_crawl_job,
        status="failed"
    )
    mock_crawl_job_repo.update.return_value = updated_job
    
    with patch('backend.services.crawl_job.get_supabase_client', return_value=None):
        result = await crawl_job_service.update_job_status(
            job_id=1,
            status="failed",
            error="Test error"
        )
    
    assert result.status == "failed"
    # Verify error and completed_at were passed to repository
    call_args = mock_crawl_job_repo.update.call_args
    assert call_args[1]['error'] == "Test error"
    assert 'completed_at' in call_args[1]


# ============================================================================
# STORE IMAGE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_store_image_metadata(
    crawl_job_service,
    mock_image_repo
):
    """Test storing image metadata."""
    image_data = {
        "original_url": "https://example.com/image.jpg",
        "filename": "image.jpg",
        "storage_url": "https://storage.example.com/image.jpg",
        "width": 800,
        "height": 600,
        "file_size": 102400,
        "format": "jpeg"
    }
    
    mock_image = Image(id=1, crawl_job_id=1, **image_data)
    mock_image_repo.create.return_value = mock_image
    
    result = await crawl_job_service.store_image_metadata(1, image_data)
    
    assert result.filename == "image.jpg"
    mock_image_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_store_bulk_images(
    crawl_job_service,
    mock_image_repo
):
    """Test storing multiple images in bulk."""
    images_data = [
        {
            "original_url": f"https://example.com/image{i}.jpg",
            "filename": f"image{i}.jpg"
        }
        for i in range(5)
    ]
    
    mock_images = [
        Image(id=i, crawl_job_id=1, **data)
        for i, data in enumerate(images_data, 1)
    ]
    mock_image_repo.bulk_create.return_value = mock_images
    
    result = await crawl_job_service.store_bulk_images(1, images_data)
    
    assert len(result) == 5
    mock_image_repo.bulk_create.assert_called_once()


# ============================================================================
# GET JOBS BY PROJECT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_jobs_by_dataset(
    crawl_job_service,
    mock_crawl_job_repo
):
    """Test retrieving jobs by dataset."""
    mock_jobs = [
        CrawlJob(id=i, dataset_id=1, name=f"Job {i}")
        for i in range(3)
    ]
    mock_crawl_job_repo.get_by_dataset.return_value = mock_jobs
    
    result = await crawl_job_service.get_jobs_by_dataset(1)
    
    assert len(result) == 3
    mock_crawl_job_repo.get_by_dataset.assert_called_once_with(1)


# ============================================================================
# GET ACTIVE JOBS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_active_jobs(
    crawl_job_service,
    mock_crawl_job_repo
):
    """Test retrieving active jobs."""
    mock_jobs = [
        CrawlJob(id=i, dataset_id=1, name=f"Job {i}", status="running")
        for i in range(2)
    ]
    mock_crawl_job_repo.get_active_jobs.return_value = mock_jobs
    
    result = await crawl_job_service.get_active_jobs()
    
    assert len(result) == 2
    assert all(job.status == "running" for job in result)
    mock_crawl_job_repo.get_active_jobs.assert_called_once()


# ============================================================================
# CANCEL JOB TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_cancel_job_success(
    crawl_job_service,
    mock_crawl_job_repo,
    mock_activity_log_repo,
    sample_crawl_job
):
    """Test successful job cancellation."""
    sample_crawl_job.status = "running"
    sample_crawl_job.task_ids = ["task-1", "task-2", "task-3"]
    
    cancelled_job = copy_model(sample_crawl_job, status="cancelled")
    
    mock_crawl_job_repo.get_by_id.return_value = sample_crawl_job
    mock_crawl_job_repo.update.return_value = cancelled_job
    
    with patch('backend.services.crawl_job.get_supabase_client', return_value=None):
        result = await crawl_job_service.cancel_job(1, str(uuid4()))
    
    # Check that result is a dictionary with expected keys
    assert isinstance(result, dict)
    assert result["job_id"] == 1
    assert result["status"] == "cancelled"
    assert result["revoked_tasks"] == 3
    assert "message" in result
    mock_activity_log_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_cancel_job_not_found(
    crawl_job_service,
    mock_crawl_job_repo
):
    """Test cancelling non-existent job."""
    mock_crawl_job_repo.get_by_id.return_value = None
    
    with pytest.raises(NotFoundError) as exc:
        await crawl_job_service.cancel_job(999)
    
    assert "not found" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_cancel_job_invalid_status(
    crawl_job_service,
    mock_crawl_job_repo,
    sample_crawl_job
):
    """Test cancelling job with completed status returns idempotent success."""
    # The cancel_job method uses idempotent design - completed jobs return
    # success without side effects instead of raising ValidationError
    sample_crawl_job.status = "completed"
    mock_crawl_job_repo.get_by_id.return_value = sample_crawl_job
    
    result = await crawl_job_service.cancel_job(1)
    
    # Should return idempotent response, not raise
    assert isinstance(result, dict)
    assert result["job_id"] == 1
    assert result["status"] == "completed"
    assert result["revoked_tasks"] == 0
    assert "idempotent" in result["message"].lower()
