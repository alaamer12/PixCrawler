import concurrent.futures
import logging
import os
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Any, Optional, Protocol

import requests
from duckduckgo_search import DDGS
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler

from helpers import progress
from config import get_search_variations, get_engines
from constants import logger
from utilities import validate_image, rename_images_sequentially, count_valid_images_in_latest_batch


class IDownloader(Protocol):
    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        ...


@dataclass
class VariationResult:
    variation: str
    downloaded_count: int
    success: bool
    error: Optional[str] = None

    def __repr__(self):
        return f"VariationResult(variation='{self.variation}', downloaded={self.downloaded_count}, success={self.success})"


class DuckDuckGoImageDownloader(IDownloader):
    """
    A class to download images using DuckDuckGo search as a fallback mechanism.

    Uses parallel processing for faster downloads.
    """

    def __init__(self, max_workers: int = 4):
        """
        Initialize the downloader with default settings.

        Args:
            max_workers: Maximum number of parallel download workers
        """
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.timeout = 20
        self.min_file_size = 1000  # bytes
        self.delay = 0.2  # seconds between downloads
        self.max_workers = max_workers
        self.lock = threading.RLock()

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

    def _download_single_image(self, result: dict, out_dir: str, index: int) -> bool:
        """
        Download a single image from a search result.

        Args:
            result: Search result dictionary
            out_dir: Output directory
            index: Image index for filename

        Returns:
            bool: True if download was successful, False otherwise
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
        Search for images with a keyword and download them in parallel.

        Args:
            keyword: Search term
            out_dir: Output directory
            max_count: Maximum number of images to download

        Returns:
            int: Number of successfully downloaded images
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
        Fetch image search results from DuckDuckGo.

        Args:
            keyword: Search term
            max_count: Maximum number of images needed

        Returns:
            List of search result dictionaries
        """
        with DDGS() as ddgs:
            # Request more images than needed to account for failures
            results = list(ddgs.images(keyword, max_results=max_count * 3))
            logger.info(f"Found {len(results)} potential images for '{keyword}'")
            return results

    def _execute_parallel_downloads(self, results: List[dict], out_dir: str, max_count: int) -> int:
        """
        Execute parallel downloads of images from search results.

        Args:
            results: List of search result dictionaries
            out_dir: Output directory
            max_count: Maximum number of images to download

        Returns:
            Number of successfully downloaded images
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
                except Exception as e:
                    logger.warning(f"Error downloading image: {e}")

        return downloaded

    @staticmethod
    def _cancel_pending_futures(futures: List[concurrent.futures.Future]) -> None:
        """
        Cancel any pending futures to avoid unnecessary downloads.

        Args:
            futures: List of futures to check and potentially cancel
        """
        for future in futures:
            if not future.done():
                future.cancel()

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

        except Exception as e:
            logger.error(f"Failed to download images for '{keyword}': {str(e)}")
            return False, 0


def download_images_ddgs(keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
    """
    Download images directly using DuckDuckGo search engine.

    Args:
        keyword: Search term for images
        out_dir: Output directory path
        max_num: Maximum number of images to download

    Returns:
        Tuple of (success_flag, downloaded_count)
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(out_dir, exist_ok=True)

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
    except Exception as e:
        logger.error(f"Error downloading images from DuckDuckGo: {str(e)}")
        return False, 0


class EngineProcessor:
    """
    A class that manages search engines and their configurations for image downloading.
    Handles engine processing, statistics, and crawler management.
    """

    def __init__(self, image_downloader):
        """
        Initialize the EngineManager.

        Args:
            image_downloader: Reference to the parent ImageDownloader instance
        """
        self.image_downloader = image_downloader
        self.engines = get_engines()
        self.engine_stats = {}

    def reset_stats(self) -> None:
        """Reset engine statistics."""
        self.engine_stats = {}

    def update_stats(self, engine_name: str, count: int) -> None:
        """
        Update statistics for a specific engine.

        Args:
            engine_name: Name of the engine
            count: Number of images downloaded
        """
        if engine_name not in self.engine_stats:
            self.engine_stats[engine_name] = 0
        self.engine_stats[engine_name] += count

    def log_engine_stats(self) -> None:
        """Log statistics about downloads from each engine."""
        if not self.engine_stats:
            return

        logger.info("Download statistics by engine:")
        total_downloaded = self.image_downloader.total_downloaded
        for engine, count in self.engine_stats.items():
            percentage = (count / total_downloaded * 100) if total_downloaded > 0 else 0
            logger.info(f"  {engine.capitalize()}: {count} images ({percentage:.1f}%)")

    def download_with_parallel_engines(self, keyword: str, variations: List[str],
                                       out_dir: str, max_num: int) -> None:
        """
        Download images using all search engines in parallel.

        Args:
            keyword: Search term
            variations: List of search variations
            out_dir: Output directory
            max_num: Maximum number of images to download
        """
        # Create a thread pool for all engines
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.image_downloader.max_parallel_engines) as executor:
            # Submit tasks for each engine
            futures = []

            # Calculate per-engine target (with some overlap to ensure we get enough images)
            per_engine_target = max(5, int(max_num / len(self.engines) * 1.5))

            # Submit tasks for each engine
            for engine_config in self.engines:
                # Get a subset of variations for this engine
                engine_variations = variations.copy()
                random.shuffle(engine_variations)  # Shuffle again for diversity

                futures.append(executor.submit(
                    self._process_engine_with_parallel_variations,
                    engine_config=engine_config,
                    variations=engine_variations,
                    out_dir=out_dir,
                    max_num=per_engine_target,
                    total_max=max_num
                ))

            # Monitor progress
            completed = 0
            while completed < len(futures) and self.image_downloader.total_downloaded < max_num:
                # Check if we've reached our download target
                if self.image_downloader.total_downloaded >= max_num:
                    # Signal workers to stop
                    self.image_downloader.stop_workers = True
                    # Cancel pending futures
                    for future in futures:
                        if not future.done():
                            future.cancel()
                    break

                # Wait for some futures to complete
                done, not_done = concurrent.futures.wait(
                    futures,
                    timeout=1.0,
                    return_when=concurrent.futures.FIRST_COMPLETED
                )

                # Update completed count
                completed += len(done)

                # Replace futures list with not_done
                futures = list(not_done)

                # Log progress
                logger.info(f"Downloaded {self.image_downloader.total_downloaded}/{max_num} images so far")

    def download_with_sequential_engines(self, keyword: str, variations: List[str],
                                         out_dir: str, max_num: int) -> None:
        """
        Download images using engines in sequence with fallbacks.

        Args:
            keyword: Search term
            variations: List of search variations
            out_dir: Output directory
            max_num: Maximum number of images to download
        """
        # Try each engine in sequence
        for engine_config in self.engines:
            if self.image_downloader.total_downloaded >= max_num:
                break

            # Process this engine
            engine = Engine(self.image_downloader)
            engine_count = engine.process(
                engine_config=engine_config,
                variations=variations,
                out_dir=out_dir,
                max_num=max_num - self.image_downloader.total_downloaded,
                total_max=max_num
            )

            # Update total downloaded
            with self.image_downloader.lock:
                self.image_downloader.total_downloaded += engine_count

                # Update engine stats
                engine_name = engine_config['name']
                self.update_stats(engine_name, engine_count)

    def _process_engine_with_parallel_variations(self, engine_config: dict, variations: List[str],
                                                 out_dir: str, max_num: int, total_max: int) -> int:
        """
        Process a search engine with parallel variations.

        Args:
            engine_config: Engine configuration
            variations: List of search variations
            out_dir: Output directory
            max_num: Maximum images for this engine
            total_max: Overall maximum images

        Returns:
            Number of images downloaded
        """
        if self.image_downloader.stop_workers:
            return 0

        engine_name = engine_config['name']
        offset_min, offset_max = engine_config['offset_range']
        variation_step = engine_config['variation_step']

        logger.info(f"Starting parallel download using {engine_name.capitalize()}ImageCrawler")

        # Track engine downloads
        engine_downloaded = 0

        # Use a thread pool for variations
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.image_downloader.max_parallel_variations) as variation_executor:
            variation_futures = []

            # Calculate how many variations to use
            variations_to_use = min(len(variations), max(3, int(max_num / 3)))
            selected_variations = variations[:variations_to_use]

            # Submit tasks for each variation
            for i, variation in enumerate(selected_variations):
                if self.image_downloader.stop_workers:
                    break

                # Calculate random offset for this variation
                random_offset = random.randint(offset_min, offset_max) + (i * variation_step)

                # Calculate per-variation limit
                per_variation_limit = max(3, int(max_num / variations_to_use))

                variation_futures.append(variation_executor.submit(
                    self._process_single_variation,
                    engine_name=engine_name,
                    variation=variation,
                    out_dir=out_dir,
                    max_num=per_variation_limit,
                    offset=random_offset,
                    engine_downloaded=engine_downloaded
                ))

                # Small delay to avoid overwhelming the search engines
                time.sleep(0.1)

            # Wait for variations to complete
            for future in concurrent.futures.as_completed(variation_futures):
                if self.image_downloader.stop_workers:
                    break

                try:
                    # Get the number of images downloaded by this variation
                    variation_count = future.result()

                    # Update engine downloaded count
                    with self.image_downloader.lock:
                        engine_downloaded += variation_count
                        self.image_downloader.total_downloaded += variation_count

                        # Update engine stats
                        self.update_stats(engine_name, variation_count)

                        # Check if we've reached the target
                        if self.image_downloader.total_downloaded >= total_max:
                            self.image_downloader.stop_workers = True
                            break

                except Exception as e:
                    logger.warning(f"Error processing variation for {engine_name}: {e}")

        logger.info(f"{engine_name.capitalize()} engine downloaded {engine_downloaded} images")
        return engine_downloaded

    def _process_single_variation(self, engine_name: str, variation: str,
                                  out_dir: str, max_num: int, offset: int,
                                  engine_downloaded: int) -> int:
        """
        Process a single search variation.

        Args:
            engine_name: Name of the search engine
            variation: Search variation
            out_dir: Output directory
            max_num: Maximum images to download
            offset: Search offset
            engine_downloaded: Current engine download count

        Returns:
            Number of images downloaded
        """
        if self.image_downloader.stop_workers:
            return 0

        logger.info(f"{engine_name}: Downloading up to {max_num} images for '{variation}' (offset: {offset})")

        try:
            # Get crawler class
            crawler_class = self.get_crawler_class(engine_name)
            if not crawler_class:
                return 0

            # Create crawler
            crawler = self.create_crawler(crawler_class, out_dir)

            # Calculate file index offset
            with self.image_downloader.lock:
                file_idx_offset = self.image_downloader.total_downloaded + engine_downloaded

            try:
                # Patch the crawler's parser to handle None gracefully
                original_parse = crawler.parser.parse

                def safe_parse_wrapper(*args, **kwargs):
                    try:
                        result = original_parse(*args, **kwargs)
                        # Ensure parse always returns an iterable
                        if result is None:
                            logger.warning(f"Parser for {engine_name} returned None, using empty list")
                            return []
                        return result
                    except Exception as e:
                        logger.warning(f"Parser exception in {engine_name}: {e}")
                        return []

                crawler.parser.parse = safe_parse_wrapper
            except Exception as e:
                logger.warning(f"Failed to patch parser for {engine_name}: {e}")

            # Crawl for images
            crawler.crawl(
                keyword=variation,
                max_num=max_num,
                min_size=self.image_downloader.min_image_size,
                offset=offset,
                file_idx_offset=file_idx_offset
            )

            # Count valid images
            with self.image_downloader.lock:
                temp_valid_count = count_valid_images_in_latest_batch(
                    out_dir,
                    file_idx_offset
                )

            logger.info(f"{engine_name} downloaded {temp_valid_count} valid images for '{variation}'")
            return temp_valid_count

        except Exception as e:
            logger.warning(f"{engine_name} crawler failed for '{variation}': {e}")
            return 0

    @staticmethod
    def get_crawler_class(engine_name: str) -> Any:
        """
        Get the crawler class based on engine name.

        Args:
            engine_name: Name of the search engine

        Returns:
            Crawler class
        """
        crawler_map = {
            "google": GoogleImageCrawler,
            "bing": BingImageCrawler,
            "baidu": BaiduImageCrawler
        }
        return crawler_map.get(engine_name)

    def create_crawler(self, crawler_class, out_dir: str):
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
            log_level=self.image_downloader.log_level,
            feeder_threads=self.image_downloader.feeder_threads,
            parser_threads=self.image_downloader.parser_threads,
            downloader_threads=self.image_downloader.downloader_threads
        )


class Engine:
    """
    A class for processing a single search engine to download images.
    """

    def __init__(self, image_downloader):
        self.image_downloader = image_downloader
        self.engine_manager = image_downloader.engine_manager

    def process(self, engine_config: dict, variations: List[str],
                out_dir: str, max_num: int, total_max: int) -> int:
        """
        Process a search engine to download images with enhanced error handling and monitoring.

        Args:
            engine_config: Engine configuration
            variations: List of search variations
            out_dir: Output directory
            max_num: Maximum images for this engine
            total_max: Overall maximum images

        Returns:
            Number of images downloaded
        """
        if self._should_stop():
            return 0

        engine_name = engine_config['name']
        engine_downloaded = 0

        try:
            # Initialize engine processing
            engine_context = self._initialize_engine_context(engine_config, variations, max_num)
            logger.info(f"Attempting download using {engine_name.capitalize()}ImageCrawler")

            # Process each variation
            for variation_result in self._process_variations(engine_context, variations, out_dir, total_max):
                if self._should_stop() or self._reached_total_limit(total_max):
                    break

                engine_downloaded += variation_result.downloaded_count

                # Log progress
                self._log_variation_progress(engine_name, variation_result, engine_downloaded, total_max)

                # Check if we've reached the engine limit
                if engine_downloaded >= max_num:
                    break

            # Log final engine statistics
            self._log_engine_completion(engine_name, engine_downloaded, max_num)

        except Exception as e:
            logger.warning(f"{engine_name} engine failed: {e}")

        return engine_downloaded

    def _should_stop(self) -> bool:
        """Check if processing should stop."""
        return self.image_downloader.stop_workers

    def _reached_total_limit(self, total_max: int) -> bool:
        """Check if total download limit has been reached."""
        return self.image_downloader.total_downloaded >= total_max

    @staticmethod
    def _initialize_engine_context(engine_config: dict, variations: List[str], max_num: int) -> dict:
        """Initialize context for engine processing."""
        offset_min, offset_max = engine_config['offset_range']
        return {
            'name': engine_config['name'],
            'random_offset': random.randint(offset_min, offset_max),
            'variation_step': engine_config['variation_step'],
            'per_variation_limit': max(2, max_num // len(variations))
        }

    def _process_variations(self, engine_context: dict, variations: List[str],
                            out_dir: str, total_max: int):
        """
        Generator that processes each variation and yields results.

        Args:
            engine_context: Engine processing context
            variations: List of search variations
            out_dir: Output directory
            total_max: Overall maximum images

        Yields:
            VariationResult: Result of processing each variation
        """
        for i, variation in enumerate(variations):
            if self._should_stop() or self._reached_total_limit(total_max):
                break

            # Calculate remaining capacity
            remaining_capacity = self._calculate_remaining_capacity(total_max)
            if remaining_capacity <= 0:
                break

            # Process single variation
            result = self._process_single_variation(
                engine_context, variation, i, out_dir, remaining_capacity
            )

            yield result

            # Delay between variations
            time.sleep(self.image_downloader.delay_between_searches)

    def _calculate_remaining_capacity(self, total_max: int) -> int:
        """Calculate remaining download capacity."""
        with self.image_downloader.lock:
            return total_max - self.image_downloader.total_downloaded

    def _process_single_variation(self, engine_context: dict, variation: str,
                                  variation_index: int, out_dir: str, max_remaining: int):
        """
        Process a single search variation.

        Args:
            engine_context: Engine processing context
            variation: Search variation to process
            variation_index: Index of the variation
            out_dir: Output directory
            max_remaining: Maximum remaining images to download

        Returns:
            VariationResult: Result of processing this variation
        """
        engine_name = engine_context['name']
        current_limit = min(max_remaining, engine_context['per_variation_limit'])
        current_offset = engine_context['random_offset'] + (variation_index * engine_context['variation_step'])

        logger.info(
            f"{engine_name}: Downloading {current_limit} images for '{variation}' (offset: {current_offset})"
        )

        try:
            # Create and configure crawler
            crawler = self._create_and_configure_crawler(engine_name, out_dir)

            # Calculate file index offset
            file_idx_offset = self._get_current_file_offset()

            # Perform crawl
            crawler.crawl(
                keyword=variation,
                max_num=current_limit,
                min_size=self.image_downloader.min_image_size,
                offset=current_offset,
                file_idx_offset=file_idx_offset
            )

            # Count and return results
            downloaded_count = self._count_variation_results(out_dir, file_idx_offset)

            return VariationResult(
                variation=variation,
                downloaded_count=downloaded_count,
                success=True,
                error=None
            )

        except Exception as e:
            logger.warning(f"{engine_name} crawler failed for '{variation}': {e}")
            return VariationResult(
                variation=variation,
                downloaded_count=0,
                success=False,
                error=str(e)
            )

    def _create_and_configure_crawler(self, engine_name: str, out_dir: str):
        """Create and configure a crawler with enhanced error handling."""
        crawler_class = self.engine_manager.get_crawler_class(engine_name)
        crawler = self.engine_manager.create_crawler(crawler_class, out_dir)

        # Apply safe parser wrapper
        self._apply_safe_parser_wrapper(crawler, engine_name)

        return crawler

    @staticmethod
    def _apply_safe_parser_wrapper(crawler, engine_name: str):
        """Apply safe parser wrapper to handle None returns gracefully."""
        try:
            original_parse = crawler.parser.parse

            def safe_parse_wrapper(*args, **kwargs):
                try:
                    result = original_parse(*args, **kwargs)
                    if result is None:
                        logger.warning(f"Parser for {engine_name} returned None, using empty list")
                        return []
                    return result
                except Exception as e:
                    logger.warning(f"Parser exception in {engine_name}: {e}")
                    return []

            crawler.parser.parse = safe_parse_wrapper
        except Exception as e:
            logger.warning(f"Failed to patch parser for {engine_name}: {e}")

    def _get_current_file_offset(self) -> int:
        """Get current file index offset for naming."""
        with self.image_downloader.lock:
            return self.image_downloader.total_downloaded

    def _count_variation_results(self, out_dir: str, file_idx_offset: int) -> int:
        """Count valid images from the latest batch."""
        with self.image_downloader.lock:
            return count_valid_images_in_latest_batch(out_dir, file_idx_offset)

    def _log_variation_progress(self, engine_name: str, result, engine_downloaded: int, total_max: int):
        """Log progress for a single variation."""
        total_so_far = self.image_downloader.total_downloaded + engine_downloaded
        logger.info(
            f"{engine_name} downloaded {result.downloaded_count} valid images for '{result.variation}', "
            f"engine total: {engine_downloaded}, overall: {total_so_far}/{total_max}"
        )

    @staticmethod
    def _log_engine_completion(engine_name: str, engine_downloaded: int, max_num: int):
        """Log completion statistics for the engine."""
        success_rate = (engine_downloaded / max_num * 100) if max_num > 0 else 0
        logger.info(
            f"{engine_name.capitalize()} engine completed: {engine_downloaded}/{max_num} images "
            f"({success_rate:.1f}% success rate)"
        )


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
        Initialize the ImageDownloader with configurable parameters.

        Args:
            feeder_threads: Number of feeder threads for crawlers
            parser_threads: Number of parser threads for crawlers
            downloader_threads: Number of downloader threads for crawlers
            min_image_size: Minimum image size as (width, height) tuple
            delay_between_searches: Delay in seconds between different search terms
            log_level: Logging level for crawlers
            max_parallel_engines: Maximum number of search engines to use in parallel
            max_parallel_variations: Maximum number of search variations to run in parallel per engine
            use_all_engines: Whether to use all engines in parallel (True) or fallback mode (False)
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
        Download images using multiple image crawlers in parallel.

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
        Try DuckDuckGo as a fallback option when other engines haven't downloaded enough images.

        Args:
            keyword: Search term
            out_dir: Output directory
            max_num: Maximum number of images to download
            total_downloaded: Current download count

        Returns:
            Updated total downloaded count
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
