import os
import time

import time
from typing import Optional, List, TextIO

from constants import logger


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
        print("\n" + "=" * 60)
        print("DATASET GENERATION SUMMARY")
        print("=" * 60)

        # Download statistics
        print(f"\n📥 IMAGE DOWNLOAD STATISTICS:")
        print(f"  ✅ Successful downloads: {self.download_successes}")
        print(f"  ❌ Failed downloads: {self.download_failures}")

        if self.failed_downloads:
            print(f"\n  📋 Download Failures:")
            for failure in self.failed_downloads:
                print(f"    • {failure}")

        # Integrity check results
        if self.integrity_failures:
            print(f"\n🔍 INTEGRITY CHECK FAILURES:")
            for failure in self.integrity_failures:
                print(f"  📁 {failure['context']}:")
                print(f"    Expected: {failure['expected']} images")
                print(f"    Valid: {failure['actual']} images")
                if failure['corrupted_files']:
                    print(f"    Corrupted files:")
                    for corrupted in failure['corrupted_files']:
                        print(f"      • {corrupted}")

        # Overall success rate
        total_operations = self.download_successes + self.download_failures
        if total_operations > 0:
            success_rate = (self.download_successes / total_operations) * 100
            print(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")

        print("=" * 60)

class ReportGenerator:
    """Class to track and generate a markdown report about dataset generation."""

    def __init__(self, output_dir: str):
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
        for item in self.sections["summary"]:
            f.write(f"- {item}\n")
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

        if data["original"]:
            f.write("**Original Keywords:**\n")
            for kw in data["original"]:
                f.write(f"- {kw}\n")
            f.write("\n")

        if data["generated"]:
            f.write("**Generated Keywords:**\n")
            for kw in data["generated"]:
                f.write(f"- {kw}\n")
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

        category_attempted = 0
        category_downloaded = 0
        category_duplicates = 0

        for keyword, data in keywords.items():
            keyword_stats = self._write_download_keyword(f, keyword, data)
            category_attempted += keyword_stats["attempted"]
            category_downloaded += keyword_stats["downloaded"]
            category_duplicates += keyword_stats["duplicates"]

        f.write(
            f"**Category Stats:** {category_downloaded}/{category_attempted} images downloaded, {category_duplicates} duplicates removed\n\n")

        return {
            "attempted": category_attempted,
            "downloaded": category_downloaded,
            "duplicates": category_duplicates
        }

    @staticmethod
    def _write_download_keyword(f: TextIO, keyword: str, data: dict) -> dict:
        """Write a single download keyword and return its statistics."""
        f.write(f"**Keyword: {keyword}**\n")

        attempted = 0
        downloaded = 0
        duplicates = 0

        if "attempted" in data and "downloaded" in data:
            f.write(f"- Downloaded: {data['downloaded']} / {data['attempted']} images\n")
            attempted = data['attempted']
            downloaded = data['downloaded']

        if "duplicates" in data:
            dup_data = data["duplicates"]
            f.write(
                f"- Duplicates: {dup_data['duplicates_removed']} removed, {dup_data['unique_kept']} unique images kept\n")
            duplicates = dup_data['duplicates_removed']

        if "errors" in data and data["errors"]:
            f.write("- Errors:\n")
            for error in data["errors"]:
                f.write(f"  - {error}\n")

        f.write("\n")

        return {
            "attempted": attempted,
            "downloaded": downloaded,
            "duplicates": duplicates
        }

    @staticmethod
    def _write_download_totals(f: TextIO, total_stats: dict) -> None:
        """Write the overall download statistics."""
        f.write(
            f"**Overall Download Stats:** {total_stats['downloaded']}/{total_stats['attempted']} images downloaded, {total_stats['duplicates']} duplicates removed\n\n")

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

        category_expected = 0
        category_valid = 0
        category_corrupted = 0

        for keyword, data in keywords.items():
            keyword_stats = self._write_integrity_keyword(f, keyword, data)
            category_expected += keyword_stats["expected"]
            category_valid += keyword_stats["valid"]
            category_corrupted += keyword_stats["corrupted"]

        f.write(
            f"**Category Integrity:** {category_valid}/{category_expected} valid images, {category_corrupted} corrupted\n\n")

        return {
            "expected": category_expected,
            "valid": category_valid,
            "corrupted": category_corrupted
        }

    def _write_integrity_keyword(self, f: TextIO, keyword: str, data: dict) -> dict:
        """Write a single integrity keyword and return its statistics."""
        f.write(f"**Keyword: {keyword}**\n")
        f.write(f"- Expected: {data['expected']} images\n")
        f.write(f"- Valid: {data['valid']} images\n")
        f.write(f"- Corrupted: {data['corrupted_count']} images\n")

        if data["corrupted_files"]:
            self._write_corrupted_files(f, data["corrupted_files"])

        f.write("\n")

        return {
            "expected": data['expected'],
            "valid": data['valid'],
            "corrupted": data['corrupted_count']
        }

    @staticmethod
    def _write_corrupted_files(f: TextIO, corrupted_files: list) -> None:
        """Write the list of corrupted files."""
        f.write("- Corrupted files:\n")
        for corrupt_file in corrupted_files[:5]:  # Show just first 5
            f.write(f"  - {os.path.basename(corrupt_file)}\n")
        if len(corrupted_files) > 5:
            f.write(f"  - ... and {len(corrupted_files) - 5} more\n")

    @staticmethod
    def _write_integrity_totals(f: TextIO, total_stats: dict) -> None:
        """Write the overall integrity statistics."""
        f.write(
            f"**Overall Integrity:** {total_stats['valid']}/{total_stats['expected']} valid images, {total_stats['corrupted']} corrupted\n\n")

    def _write_errors(self, f: TextIO) -> None:
        """Write the errors section."""
        if not self.sections["errors"]:
            return

        f.write("## Errors\n\n")
        for error in self.sections["errors"]:
            f.write(f"**Error:** {error['context']}\n")
            f.write(f"  - {error['error']}\n")
            f.write(f"  - Timestamp: {error['timestamp']}\n\n")

        logger.info(f"Report generated at {self.report_file}")

