"""
This module provides various image downloading functionalities, including DuckDuckGo search integration and a multi-threaded image downloader that leverages different search engines.

Classes:
    IDownloader: A protocol defining the interface for image downloaders.
    ABC: Abstract base class.
    SearchEngine: Base class for search engines.
    DuckDuckGo: A class to download images using DuckDuckGo search.
    ImageDownloader: A class for downloading images using multiple image crawlers sequentially.

Functions:
    download_images_ddgs: Downloads images directly using the DuckDuckGo search engine.

Features:
    - DuckDuckGo image search integration.
    - Multi-threaded image downloading.
    - Support for various search engines.
    - Sequential download processing for optimal performance.
    - Fallback mechanisms for robust image retrieval.
"""

import logging
import random
import threading
from abc import ABC
from pathlib import Path
from typing import Tuple, Optional

from _base import IDownloader
from _predefined_variations import get_search_variations
from _search_engines import download_images_ddgs
from builder._engine import EngineProcessor
from builder._helpers import progress
from _helpers import rename_images_sequentially
from utility.logging_config import get_logger

logger = get_logger(__name__)

# Image validation moved to validator package

__all__ = [
    'ABC',
    'ImageDownloader',
    'APIDownloader',
    'AioHttpDownloader'
]


class ImageDownloader(IDownloader):
    """
    A class for downloading images using multiple image crawlers sequentially.

    Uses sequential processing across search engines for optimal performance
    and reliability. Parallel execution has been deprecated as it degraded
    performance in production.
    """

    def __init__(self,
                 feeder_threads: int = 2,
                 parser_threads: int = 2,
                 downloader_threads: int = 4,
                 min_image_size: Tuple[int, int] = (100, 100),
                 delay_between_searches: float = 0.5,
                 log_level: int = logging.WARNING):
        """
        Initializes the ImageDownloader with configurable parameters.

        Args:
            feeder_threads (int): Number of feeder threads for crawlers.
            parser_threads (int): Number of parser threads for crawlers.
            downloader_threads (int): Number of downloader threads for crawlers.
            min_image_size (Tuple[int, int]): Minimum image size as (width, height) tuple.
            delay_between_searches (float): Delay in seconds between different search terms.
            log_level (int): Logging level for crawlers (e.g., logging.INFO, logging.WARNING).
        """
        self.feeder_threads = feeder_threads
        self.parser_threads = parser_threads
        self.downloader_threads = downloader_threads
        self.min_image_size = min_image_size
        self.delay_between_searches = delay_between_searches
        self.log_level = log_level

        # Initialize engine manager
        self.engine_processor = EngineProcessor(self)

        # Search variations template
        self.search_variations = get_search_variations()

        # Thread synchronization
        self.lock = threading.RLock()

        # Signal for worker threads
        self.stop_workers = False

        # Shared counter for downloaded images
        self.total_downloaded = 0

    def download(self, keyword: str, out_dir: str, max_num: int, job_id: Optional[str] = None, chunk_id: Optional[str] = None) -> Tuple[bool, int]:
        """
        Downloads images using multiple image crawlers sequentially.
        Includes fallback to DuckDuckGo if primary crawlers do not meet the download target.

        Args:
            keyword (str): The search term for images.
            out_dir (str): The output directory path where images will be saved.
            max_num (int): The maximum number of images to download.
            job_id (Optional[str]): Optional job ID for structured logging.
            chunk_id (Optional[str]): Optional chunk ID for structured logging.

        Returns:
            Tuple[bool, int]: A tuple where the first element is True if any images were downloaded,
                             and the second element is the total count of downloaded images.
        """
        # Add structured logging context
        log_context = logger.bind(
            operation="image_download",
            keyword=keyword,
            max_num=max_num,
            job_id=job_id,
            chunk_id=chunk_id
        )
        
        try:
            # Ensure output directory exists
            Path(out_dir).mkdir(parents=True, exist_ok=True)

            # Reset counters and flags
            with self.lock:
                self.total_downloaded = 0
                self.stop_workers = False
                self.engine_processor.reset_stats()

            # Update progress display
            progress.set_subtask_description(f"Starting download for: {keyword}")
            progress.set_subtask_postfix(target=max_num)
            log_context.info(f"Starting image download for keyword: {keyword}")

            # Generate search variations
            variations = [template.format(keyword=keyword) for template in
                          self.search_variations]

            # Shuffle variations to get more diverse results
            random.shuffle(variations)

            # Use engines in sequence with fallbacks
            progress.set_subtask_description(f"Downloading sequentially: {keyword}")
            log_context.info("Starting sequential engine download", variations_count=len(variations))
            self.engine_processor.download_with_sequential_engines(keyword,
                                                                       variations,
                                                                       out_dir, max_num)

            # If we still don't have enough images, try DuckDuckGo as final fallback
            if self.total_downloaded < max_num:
                progress.set_subtask_description(
                    f"Using DuckDuckGo fallback: {keyword}")
                log_context.info(
                    "Using DuckDuckGo fallback",
                    downloaded_so_far=self.total_downloaded,
                    remaining=max_num - self.total_downloaded
                )
                self._try_duckduckgo_fallback(
                    keyword=keyword,
                    out_dir=out_dir,
                    max_num=max_num,
                    total_downloaded=self.total_downloaded,
                    job_id=job_id,
                    chunk_id=chunk_id
                )

            # Rename all files sequentially
            if self.total_downloaded > 0:
                progress.set_subtask_description(f"Renaming images: {keyword}")
                rename_images_sequentially(out_dir)

            # Log engine statistics
            self.engine_processor.log_engine_stats()

            # Update progress with results
            progress.set_subtask_description(
                f"Downloaded {self.total_downloaded}/{max_num} images for {keyword}")
            log_context.info(
                f"Image download completed",
                downloaded=self.total_downloaded,
                target=max_num,
                success_rate=f"{(self.total_downloaded/max_num)*100:.1f}%"
            )

            return self.total_downloaded > 0, self.total_downloaded

        except Exception as e:
            log_context.warning(
                f"All crawlers failed with error: {e}. Trying DuckDuckGo as fallback.",
                error=str(e),
                error_type=type(e).__name__
            )
            progress.set_subtask_description(
                f"Error occurred, using final fallback: {keyword}")
            return self._final_duckduckgo_fallback(keyword, out_dir, max_num, job_id, chunk_id)

    @staticmethod
    def _try_duckduckgo_fallback(keyword: str, out_dir: str, max_num: int,
                                 total_downloaded: int, job_id: Optional[str] = None, chunk_id: Optional[str] = None) -> int:
        """
        Attempts to use DuckDuckGo as a fallback option if other engines haven't downloaded enough images.

        Args:
            keyword (str): The search term.
            out_dir (str): The output directory.
            max_num (int): The maximum number of images to download.
            total_downloaded (int): The current count of downloaded images.
            job_id (Optional[str]): Optional job ID for structured logging.
            chunk_id (Optional[str]): Optional chunk ID for structured logging.

        Returns:
            int: The updated total downloaded count after the fallback attempt.
        """
        if total_downloaded >= max_num:
            return total_downloaded

        log_context = logger.bind(
            operation="duckduckgo_fallback",
            keyword=keyword,
            job_id=job_id,
            chunk_id=chunk_id
        )
        log_context.info(
            f"Crawlers downloaded {total_downloaded}/{max_num} images. Trying DuckDuckGo as fallback.",
            total_downloaded=total_downloaded,
            max_num=max_num,
            remaining=max_num - total_downloaded
        )
        ddgs_success, ddgs_count = download_images_ddgs(
            keyword=keyword,
            out_dir=out_dir,
            max_num=max_num - total_downloaded
        )
        if ddgs_success:
            log_context.info("DuckDuckGo fallback successful", ddgs_count=ddgs_count)
            return total_downloaded + ddgs_count
        log_context.warning("DuckDuckGo fallback failed")
        return total_downloaded

    @staticmethod
    def _final_duckduckgo_fallback(keyword: str, out_dir: str, max_num: int, job_id: Optional[str] = None, chunk_id: Optional[str] = None) -> Tuple[
        bool, int]:
        """
        Performs a final fallback to DuckDuckGo when all other download methods have failed.

        Args:
            keyword (str): The search term.
            out_dir (str): The output directory.
            max_num (int): The maximum number of images to download.
            job_id (Optional[str]): Optional job ID for structured logging.
            chunk_id (Optional[str]): Optional chunk ID for structured logging.

        Returns:
            Tuple[bool, int]: A tuple indicating success (True/False) and the number of images downloaded.
        """
        log_context = logger.bind(
            operation="final_duckduckgo_fallback",
            keyword=keyword,
            max_num=max_num,
            job_id=job_id,
            chunk_id=chunk_id
        )
        log_context.info("Attempting final DuckDuckGo fallback")
        success, count = download_images_ddgs(keyword, out_dir, max_num)
        if success and count > 0:
            rename_images_sequentially(out_dir)
            log_context.info("Final fallback successful", count=count)
            return True, count
        else:
            log_context.error(f"All download methods failed for '{keyword}'")
            return False, 0

    def add_search_variation(self, variation_template: str) -> None:
        """
        Add a new search variation template.

        Args:
            variation_template: Template string with {keyword} placeholder
        """
        if variation_template not in self.search_variations:
            self.search_variations.append(variation_template)

    def remove_search_variation(self, variation_template: str) -> None:
        """
        Remove a search variation template.

        Args:
            variation_template: Template string to remove
        """
        if variation_template in self.search_variations:
            self.search_variations.remove(variation_template)

    def set_crawler_threads(self, feeder: Optional[int] = None,
                            parser: Optional[int] = None,
                            downloader: Optional[int] = None) -> None:
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


class APIDownloader(IDownloader):
    """Placeholder for API-based downloader. Disabled by default."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        raise NotImplementedError("APIDownloader not implemented")

    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        raise NotImplementedError("APIDownloader not implemented")


class AioHttpDownloader(IDownloader):
    """Placeholder for async HTTP downloader. Disabled by default."""

    def __init__(self, max_concurrent: int = 10, **kwargs):
        raise NotImplementedError("AioHttpDownloader not implemented")

    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        raise NotImplementedError("AioHttpDownloader not implemented")
