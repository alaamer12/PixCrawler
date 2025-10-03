"""
Validation management module for PixCrawler.

This module provides enhanced validation management with configurable behavior,
comprehensive tracking, and detailed reporting. It was moved from the builder
package to maintain clean separation of concerns.

Classes:
    CheckMode: Enumeration of validation modes
    DuplicateAction: Actions to take when duplicates are found
    ValidationConfig: Configuration for validation operations
    DuplicateResult: Result of duplicate checking operation
    IntegrityResult: Result of integrity checking operation
    CheckStats: Overall statistics for validation operations
    CheckManager: Enhanced manager for validation operations

Features:
    - Configurable validation modes (strict, lenient, report-only)
    - Multiple duplicate handling strategies (remove, quarantine, report)
    - Comprehensive result tracking and statistics
    - Batch processing capabilities
    - Detailed error reporting and logging
"""

import os
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Set

from logging_config import get_logger
from validator.integrity import DuplicationManager, ImageValidator

logger = get_logger(__name__)

__all__ = [
    'CheckMode',
    'DuplicateAction', 
    'ValidationConfig',
    'DuplicateResult',
    'IntegrityResult',
    'CheckStats',
    'CheckManager'
]


class CheckMode(Enum):
    """Enumeration of available validation modes"""
    STRICT = auto()      # Fail on any issues
    LENIENT = auto()     # Log warnings but continue
    REPORT_ONLY = auto() # Only report, no actions


class DuplicateAction(Enum):
    """Actions to take when duplicates are found"""
    REMOVE = auto()      # Remove duplicate files
    REPORT_ONLY = auto() # Only report duplicates
    QUARANTINE = auto()  # Move duplicates to quarantine directory


@dataclass
class ValidationConfig:
    """Configuration for validation operations"""
    mode: CheckMode = CheckMode.LENIENT
    duplicate_action: DuplicateAction = DuplicateAction.REMOVE
    supported_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif')
    max_file_size_mb: Optional[int] = None
    min_file_size_bytes: int = 1024  # 1KB minimum
    quarantine_dir: Optional[str] = None
    batch_size: int = 100  # Process images in batches
    min_image_width: int = 50
    min_image_height: int = 50


@dataclass
class DuplicateResult:
    """Result of duplicate checking operation"""
    total_images: int
    duplicates_found: int
    duplicates_removed: int
    unique_kept: int
    duplicate_groups: Dict[str, List[str]] = field(default_factory=dict)
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class IntegrityResult:
    """Result of integrity checking operation"""
    total_images: int
    valid_images: int
    corrupted_images: int
    corrupted_files: List[str] = field(default_factory=list)
    size_violations: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class CheckStats:
    """Overall statistics for validation operations"""
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    total_duplicates_found: int = 0
    total_duplicates_removed: int = 0
    total_corrupted_found: int = 0
    categories_processed: Set[str] = field(default_factory=set)
    keywords_processed: Set[str] = field(default_factory=set)
    processing_history: List[Dict[str, Any]] = field(default_factory=list)


class CheckManager:
    """
    Enhanced manager for checking image duplicates and integrity with comprehensive
    tracking, configurable behavior, and detailed reporting.
    
    This class provides a unified interface for all validation operations including
    duplicate detection, integrity checking, and comprehensive reporting.
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize the CheckManager.

        Args:
            config: Optional ValidationConfig for customizing behavior
        """
        self.config = config or ValidationConfig()
        self.stats = CheckStats()
        
        # Initialize validation components
        self.duplication_manager = DuplicationManager()
        self.image_validator = ImageValidator(
            min_width=self.config.min_image_width,
            min_height=self.config.min_image_height
        )

        # Setup quarantine directory if specified
        if (self.config.duplicate_action == DuplicateAction.QUARANTINE and
                self.config.quarantine_dir):
            Path(self.config.quarantine_dir).mkdir(parents=True, exist_ok=True)

    def _is_valid_image_file(self, file_path: Path) -> bool:
        """Check if a file is a valid image file"""
        try:
            if not file_path.is_file():
                return False

            # Check extension
            if not file_path.suffix.lower() in self.config.supported_extensions:
                return False

            # Check file size constraints
            file_size = file_path.stat().st_size
            if file_size < self.config.min_file_size_bytes:
                return False

            if (self.config.max_file_size_mb and
                    file_size > self.config.max_file_size_mb * 1024 * 1024):
                return False

            return True

        except Exception as e:
            logger.warning(f"Error checking file {file_path}: {e}")
            return False

    def _get_image_files(self, directory_path: Path) -> List[Path]:
        """Get all valid image files in a directory"""
        try:
            if not directory_path.exists():
                logger.warning(f"Directory does not exist: {directory_path}")
                return []

            image_files = []
            for file_path in directory_path.iterdir():
                if self._is_valid_image_file(file_path):
                    image_files.append(file_path)

            return image_files

        except Exception as e:
            logger.error(f"Error reading directory {directory_path}: {e}")
            return []

    def _handle_duplicates(self, duplicates: Dict[str, List[str]],
                           keyword_path: str) -> int:
        """Handle duplicate files based on configured action"""
        removed_count = 0

        try:
            if self.config.duplicate_action == DuplicateAction.REPORT_ONLY:
                return 0

            for original, duplicates_list in duplicates.items():
                for duplicate_file in duplicates_list:
                    duplicate_path = Path(keyword_path) / duplicate_file

                    if self.config.duplicate_action == DuplicateAction.REMOVE:
                        removed_count = self._unlink(duplicate_path, removed_count, duplicate_file)

                    elif self.config.duplicate_action == DuplicateAction.QUARANTINE:
                        removed_count = self._unlink_quarantine(duplicate_path, removed_count, duplicate_file)

        except Exception as e:
            logger.error(f"Error handling duplicates: {e}")

        return removed_count

    @staticmethod
    def _unlink(duplicate_path: Path, removed_count: int, duplicate_file: str) -> int:
        """Remove a duplicate file"""
        if duplicate_path.exists():
            duplicate_path.unlink()
            removed_count += 1
            logger.debug(f"Removed duplicate: {duplicate_file}")
        return removed_count

    def _unlink_quarantine(self, duplicate_path: Path, removed_count: int, duplicate_file: str) -> int:
        """Move a duplicate file to quarantine"""
        if duplicate_path.exists() and self.config.quarantine_dir:
            quarantine_path = Path(self.config.quarantine_dir) / duplicate_file
            quarantine_path.parent.mkdir(parents=True, exist_ok=True)
            duplicate_path.rename(quarantine_path)
            removed_count += 1
            logger.debug(f"Quarantined duplicate: {duplicate_file}")
        return removed_count

    def check_duplicates(self, directory: str, category_name: str = "", keyword: str = "") -> DuplicateResult:
        """
        Enhanced duplicate checking with comprehensive result tracking.

        Args:
            directory: Path to the directory to check
            category_name: Name of the category (for reporting)
            keyword: Keyword being processed (for reporting)

        Returns:
            DuplicateResult: Detailed results of the duplicate check
        """
        start_time = time.time()
        result = DuplicateResult(total_images=0, duplicates_found=0,
                                 duplicates_removed=0, unique_kept=0)

        try:
            # Get all image files
            directory_path = Path(directory)
            image_files = self._get_image_files(directory_path)
            result.total_images = len(image_files)

            if not image_files:
                logger.info(f"No images found in {directory}")
                return result

            logger.info(f"Checking for duplicates in {len(image_files)} images")
            if category_name and keyword:
                logger.info(f"Processing {category_name}/{keyword}")

            # Detect duplicates
            duplicates = self.duplication_manager.detect_duplicates(directory)

            result.duplicate_groups = duplicates
            result.duplicates_found = sum(len(dups) for dups in duplicates.values())

            # Handle duplicates based on configuration
            result.duplicates_removed = self._handle_duplicates(duplicates, directory)
            result.unique_kept = result.total_images - result.duplicates_removed

            # Update statistics
            self._update_duplicate_statistics(result, category_name, keyword)

            logger.info(f"Found {result.duplicates_found} duplicates, "
                        f"removed {result.duplicates_removed} out of {result.total_images} images")

        except Exception as e:
            error_msg = f"Failed to check duplicates: {e}"
            if category_name and keyword:
                error_msg = f"Failed to check duplicates for {category_name}/{keyword}: {e}"
            
            logger.error(error_msg)
            result.errors.append(error_msg)
            self.stats.failed_checks += 1

            if self.config.mode == CheckMode.STRICT:
                raise ValueError(error_msg) from e

        finally:
            result.processing_time = time.time() - start_time
            self.stats.total_checks += 1

            # Record processing history
            self.stats.processing_history.append({
                'operation': 'duplicate_check',
                'category': category_name,
                'keyword': keyword,
                'success': not result.errors,
                'processing_time': result.processing_time,
                'images_processed': result.total_images,
                'duplicates_found': result.duplicates_found
            })

        return result

    def check_integrity(self, directory: str, expected_count: int = 0, 
                       category_name: str = "", keyword: str = "") -> IntegrityResult:
        """
        Enhanced integrity checking with detailed result tracking.

        Args:
            directory: Path to the directory to check
            expected_count: Expected number of valid images
            category_name: Name of the category (for reporting)
            keyword: Keyword being processed (for reporting)

        Returns:
            IntegrityResult: Detailed results of the integrity check
        """
        start_time = time.time()
        result = IntegrityResult(total_images=0, valid_images=0, corrupted_images=0)

        try:
            # Count valid images
            valid_count, total_count, corrupted_files = self.image_validator.count_valid(directory)

            result.total_images = total_count
            result.valid_images = valid_count
            result.corrupted_images = len(corrupted_files)
            result.corrupted_files = corrupted_files

            # Check for size violations if configured
            if self.config.max_file_size_mb or self.config.min_file_size_bytes:
                directory_path = Path(directory)
                for file_path in self._get_image_files(directory_path):
                    file_size = file_path.stat().st_size

                    if file_size < self.config.min_file_size_bytes:
                        result.size_violations.append(f"{file_path.name} (too small: {file_size} bytes)")
                    elif (self.config.max_file_size_mb and
                          file_size > self.config.max_file_size_mb * 1024 * 1024):
                        result.size_violations.append(f"{file_path.name} (too large: {file_size} bytes)")

            # Update statistics
            self.stats.total_corrupted_found += result.corrupted_images
            if category_name:
                self.stats.categories_processed.add(category_name)
            if keyword:
                self.stats.keywords_processed.add(keyword)
            self.stats.successful_checks += 1

            logger.info(f"Integrity check: {valid_count}/{total_count} valid images, "
                        f"{result.corrupted_images} corrupted")
            if category_name and keyword:
                logger.info(f"Processed {category_name}/{keyword}")

        except Exception as e:
            error_msg = f"Failed to check integrity: {e}"
            if category_name and keyword:
                error_msg = f"Failed to check integrity for {category_name}/{keyword}: {e}"
                
            logger.error(error_msg)
            result.errors.append(error_msg)
            self.stats.failed_checks += 1

            if self.config.mode == CheckMode.STRICT:
                raise ValueError(error_msg) from e

        finally:
            result.processing_time = time.time() - start_time
            self.stats.total_checks += 1

            # Record processing history
            self.stats.processing_history.append({
                'operation': 'integrity_check',
                'category': category_name,
                'keyword': keyword,
                'success': not result.errors,
                'processing_time': result.processing_time,
                'images_processed': result.total_images,
                'valid_images': result.valid_images,
                'corrupted_images': result.corrupted_images
            })

        return result

    def check_all(self, directory: str, expected_count: int = 0,
                  category_name: str = "", keyword: str = "") -> Tuple[DuplicateResult, IntegrityResult]:
        """
        Perform both duplicate and integrity checks in sequence.

        Args:
            directory: Path to the directory to check
            expected_count: Expected number of valid images
            category_name: Name of the category (for reporting)
            keyword: Keyword being processed (for reporting)

        Returns:
            Tuple[DuplicateResult, IntegrityResult]: Results of both checks
        """
        logger.info(f"Starting comprehensive validation")
        if category_name and keyword:
            logger.info(f"Processing {category_name}/{keyword}")

        # Check duplicates first
        duplicate_result = self.check_duplicates(directory, category_name, keyword)

        # Then check integrity
        integrity_result = self.check_integrity(directory, expected_count, category_name, keyword)

        return duplicate_result, integrity_result

    def _update_duplicate_statistics(self, result: DuplicateResult, category_name: str, keyword: str):
        """Update statistics after duplicate check"""
        self.stats.total_duplicates_found += result.duplicates_found
        self.stats.total_duplicates_removed += result.duplicates_removed
        if category_name:
            self.stats.categories_processed.add(category_name)
        if keyword:
            self.stats.keywords_processed.add(keyword)
        self.stats.successful_checks += 1

    def reset_stats(self) -> None:
        """Reset validation statistics"""
        self.stats = CheckStats()

    def update_config(self, **kwargs) -> None:
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Unknown configuration parameter: {key}")

    def get_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of all validation operations"""
        return {
            'total_checks': self.stats.total_checks,
            'success_rate': (self.stats.successful_checks / self.stats.total_checks
                             if self.stats.total_checks > 0 else 0),
            'categories_processed': len(self.stats.categories_processed),
            'keywords_processed': len(self.stats.keywords_processed),
            'total_duplicates_found': self.stats.total_duplicates_found,
            'total_duplicates_removed': self.stats.total_duplicates_removed,
            'total_corrupted_found': self.stats.total_corrupted_found,
            'duplicate_removal_rate': (self.stats.total_duplicates_removed /
                                       self.stats.total_duplicates_found
                                       if self.stats.total_duplicates_found > 0 else 0),
            'processing_history': self.stats.processing_history
        }

    def get_stats(self) -> CheckStats:
        """Get current validation statistics"""
        return self.stats