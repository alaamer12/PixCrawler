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

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError, ExternalServiceError
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
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize validation service.
        
        Args:
            session: Async database session
        """
        super().__init__()
        self.session = session
        
    async def _handle_db_operation(self, operation, *args, **kwargs):
        """
        Handle database operations with proper transaction and error handling.
        
        Args:
            operation: Async function to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            NotFoundError: If resource not found
            ValidationError: If validation fails
            ExternalServiceError: For unexpected database errors
        """
        try:
            async with self.session.begin():
                return await operation(*args, **kwargs)
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Database operation failed: {str(e)}", exc_info=True)
            raise ExternalServiceError("An error occurred while accessing the database") from e

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

        async def _get_image():
            from backend.database.models import Image
            result = await self.session.execute(select(Image).where(Image.id == image_id))
            image = result.scalar_one_or_none()
            if not image:
                raise NotFoundError(f"Image with ID {image_id} not found")
            return image

        try:
            # Get image within a transaction
            image = await self._handle_db_operation(_get_image)

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
                        "format": image.format,
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

        async def _create_job():
            from backend.database.models import Dataset, Image, ValidationJob
            
            # Check if dataset exists
            result = await self.session.execute(select(Dataset).where(Dataset.id == dataset_id))
            if not result.scalar_one_or_none():
                raise NotFoundError(f"Dataset with ID {dataset_id} not found")

            # Get image count
            query = select(Image).where(Image.dataset_id == dataset_id)
            if image_ids:
                query = query.where(Image.id.in_(image_ids))
                
            result = await self.session.execute(select(func.count()).select_from(query.subquery()))
            total_images = result.scalar_one()
            
            if total_images == 0:
                raise ValidationError("No images found for validation")
                
            # Create job record
            job_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            job = ValidationJob(
                id=job_id,
                dataset_id=dataset_id,
                user_id=user_id,
                validation_level=validation_level,
                status=ValidationStatus.PROCESSING,
                total_images=total_images,
                processed_images=0,
                valid_images=0,
                invalid_images=0,
                created_at=now,
                updated_at=now
            )
            
            self.session.add(job)
            await self.session.flush()
            
            return {
                "job_id": job_id,
                "dataset_id": dataset_id,
                "validation_level": validation_level.value,
                "total_images": total_images,
                "status": ValidationStatus.PROCESSING.value,
                "created_at": now.isoformat() + "Z"
            }

        try:
            # Create job within a transaction
            job_info = await self._handle_db_operation(_create_job)
            
            # Start background task outside of transaction
            asyncio.create_task(
                self._process_validation_job(
                    job_info["job_id"], 
                    dataset_id, 
                    validation_level, 
                    image_ids
                )
            )
            
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

    async def _process_validation_job(
        self,
        job_id: str,
        dataset_id: int,
        validation_level: ValidationLevel,
        image_ids: Optional[List[int]] = None
    ) -> None:
        """
        Process a batch validation job in the background.
        
        Args:
            job_id: ID of the validation job
            dataset_id: ID of the dataset to validate
            validation_level: Level of validation to perform
            image_ids: Optional list of specific image IDs to validate
        """
        from backend.database.models import Image, ValidationJob, ValidationResult
        
        try:
            # Get job
            result = await self.session.execute(
                select(ValidationJob).where(ValidationJob.id == job_id)
            )
            job = result.scalar_one()
            
            # Get images to validate
            query = select(Image).where(Image.dataset_id == dataset_id)
            if image_ids:
                query = query.where(Image.id.in_(image_ids))
                
            result = await self.session.execute(query)
            images = result.scalars().all()
            
            # Initialize validator
            validator_config = ValidatorConfig(
                validation_level=ValidatorLevel(validation_level.upper())
            )
            validator = CheckManager(validator_config)
            
            # Process each image
            for image in images:
                try:
                    # Validate image
                    result = await asyncio.to_thread(
                        validator.check_integrity,
                        directory=str(Path(image.storage_url).parent),
                        expected_count=1,
                        keyword=str(image.id)
                    )
                    
                    # Determine if image is valid
                    is_valid = result.valid_images > 0 and not result.corrupted_files
                    quality_score = self._calculate_quality_score(validation_level, is_valid)
                    
                    # Create validation result
                    validation_result = ValidationResult(
                        job_id=job_id,
                        image_id=image.id,
                        is_valid=is_valid,
                        quality_score=quality_score,
                        issues=result.errors or [],
                        created_at=datetime.utcnow()
                    )
                    self.session.add(validation_result)
                    
                    # Update job stats
                    job.processed_images += 1
                    if is_valid:
                        job.valid_images += 1
                    else:
                        job.invalid_images += 1
                        
                    job.updated_at = datetime.utcnow()
                    await self.session.commit()
                    
                except Exception as e:
                    self.logger.error(f"Error processing image {image.id}: {str(e)}")
                    continue
                    
            # Mark job as completed
            job.status = ValidationStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            await self.session.commit()
            
        except Exception as e:
            self.logger.error(f"Error processing validation job {job_id}: {str(e)}")
            
            # Update job status to failed
            try:
                await self.session.execute(
                    update(ValidationJob)
                    .where(ValidationJob.id == job_id)
                    .values(
                        status=ValidationStatus.FAILED,
                        error=str(e),
                        updated_at=datetime.utcnow()
                    )
                )
                await self.session.commit()
            except Exception as update_error:
                self.logger.error(f"Failed to update job status: {str(update_error)}")
                await self.session.rollback()

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