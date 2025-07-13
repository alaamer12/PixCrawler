"""
Helper classes and utilities for the PixCrawler dataset generator.

This module provides helper classes for tracking dataset generation progress,
generating reports, and handling file system operations like renaming files.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Optional, List, TextIO, Any, Union, Callable
from tqdm.auto import tqdm
from constants import logger, IMAGE_EXTENSIONS

__all__ = [
    'DatasetTracker',
    'ReportGenerator',
    'FSRenamer',
    'ProgressManager'
]


class DatasetTracker:
    """Class to track dataset generation progress and issues"""

    def __init__(self):
        self.download_successes = 0
        self.download_failures = 0
        self.integrity_failures = []
        self.failed_downloads = []

    def record_download_success(self, context: str):
        self.download_successes += 1

    def record_download_failure(self, context: str, error: str):
        self.download_failures += 1
        self.failed_downloads.append(f"{context}: {error}")

    def record_integrity_failure(self, context: str, expected: int, actual: int, corrupted: List[str]):
        self.integrity_failures.append({
            'context': context,
            'expected': expected,
            'actual': actual,
            'corrupted_files': corrupted
        })

    def print_summary(self):
        """Print comprehensive summary of dataset generation"""
        logger.info("\n" + "=" * 60)
        logger.info("DATASET GENERATION SUMMARY")
        logger.info("=" * 60)

        # Download statistics
        logger.info(f"\n📥 IMAGE DOWNLOAD STATISTICS:")
        logger.info(f"  ✅ Successful downloads: {self.download_successes}")
        logger.info(f"  ❌ Failed downloads: {self.download_failures}")

        if self.failed_downloads:
            logger.info(f"\n  📋 Download Failures:")
            for failure in self.failed_downloads:
                logger.info(f"    • {failure}")

        # Integrity check results
        if self.integrity_failures:
            logger.info(f"\n🔍 INTEGRITY CHECK FAILURES:")
            for failure in self.integrity_failures:
                logger.info(f"  📁 {failure['context']}:")
                logger.info(f"    Expected: {failure['expected']} images")
                logger.info(f"    Valid: {failure['actual']} images")
                if failure['corrupted_files']:
                    logger.info(f"    Corrupted files:")
                    for corrupted in failure['corrupted_files']:
                        logger.info(f"      • {corrupted}")

        # Overall success rate
        total_operations = self.download_successes + self.download_failures
        if total_operations > 0:
            success_rate = (self.download_successes / total_operations) * 100
            logger.info(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")

        logger.info("=" * 60)


class ReportGenerator:
    """
    Class to track and generate a markdown report about dataset generation.
    
    This class collects information during the dataset generation process
    and produces a well-structured markdown report with tables and sections
    for better readability.
    """

    def __init__(self, output_dir: str):
        """
        Initialize the report generator with an output directory.
        
        Args:
            output_dir: Directory where the report will be saved
        """
        self.output_dir = output_dir
        self.report_file = os.path.join(output_dir, "REPORT.md")
        self.sections = {
            "summary": [],
            "keywords": {},
            "downloads": {},
            "integrity": {},
            "errors": []
        }
        self.start_time = time.time()

    def add_summary(self, message: str) -> None:
        """Add a summary message to the report."""
        self.sections["summary"].append(message)

    def record_keyword_generation(self, category: str, original_keywords: List[str],
                                  generated_keywords: List[str], model: str) -> None:
        """Record information about keyword generation."""
        if category not in self.sections["keywords"]:
            self.sections["keywords"][category] = {
                "original": original_keywords,
                "generated": generated_keywords,
                "model": model
            }

    def record_download(self, category: str, keyword: str,
                        success: bool, count: int,
                        attempted: int, errors: Optional[List[str]] = None) -> None:
        """Record information about downloads."""
        if category not in self.sections["downloads"]:
            self.sections["downloads"][category] = {}

        self.sections["downloads"][category][keyword] = {
            "success": success,
            "downloaded": count,
            "attempted": attempted,
            "errors": errors or []
        }

    def record_duplicates(self, category: str, keyword: str,
                          total: int, duplicates: int, kept: int) -> None:
        """Record information about duplicate detection."""
        if category not in self.sections["downloads"]:
            self.sections["downloads"][category] = {}

        if keyword not in self.sections["downloads"][category]:
            self.sections["downloads"][category][keyword] = {}

        self.sections["downloads"][category][keyword]["duplicates"] = {
            "total": total,
            "duplicates_removed": duplicates,
            "unique_kept": kept
        }

    def record_integrity(self, category: str, keyword: str,
                         expected: int, actual: int,
                         corrupted: Optional[List[str]] = None) -> None:
        """Record information about integrity checks."""
        if category not in self.sections["integrity"]:
            self.sections["integrity"][category] = {}

        self.sections["integrity"][category][keyword] = {
            "expected": expected,
            "valid": actual,
            "corrupted_count": len(corrupted or []),
            "corrupted_files": corrupted or []
        }

    def record_error(self, context: str, error: str) -> None:
        """Record an error in the report."""
        self.sections["errors"].append({
            "context": context,
            "error": error,
            "timestamp": time.time()
        })

    def generate(self) -> None:
        """Generate the final markdown report."""
        duration = time.time() - self.start_time

        with open(self.report_file, "w", encoding="utf-8") as f:
            self._write_header(f, duration)
            self._write_summary(f)
            self._write_keyword_generation(f)
            self._write_downloads(f)
            self._write_integrity(f)
            self._write_errors(f)

        logger.info(f"Report generated at {self.report_file}")

    @staticmethod
    def _write_header(f: TextIO, duration: float) -> None:
        """Write the report header with timestamp and duration."""
        f.write("# PixCrawler Dataset Generation Report\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration: {duration:.2f} seconds ({duration / 60:.2f} minutes)\n\n")

    def _write_summary(self, f: TextIO) -> None:
        """Write the summary section."""
        f.write("## Summary\n\n")

        # Create a table for summary items
        f.write("| Parameter | Value |\n")
        f.write("|-----------|-------|\n")
        for item in self.sections["summary"]:
            if ":" in item:
                param, value = item.split(":", 1)
                f.write(f"| {param.strip()} | {value.strip()} |\n")
            else:
                f.write(f"| Info | {item} |\n")
        f.write("\n")

    def _write_keyword_generation(self, f: TextIO) -> None:
        """Write the keyword generation section."""
        if not self.sections["keywords"]:
            return

        f.write("## Keyword Generation\n\n")
        for category, data in self.sections["keywords"].items():
            self._write_keyword_category(f, category, data)

    @staticmethod
    def _write_keyword_category(f: TextIO, category: str, data: dict) -> None:
        """Write a single keyword category."""
        f.write(f"### Category: {category}\n\n")
        f.write(f"AI Model used: {data['model']}\n\n")

        # Create a table comparing original and generated keywords
        f.write("| Original Keywords | Generated Keywords |\n")
        f.write("|------------------|-------------------|\n")

        # Get the maximum length of both lists
        max_length = max(len(data["original"]), len(data["generated"]))

        # Fill in the table rows
        for i in range(max_length):
            original = data["original"][i] if i < len(data["original"]) else ""
            generated = data["generated"][i] if i < len(data["generated"]) else ""
            f.write(f"| {original} | {generated} |\n")

        f.write("\n")

    def _write_downloads(self, f: TextIO) -> None:
        """Write the downloads section."""
        if not self.sections["downloads"]:
            return

        f.write("## Downloads\n\n")
        total_stats = self._write_download_categories(f)
        self._write_download_totals(f, total_stats)

    def _write_download_categories(self, f: TextIO) -> dict:
        """Write all download categories and return total statistics."""
        total_attempted = 0
        total_downloaded = 0
        total_duplicates = 0

        for category, keywords in self.sections["downloads"].items():
            category_stats = self._write_download_category(f, category, keywords)
            total_attempted += category_stats["attempted"]
            total_downloaded += category_stats["downloaded"]
            total_duplicates += category_stats["duplicates"]

        return {
            "attempted": total_attempted,
            "downloaded": total_downloaded,
            "duplicates": total_duplicates
        }

    def _write_download_category(self, f: TextIO, category: str, keywords: dict) -> dict:
        """Write a single download category and return its statistics."""
        f.write(f"### Category: {category}\n\n")

        # Create a table for keywords in this category
        f.write("| Keyword | Downloaded | Attempted | Success Rate | Duplicates Removed | Unique Images |\n")
        f.write("|---------|------------|-----------|--------------|-------------------|---------------|\n")

        category_attempted = 0
        category_downloaded = 0
        category_duplicates = 0

        for keyword, data in keywords.items():
            keyword_stats = self._write_download_keyword_table_row(f, keyword, data)
            category_attempted += keyword_stats["attempted"]
            category_downloaded += keyword_stats["downloaded"]
            category_duplicates += keyword_stats["duplicates"]

            # Write any errors for this keyword
            if "errors" in data and data["errors"]:
                f.write(f"\n**Errors for {keyword}:**\n\n")
                for error in data["errors"]:
                    f.write(f"- {error}\n")

        f.write("\n")
        f.write(
            f"**Category Stats:** {category_downloaded}/{category_attempted} images downloaded, {category_duplicates} duplicates removed\n\n")

        return {
            "attempted": category_attempted,
            "downloaded": category_downloaded,
            "duplicates": category_duplicates
        }

    @staticmethod
    def _write_download_keyword_table_row(f: TextIO, keyword: str, data: dict) -> dict:
        """Write a single keyword as a table row and return its statistics."""
        attempted = data.get('attempted', 0)
        downloaded = data.get('downloaded', 0)
        success_rate = f"{(downloaded / attempted * 100):.1f}%" if attempted > 0 else "N/A"

        duplicates_removed = 0
        unique_kept = 0

        if "duplicates" in data:
            dup_data = data["duplicates"]
            duplicates_removed = dup_data.get('duplicates_removed', 0)
            unique_kept = dup_data.get('unique_kept', 0)

        # Write the table row
        f.write(f"| {keyword} | {downloaded} | {attempted} | {success_rate} | {duplicates_removed} | {unique_kept} |\n")

        return {
            "attempted": attempted,
            "downloaded": downloaded,
            "duplicates": duplicates_removed
        }

    @staticmethod
    def _write_download_totals(f: TextIO, total_stats: dict) -> None:
        """Write the overall download statistics."""
        success_rate = f"{(total_stats['downloaded'] / total_stats['attempted'] * 100):.1f}%" if total_stats[
                                                                                                     'attempted'] > 0 else "N/A"

        f.write("### Overall Download Statistics\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total Attempted | {total_stats['attempted']} |\n")
        f.write(f"| Total Downloaded | {total_stats['downloaded']} |\n")
        f.write(f"| Success Rate | {success_rate} |\n")
        f.write(f"| Duplicates Removed | {total_stats['duplicates']} |\n")
        f.write("\n")

    def _write_integrity(self, f: TextIO) -> None:
        """Write the integrity checks section."""
        if not self.sections["integrity"]:
            return

        f.write("## Integrity Checks\n\n")
        total_stats = self._write_integrity_categories(f)
        self._write_integrity_totals(f, total_stats)

    def _write_integrity_categories(self, f: TextIO) -> dict:
        """Write all integrity categories and return total statistics."""
        total_expected = 0
        total_valid = 0
        total_corrupted = 0

        for category, keywords in self.sections["integrity"].items():
            category_stats = self._write_integrity_category(f, category, keywords)
            total_expected += category_stats["expected"]
            total_valid += category_stats["valid"]
            total_corrupted += category_stats["corrupted"]

        return {
            "expected": total_expected,
            "valid": total_valid,
            "corrupted": total_corrupted
        }

    def _write_integrity_category(self, f: TextIO, category: str, keywords: dict) -> dict:
        """Write a single integrity category and return its statistics."""
        f.write(f"### Category: {category}\n\n")

        # Create a table for integrity results
        f.write("| Keyword | Expected Images | Valid Images | Corrupted Images | Integrity Rate |\n")
        f.write("|---------|-----------------|--------------|------------------|---------------|\n")

        category_expected = 0
        category_valid = 0
        category_corrupted = 0

        for keyword, data in keywords.items():
            keyword_stats = self._write_integrity_keyword_table_row(f, keyword, data)
            category_expected += keyword_stats["expected"]
            category_valid += keyword_stats["valid"]
            category_corrupted += keyword_stats["corrupted"]

            # List corrupted files if any
            if data["corrupted_files"]:
                self._write_corrupted_files(f, data["corrupted_files"])

        f.write("\n")
        integrity_rate = f"{(category_valid / category_expected * 100):.1f}%" if category_expected > 0 else "N/A"
        f.write(
            f"**Category Integrity:** {category_valid}/{category_expected} valid images ({integrity_rate}), {category_corrupted} corrupted\n\n")

        return {
            "expected": category_expected,
            "valid": category_valid,
            "corrupted": category_corrupted
        }

    @staticmethod
    def _write_integrity_keyword_table_row(f: TextIO, keyword: str, data: dict) -> dict:
        """Write a single keyword integrity as a table row and return its statistics."""
        expected = data['expected']
        valid = data['valid']
        corrupted = data['corrupted_count']
        integrity_rate = f"{(valid / expected * 100):.1f}%" if expected > 0 else "N/A"

        # Write the table row
        f.write(f"| {keyword} | {expected} | {valid} | {corrupted} | {integrity_rate} |\n")

        return {
            "expected": expected,
            "valid": valid,
            "corrupted": corrupted
        }

    @staticmethod
    def _write_corrupted_files(f: TextIO, corrupted_files: list) -> None:
        """Write the list of corrupted files."""
        if not corrupted_files:
            return

        f.write("\n<details>\n")
        f.write("<summary>Corrupted Files (Click to expand)</summary>\n\n")

        for corrupt_file in corrupted_files[:10]:  # Show just first 10
            f.write(f"- {os.path.basename(corrupt_file)}\n")
        if len(corrupted_files) > 10:
            f.write(f"- ... and {len(corrupted_files) - 10} more\n")

        f.write("</details>\n\n")

    @staticmethod
    def _write_integrity_totals(f: TextIO, total_stats: dict) -> None:
        """Write the overall integrity statistics."""
        integrity_rate = f"{(total_stats['valid'] / total_stats['expected'] * 100):.1f}%" if total_stats[
                                                                                                 'expected'] > 0 else "N/A"

        f.write("### Overall Integrity Statistics\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total Expected | {total_stats['expected']} |\n")
        f.write(f"| Total Valid | {total_stats['valid']} |\n")
        f.write(f"| Integrity Rate | {integrity_rate} |\n")
        f.write(f"| Total Corrupted | {total_stats['corrupted']} |\n")
        f.write("\n")

    def _write_errors(self, f: TextIO) -> None:
        """Write the errors section."""
        if not self.sections["errors"]:
            return

        f.write("## Errors\n\n")

        # Create a table for errors
        f.write("| Context | Error | Timestamp |\n")
        f.write("|---------|-------|----------|\n")

        for error in self.sections["errors"]:
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(error['timestamp']))
            f.write(f"| {error['context']} | {error['error']} | {timestamp_str} |\n")

        f.write("\n")
        logger.info(f"Report generated at {self.report_file}")


class FSRenamer:
    """
    A self-encapsulated class for renaming image files sequentially.
    
    This class handles the complete process of renaming image files in a directory
    to a sequential, zero-padded format while maintaining data integrity through
    temporary directory operations.
    """

    def __init__(self, directory: str):
        """
        Initialize the FSRenamer with a target directory.

        Args:
            directory: Directory containing images to rename
        """
        self.directory_path = Path(directory)
        self.temp_dir: Optional[Path] = None
        self.image_files: List[Path] = []
        self.padding_width: int = 0

    def rename_sequentially(self) -> int:
        """
        Rename all image files in the directory to a sequential, zero-padded format.
        
        Returns:
            int: Number of renamed files
        """
        if not self._validate_directory_exists():
            return 0

        self.image_files = self._get_sorted_image_files()

        if not self.image_files:
            logger.warning(f"No image files found in {self.directory_path}")
            return 0

        self.temp_dir = self._create_temp_directory()
        self.padding_width = self._calculate_padding_width(len(self.image_files))

        renamed_count = self._copy_files_to_temp_with_new_names()

        self._delete_original_files()
        self._move_files_from_temp_to_original()
        self._cleanup_temp_directory()

        logger.info(f"Renamed {renamed_count} images in {self.directory_path} with sequential numbering")
        return renamed_count

    def _validate_directory_exists(self) -> bool:
        """Validate that the directory exists."""
        if not self.directory_path.exists():
            logger.warning(f"Directory {self.directory_path} does not exist")
            return False
        return True

    def _get_sorted_image_files(self) -> List[Path]:
        """Get all image files sorted by creation time."""
        image_files = [
            f for f in self.directory_path.iterdir()
            if f.is_file() and is_valid_image_extension(f)
        ]
        image_files.sort(key=lambda x: os.path.getctime(x))
        return image_files

    def _create_temp_directory(self) -> Path:
        """Create a temporary directory for renaming operations."""
        temp_dir = self.directory_path / ".temp_rename"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir

    @staticmethod
    def _calculate_padding_width(file_count: int) -> int:
        """Calculate the padding width for sequential numbering."""
        return max(3, len(str(file_count)))

    def _copy_files_to_temp_with_new_names(self) -> int:
        """Copy files to temp directory with new sequential names."""
        renamed_count = 0

        for i, file_path in enumerate(self.image_files, 1):
            extension = file_path.suffix.lower()
            new_filename = f"{i:0{self.padding_width}d}{extension}"
            temp_path = self.temp_dir / new_filename

            try:
                shutil.copy2(file_path, temp_path)
                renamed_count += 1
                # Log progress every 10 files
                if renamed_count % 10 == 0 or renamed_count == len(self.image_files):
                    logger.debug(f"Renamed {renamed_count}/{len(self.image_files)} images")
            except Exception as e:
                logger.error(f"Failed to copy {file_path} to temp directory: {e}")

        return renamed_count

    def _delete_original_files(self) -> None:
        """Delete original image files."""
        for file_path in self.image_files:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Failed to delete original file {file_path}: {e}")

    def _move_files_from_temp_to_original(self) -> None:
        """Move files from temp directory back to original directory."""
        if not self.temp_dir:
            return

        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                try:
                    shutil.move(str(file_path), str(self.directory_path / file_path.name))
                except Exception as e:
                    logger.error(f"Failed to move {file_path} from temp directory: {e}")

    def _cleanup_temp_directory(self) -> None:
        """Remove the temporary directory."""
        if not self.temp_dir:
            return

        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"Failed to remove temp directory: {e}")


class ProgressManager:
    """
    Centralized progress bar manager for the dataset generation process.
    
    This class provides a consistent interface for displaying progress bars
    across different steps of the dataset generation pipeline, ensuring clear
    visibility of the current stage while removing terminal logging.
    """

    def __init__(self):
        """Initialize the progress manager."""
        try:
            # Import here to handle potential import errors gracefully
            self.tqdm = tqdm
        except ImportError:
            # Fallback to a simple progress indicator if tqdm is not available
            self.tqdm = self._dummy_tqdm
            logger.warning("tqdm not available, using simple progress indicators")

        self.current_progress = None
        self.nested_progress = None

        # Step definitions with descriptions
        self.steps = {
            "init": "Initializing PixCrawler",
            "download": "Downloading Images",
            "integrity": "Checking integrity",
            "labels": "Generating labels",
            "report": "Generating report",
            "finalizing": "Finalizing"
        }

        # Step colors (if terminal supports it)
        self.colors = {
            "init": "blue",
            "download": "green",
            "integrity": "yellow",
            "labels": "magenta",
            "report": "cyan",
            "finalizing": "white"
        }

    def start_step(self, step: str, total: Optional[int] = None) -> None:
        """
        Start a new main progress step.
        
        Args:
            step: Step identifier (must be one of the predefined steps)
            total: Total units for this step (if applicable)
        """
        if step not in self.steps:
            logger.warning(f"Unknown progress step: {step}")
            desc = f"Processing {step}"
        else:
            desc = f"[{step.upper()}] {self.steps[step]}"

        # Close any existing progress bars
        self.close()

        # Ensure we have a valid total (use 1 as default if None is provided)
        # This prevents the TypeError when checking if self.current_progress evaluates to True
        if total is None:
            total = 1

        # Create new progress bar
        self.current_progress = self.tqdm(
            total=total,
            desc=desc,
            colour=self.colors.get(step, "white"),
            leave=True,
            position=0,
            dynamic_ncols=True
        )

    def update_step(self, n: int = 1) -> None:
        """
        Update the current main progress step.
        
        Args:
            n: Number of units to increment by
        """
        if self.current_progress is not None and hasattr(self.current_progress, 'update'):
            self.current_progress.update(n)

    def set_step_description(self, desc: str) -> None:
        """
        Update the description of the current main step.
        
        Args:
            desc: New description text
        """
        if self.current_progress is not None and hasattr(self.current_progress, 'set_description_str'):
            self.current_progress.set_description_str(desc)

    def set_step_postfix(self, **kwargs) -> None:
        """
        Update postfix text of the current main step.
        
        Args:
            **kwargs: Key-value pairs to display
        """
        if self.current_progress is not None and hasattr(self.current_progress, 'set_postfix'):
            self.current_progress.set_postfix(**kwargs)

    def start_subtask(self, desc: str, total: Optional[int] = None) -> None:
        """
        Start a nested progress bar for subtasks.
        
        Args:
            desc: Description of the subtask
            total: Total units for this subtask
        """
        # Close any existing nested progress bar
        if self.nested_progress:
            self.nested_progress.close()

        # Ensure we have a valid total (use 1 as default if None is provided)
        if total is None:
            total = 1

        # Create new nested progress bar
        self.nested_progress = self.tqdm(
            total=total,
            desc=f"  └─ {desc}",
            leave=False,
            position=1,
            dynamic_ncols=True
        )

    def update_subtask(self, n: int = 1) -> None:
        """
        Update the current subtask progress.
        
        Args:
            n: Number of units to increment by
        """
        if self.nested_progress is not None and hasattr(self.nested_progress, 'update'):
            self.nested_progress.update(n)

    def set_subtask_description(self, desc: str) -> None:
        """
        Update the description of the current subtask.
        
        Args:
            desc: New description text
        """
        if self.nested_progress is not None and hasattr(self.nested_progress, 'set_description_str'):
            self.nested_progress.set_description_str(f"  └─ {desc}")

    def set_subtask_postfix(self, **kwargs) -> None:
        """
        Update postfix text of the current subtask.
        
        Args:
            **kwargs: Key-value pairs to display
        """
        if self.nested_progress is not None and hasattr(self.nested_progress, 'set_postfix'):
            self.nested_progress.set_postfix(**kwargs)

    def close_subtask(self) -> None:
        """Close the current subtask progress bar."""
        if self.nested_progress is not None and hasattr(self.nested_progress, 'close'):
            self.nested_progress.close()
            self.nested_progress = None

    def close(self) -> None:
        """Close all progress bars."""
        self.close_subtask()
        if self.current_progress is not None and hasattr(self.current_progress, 'close'):
            self.current_progress.close()
            self.current_progress = None

    def _dummy_tqdm(self, *args, **kwargs):
        """Simple progress indicator for fallback if tqdm not available."""

        class DummyTqdm:
            def __init__(self):
                self.n = 0
                self.total = kwargs.get('total', 100)  # Default total

            def update(self, n=1):
                self.n += n
                print(f"\r{kwargs.get('desc', 'Progress')}: {self.n}/{self.total}", end="")

            @staticmethod
            def set_description_str(desc):
                print(f"\r{desc}", end="")

            def set_postfix(self, **kwargs):
                postfix = ' '.join(f"{k}={v}" for k, v in kwargs.items())
                print(f"\r{kwargs.get('desc', 'Progress')}: {self.n}/{self.total} {postfix}", end="")

            @staticmethod
            def close():
                print()

            def __bool__(self):
                # Always return True to avoid TypeError in bool() check
                return True

        return DummyTqdm()

    def iterate(self, iterable: Any, desc: str = None, total: Optional[int] = None,
                subtask: bool = False, unit: str = "it") -> Any:
        """
        Iterate over an iterable with a progress bar.
        
        Args:
            iterable: Any iterable object
            desc: Description for the progress bar
            total: Total number of items (inferred if not provided)
            subtask: Whether this is a subtask or main task
            unit: Unit label for the progress bar
            
        Returns:
            Iterator with progress tracking
        """
        progress_method: Union[Callable[[int], None], bool] = self.update_subtask if subtask else self.update_step
        tqdm_instance = self.nested_progress if subtask else self.current_progress

        # If we have an active progress bar, use it
        if tqdm_instance:
            if desc:
                if subtask:
                    self.set_subtask_description(desc)
                else:
                    self.set_step_description(desc)

            # Yield from the iterable and update progress
            for item in iterable:
                yield item
                progress_method(1)
        else:
            # Create a new progress bar for this iteration
            with self.tqdm(iterable, desc=desc, total=total, unit=unit) as pbar:
                for item in pbar:
                    yield item


# Create a global progress manager
progress = ProgressManager()


def is_valid_image_extension(file_path: Union[str, Path]) -> bool:
    """
    Check if a file has a valid image extension.

    Args:
        file_path: Path to check

    Returns:
        bool: True if valid image extension, False otherwise
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    return file_path.suffix.lower() in IMAGE_EXTENSIONS
