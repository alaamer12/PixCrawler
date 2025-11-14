"""
Tests for metrics collection and endpoints.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from backend.schemas.metrics import (
    MetricType,
    SystemMetricCreate,
    SystemMetricQuery,
    TimeWindow,
)
from backend.services.metrics import MetricsService
from backend.utils.metrics_collector import MetricsCollector, track_processing_time


@pytest.mark.asyncio
async def test_create_metric(session):
    """Test creating a single metric."""
    service = MetricsService(session)
    
    metric_data = SystemMetricCreate(
        metric_type=MetricType.PROCESSING_TIME,
        name="download_time",
        value=1.5,
        unit="seconds",
        service="test",
        description="Test download time",
    )
    
    result = await service.create_metric(metric_data)
    
    assert result.name == "download_time"
    assert result.value == 1.5
    assert result.metric_type == MetricType.PROCESSING_TIME
    assert result.id is not None


@pytest.mark.asyncio
async def test_track_processing_time(session):
    """Test tracking processing time with context manager."""
    import asyncio
    
    async with track_processing_time(session, "test_operation", metadata={"test": True}):
        await asyncio.sleep(0.1)  # Simulate some work
    
    # Verify metric was created
    service = MetricsService(session)
    query = SystemMetricQuery(
        name="test_operation_time",
        metric_type=MetricType.PROCESSING_TIME,
    )
    metrics = await service.get_metrics(query)
    
    assert len(metrics) > 0
    assert metrics[0].name == "test_operation_time"
    assert metrics[0].value > 0


@pytest.mark.asyncio
async def test_record_success_rate(session):
    """Test recording success rate."""
    collector = MetricsCollector(session, service_name="test")
    
    await collector.record_success_rate(
        "download",
        success_count=80,
        total_count=100,
        metadata={"job_id": 123},
    )
    await collector.flush()
    
    # Verify metric was created
    service = MetricsService(session)
    query = SystemMetricQuery(
        name="download_success",
        metric_type=MetricType.SUCCESS_RATE,
    )
    metrics = await service.get_metrics(query)
    
    assert len(metrics) > 0
    assert metrics[0].value == 80.0  # 80% success rate
    assert metrics[0].metadata["success_count"] == 80
    assert metrics[0].metadata["total_count"] == 100


@pytest.mark.asyncio
async def test_record_queue_depth(session):
    """Test recording queue depth."""
    collector = MetricsCollector(session, service_name="test")
    
    await collector.record_queue_depth(
        queue_name="celery",
        depth=5,
        wait_time_seconds=2.5,
        metadata={"queue_type": "task"},
    )
    await collector.flush()
    
    # Verify metrics were created
    service = MetricsService(session)
    query = SystemMetricQuery(
        metric_type=MetricType.QUEUE_METRICS,
    )
    metrics = await service.get_metrics(query)
    
    assert len(metrics) >= 2  # Both depth and wait time
    depth_metric = next((m for m in metrics if m.name == "queue_depth"), None)
    wait_metric = next((m for m in metrics if m.name == "queue_wait_time"), None)
    
    assert depth_metric is not None
    assert depth_metric.value == 5.0
    assert wait_metric is not None
    assert wait_metric.value == 2.5


@pytest.mark.asyncio
async def test_query_metrics(session):
    """Test querying metrics with filters."""
    service = MetricsService(session)
    
    # Create test metrics
    metrics_data = [
        SystemMetricCreate(
            metric_type=MetricType.PROCESSING_TIME,
            name="download_time",
            value=1.0,
            service="test",
        ),
        SystemMetricCreate(
            metric_type=MetricType.PROCESSING_TIME,
            name="validate_time",
            value=2.0,
            service="test",
        ),
        SystemMetricCreate(
            metric_type=MetricType.SUCCESS_RATE,
            name="download_success",
            value=95.0,
            service="test",
        ),
    ]
    
    await service.create_metrics_batch(metrics_data)
    
    # Query by type
    query = SystemMetricQuery(metric_type=MetricType.PROCESSING_TIME)
    results = await service.get_metrics(query)
    assert len(results) == 2
    
    # Query by name
    query = SystemMetricQuery(name="download_time")
    results = await service.get_metrics(query)
    assert len(results) == 1
    assert results[0].name == "download_time"
    
    # Query by service
    query = SystemMetricQuery(service="test")
    results = await service.get_metrics(query)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_collect_system_metrics(session):
    """Test collecting system metrics."""
    service = MetricsService(session)
    
    metrics = await service.collect_system_metrics(service_name="test")
    
    assert len(metrics) > 0
    
    # Check that we have CPU, memory, and disk metrics
    metric_names = [m.name for m in metrics]
    assert "cpu_usage" in metric_names
    assert "memory_usage" in metric_names
    assert "disk_usage" in metric_names


@pytest.mark.asyncio
async def test_get_system_status(session):
    """Test getting system status."""
    service = MetricsService(session)
    
    status = await service.get_system_status()
    
    assert status.status == "operational"
    assert "cpu" in status.model_dump()
    assert "memory" in status.model_dump()
    assert "disk" in status.model_dump()
    assert "process" in status.model_dump()

