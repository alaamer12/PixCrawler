"""
This module provides helper classes and utilities for the PixCrawler dataset generator. It includes functionalities for tracking dataset generation progress, generating comprehensive reports, handling file system operations like sequential renaming of images, and managing interactive progress bars for a better user experience.

Classes:
    DatasetTracker: Tracks the progress and various outcomes of the dataset generation process.
    ReportGenerator: Tracks and generates a markdown report about dataset generation.
    FSRenamer: Renames image files sequentially within a specified directory.
    ProgressManager: Manages centralized progress bars for the dataset generation process.

Functions:
    is_valid_image_extension: Checks if a file has a valid image extension.

Features:
    - Comprehensive tracking of download successes, failures, and integrity issues.
    - Generation of detailed markdown reports for dataset generation summaries.
    - Robust file system operations for renaming and organizing image files.
    - Interactive progress bars for real-time feedback during long-running operations.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Optional, List, TextIO, Any, Union, Callable
from tqdm.auto import tqdm
from constants import logger, IMAGE_EXTENSIONS
from _exceptions import PixCrawlerError

__all__ = [
    'DatasetTracker',
    'ReportGenerator',
    'FSRenamer',
    'ProgressManager',
    'valid_image_ext'
]


def valid_image_ext(file_path: Union[str, Path]) -> bool:
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

    def record_download_success(self, context: str) -> None:
        """
        Records a successful image download.

        Args:
            context (str): A string describing the context of the successful download (e.g., keyword).
        """

    def record_download_failure(self, context: str, error: str) -> None:
        """
        Records a failed image download.

        Args:
            context (str): A string describing the context of the failed download.
            error (str): The error message associated with the failure.
        """
        self.download_failures += 1
        self.failed_downloads.append(f"{context}: {error}")

    def record_integrity_failure(self, context: str, expected: int, actual: int, corrupted: List[str]) -> None:
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
            self._print_integrity_filures()

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

    def _print_integrity_filures(self) -> None:
        for failure in self.integrity_failures:
            logger.info(f"  📁 {failure['context']}:")
            logger.info(f"    Expected: {failure['expected']} images")
            logger.info(f"    Valid: {failure['actual']} images")
            if failure['corrupted_files']:
                logger.info(f"    Corrupted files:")
                for corrupted in failure['corrupted_files']:
                    logger.info(f"      • {corrupted}")


class ReportGenerator:
    """
    Class to track and generate a markdown report about dataset generation.
    
    This class collects information during the dataset generation process
    and produces a well-structured markdown report with tables and sections
    for better readability.
    """

    def __init__(self, output_dir: str):
        """
        Initializes the ReportGenerator.

        Args:
            output_dir (str): The directory where the report will be saved.
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
        """
        Adds a summary message to the report.

        Args:
            message (str): The summary message to add.
        """
        self.sections["summary"].append(message)

    def record_keyword_generation(self, category: str, original_keywords: List[str],
                                  generated_keywords: List[str], model: str) -> None:
        """
        Records information about keyword generation.

        Args:
            category (str): The category of keyword generation (e.g., 'initial', 'expanded').
            original_keywords (List[str]): A list of original keywords.
            generated_keywords (List[str]): A list of newly generated keywords.
            model (str): The AI model used for generation.
        """
        if category not in self.sections["keywords"]:
            self.sections["keywords"][category] = {
                "original": original_keywords,
                "generated": generated_keywords,
                "model": model
            }

    def record_download(self, category: str, keyword: str,
                        success: bool, count: int,
                        attempted: int, errors: Optional[List[str]] = None) -> None:
        """
        Records information about image downloads for a specific keyword and category.

        Args:
            category (str): The category of the download (e.g., 'main', 'fallback').
            keyword (str): The keyword associated with the download.
            success (bool): True if the download was successful, False otherwise.
            count (int): The number of images downloaded.
            attempted (int): The number of images attempted to download.
            errors (Optional[List[str]]): A list of error messages, if any.
        """
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
        """
        Records information about duplicate image detection and removal.

        Args:
            category (str): The category of the download (e.g., 'main', 'fallback').
            keyword (str): The keyword associated with the images.
            total (int): The total number of images before duplicate removal.
            duplicates (int): The number of duplicate images removed.
            kept (int): The number of unique images kept.
        """
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
        """
        Records information about image integrity checks.

        Args:
            category (str): The category of the integrity check.
            keyword (str): The keyword associated with the images.
            expected (int): The number of images expected to be valid.
            actual (int): The number of images actually found to be valid.
            corrupted (Optional[List[str]]): A list of corrupted file paths, if any.
        """
        if category not in self.sections["integrity"]:
            self.sections["integrity"][category] = {}

        self.sections["integrity"][category][keyword] = {
            "expected": expected,
            "valid": actual,
            "corrupted_count": len(corrupted or []),
            "corrupted_files": corrupted or []
        }

    def record_error(self, context: str, error: str) -> None:
        """
        Records an error that occurred during the dataset generation process.

        Args:
            context (str): The context in which the error occurred.
            error (str): The error message.
        """
        self.sections["errors"].append({
            "context": context,
            "error": error,
            "timestamp": time.time()
        })

    def generate(self) -> None:
        """
        Generates the final markdown report and saves it to the specified output directory.
        This method orchestrates the writing of all sections of the report.
        """
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
        """
        Writes the header section of the markdown report, including generation timestamp and duration.

        Args:
            f (TextIO): The file object to write to.
            duration (float): The total duration of the dataset generation process in seconds.
        """
        f.write("# PixCrawler Dataset Generation Report\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration: {duration:.2f} seconds ({duration / 60:.2f} minutes)\n\n")

    def _write_summary(self, f: TextIO) -> None:
        """
        Writes the summary section of the markdown report.

        Args:
            f (TextIO): The file object to write to.
        """
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
        """
        Writes the keyword generation section of the markdown report.

        Args:
            f (TextIO): The file object to write to.
        """
        if not self.sections["keywords"]:
            return

        f.write("## Keyword Generation\n\n")
        for category, data in self.sections["keywords"].items():
            self._write_keyword_category(f, category, data)

    @staticmethod
    def _write_keyword_category(f: TextIO, category: str, data: dict) -> None:
        """
        Writes a single keyword category's details to the report, including original and generated keywords.

        Args:
            f (TextIO): The file object to write to.
            category (str): The category name (e.g., 'initial', 'expanded').
            data (dict): A dictionary containing keyword generation data for the category.
        """
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
        """
        Writes the downloads section of the markdown report, including detailed statistics for each category.

        Args:
            f (TextIO): The file object to write to.
        """
        if not self.sections["downloads"]:
            return

        f.write("## Downloads\n\n")
        total_stats = self._write_download_categories(f)
        self._write_download_totals(f, total_stats)

    def _write_download_categories(self, f: TextIO) -> dict:
        """
        Writes all download categories to the report and calculates total download statistics.

        Args:
            f (TextIO): The file object to write to.

        Returns:
            dict: A dictionary containing total attempted, downloaded, and duplicate counts.
        """
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
        """
        Writes a single download category's details to the report, including keyword-specific statistics.

        Args:
            f (TextIO): The file object to write to.
            category (str): The name of the download category.
            keywords (dict): A dictionary where keys are keywords and values are their download data.

        Returns:
            dict: A dictionary containing attempted, downloaded, and duplicate counts for the category.
        """
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
        """
        Writes a single keyword's download statistics as a table row in the report.

        Args:
            f (TextIO): The file object to write to.
            keyword (str): The keyword for which to write statistics.
            data (dict): A dictionary containing download data for the keyword.

        Returns:
            dict: A dictionary containing attempted, downloaded, and duplicate counts for the keyword.
        """
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
        """
        Writes the overall download statistics to the report.

        Args:
            f (TextIO): The file object to write to.
            total_stats (dict): A dictionary containing overall download statistics.
        """
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
        """
        Writes the integrity checks section of the markdown report.

        Args:
            f (TextIO): The file object to write to.
        """
        if not self.sections["integrity"]:
            return

        f.write("## Integrity Checks\n\n")
        total_stats = self._write_integrity_categories(f)
        self._write_integrity_totals(f, total_stats)

    def _write_integrity_categories(self, f: TextIO) -> dict:
        """
        Writes all integrity categories to the report and calculates total integrity statistics.

        Args:
            f (TextIO): The file object to write to.

        Returns:
            dict: A dictionary containing total expected, valid, and corrupted image counts.
        """
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
        """
        Writes a single integrity category's details to the report, including keyword-specific statistics.

        Args:
            f (TextIO): The file object to write to.
            category (str): The name of the integrity category.
            keywords (dict): A dictionary where keys are keywords and values are their integrity data.

        Returns:
            dict: A dictionary containing expected, valid, and corrupted counts for the category.
        """
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
        """
        Writes a single keyword's integrity statistics as a table row in the report.

        Args:
            f (TextIO): The file object to write to.
            keyword (str): The keyword for which to write statistics.
            data (dict): A dictionary containing integrity data for the keyword.

        Returns:
            dict: A dictionary containing expected, valid, and corrupted counts for the keyword.
        """
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
    def _write_corrupted_files(f: TextIO, corrupted_files: List[str]) -> None:
        """
        Writes a collapsible list of corrupted files to the report.

        Args:
            f (TextIO): The file object to write to.
            corrupted_files (List[str]): A list of file paths of corrupted images.
        """
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
        """
        Writes the overall integrity statistics to the report.

        Args:
            f (TextIO): The file object to write to.
            total_stats (dict): A dictionary containing overall integrity statistics.
        """
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
        """
        Writes the errors section of the markdown report.

        Args:
            f (TextIO): The file object to write to.
        """
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
    A self-encapsulated class for renaming image files sequentially within a specified directory.
    It handles the complete process of renaming image files to a sequential, zero-padded format
    while maintaining data integrity through temporary directory operations.
    """

    def __init__(self, directory: str, padding_width: Optional[int] = None):
        """
        Initializes the FSRenamer with the target directory.

        Args:
            directory (str): The path to the directory containing images to rename.
            padding_width (Optional[int]): The desired width for zero-padding sequential filenames.
                                          If None, it will be calculated based on the number of files (min 3).
        """
        self.directory_path = Path(directory)
        self.temp_dir: Optional[Path] = None
        self.image_files: List[Path] = []
        self._user_defined_padding_width = padding_width
        self.padding_width: int = 0

    def rename_sequentially(self) -> int:
        """
        Renames all image files in the initialized directory to a sequential, zero-padded format.
        This process involves copying files to a temporary directory with new names, deleting
        original files, moving the renamed files back, and cleaning up the temporary directory.

        Returns:
            int: The number of files successfully renamed.
        """
        if not self._validate_directory_exists():
            return 0

        self.image_files = self._get_sorted_image_files()

        if not self.image_files:
            logger.warning(f"No image files found in {self.directory_path}")
            return 0

        self.temp_dir = self._create_temp_directory()
        self.padding_width = self._user_defined_padding_width if self._user_defined_padding_width is not None else self._calculate_padding_width(len(self.image_files))

        renamed_count = self._copy_files_to_temp_with_new_names()

        self._delete_original_files()
        self._move_files_from_temp_to_original()
        self._cleanup_temp_directory()

        logger.info(f"Renamed {renamed_count} images in {self.directory_path} with sequential numbering")
        return renamed_count

    def _validate_directory_exists(self) -> bool:
        """
        Validates that the target directory for renaming exists.

        Returns:
            bool: True if the directory exists, False otherwise.
        """
        if not self.directory_path.exists():
            logger.warning(f"Directory {self.directory_path} does not exist")
            return False
        return True

    def _get_sorted_image_files(self) -> List[Path]:
        """
        Retrieves a sorted list of image files within the target directory.
        Files are sorted by their creation time.

        Returns:
            List[Path]: A list of Path objects representing the image files.
        """
        image_files = [
            f for f in self.directory_path.iterdir()
            if f.is_file() and valid_image_ext(f)
        ]
        # Sort by filename to maintain any existing sequential order
        image_files.sort(key=lambda x: x.name)
        return image_files

    def _create_temp_directory(self) -> Path:
        """
        Creates a temporary directory within the target directory for renaming operations.

        Returns:
            Path: The path to the created temporary directory.
        """
        temp_dir = self.directory_path / ".temp_rename"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir

    @staticmethod
    def _calculate_padding_width(file_count: int) -> int:
        """
        Calculates the necessary padding width for sequential numbering based on the total file count.

        Args:
            file_count (int): The total number of files to be renamed.

        Returns:
            int: The calculated padding width (e.g., 3 for up to 999 files, 4 for up to 9999 files).
        """
        return max(3, len(str(file_count)))

    def _copy_files_to_temp_with_new_names(self) -> int:
        """
        Copies image files from the original directory to the temporary directory with new sequential names.

        Returns:
            int: The number of files successfully copied and renamed.
        """
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
            except IOError as ioe:
                logger.error(f"Failed to copy {file_path} to temp directory: {ioe}")
                raise PixCrawlerError(f"Failed to copy {file_path} to temp directory: {ioe}") from ioe
            except Exception as e:
                logger.error(f"An unexpected error occurred while copying {file_path} to temp directory: {e}")
                raise PixCrawlerError(f"Unexpected error copying {file_path} to temp directory: {e}") from e

        return renamed_count

    def _delete_original_files(self) -> None:
        """
        Deletes the original image files from the target directory after they have been copied and renamed.
        """
        for file_path in self.image_files:
            try:
                os.remove(file_path)
            except OSError as ose:
                logger.error(f"Failed to delete original file {file_path}: {ose}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while deleting original file {file_path}: {e}")

    def _move_files_from_temp_to_original(self) -> None:
        """
        Moves the sequentially renamed files from the temporary directory back to the original directory.
        """
        if not self.temp_dir:
            return

        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                try:
                    shutil.move(str(file_path), str(self.directory_path / file_path.name))
                except IOError as ioe:
                    logger.error(f"Failed to move {file_path} from temp directory: {ioe}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred while moving {file_path} from temp directory: {e}")

    def _cleanup_temp_directory(self) -> None:
        """
        Removes the temporary directory created during the renaming process.
        """
        if not self.temp_dir:
            return

        try:
            shutil.rmtree(self.temp_dir)
        except OSError as ose:
            logger.error(f"Failed to remove temp directory: {ose}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while removing temp directory: {e}")


class ProgressManager:
    """
    Centralized progress bar manager for the dataset generation process.
    This class provides a consistent interface for displaying progress bars
    across different steps of the dataset generation pipeline, ensuring clear
    visibility of the current stage while removing terminal logging.
    """

    def __init__(self):
        """
        Initializes the ProgressManager, setting up tqdm for progress bars
        or a dummy fallback if tqdm is not available. Defines main steps and their colors.
        """
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
        Starts a new main progress step with a description and an optional total count.

        Args:
            step (str): The identifier for the current step (e.g., 'download', 'integrity').
            total (Optional[int]): The total number of units for this step. If None, defaults to 1.
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
        Updates the current main progress step by incrementing its progress.

        Args:
            n (int): The number of units to increment the progress by (default is 1).
        """
        if self.current_progress is not None and hasattr(self.current_progress, 'update'):
            self.current_progress.update(n)

    def set_step_description(self, desc: str) -> None:
        """
        Updates the description of the current main progress step.

        Args:
            desc (str): The new description text for the step.
        """
        if self.current_progress is not None and hasattr(self.current_progress, 'set_description_str'):
            self.current_progress.set_description_str(desc)

    def set_step_postfix(self, **kwargs: Any) -> None:
        """
        Updates the postfix text of the current main progress step.

        Args:
            **kwargs (Any): Arbitrary keyword arguments to display as postfix (e.g., count=10, total=100).
        """
        if self.current_progress is not None and hasattr(self.current_progress, 'set_postfix'):
            self.current_progress.set_postfix(**kwargs)

    def start_subtask(self, desc: str, total: Optional[int] = None) -> None:
        """
        Starts a nested progress bar for subtasks, displayed below the main progress bar.

        Args:
            desc (str): The description of the subtask.
            total (Optional[int]): The total number of units for this subtask. If None, defaults to 1.
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
        Updates the current subtask progress by incrementing its progress.

        Args:
            n (int): The number of units to increment the progress by (default is 1).
        """
        if self.nested_progress is not None and hasattr(self.nested_progress, 'update'):
            self.nested_progress.update(n)

    def set_subtask_description(self, desc: str) -> None:
        """
        Updates the description of the current subtask.

        Args:
            desc (str): The new description text for the subtask.
        """
        if self.nested_progress is not None and hasattr(self.nested_progress, 'set_description_str'):
            self.nested_progress.set_description_str(f"  └─ {desc}")

    def set_subtask_postfix(self, **kwargs: Any) -> None:
        """
        Updates the postfix text of the current subtask.

        Args:
            **kwargs (Any): Arbitrary keyword arguments to display as postfix.
        """
        if self.nested_progress is not None and hasattr(self.nested_progress, 'set_postfix'):
            self.nested_progress.set_postfix(**kwargs)

    def close_subtask(self) -> None:
        """
        Closes the current subtask progress bar.
        """
        if self.nested_progress is not None and hasattr(self.nested_progress, 'close'):
            self.nested_progress.close()
            self.nested_progress = None

    def close(self) -> None:
        """
        Closes all active progress bars (both main and nested).
        """
        self.close_subtask()
        if self.current_progress is not None and hasattr(self.current_progress, 'close'):
            self.current_progress.close()
            self.current_progress = None

    def _dummy_tqdm(self, *args: Any, **kwargs: Any) -> Any:
        """
        A dummy tqdm implementation used as a fallback when the `tqdm` library is not available.
        It provides basic progress indication to the console.

        Args:
            *args (Any): Positional arguments passed to tqdm.
            **kwargs (Any): Keyword arguments passed to tqdm.

        Returns:
            Any: An instance of DummyTqdm that mimics tqdm's behavior.
        """

        class DummyTqdm:
            """
            A simple dummy class that mimics the behavior of tqdm for basic progress indication.
            Used when the `tqdm` library is not installed.
            """

            def __init__(self):
                """
                Initializes the DummyTqdm instance.
                """
                self.n = 0
                self.total = kwargs.get('total', 100)  # Default total

            def update(self, n: int = 1) -> None:
                """
                Updates the progress by incrementing the counter.

                Args:
                    n (int): The number of units to increment by (default is 1).
                """
                self.n += n
                print(f"{kwargs.get('desc', 'Progress')}: {self.n}/{self.total}", end="")

            @staticmethod
            def set_description_str(desc: str) -> None:
                """
                Sets the description string for the progress indicator.

                Args:
                    desc (str): The description text.
                """
                print(f"{desc}", end="")

            def set_postfix(self, **kwargs: Any) -> None:
                """
                Sets the postfix text for the progress indicator.

                Args:
                    **kwargs (Any): Arbitrary keyword arguments to display as postfix.
                """
                postfix = ' '.join(f"{k}={v}" for k, v in kwargs.items())
                print(f"{kwargs.get('desc', 'Progress')}: {self.n}/{self.total} {postfix}", end="")

            @staticmethod
            def close() -> None:
                """
                Closes the progress indicator, printing a newline.
                """
                print()

            def __bool__(self) -> bool:
                """
                Returns True to ensure the DummyTqdm instance is treated as truthy.
                """
                # Always return True to avoid TypeError in bool() check
                return True

        return DummyTqdm()

    def iterate(self, iterable: Any, desc: Optional[str] = None, total: Optional[int] = None,
                subtask: bool = False, unit: str = "it") -> Any:
        """
        Iterates over an iterable while displaying a progress bar.

        Args:
            iterable (Any): The iterable object to iterate over.
            desc (Optional[str]): A description for the progress bar.
            total (Optional[int]): The total number of items in the iterable. If None, it's inferred.
            subtask (bool): If True, uses a nested progress bar for a subtask.
            unit (str): The unit label for the progress bar (e.g., "it", "files").

        Returns:
            Any: An iterator that yields items from the iterable while updating the progress bar.
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
