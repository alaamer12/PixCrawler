"""
Validation service for image quality and content validation.

This module provides comprehensive image validation services including
single image analysis, batch validation, and validation statistics management.

Classes:
    ValidationLevel: Enum for validation strictness levels
    ValidationStatus: Enum for validation job statuses
    ValidationService: Service class for image validation operations

Features:
    - Single image validation with quality scoring
    - Batch validation job management
    - Validation statistics and coverage tracking
    - Configurable validation levels (basic, standard, strict)
"""

import uuid
import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from backend.core.exceptions import NotFoundError, ValidationError, ExternalServiceError
from backend.repositories import ImageRepository, DatasetRepository
from backend.services.base import BaseService
from validator import CheckManager, ValidatorConfig
from validator.level import ValidationLevel as ValidatorLevel

__all__ = [
    'ValidationLevel',
    'ValidationStatus',
    'ValidationService'
]


class ValidationLevel(str, Enum):
    """
    Validation strictness levels.

    Attributes:
        BASIC: Minimal validation checks (file integrity only)
        STANDARD: Standard validation with moderate strictness
        STRICT: Comprehensive validation with high standards
    """
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class ValidationStatus(str, Enum):
    """
    Validation job status.

    Attributes:
        PENDING: Job created but not started
        PROCESSING: Job currently running
        COMPLETED: Job finished successfully
        FAILED: Job failed with errors
    """
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationService(BaseService):
    """
    Service for image validation operations.

    Provides methods for validating images, managing validation jobs,
    and tracking validation statistics.
    
    Note: This service currently uses repositories for data access.
    When ValidationJob and ValidationResult models are created,
    a ValidationRepository should be added.
    """

    def __init__(
        self,
        image_repo: ImageRepository,
        dataset_repo: DatasetRepository
    ) -> None:
        """
        Initialize validation service with repositories.

        Args:
            image_repo: Image repository instance
            dataset_repo: Dataset repository instance
        """
        super().__init__()
        self.image_repo = image_repo
        self.dataset_repo = dataset_repo

    async def analyze_single_image(
        self,
        image_id: int,
        validation_level: ValidationLevel,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze a single image for quality and content validation.

        Performs comprehensive validation on a single image based on the
        specified validation level. Returns detailed results including
        quality score and identified issues.

        Args:
            image_id: ID of the image to validate
            validation_level: Level of validation to perform
            user_id: ID of the user requesting validation

        Returns:
            Dictionary containing validation results with keys:
                - image_id: Image ID
                - validation_level: Level used
                - is_valid: Whether image passed validation
                - quality_score: Score from 0.0 to 1.0
                - issues: List of issues found
                - metadata: Additional validation metadata
                - validated_at: ISO timestamp

        Raises:
            NotFoundError: If image not found
            ValidationError: If validation fails
            ExternalServiceError: If an unexpected error occurs
        """
        self.log_operation(
            "analyze_single_image",
            image_id=image_id,
            validation_level=validation_level.value,
            user_id=user_id
        )

        try:
            # Get image using repository
            image = await self.image_repo.get_by_id(image_id)
            if not image:
                raise NotFoundError(f"Image with ID {image_id} not found")

            # Initialize validator with appropriate level
            validator_config = ValidatorConfig(
                validation_level=ValidatorLevel(validation_level.upper())
            )
            validator = CheckManager(validator_config)

            # Perform validation
            try:
                result = await asyncio.to_thread(
                    validator.check_integrity,
                    directory=str(Path(image.storage_url).parent),
                    expected_count=1,
                    keyword=str(image_id)
                )

                is_valid = result.valid_images > 0 and not result.corrupted_files
                quality_score = self._calculate_quality_score(validation_level, is_valid)

                issues = []
                if result.corrupted_files:
                    issues.append(f"Corrupted image: {', '.join(result.corrupted_files)}")
                if result.size_violations:
                    issues.append(f"Size violations: {', '.join(result.size_violations)}")
                if result.errors:
                    issues.extend(result.errors)

                return {
                    "image_id": image_id,
                    "validation_level": validation_level.value,
                    "is_valid": is_valid,
                    "quality_score": quality_score,
                    "issues": issues,
                    "metadata": {
                        "width": image.width,
                        "height": image.height,
                        "format_": image.format_,
                        "file_size": image.file_size
                    },
                    "validated_at": datetime.utcnow().isoformat() + "Z"
                }

            except Exception as e:
                self.logger.error(f"Validation error for image {image_id}: {str(e)}")
                raise ValidationError(f"Image validation failed: {str(e)}")

        except Exception as e:
            if not isinstance(e, (NotFoundError, ValidationError)):
                self.logger.error(f"Unexpected error in analyze_single_image: {str(e)}", exc_info=True)
                raise ExternalServiceError("An error occurred during image validation") from e
            raise

    async def create_batch_validation_job(
        self,
        dataset_id: int,
        validation_level: ValidationLevel,
        image_ids: Optional[List[int]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create a batch validation job for multiple images.

        Creates a new validation job to process multiple images in a dataset.
        The job will be executed in the background.

        Note: This method currently returns mock data. When ValidationJob
        model is created, implement actual job creation using a ValidationRepository.

        Args:
            dataset_id: ID of the dataset to validate
            validation_level: Level of validation to perform
            image_ids: Optional list of specific image IDs (None = all images)
            user_id: ID of the user creating the job

        Returns:
            Dictionary containing job information with keys:
                - job_id: Unique job identifier
                - dataset_id: Dataset ID
                - validation_level: Validation level
                - total_images: Number of images to validate
                - status: Current job status
                - created_at: ISO timestamp

        Raises:
            NotFoundError: If dataset not found
            ValidationError: If job creation fails
            ExternalServiceError: If an unexpected error occurs
        """
        self.log_operation(
            "create_batch_validation_job",
            dataset_id=dataset_id,
            validation_level=validation_level.value,
            image_count=len(image_ids) if image_ids else "all",
            user_id=user_id
        )

        try:
            # Check if dataset exists using repository
            dataset = await self.dataset_repo.get_by_id(dataset_id)
            if not dataset:
                raise NotFoundError(f"Dataset with ID {dataset_id} not found")

            # Get image count using repository
            # TODO: Add method to ImageRepository to count images by dataset
            # For now, return mock data
            total_images = 100  # Mock value

            if total_images == 0:
                raise ValidationError("No images found for validation")

            # TODO: When ValidationJob model exists, create actual job record
            # using ValidationRepository
            job_id = str(uuid.uuid4())
            now = datetime.utcnow()

            job_info = {
                "job_id": job_id,
                "dataset_id": dataset_id,
                "validation_level": validation_level.value,
                "total_images": total_images,
                "status": ValidationStatus.PROCESSING.value,
                "created_at": now.isoformat() + "Z"
            }

            # TODO: Start background task when ValidationRepository is available
            # asyncio.create_task(
            #     self._process_validation_job(
            #         job_id,
            #         dataset_id,
            #         validation_level,
            #         image_ids
            #     )
            # )

            return job_info

        except Exception as e:
            if not isinstance(e, (NotFoundError, ValidationError)):
                self.logger.error(f"Unexpected error in create_batch_validation_job: {str(e)}", exc_info=True)
                raise ExternalServiceError("Failed to create validation job") from e
            raise

    async def get_validation_results(self, job_id: str) -> Dict[str, Any]:
        """
        Get validation results for a specific job.

        Retrieves detailed results for a validation job, including progress,
        status, and individual image validation results.

        Args:
            job_id: Unique identifier of the validation job

        Returns:
            Dictionary containing job results with keys:
                - job_id: Job identifier
                - dataset_id: Dataset ID
                - validation_level: Validation level used
                - status: Current job status
                - total_images: Total images in job
                - processed_images: Images processed so far
                - valid_images: Images that passed validation
                - invalid_images: Images that failed validation
                - progress: Progress percentage (0-100)
                - created_at: ISO timestamp
                - updated_at: ISO timestamp or None
                - completed_at: ISO timestamp or None
                - results: List of individual validation results

        Raises:
            NotFoundError: If job not found
        """
        self.log_operation("get_validation_results", job_id=job_id)

        # TODO: Implement actual job retrieval from database
        # For now, return mock data
        total_images = 100
        processed_images = 95
        valid_images = 90
        invalid_images = 5

        return {
            "job_id": job_id,
            "dataset_id": 1,
            "validation_level": ValidationLevel.STANDARD.value,
            "status": ValidationStatus.PROCESSING.value,
            "total_images": total_images,
            "processed_images": processed_images,
            "valid_images": valid_images,
            "invalid_images": invalid_images,
            "progress": (processed_images / total_images * 100) if total_images > 0 else 0.0,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "results": []
        }

    async def get_dataset_validation_stats(self, dataset_id: int) -> Dict[str, Any]:
        """
        Get validation statistics for a dataset.

        Retrieves comprehensive validation statistics for a dataset,
        including coverage, quality metrics, and job history.

        Args:
            dataset_id: ID of the dataset

        Returns:
            Dictionary containing statistics with keys:
                - dataset_id: Dataset ID
                - total_images: Total images in dataset
                - validated_images: Number of validated images
                - valid_images: Number of valid images
                - invalid_images: Number of invalid images
                - validation_coverage: Coverage percentage (0-100)
                - average_quality_score: Average quality score (0.0-1.0)
                - total_validation_jobs: Total jobs run

        Raises:
            NotFoundError: If dataset not found
        """
        self.log_operation("get_dataset_validation_stats", dataset_id=dataset_id)

        # TODO: Implement actual statistics retrieval from database
        total_images = 1000
        validated_images = 950
        valid_images = 900
        invalid_images = 50

        return {
            "dataset_id": dataset_id,
            "total_images": total_images,
            "validated_images": validated_images,
            "valid_images": valid_images,
            "invalid_images": invalid_images,
            "validation_coverage": (validated_images / total_images * 100) if total_images > 0 else 0.0,
            "average_quality_score": 0.92,
            "total_validation_jobs": 5
        }

    async def update_dataset_validation_level(
        self,
        dataset_id: int,
        validation_level: ValidationLevel,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Update the validation level for a dataset.

        Changes the default validation level used for new validation jobs
        on the specified dataset.

        Args:
            dataset_id: ID of the dataset
            validation_level: New validation level to apply
            user_id: ID of the user making the update

        Returns:
            Dictionary containing update information with keys:
                - dataset_id: Dataset ID
                - validation_level: New validation level
                - updated_at: ISO timestamp
                - updated_by: User ID who made the update

        Raises:
            NotFoundError: If dataset not found
            ValidationError: If update fails
        """
        self.log_operation(
            "update_dataset_validation_level",
            dataset_id=dataset_id,
            validation_level=validation_level.value,
            user_id=user_id
        )

        # TODO: Implement actual dataset update in database

        return {
            "dataset_id": dataset_id,
            "validation_level": validation_level.value,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "updated_by": int(user_id) if user_id.isdigit() else None
        }

    async def validate_job_images(
        self,
        job_id: int,
        validation_level: ValidationLevel,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Validate all images in a crawl job.

        Retrieves all images for the specified job and dispatches validation
        tasks via Celery based on the requested validation level.

        Args:
            job_id: ID of the crawl job
            validation_level: Validation level (basic/standard/strict)
            user_id: ID of the user requesting validation

        Returns:
            Dictionary containing validation job information with keys:
                - job_id: Crawl job ID
                - images_count: Number of images to validate
                - validation_level: Validation level used
                - task_ids: List of Celery task IDs
                - message: Success message

        Raises:
            NotFoundError: If job not found or no images found
            ValidationError: If validation dispatch fails
            ExternalServiceError: If an unexpected error occurs
        """
        from validator.tasks import (
            validate_image_fast_task,
            validate_image_medium_task,
            validate_image_slow_task
        )
        
        self.log_operation(
            "validate_job_images",
            job_id=job_id,
            validation_level=validation_level.value,
            user_id=user_id
        )

        try:
            # Get all images for the job
            images = await self.image_repo.get_by_crawl_job(job_id)
            
            if not images:
                raise NotFoundError(f"No images found for job {job_id}")

            # Select validation task based on level
            task_map = {
                ValidationLevel.BASIC: validate_image_fast_task,
                ValidationLevel.STANDARD: validate_image_medium_task,
                ValidationLevel.STRICT: validate_image_slow_task
            }
            
            validation_task = task_map.get(validation_level)
            if not validation_task:
                raise ValidationError(f"Invalid validation level: {validation_level}")
            
            # Dispatch validation tasks
            task_ids = []
            
            self.logger.info(
                f"Dispatching {len(images)} validation tasks for job {job_id} "
                f"at level {validation_level.value}"
            )
            
            for image in images:
                # Dispatch task with image path
                task = validation_task.delay(
                    image_path=image.storage_url,
                    job_id=str(job_id),
                    image_id=str(image.id)
                )
                
                task_ids.append(task.id)
                
                self.logger.debug(
                    f"Dispatched validation task for image {image.id}: {task.id}",
                    job_id=job_id,
                    image_id=image.id,
                    task_id=task.id,
                    validation_level=validation_level.value
                )
            
            self.logger.info(
                f"Successfully dispatched {len(task_ids)} validation tasks for job {job_id}",
                job_id=job_id,
                task_count=len(task_ids),
                validation_level=validation_level.value
            )

            return {
                "job_id": job_id,
                "images_count": len(images),
                "validation_level": validation_level.value,
                "task_ids": task_ids,
                "message": f"Validation started for {len(images)} images"
            }

        except Exception as e:
            if not isinstance(e, (NotFoundError, ValidationError)):
                self.logger.error(
                    f"Unexpected error in validate_job_images: {str(e)}",
                    exc_info=True
                )
                raise ExternalServiceError("Failed to start validation") from e
            raise

    async def handle_validation_result(
        self,
        image_id: int,
        result: Dict[str, Any]
    ) -> None:
        """
        Handle validation task result callback.
        
        This method processes validation task completion results and updates
        the image record with validation status:
        1. Retrieve image from repository
        2. Update validation status using mark_validated()
        3. Update is_valid and is_duplicate flags
        4. Store validation metadata
        
        Args:
            image_id: ID of the image
            result: Validation result dictionary containing:
                - is_valid: Boolean validation status
                - is_duplicate: Boolean duplicate status (optional)
                - quality_score: Float quality score (optional)
                - issues: List of validation issues (optional)
                - metadata: Additional validation metadata (optional)
        
        Raises:
            NotFoundError: If image not found
        """
        self.log_operation(
            "handle_validation_result",
            image_id=image_id,
            is_valid=result.get('is_valid', False)
        )
        
        try:
            # Retrieve image
            image = await self.image_repo.get_by_id(image_id)
            if not image:
                raise NotFoundError(f"Image with ID {image_id} not found")
            
            # Prepare validation result for storage
            validation_data = {
                'is_valid': result.get('is_valid', False),
                'is_duplicate': result.get('is_duplicate', False)
            }
            
            # Build metadata from validation result
            metadata = {}
            if 'quality_score' in result:
                metadata['quality_score'] = result['quality_score']
            if 'issues' in result:
                metadata['validation_issues'] = result['issues']
            if 'metadata' in result:
                metadata.update(result['metadata'])
            
            if metadata:
                validation_data['metadata'] = metadata
            
            # Update image with validation results
            await self.image_repo.mark_validated(image_id, validation_data)
            
            self.logger.info(
                f"Updated validation results for image {image_id}",
                image_id=image_id,
                is_valid=validation_data['is_valid'],
                is_duplicate=validation_data['is_duplicate']
            )
            
        except Exception as e:
            if not isinstance(e, NotFoundError):
                self.logger.error(
                    f"Unexpected error in handle_validation_result: {str(e)}",
                    exc_info=True
                )
            raise
    
    async def _process_validation_job(
        self,
        job_id: str,
        dataset_id: int,
        validation_level: ValidationLevel,
        image_ids: Optional[List[int]] = None
    ) -> None:
        """
        Process a batch validation job in the background.

        Note: This method is a placeholder. When ValidationJob and ValidationResult
        models are created, implement using ValidationRepository.

        Args:
            job_id: ID of the validation job
            dataset_id: ID of the dataset to validate
            validation_level: Level of validation to perform
            image_ids: Optional list of specific image IDs to validate
        """
        try:
            # TODO: When ValidationJob model exists, implement using repositories
            # 1. Get job using ValidationRepository
            # 2. Get images using ImageRepository
            # 3. Process each image with validator
            # 4. Store results using ValidationRepository
            # 5. Update job status using ValidationRepository
            
            self.logger.info(
                f"Validation job {job_id} processing started (placeholder implementation)"
            )
            
            # Placeholder: Log that this needs implementation
            self.logger.warning(
                "Validation job processing not fully implemented. "
                "Requires ValidationJob and ValidationResult models and ValidationRepository."
            )

        except Exception as e:
            self.logger.error(f"Error processing validation job {job_id}: {str(e)}")

    def _calculate_quality_score(
        self,
        validation_level: ValidationLevel,
        is_valid: bool
    ) -> float:
        """
        Calculate quality score based on validation level and result.

        Args:
            validation_level: Validation level used
            is_valid: Whether image passed validation

        Returns:
            Quality score from 0.0 to 1.0
        """
        if not is_valid:
            return 0.0
        
        # Base score on validation level
        scores = {
            ValidationLevel.BASIC: 0.6,
            ValidationLevel.STANDARD: 0.8,
            ValidationLevel.STRICT: 1.0
        }
        return scores.get(validation_level, 0.7)

    def _get_threshold(self, validation_level: ValidationLevel) -> float:
        """
        Get quality threshold for validation level.

        Args:
            validation_level: Validation level

        Returns:
            Minimum quality score required to pass
        """
        thresholds = {
            ValidationLevel.BASIC: 0.5,  # 50% for basic validation
            ValidationLevel.STANDARD: 0.7,  # 70% for standard validation
            ValidationLevel.STRICT: 0.9  # 90% for strict validation
        }
        return thresholds.get(validation_level, 0.7)

    def _get_validation_issues(self, validation_level: ValidationLevel) -> List[str]:
        """
        Get validation issues based on level.

        Args:
            validation_level: Validation level

        Returns:
            List of validation issues
        """
        if validation_level == ValidationLevel.STRICT:
            return [
                "Image does not meet strict quality standards",
                "Resolution below threshold",
                "Compression artifacts detected"
            ]
        elif validation_level == ValidationLevel.STANDARD:
            return [
                "Image quality below standard",
                "Minor compression artifacts"
            ]
        else:
            return ["Basic validation failed"]
