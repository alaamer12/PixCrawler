"""
Backend progress tracking and caching module for PixCrawler.

This module handles progress tracking, caching, and dataset management
that was previously in the builder package.

Classes:
    ProgressCache: Manages progress caching for dataset generation
    DatasetTracker: Tracks dataset generation progress and outcomes
    ProgressManager: Manages centralized progress tracking

Functions:
    load_progress: Load progress from cache file
    save_progress: Save progress to cache file
"""

import json
import os
import time
from typing import Any, Dict, Optional, List

from utility.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_CACHE_FILE = "progress_cache.json"

__all__ = [
    'ProgressCache',
    'DatasetTracker',
    'ProgressManager',
    'load_progress',
    'save_progress'
]


class ProgressCache:
    """
    Manages the caching of progress for dataset generation, allowing the process
    to be resumed from where it left off in case of interruption.
    """

    def __init__(self, cache_file: str = DEFAULT_CACHE_FILE):
        """
        Initializes the ProgressCache.

        Args:
            cache_file (str): The path to the JSON file used for caching progress.
        """
        self.cache_file: str = cache_file
        self.completed_paths: Dict[str, Dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads the progress cache from the specified cache file.
        If the file does not exist or an error occurs during loading, an empty dictionary is returned.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary representing the loaded cache.
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load progress cache: {e}")
                return {}
        return {}

    def save_cache(self) -> None:
        """
        Saves the current progress cache to the cache file.
        """
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.completed_paths, f, indent=2)
            logger.debug(f"Progress cache saved to {self.cache_file}")
        except IOError as ioe:
            logger.error(f"Failed to save progress cache: {ioe}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while saving progress cache: {e}")

    def is_completed(self, category: str, keyword: str) -> bool:
        """
        Checks if a specific category/keyword combination has already been marked as completed.

        Args:
            category (str): The category name.
            keyword (str): The keyword name.

        Returns:
            bool: True if the combination is found in the completed paths, False otherwise.
        """
        path_key = f"{category}/{keyword}"
        return path_key in self.completed_paths

    def mark_completed(self, category: str, keyword: str,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Marks a specific category/keyword combination as completed and stores optional metadata.
        The cache is saved immediately after marking to ensure persistence.

        Args:
            category (str): The category name.
            keyword (str): The keyword name.
            metadata (Optional[Dict[str, Any]]): Optional dictionary of metadata to store with the completion record.
        """
        path_key = f"{category}/{keyword}"
        self.completed_paths[path_key] = {
            "timestamp": time.time(),
            "category": category,
            "keyword": keyword,
            "metadata": metadata or {}
        }
        # Save after each update to ensure progress is not lost
        self.save_cache()

    def get_completion_stats(self) -> Dict[str, int]:
        """
        Retrieves statistics about the completion progress.

        Returns:
            Dict[str, int]: A dictionary containing 'total_completed' (number of completed items)
                            and 'categories' (number of unique categories completed).
        """
        return {
            "total_completed": len(self.completed_paths),
            "categories": len(
                set(item["category"] for item in self.completed_paths.values()))
        }

    def clear_cache(self) -> None:
        """Clear all cached progress."""
        self.completed_paths.clear()
        self.save_cache()

    def remove_completed(self, category: str, keyword: str) -> bool:
        """
        Remove a specific completion record.

        Args:
            category (str): The category name.
            keyword (str): The keyword name.

        Returns:
            bool: True if the record was removed, False if it didn't exist.
        """
        path_key = f"{category}/{keyword}"
        if path_key in self.completed_paths:
            del self.completed_paths[path_key]
            self.save_cache()
            return True
        return False


class DatasetTracker:
    """
    A class to track the progress and various outcomes of the dataset generation process.
    It records successful and failed downloads, as well as image integrity issues.
    """

    def __init__(self):
        """
        Initializes the DatasetTracker with counters for download successes and failures,
        and lists to store details of integrity failures and failed downloads.
        """
        self.download_successes: int = 0
        self.download_failures: int = 0
        self.integrity_failures: List[dict] = []
        self.failed_downloads: List[str] = []
        self.start_time: float = time.time()

    def record_download_success(self, context: str, count: int = 1) -> None:
        """
        Records successful image downloads.

        Args:
            context (str): A string describing the context of the successful download (e.g., keyword).
            count (int): Number of successful downloads to record.
        """
        self.download_successes += count
        logger.debug(f"Recorded {count} successful downloads for {context}")

    def record_download_failure(self, context: str, error: str) -> None:
        """
        Records a failed image download.

        Args:
            context (str): A string describing the context of the failed download.
            error (str): The error message associated with the failure.
        """
        self.download_failures += 1
        self.failed_downloads.append(f"{context}: {error}")
        logger.warning(f"Download failure recorded for {context}: {error}")

    def record_integrity_failure(self, context: str, expected: int, actual: int,
                                 corrupted: List[str]) -> None:
        """
        Records an image integrity check failure.

        Args:
            context (str): A string describing the context of the integrity check.
            expected (int): The number of images expected to be valid.
            actual (int): The number of images actually found to be valid.
            corrupted (List[str]): A list of file paths of corrupted images.
        """
        self.integrity_failures.append({
            'context': context,
            'expected': expected,
            'actual': actual,
            'corrupted_files': corrupted
        })
        logger.warning(
            f"Integrity failure recorded for {context}: {actual}/{expected} valid images")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of tracking statistics.

        Returns:
            Dict[str, Any]: Summary statistics
        """
        total_operations = self.download_successes + self.download_failures
        success_rate = (
            self.download_successes / total_operations * 100) if total_operations > 0 else 0

        return {
            'download_successes': self.download_successes,
            'download_failures': self.download_failures,
            'success_rate': success_rate,
            'integrity_failures': len(self.integrity_failures),
            'failed_downloads': len(self.failed_downloads),
            'duration': time.time() - self.start_time
        }

    def print_summary(self) -> None:
        """
        Prints a comprehensive summary of the dataset generation process,
        including download statistics and integrity check results.
        """
        self._print_header()

        # Download statistics
        self.print_statistics()

        if self.failed_downloads:
            logger.info(f"\n  📋 Download Failures:")
            self._print_failed_downloads()

        # Integrity check results
        if self.integrity_failures:
            logger.info(f"\n🔍 INTEGRITY CHECK FAILURES:")
            self._print_integrity_failures()

        # Overall success rate
        total_operations = self.download_successes + self.download_failures
        if total_operations > 0:
            success_rate = (self.download_successes / total_operations) * 100
            logger.info(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")

        logger.info("=" * 60)

    @staticmethod
    def _print_header() -> None:
        logger.info("\n" + "=" * 60)
        logger.info("DATASET GENERATION SUMMARY")
        logger.info("=" * 60)

    def print_statistics(self) -> None:
        logger.info(f"\n📥 IMAGE DOWNLOAD STATISTICS:")
        logger.info(f"  ✅ Successful downloads: {self.download_successes}")
        logger.info(f"  ❌ Failed downloads: {self.download_failures}")

    def _print_failed_downloads(self) -> None:
        for failure in self.failed_downloads:
            logger.info(f"    • {failure}")

    def _print_integrity_failures(self) -> None:
        for failure in self.integrity_failures:
            logger.info(f"  📁 {failure['context']}:")
            logger.info(f"    Expected: {failure['expected']} images")
            logger.info(f"    Valid: {failure['actual']} images")
            if failure['corrupted_files']:
                logger.info(f"    Corrupted files:")
                for corrupted in failure['corrupted_files']:
                    logger.info(f"      • {corrupted}")

    def reset(self) -> None:
        """Reset all tracking counters."""
        self.download_successes = 0
        self.download_failures = 0
        self.integrity_failures.clear()
        self.failed_downloads.clear()
        self.start_time = time.time()


class ProgressManager:
    """
    Manages centralized progress tracking for dataset generation processes.
    """

    def __init__(self, cache_file: str = DEFAULT_CACHE_FILE):
        """
        Initialize the progress manager.

        Args:
            cache_file (str): Path to the progress cache file.
        """
        self.cache = ProgressCache(cache_file)
        self.tracker = DatasetTracker()

    def is_completed(self, category: str, keyword: str) -> bool:
        """Check if a category/keyword combination is completed."""
        return self.cache.is_completed(category, keyword)

    def mark_completed(self, category: str, keyword: str,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark a category/keyword combination as completed."""
        self.cache.mark_completed(category, keyword, metadata)

    def record_success(self, context: str, count: int = 1) -> None:
        """Record successful downloads."""
        self.tracker.record_download_success(context, count)

    def record_failure(self, context: str, error: str) -> None:
        """Record download failures."""
        self.tracker.record_download_failure(context, error)

    def record_integrity_issue(self, context: str, expected: int,
                               actual: int, corrupted: List[str]) -> None:
        """Record integrity check failures."""
        self.tracker.record_integrity_failure(context, expected, actual, corrupted)

    def get_stats(self) -> Dict[str, Any]:
        """Get combined statistics."""
        cache_stats = self.cache.get_completion_stats()
        tracker_stats = self.tracker.get_summary()

        return {
            'cache': cache_stats,
            'tracker': tracker_stats,
            'combined': {
                'total_completed': cache_stats['total_completed'],
                'success_rate': tracker_stats['success_rate'],
                'duration': tracker_stats['duration']
            }
        }

    def print_summary(self) -> None:
        """Print comprehensive progress summary."""
        self.tracker.print_summary()

        # Add cache statistics
        cache_stats = self.cache.get_completion_stats()
        logger.info(f"\n📊 PROGRESS CACHE STATISTICS:")
        logger.info(f"  ✅ Completed items: {cache_stats['total_completed']}")
        logger.info(f"  📁 Categories processed: {cache_stats['categories']}")

    def reset(self) -> None:
        """Reset all progress tracking."""
        self.cache.clear_cache()
        self.tracker.reset()


# Convenience functions
def load_progress(cache_file: str = DEFAULT_CACHE_FILE) -> Dict[str, Dict[str, Any]]:
    """
    Load progress from cache file.

    Args:
        cache_file (str): Path to cache file

    Returns:
        Dict containing cached progress
    """
    cache = ProgressCache(cache_file)
    return cache.completed_paths


def save_progress(progress_data: Dict[str, Dict[str, Any]],
                  cache_file: str = DEFAULT_CACHE_FILE) -> None:
    """
    Save progress to cache file.

    Args:
        progress_data (Dict): Progress data to save
        cache_file (str): Path to cache file
    """
    cache = ProgressCache(cache_file)
    cache.completed_paths = progress_data
    cache.save_cache()
