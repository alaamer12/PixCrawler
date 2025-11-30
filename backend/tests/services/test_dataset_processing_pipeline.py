"""
Tests for DatasetProcessingPipeline service.

Comprehensive test suite covering pipeline creation, execution,
step handlers, and metrics tracking.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from backend.services.dataset_processing_pipeline import (
    DatasetProcessingPipeline,
    PipelineConfig,
    PipelineMetrics,
)
from backend.services.job_orchestrator import JobOrchestrator
from backend.services.crawl_job import CrawlJobService
from backend.services.storage import StorageService
from backend.services.metrics import MetricsService
from backend.models import WorkflowState


@pytest.fixture
def mock_orchestrator():
    """Mock JobOrchestrator."""
    return AsyncMock(spec=JobOrchestrator)


@pytest.fixture
def mock_crawl_job_service():
    """Mock CrawlJobService."""
    return AsyncMock(spec=CrawlJobService)


@pytest.fixture
def mock_storage_service():
    """Mock StorageService."""
    return AsyncMock(spec=StorageService)


@pytest.fixture
def mock_metrics_service():
    """Mock MetricsService."""
    return AsyncMock(spec=MetricsService)


@pytest.fixture
def pipeline_config():
    """Create pipeline configuration."""
    return PipelineConfig(
        enable_validation=True,
        enable_deduplication=True,
        enable_labeling=False,
        enable_storage_tiering=True,
        enable_quality_report=True,
        hot_storage_threshold=1000,
    )


@pytest.fixture
def pipeline(mock_orchestrator, mock_crawl_job_service, mock_storage_service, mock_metrics_service, pipeline_config):
    """Create DatasetProcessingPipeline instance."""
    return DatasetProcessingPipeline(
        orchestrator=mock_orchestrator,
        crawl_job_service=mock_crawl_job_service,
        storage_service=mock_storage_service,
        metrics_service=mock_metrics_service,
        config=pipeline_config,
    )


class TestPipelineConfig:
    """Tests for PipelineConfig."""

    def test_config_creation_with_defaults(self):
        """Test config creation with default values."""
        config = PipelineConfig()
        assert config.enable_validation is True
        assert config.enable_deduplication is True
        assert config.enable_labeling is False
        assert config.enable_storage_tiering is True
        assert config.hot_storage_threshold == 1000

    def test_config_creation_with_custom_values(self):
        """Test config creation with custom values."""
        config = PipelineConfig(
            enable_validation=False,
            enable_labeling=True,
            hot_storage_threshold=500,
        )
        assert config.enable_validation is False
        assert config.enable_labeling is True
        assert config.hot_storage_threshold == 500


class TestPipelineMetrics:
    """Tests for PipelineMetrics."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = PipelineMetrics()
        assert metrics.start_time is None
        assert metrics.end_time is None
        assert metrics.total_duration == 0.0
        assert metrics.images_crawled == 0
        assert metrics.quality_score == 0.0

    def test_metrics_to_dict(self):
        """Test metrics conversion to dictionary."""
        metrics = PipelineMetrics()
        metrics.images_crawled = 100
        metrics.valid_images = 90
        metrics.quality_score = 90.0

        metrics_dict = metrics.to_dict()
        assert metrics_dict["images_crawled"] == 100
        assert metrics_dict["valid_images"] == 90
        assert metrics_dict["quality_score"] == 90.0


class TestDatasetProcessingPipeline:
    """Tests for DatasetProcessingPipeline."""

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline.orchestrator is not None
        assert pipeline.crawl_job_service is not None
        assert pipeline.storage_service is not None
        assert pipeline.metrics_service is not None
        assert pipeline.config is not None
        assert pipeline.metrics is not None

    @pytest.mark.asyncio
    async def test_create_pipeline_workflow(self, pipeline, mock_orchestrator):
        """Test creating pipeline workflow."""
        workflow = MagicMock(spec=WorkflowState)
        workflow.id = 1
        mock_orchestrator.create_workflow.return_value = workflow

        result = await pipeline.create_pipeline_workflow(
            job_id=1,
            dataset_name="Test Dataset",
        )

        assert result.id == 1
        mock_orchestrator.create_workflow.assert_called_once()

    def test_define_workflow_steps_all_enabled(self, pipeline):
        """Test workflow step definition with all steps enabled."""
        steps = pipeline._define_workflow_steps()
        
        # Should have: setup, crawl, validate, deduplicate, label, storage, report, cleanup
        assert len(steps) >= 8
        assert steps[0].name == "Setup Workspace"
        assert steps[1].name == "Crawl Images"

    def test_define_workflow_steps_minimal(self):
        """Test workflow step definition with minimal config."""
        config = PipelineConfig(
            enable_validation=False,
            enable_deduplication=False,
            enable_labeling=False,
            enable_storage_tiering=False,
            enable_quality_report=False,
        )
        pipeline = DatasetProcessingPipeline(
            orchestrator=AsyncMock(spec=JobOrchestrator),
            crawl_job_service=AsyncMock(spec=CrawlJobService),
            storage_service=AsyncMock(spec=StorageService),
            metrics_service=AsyncMock(spec=MetricsService),
            config=config,
        )
        
        steps = pipeline._define_workflow_steps()
        
        # Should have: setup, crawl, cleanup
        assert len(steps) == 3
        assert steps[0].name == "Setup Workspace"
        assert steps[1].name == "Crawl Images"
        assert steps[2].name == "Cleanup"

    @pytest.mark.asyncio
    async def test_execute_pipeline(self, pipeline, mock_orchestrator):
        """Test pipeline execution."""
        workflow = MagicMock(spec=WorkflowState)
        workflow.id = 1
        mock_orchestrator.execute_workflow.return_value = workflow

        result_workflow, metrics = await pipeline.execute_pipeline(workflow_id=1)

        assert result_workflow.id == 1
        assert metrics is not None
        assert metrics.start_time is not None
        assert metrics.end_time is not None

    @pytest.mark.asyncio
    async def test_setup_workspace(self, pipeline):
        """Test workspace setup."""
        result = await pipeline._setup_workspace()
        
        assert result["status"] == "success"
        assert "workspace_path" in result
        assert pipeline.temp_workspace is not None
        
        # Check required folder structure
        assert (pipeline.temp_workspace / "crawled").exists()
        assert (pipeline.temp_workspace / "validated").exists()
        assert (pipeline.temp_workspace / "deduplicated").exists()
        assert (pipeline.temp_workspace / "labeled").exists()

    @pytest.mark.asyncio
    async def test_run_crawling(self, pipeline):
        """Test crawling step."""
        result = await pipeline._run_crawling()
        
        assert result["status"] == "success"
        assert "images_crawled" in result
        assert "duration" in result

    @pytest.mark.asyncio
    async def test_perform_validation_no_workspace(self, pipeline):
        """Test validation fails without workspace."""
        with pytest.raises(Exception):
            await pipeline._perform_validation()

    @pytest.mark.asyncio
    async def test_generate_quality_report(self, pipeline):
        """Test quality report generation."""
        pipeline.metrics.images_crawled = 100
        pipeline.metrics.unique_images = 90
        
        result = await pipeline._generate_quality_report()
        
        assert result["status"] == "success"
        assert result["quality_score"] == 90.0
        assert pipeline.metrics.report_generated is True

    @pytest.mark.asyncio
    async def test_cleanup_workspace(self, pipeline):
        """Test workspace cleanup."""
        # Create a temporary workspace
        await pipeline._setup_workspace()
        assert pipeline.temp_workspace is not None
        
        result = await pipeline._cleanup_workspace()
        
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_get_pipeline_progress(self, pipeline, mock_orchestrator):
        """Test getting pipeline progress."""
        progress_data = {
            "workflow_id": 1,
            "status": "running",
            "progress": 50,
        }
        mock_orchestrator.get_workflow_progress.return_value = progress_data
        
        result = await pipeline.get_pipeline_progress(workflow_id=1)
        
        assert result["workflow_id"] == 1
        assert result["status"] == "running"
        assert "metrics" in result

    @pytest.mark.asyncio
    async def test_get_pipeline_metrics(self, pipeline):
        """Test getting pipeline metrics."""
        result = await pipeline.get_pipeline_metrics()
        
        assert result is not None
        assert isinstance(result, PipelineMetrics)

    def test_workflow_step_dependencies(self, pipeline):
        """Test workflow step dependencies are correctly set."""
        steps = pipeline._define_workflow_steps()
        
        # Setup should have no dependencies
        assert steps[0].dependencies == []
        
        # Crawl should depend on setup
        assert 0 in steps[1].dependencies
        
        # Cleanup should depend on previous step
        assert steps[-1].dependencies == [len(steps) - 2]

    def test_workflow_step_handlers(self, pipeline):
        """Test all workflow steps have handlers."""
        steps = pipeline._define_workflow_steps()
        
        for step in steps:
            assert step.handler is not None
            assert callable(step.handler)

    def test_pipeline_config_integration(self, pipeline):
        """Test pipeline respects configuration."""
        assert pipeline.config.enable_validation is True
        assert pipeline.config.enable_deduplication is True
        assert pipeline.config.enable_labeling is False
        assert pipeline.config.enable_storage_tiering is True
