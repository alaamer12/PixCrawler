"""
PixCrawler Validator Package

This package provides comprehensive image validation, integrity checking, and duplicate detection
functionality for image datasets. It was separated from the builder package to maintain
clean separation of concerns.

Classes:
    ImageHasher: Computes image hashes for duplicate detection
    DuplicationManager: Detects and manages duplicate images
    ImageValidator: Validates image integrity and quality
    IntegrityProcessor: Main processor for integrity workflows
    CheckManager: Enhanced manager for validation operations
    ValidationConfig: Configuration for validation operations

Functions:
    validate_dataset: Validates an entire dataset
    remove_duplicates: Removes duplicates from a dataset
    process_integrity: Main entry point for integrity processing

Example:
    ```python
    from validator import IntegrityProcessor, ValidationConfig
    
    # Simple validation
    processor = IntegrityProcessor()
    results = processor.process_dataset("./dataset", remove_duplicates=True)
    
    # Advanced validation with custom config
    config = ValidationConfig(
        mode=CheckMode.STRICT,
        duplicate_action=DuplicateAction.QUARANTINE,
        min_file_size_bytes=2048
    )
    processor = IntegrityProcessor(config)
    results = processor.process_dataset("./dataset")
    ```

Features:
    - Comprehensive image integrity validation
    - Advanced duplicate detection using content and perceptual hashing
    - Configurable validation modes (strict, lenient, report-only)
    - Batch processing for large datasets
    - Detailed reporting and statistics
    - Quarantine functionality for problematic images
"""

from validator.integrity import (
    ImageHasher,
    DuplicationManager,
    ImageValidator,
    IntegrityProcessor,
    validate_dataset,
    remove_duplicates,
    process_integrity
)

from validator.validation import (
    CheckManager,
    ValidationConfig,
    CheckMode,
    DuplicateAction,
    DuplicateResult,
    IntegrityResult,
    CheckStats
)

__version__ = "0.1.0"
__author__ = "PixCrawler Team"
__email__ = "team@pixcrawler.com"

__all__ = [
    # Core integrity classes
    "ImageHasher",
    "DuplicationManager", 
    "ImageValidator",
    "IntegrityProcessor",
    
    # Validation management
    "CheckManager",
    "ValidationConfig",
    "CheckMode",
    "DuplicateAction",
    "DuplicateResult",
    "IntegrityResult",
    "CheckStats",
    
    # Convenience functions
    "validate_dataset",
    "remove_duplicates",
    "process_integrity"
]