import argparse
import contextlib
import json
import logging
import os
import random
import shutil
import signal
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union, TextIO

import g4f
import jsonschema
import requests
from PIL import Image
from duckduckgo_search import DDGS
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler
from jsonschema import validate
from tqdm.auto import tqdm

from config import DatasetGenerationConfig, CONFIG_SCHEMA
from constants import DEFAULT_CACHE_FILE, DEFAULT_CONFIG_FILE, DEFAULT_LOG_FILE, ENGINES, IMAGE_EXTENSIONS, \
    console_handler, file_formatter
from constants import logger
from helpers import remove_duplicate_images, ProgressCache, TimeoutException, detect_duplicate_images


@contextmanager
def timeout_context(seconds: float):
    """Context manager for timeout operations"""

    def timeout_handler(signum, frame):
        raise TimeoutException(f"Operation timed out after {seconds} seconds")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(seconds))

    try:
        yield
    finally:
        # Restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class Report:
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


def _apply_config_options(config: DatasetGenerationConfig, options: Dict[str, Any]) -> None:
    """
    Apply configuration options from config file to the configuration object.
    
    This function selectively overrides default configuration values with values
    from the config file, but only when CLI arguments haven't explicitly set them.
    
    Args:
        config: The configuration object to modify
        options: Dictionary containing configuration options from config file
    """
    config_mappings = {
        'max_images': (config.max_images == 10, lambda: options.get('max_images')),
        'output_dir': (config.output_dir is None, lambda: options.get('output_dir')),
        'integrity': (config.integrity is True, lambda: options.get('integrity')),
        'max_retries': (config.max_retries == 5, lambda: options.get('max_retries')),
        'cache_file': (config.cache_file == DEFAULT_CACHE_FILE, lambda: options.get('cache_file')),
        'keyword_generation': (config.keyword_generation == "auto", lambda: options.get('keyword_generation')),
        'ai_model': (config.ai_model == "gpt4-mini", lambda: options.get('ai_model'))
    }

    for option_name, (should_apply, value_getter) in config_mappings.items():
        if should_apply and option_name in options:
            new_value = value_getter()
            setattr(config, option_name, new_value)
            logger.info(f"Applied {option_name}={new_value} from config file")


def validate_image(image_path: str) -> bool:
    """
    Validate if an image file is not corrupted using Pillow.

    Args:
        image_path: Path to the image file

    Returns:
        bool: True if image is valid, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            img.verify()  # Verify image integrity

            # Additional check for very small or empty images
            if img.width < 50 or img.height < 50:
                logger.warning(f"Image too small: {image_path} ({img.width}x{img.height})")
                return False

        return True
    except Exception as e:
        logger.error(f"Corrupted image detected: {image_path} - {str(e)}")
        return False


def count_valid_images(directory: str) -> Tuple[int, int, List[str]]:
    """
    Count valid and invalid images in a directory.

    Args:
        directory: Directory path to check

    Returns:
        Tuple of (valid_count, total_count, corrupted_files)
    """
    valid_count = 0
    total_count = 0
    corrupted_files = []

    directory_path = Path(directory)
    if not directory_path.exists():
        return 0, 0, []

    for file_path in tqdm(directory_path.iterdir(), desc="Validating", leave=False, unit="file"):
        if file_path.is_file() and is_valid_image_extension(file_path):
            total_count += 1
            if validate_image(str(file_path)):
                valid_count += 1
            else:
                corrupted_files.append(str(file_path))

    return valid_count, total_count, corrupted_files


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


class DuckDuckGoImageDownloader:
    """
    A class to download images using DuckDuckGo search as a fallback mechanism.
    """

    def __init__(self):
        """Initialize the downloader with default settings."""
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.timeout = 20
        self.min_file_size = 1000  # bytes
        self.delay = 0.5  # seconds between downloads

    def _get_image(self, image_url: str, file_path: str) -> bool:
        """
        Download a single image from URL and save it to file path.
        
        Args:
            image_url: URL of the image to download
            file_path: Path where to save the image
            
        Returns:
            bool: True if download was successful, False otherwise
        """
        try:
            # First try with verification
            response = requests.get(
                image_url,
                timeout=self.timeout,
                verify=True,
                headers={'User-Agent': self.user_agent}
            )

            # Retry without SSL verification if it fails with verification
            if response.status_code != 200:
                logger.warning(
                    f"Initial request failed with status {response.status_code}. Retrying without SSL verification.")
                response = requests.get(
                    image_url,
                    timeout=self.timeout,
                    verify=False,
                    headers={'User-Agent': self.user_agent}
                )

            response.raise_for_status()

            # Check content type and file size before saving
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"Skipping non-image content type: {content_type}")
                return False

            if len(response.content) < self.min_file_size:
                logger.warning(f"Skipping too small image ({len(response.content)} bytes)")
                return False

            with open(file_path, "wb") as f:
                f.write(response.content)

            # Validate the downloaded image
            if validate_image(file_path):
                return True
            else:
                # Remove corrupted image
                try:
                    os.remove(file_path)
                    logger.warning(f"Removed corrupted image: {file_path}")
                except Exception:
                    pass
                return False

        except Exception as e:
            logger.warning(f"Failed to download {image_url}: {e}")
            return False

    def _search_and_download(self, keyword: str, out_dir: str, max_count: int, current_count: int = 0) -> int:
        """
        Search for images with a keyword and download them.
        
        Args:
            keyword: Search term
            out_dir: Output directory
            max_count: Maximum number of images to download
            current_count: Current count of downloaded images
            
        Returns:
            int: Number of successfully downloaded images
        """
        downloaded = current_count

        try:
            with DDGS() as ddgs:
                # Request more images than needed to account for failures
                results = list(ddgs.images(keyword, max_results=max_count * 3))
                logger.info(f"Found {len(results)} potential images for '{keyword}'")

                if not results:
                    return downloaded

                for i, result in enumerate(results):
                    if downloaded >= max_count:
                        break

                    image_url = result.get("image")
                    if not image_url:
                        continue

                    filename = f"{keyword.replace(' ', '_')}_{i + 1}.jpg"
                    file_path = os.path.join(out_dir, filename)

                    if self._get_image(image_url, file_path):
                        downloaded += 1
                        logger.info(f"Downloaded: {file_path} [{downloaded}/{max_count}]")

                    # Add small delay between downloads
                    time.sleep(self.delay)
        except Exception as e:
            logger.warning(f"Failed to search for keyword '{keyword}': {e}")

        return downloaded

    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """
        Download images using DuckDuckGo search.
        
        Args:
            keyword: Search term for images
            out_dir: Output directory path
            max_num: Maximum number of images to download
            
        Returns:
            Tuple of (success_flag, downloaded_count)
        """
        logger.warning("GoogleImageCrawler not available or had an error. Using DuckDuckGo image search instead.")

        try:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            downloaded_count = 0

            # Try with the original keyword first
            downloaded_count = self._search_and_download(keyword, out_dir, max_num)

            # Try additional search terms if we still don't have enough images
            if downloaded_count < max_num:
                alternate_keywords = [
                    f"{keyword} image",
                    f"{keyword} photo",
                    f"{keyword} high quality",
                    f"{keyword} closeup",
                    f"{keyword} detailed"
                ]

                for alt_keyword in alternate_keywords:
                    if downloaded_count >= max_num:
                        break

                    logger.info(f"Trying alternate keyword: '{alt_keyword}'")
                    remaining = max_num - downloaded_count

                    # The _search_and_download function will update our count
                    downloaded_count = self._search_and_download(
                        alt_keyword,
                        out_dir,
                        remaining,
                        downloaded_count
                    )

            return downloaded_count > 0, downloaded_count

        except Exception as e:
            logger.error(f"Failed to download images for '{keyword}': {str(e)}")
            return False, 0


def download_images_ddgs(keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
    """
    Download images using DuckDuckGo search as fallback if GoogleImageCrawler is not available.

    Args:
        keyword: Search term for images
        out_dir: Output directory path
        max_num: Maximum number of images to download

    Returns:
        Tuple of (success_flag, downloaded_count)
    """
    downloader = DuckDuckGoImageDownloader()
    return downloader.download(keyword, out_dir, max_num)


class ImageDownloader:
    """
    A class for downloading images using multiple image crawlers with fallbacks and random offsets.
    """

    def __init__(self,
                 feeder_threads: int = 1,
                 parser_threads: int = 1,
                 downloader_threads: int = 3,
                 min_image_size: Tuple[int, int] = (100, 100),
                 delay_between_searches: float = 1.0,
                 log_level: int = logging.WARNING):
        """
        Initialize the ImageDownloader with configurable parameters.

        Args:
            feeder_threads: Number of feeder threads for crawlers
            parser_threads: Number of parser threads for crawlers
            downloader_threads: Number of downloader threads for crawlers
            min_image_size: Minimum image size as (width, height) tuple
            delay_between_searches: Delay in seconds between different search terms
            log_level: Logging level for crawlers
        """
        self.feeder_threads = feeder_threads
        self.parser_threads = parser_threads
        self.downloader_threads = downloader_threads
        self.min_image_size = min_image_size
        self.delay_between_searches = delay_between_searches
        self.log_level = log_level

        # Define engine configurations
        self.engines = [
            {
                'name': 'google',
                'func': self._download_with_google,
                'offset_range': (0, 20),
                'variation_step': 20
            },
            {
                'name': 'bing',
                'func': self._download_with_bing,
                'offset_range': (0, 30),
                'variation_step': 10
            },
            {
                'name': 'baidu',
                'func': self._download_with_baidu,
                'offset_range': (10, 50),
                'variation_step': 15
            }
        ]

        # Search variations template
        self.search_variations = [
            "{keyword}",
            "{keyword} photo",
            "{keyword} high resolution"
        ]

    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """
        Download images using multiple image crawlers with fallbacks and random offsets.

        Args:
            keyword: Search term for images
            out_dir: Output directory path
            max_num: Maximum number of images to download

        Returns:
            Tuple of (success_flag, downloaded_count)
        """
        try:
            # Ensure output directory exists
            Path(out_dir).mkdir(parents=True, exist_ok=True)

            # Generate search variations
            variations = [template.format(keyword=keyword) for template in self.search_variations]

            total_downloaded = 0
            per_variation_limit = max(3, max_num // len(variations))

            # Try each engine in sequence
            for engine_config in self.engines:
                if total_downloaded >= max_num:
                    break

                total_downloaded = self._try_engine(
                    engine_config=engine_config,
                    variations=variations,
                    out_dir=out_dir,
                    max_num=max_num,
                    per_variation_limit=per_variation_limit,
                    total_downloaded=total_downloaded
                )

            # Fallback to DuckDuckGo if needed
            if total_downloaded < max_num:
                total_downloaded = self._try_duckduckgo_fallback(
                    keyword=keyword,
                    out_dir=out_dir,
                    max_num=max_num,
                    total_downloaded=total_downloaded
                )

            # Rename all files sequentially
            if total_downloaded > 0:
                rename_images_sequentially(out_dir)

            return total_downloaded > 0, total_downloaded

        except Exception as e:
            # Try fallback to DuckDuckGo
            logger.warning(f"All crawlers failed with error: {e}. Trying DuckDuckGo as fallback.")
            return self._final_duckduckgo_fallback(keyword, out_dir, max_num)

    @staticmethod
    def _try_engine(engine_config: dict, variations: List[str],
                    out_dir: str, max_num: int, per_variation_limit: int,
                    total_downloaded: int) -> int:
        """
        Try downloading images using the specified engine.

        Args:
            engine_config: Engine configuration dictionary
            variations: List of search term variations
            out_dir: Output directory
            max_num: Maximum number of images to download
            per_variation_limit: Maximum images per variation
            total_downloaded: Current download count

        Returns:
            Updated total downloaded count
        """
        engine_name = engine_config['name']
        download_func = engine_config['func']
        offset_min, offset_max = engine_config['offset_range']
        random_offset = random.randint(offset_min, offset_max)

        logger.info(f"Attempting download using {engine_name.capitalize()}ImageCrawler")
        try:
            total_downloaded = download_func(
                variations=variations,
                out_dir=out_dir,
                max_num=max_num - total_downloaded,
                per_variation_limit=per_variation_limit,
                total_downloaded=total_downloaded,
                offset=random_offset,
                variation_step=engine_config['variation_step']
            )
        except Exception as e:
            logger.warning(f"{engine_name.capitalize()}ImageCrawler failed: {e}")

        return total_downloaded

    @staticmethod
    def _try_duckduckgo_fallback(keyword: str, out_dir: str, max_num: int, total_downloaded: int) -> int:
        """
        Try DuckDuckGo as a fallback option when other engines haven't downloaded enough images.

        Args:
            keyword: Search term
            out_dir: Output directory
            max_num: Maximum number of images to download
            total_downloaded: Current download count

        Returns:
            Updated total downloaded count
        """
        logger.info(f"Crawlers downloaded {total_downloaded}/{max_num} images. Trying DuckDuckGo as fallback.")
        ddgs_success, ddgs_count = download_images_ddgs(
            keyword=keyword,
            out_dir=out_dir,
            max_num=max_num - total_downloaded
        )
        if ddgs_success:
            total_downloaded += ddgs_count

        return total_downloaded

    @staticmethod
    def _final_duckduckgo_fallback(keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """
        Final fallback to DuckDuckGo when all other methods have failed.

        Args:
            keyword: Search term
            out_dir: Output directory
            max_num: Maximum number of images to download

        Returns:
            Tuple of (success_flag, downloaded_count)
        """
        success, count = download_images_ddgs(keyword, out_dir, max_num)
        if success and count > 0:
            rename_images_sequentially(out_dir)
            return True, count
        else:
            logger.error(f"All download methods failed for '{keyword}'")
            return False, 0

    def _create_crawler(self, crawler_class, out_dir: str):
        """
        Create a crawler instance with the configured parameters.

        Args:
            crawler_class: The crawler class to instantiate
            out_dir: Output directory for the crawler

        Returns:
            Configured crawler instance
        """
        return crawler_class(
            storage={'root_dir': out_dir},
            log_level=self.log_level,
            feeder_threads=self.feeder_threads,
            parser_threads=self.parser_threads,
            downloader_threads=self.downloader_threads
        )

    def _download_with_crawler(self, crawler_class, variations: List[str], out_dir: str,
                               max_num: int, per_variation_limit: int, total_downloaded: int,
                               offset: int, variation_step: int, engine_name: str) -> int:
        """
        Generic helper function to download images using any crawler.

        Args:
            crawler_class: The crawler class to use
            variations: List of search term variations
            out_dir: Output directory
            max_num: Maximum number of images to download
            per_variation_limit: Maximum images per variation
            total_downloaded: Current download count
            offset: Random offset for search results
            variation_step: Step size for offset between variations
            engine_name: Name of the engine for logging

        Returns:
            Updated total downloaded count
        """
        for i, variation in enumerate(variations):
            if total_downloaded >= max_num:
                break

            # Calculate remaining images needed
            remaining = max_num - total_downloaded
            current_limit = min(remaining, per_variation_limit)
            current_offset = offset + (i * variation_step)

            logger.info(
                f"{engine_name}: Trying to download {current_limit} images with query: '{variation}' (offset: {current_offset})")

            try:
                crawler = self._create_crawler(crawler_class, out_dir)

                crawler.crawl(
                    keyword=variation,
                    max_num=current_limit,
                    min_size=self.min_image_size,
                    offset=current_offset,
                    file_idx_offset=total_downloaded
                )

                # Count valid images after this batch download
                temp_valid_count = count_valid_images_in_latest_batch(out_dir, total_downloaded)
                total_downloaded += temp_valid_count

                logger.info(
                    f"{engine_name} downloaded {temp_valid_count} valid images for '{variation}', total: {total_downloaded}/{max_num}")

                # Small delay between different search terms
                time.sleep(self.delay_between_searches)

            except Exception as e:
                logger.warning(f"{engine_name} crawler failed with query '{variation}': {e}")

        return total_downloaded

    def _download_with_google(self, variations: List[str], out_dir: str, max_num: int,
                              per_variation_limit: int, total_downloaded: int = 0,
                              offset: int = 0, variation_step: int = 20) -> int:
        """Helper function to download images using Google Image Crawler"""
        return self._download_with_crawler(
            GoogleImageCrawler, variations, out_dir, max_num,
            per_variation_limit, total_downloaded, offset, variation_step, "Google"
        )

    def _download_with_bing(self, variations: List[str], out_dir: str, max_num: int,
                            per_variation_limit: int, total_downloaded: int = 0,
                            offset: int = 0, variation_step: int = 10) -> int:
        """Helper function to download images using Bing Image Crawler"""
        return self._download_with_crawler(
            BingImageCrawler, variations, out_dir, max_num,
            per_variation_limit, total_downloaded, offset, variation_step, "Bing"
        )

    def _download_with_baidu(self, variations: List[str], out_dir: str, max_num: int,
                             per_variation_limit: int, total_downloaded: int = 0,
                             offset: int = 0, variation_step: int = 15) -> int:
        """Helper function to download images using Baidu Image Crawler"""
        return self._download_with_crawler(
            BaiduImageCrawler, variations, out_dir, max_num,
            per_variation_limit, total_downloaded, offset, variation_step, "Baidu"
        )

    def add_search_variation(self, variation_template: str):
        """
        Add a new search variation template.

        Args:
            variation_template: Template string with {keyword} placeholder
        """
        if variation_template not in self.search_variations:
            self.search_variations.append(variation_template)

    def remove_search_variation(self, variation_template: str):
        """
        Remove a search variation template.

        Args:
            variation_template: Template string to remove
        """
        if variation_template in self.search_variations:
            self.search_variations.remove(variation_template)

    def set_crawler_threads(self, feeder: int = None, parser: int = None, downloader: int = None):
        """
        Update crawler thread configuration.

        Args:
            feeder: Number of feeder threads
            parser: Number of parser threads
            downloader: Number of downloader threads
        """
        if feeder is not None:
            self.feeder_threads = feeder
        if parser is not None:
            self.parser_threads = parser
        if downloader is not None:
            self.downloader_threads = downloader


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


def rename_images_sequentially(directory: str) -> int:
    """
    Rename all image files in a directory to a sequential, zero-padded format.
    
    Args:
        directory: Directory containing images to rename
        
    Returns:
        int: Number of renamed files
    """
    renamer = FSRenamer(directory)
    return renamer.rename_sequentially()


def count_valid_images_in_latest_batch(directory: str, previous_count: int) -> int:
    """
    Count valid images in the latest batch, starting from previous_count index.
    
    Args:
        directory: Directory path to check
        previous_count: Number of images that existed before this batch
        
    Returns:
        int: Number of valid images in the latest batch
    """
    valid_count = 0

    directory_path = Path(directory)
    if not directory_path.exists():
        return 0

    # Get all image files
    image_files = [
        f for f in directory_path.iterdir()
        if f.is_file() and is_valid_image_extension(f)
    ]

    # Sort by creation time to get the latest batch
    image_files.sort(key=lambda x: os.path.getctime(x))

    # Take only files that were likely created in this batch
    latest_batch = image_files[previous_count:]

    for file_path in latest_batch:
        if validate_image(str(file_path)):
            valid_count += 1
        else:
            # Remove corrupted image
            try:
                os.remove(file_path)
                logger.warning(f"Removed corrupted image: {file_path}")
            except Exception:
                pass

    return valid_count


def _download_with_engine(engine_name: str, keyword: str, out_dir: str, max_num: int,
                          offset: int = 0, file_idx_offset: int = 0) -> bool:
    """
    Download images using a specific search engine.
    
    Args:
        engine_name: Name of the search engine to use ("google", "bing", "baidu", "ddgs")
        keyword: Search term for images
        out_dir: Output directory path
        max_num: Maximum number of images to download
        offset: Search offset to avoid duplicate results
        file_idx_offset: Starting index for file naming
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        if engine_name == "ddgs":
            success, _ = download_images_ddgs(keyword=keyword, out_dir=out_dir, max_num=max_num)
            return success

        # Configure crawler based on engine
        crawler_class = {
            "google": GoogleImageCrawler,
            "bing": BingImageCrawler,
            "baidu": BaiduImageCrawler
        }.get(engine_name)

        if not crawler_class:
            logger.warning(f"Unknown engine: {engine_name}")
            return False

        crawler = crawler_class(
            storage={'root_dir': out_dir},
            log_level=logging.WARNING,
            feeder_threads=1,
            parser_threads=1,
            downloader_threads=3
        )

        crawler.crawl(
            keyword=keyword,
            max_num=max_num,
            min_size=(100, 100),
            offset=offset,
            file_idx_offset=file_idx_offset
        )
        return True
    except Exception as e:
        logger.warning(f"{engine_name.capitalize()}ImageCrawler failed: {e}")
        return False


def _generate_alternative_terms(keyword: str, retry_num: int) -> List[str]:
    """
    Generate alternative search terms for better results.
    
    Args:
        keyword: Base keyword to generate alternatives for
        retry_num: Current retry number
        
    Returns:
        List of alternative search terms
    """
    alternative_terms = [
        f"{keyword} {retry_num}",
        f"{keyword} example {retry_num}",
        f"{keyword} illustration",
        f"what is {keyword}",
        f"{keyword} image",
        f"{keyword} photo",
        f"{keyword} example",
        f"{keyword} best"
    ]
    return alternative_terms


def _update_image_count(out_dir: str) -> int:
    """
    Remove duplicates and return the updated count of valid images.
    
    Args:
        out_dir: Directory containing images
        
    Returns:
        int: Updated count of valid images
    """
    remove_duplicate_images(out_dir)
    valid_count, _, _ = count_valid_images(out_dir)
    return valid_count


def retry_download_images(keyword: str, out_dir: str, max_num: int, max_retries: int = 10) -> Tuple[bool, int]:
    """
    Retry downloading images until reaching the desired count or max retries.
    
    Args:
        keyword: Search term for images
        out_dir: Output directory path
        max_num: Maximum number of images to download
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (success_flag, downloaded_count)
    """
    # First attempt
    downloader = ImageDownloader()
    success, count = downloader.download(keyword, out_dir, max_num)

    # Remove any duplicates after initial download
    if count > 1:
        count = _update_image_count(out_dir)
        logger.info(f"After removing duplicates: {count} unique images remain")

    # Calculate how many more images we need
    images_needed = max(0, max_num - count)
    retries = 0

    # Retry if needed and we haven't exceeded max retries
    while images_needed > 0 and retries < max_retries:
        retries += 1
        logger.info(f"Retry #{retries}: Attempting to download {images_needed} more images for '{keyword}'")

        # Slight delay before retry
        time.sleep(0.5)

        # Generate alternative search terms and select one based on retry number
        alternative_terms = _generate_alternative_terms(keyword, retries)
        retry_term = alternative_terms[min(retries - 1, len(alternative_terms) - 1)]

        # Select an engine to use for this retry (cycle through available engines)
        engine_index = (retries - 1) % len(ENGINES)
        current_engine = ENGINES[engine_index]
        random_offset = random.randint(20, 50 + retries * 10)  # Increasing offset with retries

        logger.info(f"Retry #{retries}: Using {current_engine} with random offset {random_offset}")

        # Try to download more images with the selected engine
        retry_success = _download_with_engine(
            engine_name=current_engine,
            keyword=retry_term,
            out_dir=out_dir,
            max_num=images_needed,
            offset=random_offset,
            file_idx_offset=count
        )

        # Update count and calculate remaining needed
        if retry_success:
            count = _update_image_count(out_dir)
            images_needed = max(0, max_num - count)
            logger.info(f"After retry #{retries}: {count}/{max_num} unique images")

        if images_needed == 0:
            logger.info(f"Successfully downloaded {count}/{max_num} unique images after {retries} retries")
            break

    # Final deduplication pass
    if count > 1:
        count = _update_image_count(out_dir)

    # Ensure all images are renamed sequentially regardless of which engine downloaded them
    if count > 0:
        renamed = rename_images_sequentially(out_dir)
        logger.info(f"Final step: Renamed {renamed} images sequentially")

    return count >= 1, count  # Consider success if at least one image was downloaded


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


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load dataset configuration from a JSON file and validate against schema.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict containing dataset configuration
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Validate against schema
        try:
            validate(instance=config, schema=CONFIG_SCHEMA)
            logger.info(f"Config file {config_path} successfully validated against schema")
        except jsonschema.exceptions.ValidationError as e:
            logger.warning(f"Config file validation error: {e}")

            # Provide fallbacks for required fields if missing
            if 'dataset_name' not in config:
                logger.warning("Missing 'dataset_name' in config file, using 'dataset' as default")
                config['dataset_name'] = 'dataset'

            if 'categories' not in config or not isinstance(config['categories'], dict):
                logger.error("Invalid or missing 'categories' in config file")
                raise ValueError("Config must contain a 'categories' dictionary")

        # Ensure at least one category is defined
        if not config['categories']:
            logger.error("No categories defined in config file")
            raise ValueError("At least one category must be defined")

        return config

    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Config validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        raise


def generate_keywords(category: str, ai_model: str = "gpt4-mini") -> List[str]:
    """
    Generate related keywords for a category using G4F (GPT-4) API.
    
    Args:
        category: The category name to generate keywords for
        ai_model: The AI model to use ("gpt4" or "gpt4-mini")
        
    Returns:
        List of generated keywords related to the category
    """
    # Try using G4F to generate keywords
    try:
        # Select the appropriate model
        provider = None  # Let g4f choose the best available provider
        model = g4f.models.gpt_4 if ai_model == "gpt4" else g4f.models.gpt_4o_mini

        # Create the prompt
        prompt = f"""Generate 10-15 search keywords related to "{category}" that would be useful for 
        finding diverse, high-quality images of this concept. 
        
        Include variations that would work well for image search engines.
        
        Return ONLY the keywords as a Python list of strings, with no explanation or other text.
        Example format: ["keyword 1", "keyword 2", "keyword 3"]
        """

        # Make the API call
        logger.info(f"Generating keywords for '{category}' using {ai_model}")
        response = g4f.ChatCompletion.create(
            model=model,
            provider=provider,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract keywords from response
        keywords = _extract_keywords_from_response(response, category)

        logger.info(f"Generated {len(keywords)} keywords for '{category}' using {ai_model}")
        return keywords

    except Exception as e:
        logger.warning(f"Failed to generate keywords using {ai_model}: {str(e)}")
        # Fall back to rule-based keyword generation
        print(f"Try to provide keywords manually for {category} or try again!")
        print("System will exit now...")
        sys.exit(1)


def _extract_keywords_from_response(response: str, category: str) -> List[str]:
    """Extract keywords from the AI response."""
    try:
        # Try to find a list pattern in the response
        import re
        list_pattern = r'\[.*?\]'
        match = re.search(list_pattern, response, re.DOTALL)

        if match:
            # Found a list pattern, try to parse it
            list_str = match.group(0)
            with contextlib.suppress(Exception):
                # Parse as Python list
                keywords = eval(list_str)
                if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
                    return keywords

        # If we couldn't parse a proper list, try to extract keywords line by line
        lines = [line.strip() for line in response.split('\n')]
        keywords = []

        for line in lines:
            # Remove common list markers and quotes
            line = re.sub(r'^[-*•"]', '', line).strip()
            line = re.sub(r'^[0-9]+\.', '', line).strip()
            line = line.strip('"\'')

            if line and not line.startswith('[') and not line.startswith(']'):
                keywords.append(line)

        # Remove duplicates and empty strings
        keywords = [k for k in keywords if k]
        keywords = list(dict.fromkeys(keywords))

        # Always include the category itself
        if category not in keywords:
            keywords.insert(0, category)

        return keywords
    except Exception as e:
        logger.warning(f"Error extracting keywords from AI response: {str(e)}")
        # Return at least the category itself
        return [category]


def create_arg_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser.add_argument("-c", "--config", default=DEFAULT_CONFIG_FILE,
                        help=f"Path to configuration file (default: {DEFAULT_CONFIG_FILE})")
    parser.add_argument("-m", "--max-images", type=int, default=10, help="Maximum number of images per keyword")
    parser.add_argument("-o", "--output", help="Custom output directory")
    parser.add_argument("--no-integrity", action="store_true", help="Skip integrity checks")
    parser.add_argument("-r", "--max-retries", type=int, default=5, help="Maximum retry attempts")
    parser.add_argument("--continue", dest="continue_last", action="store_true", help="Continue from last run")
    parser.add_argument("--cache", default=DEFAULT_CACHE_FILE, help="Cache file for progress tracking")

    # Keyword generation options
    keyword_group = parser.add_argument_group('Keyword Generation')
    generation_mode = keyword_group.add_mutually_exclusive_group()
    generation_mode.add_argument("--keywords-auto", action="store_const", const="auto", dest="keyword_mode",
                                 help="Generate keywords only if none provided (default)")
    generation_mode.add_argument("--keywords-enabled", action="store_const", const="enabled", dest="keyword_mode",
                                 help="Always generate additional keywords")
    generation_mode.add_argument("--keywords-disabled", action="store_const", const="disabled", dest="keyword_mode",
                                 help="Disable keyword generation completely")
    parser.set_defaults(keyword_mode="auto")

    # AI model selection
    keyword_group.add_argument("--ai-model", choices=["gpt4", "gpt4-mini"], default="gpt4-mini",
                               help="AI model to use for keyword generation (default: gpt4-mini)")

    # Logging options
    log_group = parser.add_argument_group('Logging')
    log_group.add_argument("--log-file", default=DEFAULT_LOG_FILE,
                           help=f"Path to log file (default: {DEFAULT_LOG_FILE})")
    log_group.add_argument("-v", "--verbose", action="store_true",
                           help="Show detailed logs in console (not just warnings/errors)")

    return parser


class DatasetGenerator:
    """Class responsible for generating image datasets based on configuration."""

    def __init__(self, config: DatasetGenerationConfig):
        """
        Initialize the dataset generator.
        
        Args:
            config: Dataset generation configuration
        """
        self.config = config
        self.dataset_config = self._load_and_validate_config()
        self.dataset_name = self.dataset_config['dataset_name']
        self.categories = self.dataset_config['categories']
        self.root_dir = self._setup_output_directory()
        self.tracker = DatasetTracker()
        self.progress_cache = self._initialize_progress_cache()
        self.report = self._initialize_report()

    def generate(self) -> None:
        """Generate the dataset based on the provided configuration."""
        # Process each category
        for category_name, keywords in tqdm(self.categories.items(), desc="Processing Categories", leave=True):
            logger.info(f"Processing category: {category_name}")
            self._process_category(category_name, keywords)

        # Print comprehensive summary
        self.tracker.print_summary()

        # Generate the markdown report
        self.report.generate()

        logger.info(f"Dataset generation completed. Output directory: {self.root_dir}")

    def _setup_output_directory(self) -> Path:
        """Set up and create the output directory."""
        root_dir = self.config.output_dir or self.dataset_name
        root_path = Path(root_dir)
        root_path.mkdir(parents=True, exist_ok=True)
        return root_path

    def _initialize_progress_cache(self) -> Optional[ProgressCache]:
        """Initialize the progress cache if continuing from last run."""
        if not self.config.continue_from_last:
            return None

        progress_cache = ProgressCache(self.config.cache_file)
        stats = progress_cache.get_completion_stats()
        logger.info(
            f"Continuing from previous run. Already completed: {stats['total_completed']} items across {stats['categories']} categories.")
        return progress_cache

    def _initialize_report(self) -> Report:
        """Initialize the report generator with dataset information."""
        report = Report(str(self.root_dir))
        report.add_summary(f"Dataset name: {self.dataset_name}")
        report.add_summary(f"Configuration: {self.config.config_path}")
        report.add_summary(f"Categories: {len(self.categories)}")
        report.add_summary(f"Max images per keyword: {self.config.max_images}")
        report.add_summary(f"Keyword generation mode: {self.config.keyword_generation}")

        if self.config.keyword_generation != "disabled":
            report.add_summary(f"AI model for keyword generation: {self.config.ai_model}")

        if self.config.continue_from_last and self.progress_cache:
            stats = self.progress_cache.get_completion_stats()
            report.add_summary(f"Continuing from previous run with {stats['total_completed']} completed items")

        return report

    def _load_and_validate_config(self) -> Dict[str, Any]:
        """Load and validate the dataset configuration, applying config file options."""
        dataset_config = load_config(self.config.config_path)

        # Extract options from config if available, with CLI arguments taking precedence
        if 'options' in dataset_config and isinstance(dataset_config['options'], dict):
            options = dataset_config['options']
            # Apply config file options if CLI arguments weren't explicitly provided
            _apply_config_options(self.config, options)

        return dataset_config

    def _process_category(self, category_name: str, keywords: List[str]) -> None:
        """Process a single category with its keywords."""
        # Create category directory
        category_path = self.root_dir / category_name
        category_path.mkdir(parents=True, exist_ok=True)

        # Handle keywords based on configuration
        keywords_to_process = self._prepare_keywords(category_name, keywords)

        # Process each keyword
        self._process_keywords_for_category(category_name, keywords_to_process, category_path)

    def _prepare_keywords(self, category_name: str, keywords: List[str]) -> List[str]:
        """Prepare keywords for processing based on configuration."""
        # Record original keywords before any potential generation
        original_keywords = keywords.copy() if keywords else []
        generated_keywords = []

        if not keywords and self.config.keyword_generation in ["auto", "enabled"]:
            # No keywords provided and generation enabled
            generated_keywords = generate_keywords(category_name, self.config.ai_model)
            keywords = generated_keywords
            logger.info(f"No keywords provided for category '{category_name}', generated {len(keywords)} keywords")
        elif not keywords and self.config.keyword_generation == "disabled":
            # No keywords and generation disabled, use category name as keyword
            keywords = [category_name]
            logger.info(
                f"No keywords provided for category '{category_name}' and generation disabled, using category name as keyword")
        elif self.config.keyword_generation == "enabled" and keywords:
            # Keywords provided and asked to generate more
            generated_keywords = generate_keywords(category_name, self.config.ai_model)
            # Add generated keywords to user-provided ones, avoiding duplicates
            original_count = len(keywords)
            keywords = list(set(keywords + generated_keywords))
            logger.info(
                f"Added {len(keywords) - original_count} generated keywords to {original_count} user-provided ones")

        # Record keyword generation in report if any generation occurred
        if generated_keywords:
            self.report.record_keyword_generation(
                category_name,
                original_keywords,
                generated_keywords,
                self.config.ai_model
            )

        return keywords

    def _process_keywords_for_category(self, category_name: str, keywords: List[str], category_path: Path) -> None:
        """Process all keywords for a specific category."""
        for keyword in tqdm(keywords, desc=f"Keywords in {category_name}", leave=False):
            # Skip if already processed and continuing from last run
            if self.config.continue_from_last and self.progress_cache and self.progress_cache.is_completed(
                    category_name, keyword):
                logger.info(f"Skipping already processed: {category_name}/{keyword}")
                continue

            # Create keyword directory
            keyword_safe = keyword.replace('/', '_').replace('\\', '_')
            keyword_path = category_path / keyword_safe
            keyword_path.mkdir(parents=True, exist_ok=True)

            # Download images
            download_context = f"{category_name}/{keyword}"
            success, count = retry_download_images(
                keyword=keyword,
                out_dir=str(keyword_path),
                max_num=self.config.max_images,
                max_retries=self.config.max_retries
            )

            # Track results and record in report
            self._track_download_results(download_context, success, count, category_name, keyword)

            # Check and record duplicates
            check_duplicates(category_name, keyword, str(keyword_path), self.report)

            # Check integrity if enabled
            if self.config.integrity:
                self._check_image_integrity(download_context, str(keyword_path), category_name, keyword)

            # Update progress cache if continuing from last run
            if self.config.continue_from_last and self.progress_cache:
                metadata = {
                    "success": success,
                    "downloaded_count": count,
                }
                self.progress_cache.mark_completed(category_name, keyword, metadata)

            # Small delay to be respectful to image services
            time.sleep(0.5)

    def _track_download_results(self, download_context: str, success: bool, count: int, category_name: str,
                                keyword: str) -> None:
        """Track the results of image downloads."""
        if success:
            self.tracker.record_download_success(download_context)
            logger.info(f"Successfully downloaded {count} images for {download_context}")
        else:
            error_msg = "Failed to download any valid images after retries"
            self.tracker.record_download_failure(download_context, error_msg)
            self.report.record_error(f"{category_name}/{keyword} download", error_msg)

    def _check_image_integrity(self, download_context: str, keyword_path: str, category_name: str,
                               keyword: str) -> None:
        """Check image integrity and record results."""
        valid_count, total_count, corrupted_files = count_valid_images(keyword_path)

        if valid_count < total_count:
            self.tracker.record_integrity_failure(
                download_context,
                total_count,
                valid_count,
                corrupted_files
            )

        self.report.record_integrity(
            category=category_name,
            keyword=keyword,
            expected=total_count,
            actual=valid_count,
            corrupted=total_count - valid_count
        )


def generate_dataset(config: DatasetGenerationConfig) -> None:
    """
    Generate image dataset based on configuration file.
    
    Args:
        config: Dataset generation configuration
    """
    generator = DatasetGenerator(config)
    generator.generate()


def check_duplicates(category_name: str, keyword: str, keyword_path: str, report: Report) -> None:
    """Check for and record duplicates in the report."""
    try:
        # Get all image files
        image_files = [
            f for f in Path(keyword_path).iterdir()
            if f.is_file() and is_valid_image_extension(f)
        ]
        total_images = len(image_files)

        # Detect duplicates
        duplicates = detect_duplicate_images(keyword_path)
        duplicates_count = sum(len(dups) for dups in duplicates.values())
        unique_kept = total_images - duplicates_count

        # Record in report
        report.record_duplicates(
            category=category_name,
            keyword=keyword,
            total=total_images,
            duplicates=duplicates_count,
            kept=unique_kept
        )

    except Exception as e:
        logger.warning(f"Failed to check duplicates for {category_name}/{keyword}: {e}")
        report.record_error(f"{category_name}/{keyword} duplicates check", str(e))


def _track_download_results(
        tracker: DatasetTracker,
        download_context: str,
        success: bool,
        count: int,
        report: Report,
        category_name: str,
        keyword: str,
        max_images: int
) -> None:
    """Track the results of image downloads."""
    errors = []

    if success:
        tracker.record_download_success(download_context)
        logger.info(f"Successfully downloaded {count} images for {download_context}")
    else:
        error_msg = "Failed to download any valid images after retries"
        tracker.record_download_failure(download_context, error_msg)
        logger.warning(f"Failed to download images for: {download_context}")
        errors.append(error_msg)

    # Record in report
    report.record_download(
        category=category_name,
        keyword=keyword,
        success=success,
        count=count,
        attempted=max_images,
        errors=errors
    )


def check_image_integrity(
        tracker: DatasetTracker,
        download_context: str,
        keyword_path: str,
        max_images: int,
        report: Report,
        category_name: str,
        keyword: str
) -> None:
    """Check the integrity of downloaded images."""
    valid_count, total_count, corrupted_files = count_valid_images(keyword_path)
    if valid_count < max_images:
        tracker.record_integrity_failure(
            download_context,
            max_images,
            valid_count,
            corrupted_files
        )

    # Record in report
    report.record_integrity(
        category=category_name,
        keyword=keyword,
        expected=max_images,
        actual=valid_count,
        corrupted=corrupted_files
    )


def main():
    """Main function to parse arguments and generate dataset"""
    parser = argparse.ArgumentParser(description="PixCrawler: Image Dataset Generator")
    parser = create_arg_parser(parser)

    args = parser.parse_args()

    # Configure console log level based on verbosity
    if args.verbose:
        console_handler.setLevel(logging.INFO)

    # Update log file if specified
    if args.log_file != DEFAULT_LOG_FILE:
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                logger.removeHandler(handler)

        new_file_handler = logging.FileHandler(args.log_file, encoding='utf-8')
        new_file_handler.setLevel(logging.INFO)
        new_file_handler.setFormatter(file_formatter)
        logger.addHandler(new_file_handler)

    config = DatasetGenerationConfig(
        config_path=args.config,
        max_images=args.max_images,
        output_dir=args.output,
        integrity=not args.no_integrity,
        max_retries=args.max_retries,
        continue_from_last=args.continue_last,
        cache_file=args.cache,
        keyword_generation=args.keyword_mode,
        ai_model=args.ai_model
    )

    generate_dataset(config)


if __name__ == "__main__":
    main()
