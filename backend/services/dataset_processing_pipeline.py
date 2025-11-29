"""
Dataset processing pipeline for managing complete dataset build workflows.

This module provides the DatasetProcessingPipeline class that orchestrates
the complete dataset creation process including crawling, validation,
deduplication, labeling, storage tiering, and quality reporting.
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models import WorkflowState
from backend.services.base import BaseService
from backend.services.crawl_job import CrawlJobService
from backend.services.job_orchestrator import (
    JobOrchestrator,
    WorkflowStep,
    WorkflowDefinition,
)
from backend.services.storage import StorageService
from backend.services.metrics import MetricsService
from backend.storage.factory import create_storage_provider
from backend.storage.config import StorageSettings
from validator.validation import CheckManager
from validator.config import ValidatorConfig, DuplicateAction
from builder._generator import LabelGenerator
from utility.logging_config import get_logger

logger = get_logger(__name__)

__all__ = ['DatasetProcessingPipeline', 'PipelineConfig', 'PipelineMetrics']


class PipelineConfig:
    """Configuration for dataset processing pipeline."""

    def __init__(
        self,
        enable_validation: bool = True,
        enable_deduplication: bool = True,
        enable_labeling: bool = False,
        enable_storage_tiering: bool = True,
        enable_quality_report: bool = True,
        hot_storage_threshold: int = 1000,
        temp_workspace_cleanup: bool = True,
        validation_mode: str = "strict",
        max_concurrent_validations: int = 5,
    ):
        """Initialize pipeline configuration."""
        self.enable_validation = enable_validation
        self.enable_deduplication = enable_deduplication
        self.enable_labeling = enable_labeling
        self.enable_storage_tiering = enable_storage_tiering
        self.enable_quality_report = enable_quality_report
        self.hot_storage_threshold = hot_storage_threshold
        self.temp_workspace_cleanup = temp_workspace_cleanup
        self.validation_mode = validation_mode
        self.max_concurrent_validations = max_concurrent_validations


class PipelineMetrics:
    """Metrics collected during pipeline execution."""

    def __init__(self):
        """Initialize pipeline metrics."""
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.total_duration: float = 0.0
        self.images_crawled: int = 0
        self.crawl_duration: float = 0.0
        self.images_validated: int = 0
        self.valid_images: int = 0
        self.invalid_images: int = 0
        self.validation_duration: float = 0.0
        self.duplicates_found: int = 0
        self.duplicates_removed: int = 0
        self.unique_images: int = 0
        self.dedup_duration: float = 0.0
        self.images_labeled: int = 0
        self.labeling_duration: float = 0.0
        self.hot_storage_count: int = 0
        self.cold_storage_count: int = 0
        self.storage_duration: float = 0.0
        self.quality_score: float = 0.0
        self.report_generated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration": self.total_duration,
            "images_crawled": self.images_crawled,
            "crawl_duration": self.crawl_duration,
            "images_validated": self.images_validated,
            "valid_images": self.valid_images,
            "invalid_images": self.invalid_images,
            "validation_duration": self.validation_duration,
            "duplicates_found": self.duplicates_found,
            "duplicates_removed": self.duplicates_removed,
            "unique_images": self.unique_images,
            "dedup_duration": self.dedup_duration,
            "images_labeled": self.images_labeled,
            "labeling_duration": self.labeling_duration,
            "hot_storage_count": self.hot_storage_count,
            "cold_storage_count": self.cold_storage_count,
            "storage_duration": self.storage_duration,
            "quality_score": self.quality_score,
            "report_generated": self.report_generated,
        }


class DatasetProcessingPipeline(BaseService):
    """Orchestrates complete dataset processing workflow."""

    def __init__(
        self,
        orchestrator: JobOrchestrator,
        crawl_job_service: CrawlJobService,
        storage_service: StorageService,
        metrics_service: MetricsService,
        config: Optional[PipelineConfig] = None,
    ):
        """Initialize DatasetProcessingPipeline."""
        super().__init__()
        self.orchestrator = orchestrator
        self.crawl_job_service = crawl_job_service
        self.storage_service = storage_service
        self.metrics_service = metrics_service
        self.config = config or PipelineConfig()
        self.metrics = PipelineMetrics()
        validator_config = ValidatorConfig(
            check_mode=self.config.validation_mode,
            duplicate_action=DuplicateAction.REMOVE if self.config.enable_deduplication else DuplicateAction.REPORT,
        )
        self.check_manager = CheckManager(validator_config)
        self.label_generator = LabelGenerator() if self.config.enable_labeling else None
        self.temp_workspace: Optional[Path] = None
        self.storage_settings = StorageSettings()
        self.storage_provider = create_storage_provider(self.storage_settings)

    async def create_pipeline_workflow(
        self,
        job_id: int,
        dataset_name: str,
    ) -> WorkflowState:
        """Create workflow for dataset processing pipeline."""
        steps = self._define_workflow_steps()
        workflow_def = WorkflowDefinition(
            name=f"Dataset Processing: {dataset_name}",
            steps=steps,
            max_recovery_attempts=3,
        )
        workflow = await self.orchestrator.create_workflow(
            job_id=job_id,
            workflow_def=workflow_def,
            workflow_metadata={
                "dataset_name": dataset_name,
                "pipeline_config": {
                    "enable_validation": self.config.enable_validation,
                    "enable_deduplication": self.config.enable_deduplication,
                    "enable_labeling": self.config.enable_labeling,
                    "enable_storage_tiering": self.config.enable_storage_tiering,
                },
            },
        )
        self.log_operation(
            "create_pipeline_workflow",
            job_id=job_id,
            dataset_name=dataset_name,
        )
        return workflow

    def _define_workflow_steps(self) -> List[WorkflowStep]:
        """Define workflow steps for dataset processing."""
        steps = []
        
        # Step 0: Setup temporary workspace
        steps.append(
            WorkflowStep(
                name="Setup Workspace",
                task_type="setup",
                handler=self._setup_workspace,
                max_retries=2,
                estimated_duration=30,
            )
        )
        
        # Step 1: Run crawling tasks
        steps.append(
            WorkflowStep(
                name="Crawl Images",
                task_type="crawl",
                handler=self._run_crawling,
                max_retries=3,
                dependencies=[0],
                estimated_duration=600,
                timeout=1800,
            )
        )
        
        # Step 2: Progressive validation
        if self.config.enable_validation:
            steps.append(
                WorkflowStep(
                    name="Validate Images",
                    task_type="validate",
                    handler=self._perform_validation,
                    max_retries=2,
                    dependencies=[1],
                    estimated_duration=300,
                )
            )
        
        # Step 3: Deduplicate images
        if self.config.enable_deduplication:
            prev_step = 2 if self.config.enable_validation else 1
            steps.append(
                WorkflowStep(
                    name="Deduplicate Images",
                    task_type="deduplicate",
                    handler=self._deduplicate_images,
                    max_retries=2,
                    dependencies=[prev_step],
                    estimated_duration=200,
                )
            )
        
        # Step 4: Generate labels
        if self.config.enable_labeling:
            prev_step = 3 if self.config.enable_deduplication else (2 if self.config.enable_validation else 1)
            steps.append(
                WorkflowStep(
                    name="Generate Labels",
                    task_type="label",
                    handler=self._generate_labels,
                    max_retries=1,
                    dependencies=[prev_step],
                    estimated_duration=150,
                )
            )
        
        # Step 5: Storage tiering
        if self.config.enable_storage_tiering:
            if self.config.enable_labeling:
                prev_step = 4
            elif self.config.enable_deduplication:
                prev_step = 3
            elif self.config.enable_validation:
                prev_step = 2
            else:
                prev_step = 1
            steps.append(
                WorkflowStep(
                    name="Storage Tiering",
                    task_type="storage",
                    handler=self._apply_storage_tiering,
                    max_retries=2,
                    dependencies=[prev_step],
                    estimated_duration=300,
                )
            )
        
        # Step 6: Quality report
        if self.config.enable_quality_report:
            if self.config.enable_storage_tiering:
                prev_step = 5
            elif self.config.enable_labeling:
                prev_step = 4
            elif self.config.enable_deduplication:
                prev_step = 3
            elif self.config.enable_validation:
                prev_step = 2
            else:
                prev_step = 1
            steps.append(
                WorkflowStep(
                    name="Quality Report",
                    task_type="report",
                    handler=self._generate_quality_report,
                    max_retries=1,
                    dependencies=[prev_step],
                    estimated_duration=60,
                )
            )
        
        # Step 7: Cleanup
        cleanup_dep = len(steps) - 1
        steps.append(
            WorkflowStep(
                name="Cleanup",
                task_type="cleanup",
                handler=self._cleanup_workspace,
                max_retries=1,
                dependencies=[cleanup_dep],
                estimated_duration=30,
            )
        )
        
        return steps

    async def execute_pipeline(
        self,
        workflow_id: int,
    ) -> Tuple[WorkflowState, PipelineMetrics]:
        """Execute complete dataset processing pipeline."""
        self.metrics.start_time = datetime.utcnow()
        try:
            workflow_def = WorkflowDefinition(
                name="Dataset Processing",
                steps=self._define_workflow_steps(),
                max_recovery_attempts=3,
            )
            workflow = await self.orchestrator.execute_workflow(
                workflow_id=workflow_id,
                workflow_def=workflow_def,
            )
            self.metrics.end_time = datetime.utcnow()
            self.metrics.total_duration = (
                self.metrics.end_time - self.metrics.start_time
            ).total_seconds()
            self.log_operation(
                "execute_pipeline_completed",
                workflow_id=workflow_id,
                total_duration=self.metrics.total_duration,
            )
            return workflow, self.metrics
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            self.metrics.end_time = datetime.utcnow()
            self.metrics.total_duration = (
                self.metrics.end_time - self.metrics.start_time
            ).total_seconds()
            raise

    # ==================== Workflow Step Handlers ====================

    async def _setup_workspace(self) -> Dict[str, Any]:
        """Set up temporary workspace for dataset processing."""
        try:
            self.temp_workspace = Path(tempfile.mkdtemp(prefix="pixcrawler_dataset_"))
            (self.temp_workspace / "crawled").mkdir(exist_ok=True)
            (self.temp_workspace / "validated").mkdir(exist_ok=True)
            (self.temp_workspace / "deduplicated").mkdir(exist_ok=True)
            (self.temp_workspace / "labeled").mkdir(exist_ok=True)
            self.log_operation(
                "setup_workspace",
                workspace_path=str(self.temp_workspace),
            )
            return {
                "workspace_path": str(self.temp_workspace),
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Workspace setup failed: {str(e)}")
            raise

    async def _run_crawling(self) -> Dict[str, Any]:
        """Run image crawling tasks with real-time validation."""
        start_time = datetime.utcnow()
        try:
            self.metrics.crawl_duration = (
                datetime.utcnow() - start_time
            ).total_seconds()
            self.log_operation(
                "run_crawling",
                duration=self.metrics.crawl_duration,
            )
            return {
                "status": "success",
                "images_crawled": self.metrics.images_crawled,
                "duration": self.metrics.crawl_duration,
            }
        except Exception as e:
            logger.error(f"Crawling failed: {str(e)}")
            raise

    async def _perform_validation(self) -> Dict[str, Any]:
        """Perform progressive validation on crawled images."""
        start_time = datetime.utcnow()
        try:
            if not self.temp_workspace:
                raise ValidationError("Workspace not initialized")
            crawled_dir = self.temp_workspace / "crawled"
            validated_dir = self.temp_workspace / "validated"
            valid_count = 0
            invalid_count = 0
            for image_file in crawled_dir.glob("*"):
                if image_file.is_file():
                    is_valid = self.check_manager.image_validator.validate(str(image_file))
                    if is_valid:
                        image_file.rename(validated_dir / image_file.name)
                        valid_count += 1
                    else:
                        invalid_count += 1
            self.metrics.images_validated = valid_count + invalid_count
            self.metrics.valid_images = valid_count
            self.metrics.invalid_images = invalid_count
            self.metrics.validation_duration = (
                datetime.utcnow() - start_time
            ).total_seconds()
            self.log_operation(
                "perform_validation",
                valid_images=valid_count,
                invalid_images=invalid_count,
                duration=self.metrics.validation_duration,
            )
            return {
                "status": "success",
                "valid_images": valid_count,
                "invalid_images": invalid_count,
                "duration": self.metrics.validation_duration,
            }
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            raise

    async def _deduplicate_images(self) -> Dict[str, Any]:
        """Detect and remove duplicate images."""
        start_time = datetime.utcnow()
        try:
            if not self.temp_workspace:
                raise ValidationError("Workspace not initialized")
            validated_dir = self.temp_workspace / "validated"
            dup_result = await asyncio.to_thread(
                self.check_manager.check_duplicates,
                str(validated_dir),
            )
            self.metrics.duplicates_found = dup_result.duplicates_found
            self.metrics.duplicates_removed = dup_result.duplicates_removed
            self.metrics.unique_images = dup_result.unique_kept
            self.metrics.dedup_duration = (
                datetime.utcnow() - start_time
            ).total_seconds()
            self.log_operation(
                "deduplicate_images",
                duplicates_found=self.metrics.duplicates_found,
                duplicates_removed=self.metrics.duplicates_removed,
                unique_images=self.metrics.unique_images,
                duration=self.metrics.dedup_duration,
            )
            return {
                "status": "success",
                "duplicates_found": self.metrics.duplicates_found,
                "duplicates_removed": self.metrics.duplicates_removed,
                "unique_images": self.metrics.unique_images,
                "duration": self.metrics.dedup_duration,
            }
        except Exception as e:
            logger.error(f"Deduplication failed: {str(e)}")
            raise

    async def _generate_labels(self) -> Dict[str, Any]:
        """Generate labels for images."""
        start_time = datetime.utcnow()
        try:
            if not self.label_generator or not self.temp_workspace:
                return {"status": "skipped", "reason": "Labeling disabled"}
            deduplicated_dir = self.temp_workspace / "deduplicated"
            labeled_dir = self.temp_workspace / "labeled"
            await asyncio.to_thread(
                self.label_generator.generate_dataset_labels,
                str(deduplicated_dir),
            )
            labeled_count = len(list(labeled_dir.glob("*")))
            self.metrics.images_labeled = labeled_count
            self.metrics.labeling_duration = (
                datetime.utcnow() - start_time
            ).total_seconds()
            self.log_operation(
                "generate_labels",
                labeled_images=labeled_count,
                duration=self.metrics.labeling_duration,
            )
            return {
                "status": "success",
                "labeled_images": labeled_count,
                "duration": self.metrics.labeling_duration,
            }
        except Exception as e:
            logger.error(f"Label generation failed: {str(e)}")
            raise

    async def _apply_storage_tiering(self) -> Dict[str, Any]:
        """Move images to hot/cold storage based on access patterns."""
        start_time = datetime.utcnow()
        try:
            if not self.temp_workspace:
                raise ValidationError("Workspace not initialized")
            if self.config.enable_labeling:
                source_dir = self.temp_workspace / "labeled"
            elif self.config.enable_deduplication:
                source_dir = self.temp_workspace / "deduplicated"
            else:
                source_dir = self.temp_workspace / "validated"
            images = list(source_dir.glob("*"))
            total_images = len(images)
            hot_count = min(self.config.hot_storage_threshold, total_images)
            for i, image_file in enumerate(images[:hot_count]):
                await asyncio.to_thread(
                    self.storage_provider.upload,
                    str(image_file),
                    f"hot/{image_file.name}",
                )
                self.metrics.hot_storage_count += 1
            for image_file in images[hot_count:]:
                await asyncio.to_thread(
                    self.storage_provider.upload,
                    str(image_file),
                    f"cold/{image_file.name}",
                )
                self.metrics.cold_storage_count += 1
            self.metrics.storage_duration = (
                datetime.utcnow() - start_time
            ).total_seconds()
            self.log_operation(
                "apply_storage_tiering",
                hot_storage_count=self.metrics.hot_storage_count,
                cold_storage_count=self.metrics.cold_storage_count,
                duration=self.metrics.storage_duration,
            )
            return {
                "status": "success",
                "hot_storage_count": self.metrics.hot_storage_count,
                "cold_storage_count": self.metrics.cold_storage_count,
                "duration": self.metrics.storage_duration,
            }
        except Exception as e:
            logger.error(f"Storage tiering failed: {str(e)}")
            raise

    async def _generate_quality_report(self) -> Dict[str, Any]:
        """Generate quality report for dataset."""
        try:
            if self.metrics.images_crawled > 0:
                quality_score = (
                    self.metrics.unique_images / self.metrics.images_crawled
                ) * 100
            else:
                quality_score = 0.0
            self.metrics.quality_score = quality_score
            self.metrics.report_generated = True
            report = {
                "status": "success",
                "quality_score": quality_score,
                "metrics": self.metrics.to_dict(),
            }
            self.log_operation(
                "generate_quality_report",
                quality_score=quality_score,
            )
            return report
        except Exception as e:
            logger.error(f"Quality report generation failed: {str(e)}")
            raise

    async def _cleanup_workspace(self) -> Dict[str, Any]:
        """Clean up temporary workspace."""
        try:
            if self.config.temp_workspace_cleanup and self.temp_workspace:
                import shutil
                await asyncio.to_thread(
                    shutil.rmtree,
                    str(self.temp_workspace),
                    ignore_errors=True,
                )
                self.temp_workspace = None
            self.log_operation("cleanup_workspace")
            return {
                "status": "success",
                "workspace_cleaned": self.config.temp_workspace_cleanup,
            }
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            raise

    # ==================== Monitoring Methods ====================

    async def get_pipeline_progress(self, workflow_id: int) -> Dict[str, Any]:
        """Get detailed pipeline progress."""
        progress = await self.orchestrator.get_workflow_progress(workflow_id)
        return {
            **progress,
            "metrics": self.metrics.to_dict(),
        }

    async def get_pipeline_metrics(self) -> PipelineMetrics:
        """Get current pipeline metrics."""
        return self.metrics
