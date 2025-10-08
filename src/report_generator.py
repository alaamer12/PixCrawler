"""
Report generation module for PixCrawler.

This module provides comprehensive report generation functionality for dataset generation
processes. It was moved from the builder package to maintain clean separation of concerns.

Classes:
    ReportGenerator: Tracks and generates markdown reports about dataset generation

Features:
    - Comprehensive tracking of dataset generation progress
    - Markdown report generation with tables and sections
    - Keyword generation tracking and reporting
    - Download statistics and error reporting
    - Detailed timestamp and duration tracking
"""

import os
import time
from typing import Optional, List, TextIO

from logging_config import get_logger

logger = get_logger(__name__)

__all__ = ['ReportGenerator']


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
            dict: A dictionary containing total attempted and downloaded counts.
        """
        total_attempted = 0
        total_downloaded = 0

        for category, keywords in self.sections["downloads"].items():
            category_stats = self._write_download_category(f, category, keywords)
            total_attempted += category_stats["attempted"]
            total_downloaded += category_stats["downloaded"]

        return {
            "attempted": total_attempted,
            "downloaded": total_downloaded
        }

    def _write_download_category(self, f: TextIO, category: str, keywords: dict) -> dict:
        """
        Writes a single download category's details to the report, including keyword-specific statistics.

        Args:
            f (TextIO): The file object to write to.
            category (str): The name of the download category.
            keywords (dict): A dictionary where keys are keywords and values are their download data.

        Returns:
            dict: A dictionary containing attempted and downloaded counts for the category.
        """
        f.write(f"### Category: {category}\n\n")

        # Create a table for keywords in this category
        f.write("| Keyword | Downloaded | Attempted | Success Rate |\n")
        f.write("|---------|------------|-----------|--------------|\n")

        category_attempted = 0
        category_downloaded = 0

        for keyword, data in keywords.items():
            keyword_stats = self._write_download_keyword_table_row(f, keyword, data)
            category_attempted += keyword_stats["attempted"]
            category_downloaded += keyword_stats["downloaded"]

            # Write any errors for this keyword
            if "errors" in data and data["errors"]:
                f.write(f"\n**Errors for {keyword}:**\n\n")
                for error in data["errors"]:
                    f.write(f"- {error}\n")

        f.write("\n")
        f.write(f"**Category Stats:** {category_downloaded}/{category_attempted} images downloaded\n\n")

        return {
            "attempted": category_attempted,
            "downloaded": category_downloaded
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
            dict: A dictionary containing attempted and downloaded counts for the keyword.
        """
        attempted = data.get('attempted', 0)
        downloaded = data.get('downloaded', 0)
        success_rate = f"{(downloaded / attempted * 100):.1f}%" if attempted > 0 else "N/A"

        # Write the table row
        f.write(f"| {keyword} | {downloaded} | {attempted} | {success_rate} |\n")

        return {
            "attempted": attempted,
            "downloaded": downloaded
        }

    @staticmethod
    def _write_download_totals(f: TextIO, total_stats: dict) -> None:
        """
        Writes the overall download statistics to the report.

        Args:
            f (TextIO): The file object to write to.
            total_stats (dict): A dictionary containing overall download statistics.
        """
        success_rate = f"{(total_stats['downloaded'] / total_stats['attempted'] * 100):.1f}%" if total_stats['attempted'] > 0 else "N/A"

        f.write("### Overall Download Statistics\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total Attempted | {total_stats['attempted']} |\n")
        f.write(f"| Total Downloaded | {total_stats['downloaded']} |\n")
        f.write(f"| Success Rate | {success_rate} |\n")
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
