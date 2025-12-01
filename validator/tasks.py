"""
Celery tasks for PixCrawler validator package.

This module provides Celery task definitions for background validation operations
using the validator package's real functionality through CheckManager.

Tasks:
    check_duplicates_task: Check for duplicate images
    check_integrity_task: Check image integrity
    check_all_task: Perform both duplicate and integrity checks
    validate_image_fast_task: Fast image validation
    validate_image_medium_task: Medium image validation
    validate_image_slow_task: Thorough image validation
"""

from pathlib import Path
from typing import Dict, Any, Optional

from celery_core.base import BaseTask
from celery_core.base import BaseTask as Self
from celery_core.app import get_celery_app
from utility.logging_config import get_logger

# Import real validator functionality
from validator.validation import CheckManager
from validator.config import ValidatorConfig, CheckMode, DuplicateAction
from validator.level import get_validation_strategy, ValidationLevel

logger = get_logger(__name__)
app = get_celery_app()

__all__ = [
    "check_duplicates_task",
    "check_integrity_task",
    "check_all_task",
    "validate_image_fast_task",
    "validate_image_medium_task",
    "validate_image_slow_task",
]

def check_duplicates_impl(
    directory: str,
    category_name: str = "",
    keyword: str = "",
    config: Optional[ValidatorConfig] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Implementation for checking duplicate images.

    Uses CheckManager.check_duplicates() from validation.py.
    """
    # Add structured logging context
    log_context = logger.bind(
        operation="check_duplicates",
        directory=directory,
        category_name=category_name,
        keyword=keyword,
        job_id=job_id
    )
    log_context.info(f"Checking duplicates in: {directory}")

    try:
        if not Path(directory).exists():
            return {"error": f"Directory does not exist: {directory}"}

        # Use real CheckManager
        check_manager = CheckManager(config=config)
        result = check_manager.check_duplicates(directory, category_name, keyword)

        log_context.info(
            "Duplicate check completed",
            total_images=result.total_images,
            duplicates_found=result.duplicates_found,
            duplicates_removed=result.duplicates_removed,
            processing_time=result.processing_time
        )

        return {
            "success": True,
            "total_images": result.total_images,
            "duplicates_found": result.duplicates_found,
            "duplicates_removed": result.duplicates_removed,
            "unique_kept": result.unique_kept,
            "duplicate_groups": result.duplicate_groups,
            "processing_time": result.processing_time,
            "errors": result.errors,
        }

    except Exception as e:
        log_context.error(
            f"Duplicate check failed for {directory}: {str(e)}",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "success": False,
            "error": str(e),
        }


def check_integrity_impl(
    directory: str,
    expected_count: int = 0,
    category_name: str = "",
    keyword: str = "",
    config: Optional[ValidatorConfig] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Implementation for checking image integrity.

    Uses CheckManager.check_integrity() from validation.py.
    """
    # Add structured logging context
    log_context = logger.bind(
        operation="check_integrity",
        directory=directory,
        expected_count=expected_count,
        category_name=category_name,
        keyword=keyword,
        job_id=job_id
    )
    log_context.info(f"Checking integrity in: {directory}")

    try:
        if not Path(directory).exists():
            return {"error": f"Directory does not exist: {directory}"}

        # Use real CheckManager
        check_manager = CheckManager(config=config)
        result = check_manager.check_integrity(directory, expected_count, category_name, keyword)

        log_context.info(
            "Integrity check completed",
            total_images=result.total_images,
            valid_images=result.valid_images,
            corrupted_images=result.corrupted_images,
            processing_time=result.processing_time
        )

        return {
            "success": True,
            "total_images": result.total_images,
            "valid_images": result.valid_images,
            "corrupted_images": result.corrupted_images,
            "corrupted_files": result.corrupted_files,
            "size_violations": result.size_violations,
            "processing_time": result.processing_time,
            "errors": result.errors,
        }

    except Exception as e:
        log_context.error(
            f"Integrity check failed for {directory}: {str(e)}",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "success": False,
            "error": str(e),
        }


def check_all_impl(
    directory: str,
    expected_count: int = 0,
    category_name: str = "",
    keyword: str = "",
    config: Optional[ValidatorConfig] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Implementation for performing both duplicate and integrity checks.

    Uses CheckManager.check_all() from validation.py.
    """
    # Add structured logging context
    log_context = logger.bind(
        operation="check_all",
        directory=directory,
        expected_count=expected_count,
        category_name=category_name,
        keyword=keyword,
        job_id=job_id
    )
    log_context.info(f"Running comprehensive validation on: {directory}")

    try:
        if not Path(directory).exists():
            return {"error": f"Directory does not exist: {directory}"}

        # Use real CheckManager
        check_manager = CheckManager(config=config)
        duplicate_result, integrity_result = check_manager.check_all(
            directory, expected_count, category_name, keyword
        )

        log_context.info(
            "Comprehensive validation completed",
            duplicates_found=duplicate_result.duplicates_found,
            duplicates_removed=duplicate_result.duplicates_removed,
            valid_images=integrity_result.valid_images,
            corrupted_images=integrity_result.corrupted_images,
            total_processing_time=duplicate_result.processing_time + integrity_result.processing_time
        )

        return {
            "success": True,
            "duplicate_result": {
                "total_images": duplicate_result.total_images,
                "duplicates_found": duplicate_result.duplicates_found,
                "duplicates_removed": duplicate_result.duplicates_removed,
                "unique_kept": duplicate_result.unique_kept,
                "processing_time": duplicate_result.processing_time,
                "errors": duplicate_result.errors,
            },
            "integrity_result": {
                "total_images": integrity_result.total_images,
                "valid_images": integrity_result.valid_images,
                "corrupted_images": integrity_result.corrupted_images,
                "corrupted_files": integrity_result.corrupted_files,
                "processing_time": integrity_result.processing_time,
                "errors": integrity_result.errors,
            },
            "summary": check_manager.get_summary_report(),
        }

    except Exception as e:
        log_context.error(
            f"Comprehensive validation failed for {directory}: {str(e)}",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "success": False,
            "error": str(e),
        }


def validate_image_impl(
    image_path: str,
    validation_level: ValidationLevel,
    job_id: Optional[str] = None,
    image_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Implementation for validating a single image.

    Uses get_validation_strategy() from level.py.
    """
    # Add structured logging context
    log_context = logger.bind(
        operation="validate_image",
        image_path=image_path,
        validation_level=validation_level.name,
        job_id=job_id,
        image_id=image_id
    )
    log_context.info(f"Validating image: {image_path} (level: {validation_level.name})")

    try:
        if not Path(image_path).exists():
            return {"error": f"Image file does not exist: {image_path}"}

        strategy = get_validation_strategy(validation_level)
        result = strategy.validate(image_path)

        log_context.info(
            "Image validation completed",
            is_valid=result.is_valid,
            issues_found=result.issues_found,
            processing_time=result.processing_time
        )

        return {
            "success": True,
            "is_valid": result.is_valid,
            "issues_found": result.issues_found,
            "metadata": result.metadata,
            "processing_time": result.processing_time,
            "validation_level": result.validation_level.name,
            "file_path": result.file_path,
            "file_size_bytes": result.file_size_bytes,
        }

    except Exception as e:
        log_context.error(
            f"Image validation failed for {image_path}: {str(e)}",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "success": False,
            "error": str(e),
        }


@app.task(
    bind=True,
    base=BaseTask,
    name="validator.check_duplicates",
    # Pydantic Support
    typing=True,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    reject_on_worker_lost=True,
    track_started=True,
    # Time Limits
    soft_time_limit=300,
    time_limit=600,
    # Serialization
    serializer="json",
)
def check_duplicates_task(
    self: Self,
    directory: str,
    category_name: str = "",
    keyword: str = "",
    mode: str = "lenient",
    duplicate_action: str = "remove",
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task for checking duplicate images.
    
    Retry Strategy:
        - Infrastructure failures: Retry up to 3 times with 60s delay
        - Permanent errors: Fail immediately

    Args:
        self: BaseTask Type from Celery
        directory: Path to directory to check
        category_name: Category name for reporting
        keyword: Keyword for reporting
        mode: Validation mode (strict, lenient, report_only)
        duplicate_action: Action for duplicates (remove, quarantine, report_only)
        job_id: Optional job ID for structured logging
    """
    try:
        config = ValidatorConfig(
            mode=CheckMode(mode),
            duplicate_action=DuplicateAction(duplicate_action),
        )
        return check_duplicates_impl(directory, category_name, keyword, config, job_id)
    except (MemoryError, OSError) as e:
        logger.error(
            f"Infrastructure failure for duplicate check '{directory}': {e}",
            directory=directory,
            error_type=type(e).__name__,
            retry_count=self.request.retries
        )
        raise self.retry(exc=e, max_retries=3, countdown=60)
    except Exception as e:
        logger.exception(
            f"Unexpected error for duplicate check '{directory}': {e}",
            directory=directory,
            error_type=type(e).__name__
        )
        raise


@app.task(
    bind=True,
    base=BaseTask,
    name="validator.check_integrity",
    # Pydantic Support
    typing=True,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    reject_on_worker_lost=True,
    track_started=True,
    # Time Limits
    soft_time_limit=300,
    time_limit=600,
    # Serialization
    serializer="json",
)
def check_integrity_task(
    self: Self,
    directory: str,
    expected_count: int = 0,
    category_name: str = "",
    keyword: str = "",
    mode: str = "lenient",
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task for checking image integrity.
    
    Retry Strategy:
        - Infrastructure failures: Retry up to 3 times with 60s delay
        - Permanent errors: Fail immediately

    Args:
        self: BaseTask Type from Celery
        directory: Path to directory to check
        expected_count: Expected number of valid images
        category_name: Category name for reporting
        keyword: Keyword for reporting
        mode: Validation mode (strict, lenient, report_only)
        job_id: Optional job ID for structured logging
    """
    try:
        config = ValidatorConfig(mode=CheckMode(mode))
        return check_integrity_impl(directory, expected_count, category_name, keyword, config, job_id)
    except (MemoryError, OSError) as e:
        logger.error(
            f"Infrastructure failure for integrity check '{directory}': {e}",
            directory=directory,
            error_type=type(e).__name__,
            retry_count=self.request.retries
        )
        raise self.retry(exc=e, max_retries=3, countdown=60)
    except Exception as e:
        logger.exception(
            f"Unexpected error for integrity check '{directory}': {e}",
            directory=directory,
            error_type=type(e).__name__
        )
        raise


@app.task(
    bind=True,
    base=BaseTask,
    name="validator.check_all",
    # Pydantic Support
    typing=True,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    reject_on_worker_lost=True,
    track_started=True,
    # Time Limits (longer for comprehensive check)
    soft_time_limit=600,
    time_limit=900,
    # Serialization
    serializer="json",
)
def check_all_task(
    self: Self,
    directory: str,
    expected_count: int = 0,
    category_name: str = "",
    keyword: str = "",
    mode: str = "lenient",
    duplicate_action: str = "remove",
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task for performing both duplicate and integrity checks.
    
    Retry Strategy:
        - Infrastructure failures: Retry up to 3 times with 60s delay
        - Permanent errors: Fail immediately

    Args:
        self: BaseTask Type from Celery
        directory: Path to directory to check
        expected_count: Expected number of valid images
        category_name: Category name for reporting
        keyword: Keyword for reporting
        mode: Validation mode (strict, lenient, report_only)
        duplicate_action: Action for duplicates (remove, quarantine, report_only)
        job_id: Optional job ID for structured logging
    """
    try:
        config = ValidatorConfig(
            mode=CheckMode(mode),
            duplicate_action=DuplicateAction(duplicate_action),
        )
        return check_all_impl(directory, expected_count, category_name, keyword, config, job_id)
    except (MemoryError, OSError) as e:
        logger.error(
            f"Infrastructure failure for comprehensive check '{directory}': {e}",
            directory=directory,
            error_type=type(e).__name__,
            retry_count=self.request.retries
        )
        raise self.retry(exc=e, max_retries=3, countdown=60)
    except Exception as e:
        logger.exception(
            f"Unexpected error for comprehensive check '{directory}': {e}",
            directory=directory,
            error_type=type(e).__name__
        )
        raise


@app.task(
    bind=True,
    base=BaseTask,
    name="validator.validate_image_fast",
    # Pydantic Support
    typing=True,
    # Result Storage
    ignore_result=False,
    acks_late=True,
    track_started=False,
    # Time Limits (short for fast validation)
    soft_time_limit=5,
    time_limit=10,
    # Rate Limiting (high throughput)
    rate_limit="1000/m",
    # Serialization
    serializer="json",
)
def validate_image_fast_task(
    self: Self,
    image_path: str,
    job_id: Optional[str] = None,
    image_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task for fast image validation.
    
    Retry Strategy:
        - Infrastructure failures: Retry up to 3 times with 60s delay
        - Permanent errors: Fail immediately

    Fast validation checks:
    - File exists and is readable
    - Valid image format
    - Basic file size checks

    Args:
        self: BaseTask Type from Celery
        image_path: Path to image file
        job_id: Optional job ID for structured logging
        image_id: Optional image ID for structured logging
    """
    try:
        return validate_image_impl(image_path, ValidationLevel.FAST, job_id, image_id)
    except (MemoryError, OSError) as e:
        logger.error(
            f"Infrastructure failure for fast validation '{image_path}': {e}",
            image_path=image_path,
            error_type=type(e).__name__,
            retry_count=self.request.retries
        )
        raise self.retry(exc=e, max_retries=3, countdown=60)
    except Exception as e:
        logger.exception(
            f"Unexpected error for fast validation '{image_path}': {e}",
            image_path=image_path,
            error_type=type(e).__name__
        )
        raise


@app.task(
    bind=True,
    base=BaseTask,
    name="validator.validate_image_medium",
    # Pydantic Support
    typing=True,
    # Result Storage
    ignore_result=False,
    acks_late=True,
    track_started=False,
    # Time Limits (moderate)
    soft_time_limit=15,
    time_limit=30,
    # Rate Limiting (moderate throughput)
    rate_limit="500/m",
    # Serialization
    serializer="json",
)
def validate_image_medium_task(
    self,
    image_path: str,
    job_id: Optional[str] = None,
    image_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task for medium image validation.
    
    Retry Strategy:
        - Infrastructure failures: Retry up to 3 times with 60s delay
        - Permanent errors: Fail immediately

    Medium validation checks:
    - All fast checks
    - Image dimensions
    - Image can be opened
    - Basic corruption detection

    Args:
        self: BaseTask Type from Celery
        image_path: Path to image file
        job_id: Optional job ID for structured logging
        image_id: Optional image ID for structured logging
    """
    try:
        return validate_image_impl(image_path, ValidationLevel.MEDIUM, job_id, image_id)
    except (MemoryError, OSError) as e:
        logger.error(
            f"Infrastructure failure for medium validation '{image_path}': {e}",
            image_path=image_path,
            error_type=type(e).__name__,
            retry_count=self.request.retries
        )
        raise self.retry(exc=e, max_retries=3, countdown=60)
    except Exception as e:
        logger.exception(
            f"Unexpected error for medium validation '{image_path}': {e}",
            image_path=image_path,
            error_type=type(e).__name__
        )
        raise


@app.task(
    bind=True,
    base=BaseTask,
    name="validator.validate_image_slow",
    # Pydantic Support
    typing=True,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    track_started=True,
    # Time Limits (longer for thorough validation)
    soft_time_limit=60,
    time_limit=120,
    # Rate Limiting (lower throughput)
    rate_limit="100/m",
    # Serialization
    serializer="json",
)
def validate_image_slow_task(
    self,
    image_path: str,
    job_id: Optional[str] = None,
    image_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task for thorough image validation.
    
    Retry Strategy:
        - Infrastructure failures: Retry up to 3 times with 60s delay
        - Permanent errors: Fail immediately

    Slow validation checks:
    - All medium checks
    - Deep corruption detection
    - Metadata extraction
    - Comprehensive quality checks

    Args:
        self: BaseTask Type from Celery
        image_path: Path to image file
        job_id: Optional job ID for structured logging
        image_id: Optional image ID for structured logging
    """
    try:
        return validate_image_impl(image_path, ValidationLevel.SLOW, job_id, image_id)
    except (MemoryError, OSError) as e:
        logger.error(
            f"Infrastructure failure for slow validation '{image_path}': {e}",
            image_path=image_path,
            error_type=type(e).__name__,
            retry_count=self.request.retries
        )
        raise self.retry(exc=e, max_retries=3, countdown=60)
    except Exception as e:
        logger.exception(
            f"Unexpected error for slow validation '{image_path}': {e}",
            image_path=image_path,
            error_type=type(e).__name__
        )
        raise
