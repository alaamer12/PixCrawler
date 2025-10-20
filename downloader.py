"""
This module provides various image downloading functionalities, including DuckDuckGo search integration and a multi-threaded image downloader that leverages different search engines.

Classes:
    IDownloader: A protocol defining the interface for image downloaders.
    DuckDuckGoImageDownloader: A class to download images using DuckDuckGo search.
    ImageDownloader: A class for downloading images using multiple image crawlers in parallel.

Functions:
    download_images_ddgs: Downloads images directly using the DuckDuckGo search engine.

Features:
    - DuckDuckGo image search integration.
    - Multi-threaded image downloading.
    - Support for various search engines.
    - Parallel and sequential download processing.
    - Fallback mechanisms for robust image retrieval.
"""

import concurrent.futures
import logging
import os
import random
import threading
import time
from pathlib import Path
from typing import List, Tuple, Optional, Protocol

import requests
from ddgs import DDGS

from _engine import EngineProcessor
from config import get_search_variations
from constants import logger
from helpers import progress
from utilities import rename_images_sequentially, image_validator
from _exceptions import DownloadError, ImageValidationError

__all__ = [
    'IDownloader',
    'DuckDuckGoImageDownloader',
    'download_images_ddgs',
    'ImageDownloader'
]


class IDownloader(Protocol):
    """
    A protocol defining the interface for image downloaders.
    Any class implementing this protocol must provide a `download` method.
    """
    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        ...


class DuckDuckGoImageDownloader(IDownloader):
    """
    A class to download images using DuckDuckGo search as a fallback mechanism.

    Uses parallel processing for faster downloads.
    """

    def __init__(self, max_workers: int = 4):
        """
        Initializes the DuckDuckGoImageDownloader with default settings.

        Args:
            max_workers (int): The maximum number of parallel download workers.
        """
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.timeout = 20
        self.min_file_size = 1000  # bytes
        self.delay = 0.2  # seconds between downloads
        self.max_workers = max_workers
        self.lock = threading.RLock()

    def _get_image(self, image_url: str, file_path: str) -> bool:
        """
        Downloads a single image from a given URL and saves it to the specified file path.
        Includes retry logic for SSL verification and checks for content type and file size.

        Args:
            image_url (str): The URL of the image to download.
            file_path (str): The absolute path where the image should be saved.

        Returns:
            bool: True if the download and validation were successful, False otherwise.
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
                raise ImageValidationError(f"Skipping non-image content type: {content_type}")

            if len(response.content) < self.min_file_size:
                raise ImageValidationError(f"Skipping too small image ({len(response.content)} bytes)")

            with open(file_path, "wb") as f:
                f.write(response.content)

            # Validate the downloaded image
            if not image_validator.validate(file_path):
                # Remove corrupted image
                try:
                    os.remove(file_path)
                    logger.warning(f"Removed corrupted image: {file_path}")
                except OSError as ose:
                    logger.error(f"Error removing corrupted image {file_path}: {ose}")
                raise ImageValidationError(f"Downloaded image failed validation: {file_path}")
            return True

        except requests.exceptions.RequestException as req_e:
            logger.warning(f"Network or request error downloading {image_url}: {req_e}")
            raise DownloadError(f"Network or request error downloading {image_url}: {req_e}") from req_e
        except ImageValidationError as ive:
            logger.warning(f"Image validation error for {image_url}: {ive}")
            raise ive
        except Exception as e:
            logger.warning(f"An unexpected error occurred while downloading {image_url}: {e}")
            raise DownloadError(f"Unexpected error downloading {image_url}: {e}") from e

    def _download_single_image(self, result: dict, out_dir: str, index: int) -> bool:
        """
        Downloads a single image from a search result dictionary.

        Args:
            result (dict): A dictionary containing image information, including its URL.
            out_dir (str): The output directory where the image will be saved.
            index (int): The index of the image, used for generating a unique filename.

        Returns:
            bool: True if the image was successfully downloaded, False otherwise.
        """
        image_url = result.get("image")
        if not image_url:
            return False

        # Create a unique filename based on the index
        filename = f"ddgs_{index:03d}.jpg"
        file_path = os.path.join(out_dir, filename)

        # Download the image
        success = self._get_image(image_url, file_path)

        # Add small delay between downloads
        time.sleep(self.delay)

        return success

    def _search_and_download_parallel(self, keyword: str, out_dir: str, max_count: int) -> int:
        """
        Searches for images using a keyword and downloads them in parallel.

        Args:
            keyword (str): The search term for images.
            out_dir (str): The output directory where images will be saved.
            max_count (int): The maximum number of images to download.

        Returns:
            int: The number of successfully downloaded images.
        """
        downloaded = 0

        try:
            # Fetch search results
            results = self._fetch_search_results(keyword, max_count)
            if not results:
                return 0

            # Download images in parallel
            downloaded = self._execute_parallel_downloads(results, out_dir, max_count)

        except Exception as e:
            logger.warning(f"Failed to search for keyword '{keyword}': {e}")

        return downloaded

    @staticmethod
    def _fetch_search_results(keyword: str, max_count: int) -> List[dict]:
        """
        Fetches image search results from DuckDuckGo.

        Args:
            keyword (str): The search term.
            max_count (int): The maximum number of images needed.

        Returns:
            List[dict]: A list of search result dictionaries.
        """
        with DDGS() as ddgs:
            # Request more images than needed to account for failures
            results = list(ddgs.images(keyword, max_results=max_count * 3))
            logger.info(f"Found {len(results)} potential images for '{keyword}'")
            return results

    def _execute_parallel_downloads(self, results: List[dict], out_dir: str, max_count: int) -> int:
        """
        Executes parallel downloads of images from a list of search results.

        Args:
            results (List[dict]): A list of search result dictionaries.
            out_dir (str): The output directory for downloaded images.
            max_count (int): The maximum number of images to download.

        Returns:
            int: The number of successfully downloaded images.
        """
        downloaded = 0

        # Create a thread pool for parallel downloads
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit download tasks
            futures = []
            for i, result in enumerate(results):
                if i >= max_count * 2:  # Limit the number of futures to avoid excessive memory usage
                    break

                futures.append(executor.submit(
                    self._download_single_image,
                    result=result,
                    out_dir=out_dir,
                    index=i + 1
                ))

            # Process completed downloads
            for future in concurrent.futures.as_completed(futures):
                if downloaded >= max_count:
                    self._cancel_pending_futures(futures)
                    break

                try:
                    if future.result():
                        with self.lock:
                            downloaded += 1
                            logger.info(f"Downloaded image from DuckDuckGo [{downloaded}/{max_count}]")
                except (DownloadError, ImageValidationError) as e:
                    logger.warning(f"Error downloading image: {e}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred during parallel download: {e}")

        return downloaded

    @staticmethod
    def _cancel_pending_futures(futures: List[concurrent.futures.Future]) -> None:
        """
        Cancels any pending futures in a list to prevent unnecessary downloads.

        Args:
            futures (List[concurrent.futures.Future]): A list of Future objects to check and potentially cancel.
        """
        for future in futures:
            if not future.done():
                future.cancel()

    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """
        Downloads images using DuckDuckGo search, including fallback mechanisms with alternate keywords.

        Args:
            keyword (str): The primary search term for images.
            out_dir (str): The output directory path where images will be saved.
            max_num (int): The maximum number of images to download.

        Returns:
            Tuple[bool, int]: A tuple where the first element is True if any images were downloaded,
                             and the second element is the total count of downloaded images.
        """
        logger.warning("Using DuckDuckGo image search with parallel downloading")

        try:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            downloaded_count = 0

            # Try with the original keyword first
            downloaded_count = self._search_and_download_parallel(keyword, out_dir, max_num)

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

                    # The _search_and_download_parallel function will update our count
                    additional_count = self._search_and_download_parallel(
                        alt_keyword,
                        out_dir,
                        remaining
                    )
                    downloaded_count += additional_count

            return downloaded_count > 0, downloaded_count

        except DownloadError as de:
            logger.error(f"A download-specific error occurred for '{keyword}': {de}")
            raise de
        except Exception as e:
            logger.error(f"An unexpected error occurred while downloading images for '{keyword}': {e}")
            raise DownloadError(f"Unexpected error during download for '{keyword}': {e}") from e


def download_images_ddgs(keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
    """
    Downloads images directly using the DuckDuckGo search engine.
    This function serves as a wrapper for the `DuckDuckGoImageDownloader` class.

    Args:
        keyword (str): The search term for images.
        out_dir (str): The output directory path where images will be saved.
        max_num (int): The maximum number of images to download.

    Returns:
        Tuple[bool, int]: A tuple where the first element is True if any images were downloaded,
                         and the second element is the total count of downloaded images.
    """
    try:
        # Create the output directory if it doesn't exist
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        # Initialize the DuckDuckGo downloader with parallel processing
        ddg_downloader = DuckDuckGoImageDownloader(max_workers=6)

        # Get the current count of images in the directory
        initial_count = len([f for f in os.listdir(out_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

        logger.info(f"Using DuckDuckGo to download up to {max_num} images for '{keyword}'")

        # Download images
        downloaded = ddg_downloader.download(keyword, out_dir, max_num)

        # Get the new count of images
        final_count = len([f for f in os.listdir(out_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        actual_downloaded = final_count - initial_count

        logger.info(f"DuckDuckGo download complete: {actual_downloaded} new images")

        return True, actual_downloaded
    except DownloadError as de:
        logger.error(f"DuckDuckGo download failed for '{keyword}': {de}")
        return False, 0
    except Exception as e:
        logger.error(f"An unexpected error occurred during DuckDuckGo download for '{keyword}': {e}")
        return False, 0


class ImageDownloader(IDownloader):
    """
    A class for downloading images using multiple image crawlers in parallel.

    Supports true parallel processing across all search engines simultaneously
    for maximum speed while maintaining thread safety.
    """

    def __init__(self,
                 feeder_threads: int = 2,
                 parser_threads: int = 2,
                 downloader_threads: int = 4,
                 min_image_size: Tuple[int, int] = (100, 100),
                 delay_between_searches: float = 0.5,
                 log_level: int = logging.WARNING,
                 max_parallel_engines: int = 4,
                 max_parallel_variations: int = 3,
                 use_all_engines: bool = True):
        """
        Initializes the ImageDownloader with configurable parameters.

        Args:
            feeder_threads (int): Number of feeder threads for crawlers.
            parser_threads (int): Number of parser threads for crawlers.
            downloader_threads (int): Number of downloader threads for crawlers.
            min_image_size (Tuple[int, int]): Minimum image size as (width, height) tuple.
            delay_between_searches (float): Delay in seconds between different search terms.
            log_level (int): Logging level for crawlers (e.g., logging.INFO, logging.WARNING).
            max_parallel_engines (int): Maximum number of search engines to use in parallel.
            max_parallel_variations (int): Maximum number of search variations to run in parallel per engine.
            use_all_engines (bool): Whether to use all engines in parallel (True) or fallback mode (False).
        """
        self.feeder_threads = feeder_threads
        self.parser_threads = parser_threads
        self.downloader_threads = downloader_threads
        self.min_image_size = min_image_size
        self.delay_between_searches = delay_between_searches
        self.log_level = log_level
        self.max_parallel_engines = max_parallel_engines
        self.max_parallel_variations = max_parallel_variations
        self.use_all_engines = use_all_engines

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

    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """
        Downloads images using multiple image crawlers, supporting both parallel and sequential processing.
        Includes fallback to DuckDuckGo if primary crawlers do not meet the download target.

        Args:
            keyword (str): The search term for images.
            out_dir (str): The output directory path where images will be saved.
            max_num (int): The maximum number of images to download.

        Returns:
            Tuple[bool, int]: A tuple where the first element is True if any images were downloaded,
                             and the second element is the total count of downloaded images.
        """
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

            # Generate search variations
            variations = [template.format(keyword=keyword) for template in self.search_variations]

            # Shuffle variations to get more diverse results
            random.shuffle(variations)

            if self.use_all_engines:
                # Use all engines in parallel for maximum speed
                progress.set_subtask_description(f"Downloading with parallel engines: {keyword}")
                self.engine_processor.download_with_parallel_engines(keyword, variations, out_dir, max_num)
            else:
                # Use engines in sequence with fallbacks (original approach)
                progress.set_subtask_description(f"Downloading sequentially: {keyword}")
                self.engine_processor.download_with_sequential_engines(keyword, variations, out_dir, max_num)

            # If we still don't have enough images, try DuckDuckGo as final fallback
            if self.total_downloaded < max_num:
                progress.set_subtask_description(f"Using DuckDuckGo fallback: {keyword}")
                self._try_duckduckgo_fallback(
                    keyword=keyword,
                    out_dir=out_dir,
                    max_num=max_num,
                    total_downloaded=self.total_downloaded
                )

            # Rename all files sequentially
            if self.total_downloaded > 0:
                progress.set_subtask_description(f"Renaming images: {keyword}")
                rename_images_sequentially(out_dir)

            # Log engine statistics
            self.engine_processor.log_engine_stats()

            # Update progress with results
            progress.set_subtask_description(f"Downloaded {self.total_downloaded}/{max_num} images for {keyword}")

            return self.total_downloaded > 0, self.total_downloaded

        except Exception as e:
            logger.warning(f"All crawlers failed with error: {e}. Trying DuckDuckGo as fallback.")
            progress.set_subtask_description(f"Error occurred, using final fallback: {keyword}")
            return self._final_duckduckgo_fallback(keyword, out_dir, max_num)

    @staticmethod
    def _try_duckduckgo_fallback(keyword: str, out_dir: str, max_num: int, total_downloaded: int) -> int:
        """
        Attempts to use DuckDuckGo as a fallback option if other engines haven't downloaded enough images.

        Args:
            keyword (str): The search term.
            out_dir (str): The output directory.
            max_num (int): The maximum number of images to download.
            total_downloaded (int): The current count of downloaded images.

        Returns:
            int: The updated total downloaded count after the fallback attempt.
        """
        if total_downloaded >= max_num:
            return total_downloaded

        logger.info(f"Crawlers downloaded {total_downloaded}/{max_num} images. Trying DuckDuckGo as fallback.")
        ddgs_success, ddgs_count = download_images_ddgs(
            keyword=keyword,
            out_dir=out_dir,
            max_num=max_num - total_downloaded
        )
        if ddgs_success:
            return total_downloaded + ddgs_count
        return total_downloaded

    @staticmethod
    def _final_duckduckgo_fallback(keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """
        Performs a final fallback to DuckDuckGo when all other download methods have failed.

        Args:
            keyword (str): The search term.
            out_dir (str): The output directory.
            max_num (int): The maximum number of images to download.

        Returns:
            Tuple[bool, int]: A tuple indicating success (True/False) and the number of images downloaded.
        """
        success, count = download_images_ddgs(keyword, out_dir, max_num)
        if success and count > 0:
            rename_images_sequentially(out_dir)
            return True, count
        else:
            logger.error(f"All download methods failed for '{keyword}'")
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
