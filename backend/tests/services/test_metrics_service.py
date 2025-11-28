"""
Unit tests for MetricsService.

Tests business logic for metrics collection including processing metrics,
resource metrics, queue metrics, and aggregated summaries.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal

from backend.models import ProcessingMetric, ResourceMetric, QueueMetric
from backend.services.metrics import MetricsService
from backend.schemas.metrics import (
    ProcessingMetricResponse,
    ResourceMetricResponse,
    QueueMetricResponse,
)


def create_processing_metric(**overrides):
    """Helper to create ProcessingMetric with all required fields."""
    defaults = {
        "id": uuid4(),
        "job_id": 1,
        "user_id": uuid4(),
        "operation_type": "download",
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "duration_ms": None,
        "status": "running",
        "images_processed": 0,
        "images_succeeded": 0,
        "images_failed": 0,
        "error_details": None,
        "metadata_": {},
        "created_at": datetime.utcnow(),
    }
    defaults.update(overrides)
    return ProcessingMetric(**defaults)


def create_resource_metric(**overrides):
    """Helper to create ResourceMetric with all required fields."""
    defaults = {
        "id": uuid4(),
        "job_id": None,
        "metric_type": "cpu",
        "timestamp": datetime.utcnow(),
        "value": Decimal("50.0"),
        "unit": "percent",
        "hostname": "worker-1",
        "metadata_": {},
        "created_at": datetime.utcnow(),
    }
    defaults.update(overrides)
    return ResourceMetric(**defaults)


def create_queue_metric(**overrides):
    """Helper to create QueueMetric with all required fields."""
    defaults = {
        "id": uuid4(),
        "queue_name": "default",
        "timestamp": datetime.utcnow(),
        "pending_tasks": 0,
        "active_tasks": 0,
        "reserved_tasks": 0,
        "failed_tasks": 0,
        "worker_count": 1,
        "avg_wait_time_ms": None,
        "metadata_": {},
        "created_at": datetime.utcnow(),
    }
    defaults.update(overrides)
    return QueueMetric(**defaults)


@pytest.fixture
def mock_processing_repo():
    """Create mock processing metric repository."""
    return AsyncMock()


@pytest.fixture
def mock_resource_repo():
    """Create mock resource metric repository."""
    return AsyncMock()


@pytest.fixture
def mock_queue_repo():
    """Create mock queue metric repository."""
    return AsyncMock()


@pytest.fixture
def metrics_service(mock_processing_repo, mock_resource_repo, mock_queue_repo):
    """Create metrics service with mocked repositories."""
    return MetricsService(
        mock_processing_repo,
        mock_resource_repo,
        mock_queue_repo
    )


# ============================================================================
# PROCESSING METRICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_start_processing_metric(metrics_service, mock_processing_repo):
    """Test starting a processing metric."""
    metric_id = uuid4()
    job_id = 1
    user_id = uuid4()
    
    mock_metric = create_processing_metric(
        id=metric_id,
        job_id=job_id,
        user_id=user_id,
        operation_type="download"
    )
    mock_processing_repo.create.return_value = mock_metric
    
    result = await metrics_service.start_processing_metric(
        operation_type="download",
        job_id=job_id,
        user_id=user_id
    )
    
    assert isinstance(result, ProcessingMetricResponse)
    assert result.operation_type == "download"
    mock_processing_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_complete_processing_metric_success(
    metrics_service,
    mock_processing_repo
):
    """Test completing a processing metric successfully."""
    metric_id = uuid4()
    started_at = datetime.utcnow() - timedelta(seconds=10)
    
    mock_metric = create_processing_metric(
        id=metric_id,
        started_at=started_at,
        status="running"
    )
    
    updated_metric = create_processing_metric(
        id=metric_id,
        started_at=started_at,
        completed_at=datetime.utcnow(),
        duration_ms=10000,
        status="success",
        images_processed=100,
        images_succeeded=95,
        images_failed=5
    )
    
    mock_processing_repo.get_by_id.return_value = mock_metric
    mock_processing_repo.update.return_value = updated_metric
    
    result = await metrics_service.complete_processing_metric(
        metric_id=metric_id,
        status="success",
        images_processed=100,
        images_succeeded=95,
        images_failed=5
    )
    
    assert result.status == "success"
    assert result.images_processed == 100
    mock_processing_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_complete_processing_metric_not_found(
    metrics_service,
    mock_processing_repo
):
    """Test completing a non-existent metric raises error."""
    metric_id = uuid4()
    mock_processing_repo.get_by_id.return_value = None
    
    with pytest.raises(ValueError) as exc:
        await metrics_service.complete_processing_metric(
            metric_id=metric_id,
            status="success"
        )
    
    assert "not found" in str(exc.value)


@pytest.mark.asyncio
async def test_get_processing_metrics_by_job(
    metrics_service,
    mock_processing_repo
):
    """Test retrieving processing metrics by job ID."""
    job_id = 1
    mock_metrics = [
        create_processing_metric(job_id=job_id, operation_type="download")
    ]
    mock_processing_repo.get_by_job_id.return_value = mock_metrics
    
    result = await metrics_service.get_processing_metrics(job_id=job_id)
    
    assert len(result) == 1
    mock_processing_repo.get_by_job_id.assert_called_once()


@pytest.mark.asyncio
async def test_get_processing_metrics_by_time_range(
    metrics_service,
    mock_processing_repo
):
    """Test retrieving processing metrics by time range."""
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow()
    
    mock_metrics = [
        create_processing_metric(operation_type="validate")
    ]
    mock_processing_repo.get_by_time_range.return_value = mock_metrics
    
    result = await metrics_service.get_processing_metrics(
        start_time=start_time,
        end_time=end_time
    )
    
    assert len(result) == 1
    mock_processing_repo.get_by_time_range.assert_called_once()


# ============================================================================
# RESOURCE METRICS TESTS
# ============================================================================

@pytest.mark.asyncio
@patch('psutil.cpu_percent')
@patch('psutil.virtual_memory')
@patch('psutil.disk_usage')
@patch('psutil.net_io_counters')
async def test_collect_resource_metrics(
    mock_net_io,
    mock_disk,
    mock_memory,
    mock_cpu,
    metrics_service,
    mock_resource_repo
):
    """Test collecting system resource metrics."""
    # Mock psutil responses
    mock_cpu.return_value = 45.5
    
    mock_memory_obj = type('obj', (object,), {
        'used': 4 * 1024 * 1024 * 1024,  # 4GB
        'total': 16 * 1024 * 1024 * 1024,  # 16GB
        'percent': 25.0
    })()
    mock_memory.return_value = mock_memory_obj
    
    mock_disk_obj = type('obj', (object,), {
        'used': 100 * 1024 * 1024 * 1024,  # 100GB
        'total': 500 * 1024 * 1024 * 1024,  # 500GB
        'percent': 20.0
    })()
    mock_disk.return_value = mock_disk_obj
    
    mock_net_obj = type('obj', (object,), {
        'bytes_sent': 1024 * 1024 * 1024,  # 1GB
        'bytes_recv': 2 * 1024 * 1024 * 1024,  # 2GB
        'packets_sent': 1000,
        'packets_recv': 2000
    })()
    mock_net_io.return_value = mock_net_obj
    
    # Mock repository responses
    mock_resource_repo.create.side_effect = [
        create_resource_metric(metric_type="cpu", value=Decimal("45.5"), unit="percent"),
        create_resource_metric(metric_type="memory", value=Decimal("4096"), unit="mb"),
        create_resource_metric(metric_type="disk", value=Decimal("100"), unit="gb"),
        create_resource_metric(metric_type="network", value=Decimal("3072"), unit="mbps"),
    ]
    
    result = await metrics_service.collect_resource_metrics()
    
    assert len(result) == 4
    assert result[0].metric_type == "cpu"
    assert result[1].metric_type == "memory"
    assert result[2].metric_type == "disk"
    assert result[3].metric_type == "network"
    assert mock_resource_repo.create.call_count == 4


@pytest.mark.asyncio
async def test_get_resource_metrics_by_job(
    metrics_service,
    mock_resource_repo
):
    """Test retrieving resource metrics by job ID."""
    job_id = 1
    mock_metrics = [
        create_resource_metric(job_id=job_id, metric_type="cpu", value=Decimal("50.0"))
    ]
    mock_resource_repo.get_by_job_id.return_value = mock_metrics
    
    result = await metrics_service.get_resource_metrics(job_id=job_id)
    
    assert len(result) == 1
    mock_resource_repo.get_by_job_id.assert_called_once()


# ============================================================================
# QUEUE METRICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_collect_queue_metrics(metrics_service, mock_queue_repo):
    """Test collecting queue metrics."""
    mock_metric = create_queue_metric(
        queue_name="default",
        pending_tasks=10,
        active_tasks=5,
        reserved_tasks=2,
        failed_tasks=1,
        worker_count=3
    )
    mock_queue_repo.create.return_value = mock_metric
    
    result = await metrics_service.collect_queue_metrics(
        queue_name="default",
        pending_tasks=10,
        active_tasks=5,
        reserved_tasks=2,
        failed_tasks=1,
        worker_count=3
    )
    
    assert isinstance(result, QueueMetricResponse)
    assert result.queue_name == "default"
    assert result.pending_tasks == 10
    mock_queue_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_queue_metrics_by_name(metrics_service, mock_queue_repo):
    """Test retrieving queue metrics by queue name."""
    queue_name = "default"
    mock_metrics = [
        create_queue_metric(
            queue_name=queue_name,
            pending_tasks=5,
            active_tasks=2
        )
    ]
    mock_queue_repo.get_by_queue_name.return_value = mock_metrics
    
    result = await metrics_service.get_queue_metrics(queue_name=queue_name)
    
    assert len(result) == 1
    mock_queue_repo.get_by_queue_name.assert_called_once()


@pytest.mark.asyncio
async def test_get_latest_queue_status(metrics_service, mock_queue_repo):
    """Test retrieving latest queue status."""
    queue_name = "default"
    mock_metric = create_queue_metric(
        queue_name=queue_name,
        pending_tasks=3,
        active_tasks=1
    )
    mock_queue_repo.get_latest_by_queue.return_value = mock_metric
    
    result = await metrics_service.get_latest_queue_status(queue_name)
    
    assert result is not None
    assert result.queue_name == queue_name
    mock_queue_repo.get_latest_by_queue.assert_called_once()


@pytest.mark.asyncio
async def test_get_latest_queue_status_not_found(
    metrics_service,
    mock_queue_repo
):
    """Test retrieving latest queue status when none exists."""
    mock_queue_repo.get_latest_by_queue.return_value = None
    
    result = await metrics_service.get_latest_queue_status("nonexistent")
    
    assert result is None


# ============================================================================
# AGGREGATED METRICS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_metrics_summary(
    metrics_service,
    mock_processing_repo,
    mock_resource_repo,
    mock_queue_repo
):
    """Test retrieving comprehensive metrics summary."""
    start_time = datetime.utcnow() - timedelta(hours=24)
    end_time = datetime.utcnow()
    
    # Mock processing stats - must include all required PerformanceStats fields
    mock_processing_repo.get_aggregated_stats.return_value = {
        'total_operations': 100,
        'successful_operations': 95,
        'failed_operations': 5,
        'avg_duration_ms': 5000.0,
        'min_duration_ms': 1000,
        'max_duration_ms': 10000,
        'total_images_processed': 10000,
        'total_images_succeeded': 9500,
        'total_images_failed': 500
    }
    
    # Mock resource averages
    mock_resource_repo.get_average_by_type.side_effect = [
        Decimal("45.5"),  # CPU
        Decimal("4096"),  # Memory
        Decimal("100"),   # Disk
        Decimal("50")     # Network
    ]
    
    # Mock queue average
    mock_queue_repo.get_average_queue_depth.return_value = Decimal("15.5")
    
    result = await metrics_service.get_metrics_summary(start_time, end_time)
    
    assert result.total_jobs == 100
    assert result.successful_jobs == 95
    assert result.failed_jobs == 5
    assert result.avg_cpu_percent == Decimal("45.5")
    assert len(result.processing_stats) > 0
