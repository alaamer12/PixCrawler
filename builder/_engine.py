"""
This module provides the core logic for processing search engines and downloading images. It includes classes for managing engine configurations, tracking statistics, and orchestrating parallel and sequential image downloads.

Classes:
    EngineMode: Enumeration for different engine processing modes (parallel, sequential).
    EngineConfig: Configuration for a search engine, including offset range and variation step.
    VariationResult: Represents the outcome of processing a single search variation.
    EngineResult: Represents the aggregated result of processing a single search engine.
    EngineStats: Tracks performance statistics for individual search engines.
    EngineProcessor: Manages and orchestrates image downloads across multiple search engines, supporting parallel and sequential modes.
    SingleEngineProcessor: Handles the detailed processing of a single search engine, including its variations.

Functions:
    load_engine_configs: Loads and converts raw engine configurations into EngineConfig objects.
    select_variations: Selects an optimal number of search variations based on download targets.

Features:
    - Centralized management of search engine configurations.
    - Detailed tracking and logging of engine performance and download statistics.
    - Support for parallel and sequential image downloading across various search engines.
    - Intelligent selection and processing of search variations to optimize image retrieval.
    - Robust error handling and monitoring during the download process.
"""

import concurrent.futures
import random
import threading
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import List, Dict, Any, Union, Type

from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler

from _search_engines import SearchEngineConfig, VariationResult, EngineResult, \
    download_google_images, download_bing_images, download_baidu_images
from builder._config import get_engines
from builder._constants import logger
from builder._exceptions import DownloadError, CrawlerError, CrawlerInitializationError, \
    CrawlerExecutionError
from builder._utilities import image_validator

__all__ = [
    'EngineMode',
    'EngineStats',
    'EngineProcessor',
    'SingleEngineProcessor'
]


def load_engine_configs() -> List["SearchEngineConfig"]:
    """
    Loads engine configurations from the system and converts them into a list of EngineConfig objects.

    Returns:
        List[_search_engines.SearchEngineConfig]: A list of configured engine objects.
    """
    raw_engines = get_engines()
    return [
        SearchEngineConfig(
            name=engine['name'],
            offset_range=engine['offset_range'],
            variation_step=engine['variation_step']
        )
        for engine in raw_engines
    ]


def select_variations(variations: List[str], max_num: int) -> List[str]:
    """
    Selects an optimal number of variations based on the target maximum number of images.
    Prioritizes using more variations for higher targets, up to a certain limit.

    Args:
        variations (List[str]): A list of available search variations.
        max_num (int): The maximum number of images to download.

    Returns:
        List[str]: A shuffled list of selected variations.
    """
    # Use more variations for higher targets
    max_variations = min(len(variations), max(3, max_num // 5))
    selected = variations[:max_variations]
    random.shuffle(selected)
    return selected


class EngineMode(StrEnum):
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


@dataclass
class EngineStats:
    """
    Statistics tracking for engine performance.

    Attributes:
        download_count (int): Total number of images downloaded.
        success_count (int): Number of successful variation processes.
        failure_count (int): Number of failed variation processes.
        total_processing_time (float): Total time spent processing.
    """
    download_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_processing_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """
        Calculates the success rate percentage based on successful and failed attempts.

        Returns:
            float: The success rate as a percentage (0.0 to 100.0).
        """
        total_attempts = self.success_count + self.failure_count
        return (
                self.success_count / total_attempts * 100) if total_attempts > 0 else 0.0


class EngineProcessor:
    """
    Enhanced engine processor for managing search engines and image downloading.
    Provides both parallel and sequential processing modes with improved error handling.
    """

    def __init__(self, image_downloader: Any):
        """
        Initializes the EngineProcessor.

        Args:
            image_downloader (Any): An instance of the image downloader, providing download-related functionalities.
        """
        self.image_downloader = image_downloader
        self.engine_configs = load_engine_configs()
        self.engine_stats: Dict[str, EngineStats] = {}
        self.processing_lock = threading.Lock()

    def reset_stats(self) -> None:
        """
        Resets all accumulated engine statistics.
        """
        with self.processing_lock:
            self.engine_stats.clear()

    def _get_or_create_stats(self, engine_name: str) -> EngineStats:
        """
        Retrieves existing statistics for a given engine or creates a new EngineStats object if none exists.

        Args:
            engine_name (str): The name of the engine.

        Returns:
            EngineStats: The statistics object for the specified engine.
        """
        if engine_name not in self.engine_stats:
            self.engine_stats[engine_name] = EngineStats()
        return self.engine_stats[engine_name]

    def update_stats(self, engine_name: str, result: VariationResult) -> None:
        """
        Updates the statistics for a specific engine based on the result of a variation.

        Args:
            engine_name (str): The name of the engine to update.
            result (VariationResult): The result object from a processed variation.
        """
        with self.processing_lock:
            stats = self._get_or_create_stats(engine_name)
            stats.download_count += result.downloaded_count
            stats.total_processing_time += result.processing_time

            if result.success:
                stats.success_count += 1
            else:
                stats.failure_count += 1

    def log_engine_stats(self) -> None:
        """
        Logs comprehensive statistics about image downloads from each engine.
        If no statistics are available, it logs a corresponding message.
        """
        if not self.engine_stats:
            logger.info("No engine statistics available")
            return

        logger.info("=" * 60)
        logger.info("ENGINE PERFORMANCE STATISTICS")
        logger.info("=" * 60)

        total_downloaded = self.image_downloader.total_downloaded

        for engine_name, stats in self.engine_stats.items():
            percentage = (
                    stats.download_count / total_downloaded * 100) if total_downloaded > 0 else 0
            avg_time = stats.total_processing_time / (
                    stats.success_count + stats.failure_count) if (
                                                                      stats.success_count + stats.failure_count) > 0 else 0

            logger.info(f"{engine_name.upper()}:")
            logger.info(
                f"  Downloads: {stats.download_count} images ({percentage:.1f}%)")
            logger.info(f"  Success Rate: {stats.success_rate:.1f}%")
            logger.info(f"  Avg Processing Time: {avg_time:.2f}s")
            logger.info(f"  Total Processing Time: {stats.total_processing_time:.2f}s")
            logger.info("-" * 40)

    def download_with_parallel_engines(self, keyword: str, variations: List[str],
                                       out_dir: str, max_num: int) -> List[
        EngineResult]:
        """
        Downloads images using all configured search engines in parallel.

        Args:
            keyword (str): The main search keyword.
            variations (List[str]): A list of search variations for the keyword.
            out_dir (str): The output directory for downloaded images.
            max_num (int): The maximum number of images to download in total.

        Returns:
            List[EngineResult]: A list of results from each processed engine.
        """
        logger.info(
            f"Starting parallel engine processing for '{keyword}' (target: {max_num} images)")

        results = []
        per_engine_target = self._calculate_per_engine_target(max_num)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.image_downloader.max_parallel_engines,
            thread_name_prefix="EnginePool"
        ) as executor:

            # Submit engine tasks
            engine_futures = {}
            for config in self.engine_configs:
                if config.name == "google":
                    future = executor.submit(download_google_images, keyword,
                                             variations.copy(), out_dir,
                                             per_engine_target, config,
                                             self.image_downloader)
                elif config.name == "bing":
                    future = executor.submit(download_bing_images, keyword,
                                             variations.copy(), out_dir,
                                             per_engine_target, config,
                                             self.image_downloader)
                elif config.name == "baidu":
                    future = executor.submit(download_baidu_images, keyword,
                                             variations.copy(), out_dir,
                                             per_engine_target, config,
                                             self.image_downloader)
                else:
                    future = executor.submit(self._process_engine_parallel, config,
                                             variations.copy(), out_dir,
                                             per_engine_target, max_num)
                engine_futures[future] = config

            # Monitor and collect results
            for future in concurrent.futures.as_completed(engine_futures):
                if self._should_stop_processing(max_num):
                    self._cancel_remaining_futures(engine_futures)
                    break

                try:
                    result = future.result(timeout=300)  # 5 minute timeout per engine
                    results.append(result)
                    logger.info(
                        f"Engine {result.engine_name} completed: {result.total_downloaded} images")
                except concurrent.futures.TimeoutError:
                    config = engine_futures[future]
                    logger.warning(f"Engine {config.name} timed out")
                    results.append(EngineResult(
                        engine_name=config.name,
                        total_downloaded=0,
                        variations_processed=0,
                        success_rate=0.0,
                        processing_time=0.0,
                        variations=[]
                    ))
                except CrawlerError as ce:
                    config = engine_futures[future]
                    logger.error(
                        f"Engine {config.name} failed with crawler error: {ce}")
                    raise ce
                except Exception as e:
                    config = engine_futures[future]
                    logger.error(
                        f"Engine {config.name} failed with unexpected error: {e}")
                    raise DownloadError(
                        f"Engine {config.name} failed during parallel download: {e}") from e

        return results

    def download_with_sequential_engines(self, keyword: str, variations: List[str],
                                         out_dir: str, max_num: int) -> List[
        EngineResult]:
        """
        Downloads images using configured search engines sequentially.

        Args:
            keyword (str): The main search keyword.
            variations (List[str]): A list of search variations for the keyword.
            out_dir (str): The output directory for downloaded images.
            max_num (int): The maximum number of images to download in total.

        Returns:
            List[EngineResult]: A list of results from each processed engine.
        """
        logger.info(
            f"Starting sequential engine processing for '{keyword}' (target: {max_num} images)")

        results = []

        for config in self.engine_configs:
            if self._should_stop_processing(max_num):
                break

            remaining_target = max_num - self.image_downloader.total_downloaded
            if remaining_target <= 0:
                break

            logger.info(
                f"Processing engine: {config.name} (remaining target: {remaining_target})")

            if config.name == "google":
                result = download_google_images(keyword, variations, out_dir,
                                                remaining_target, config,
                                                self.image_downloader)
            elif config.name == "bing":
                result = download_bing_images(keyword, variations, out_dir,
                                              remaining_target, config,
                                              self.image_downloader)
            elif config.name == "baidu":
                result = download_baidu_images(keyword, variations, out_dir,
                                               remaining_target, config,
                                               self.image_downloader)
            else:
                engine_processor = SingleEngineProcessor(self.image_downloader, self)
                result = engine_processor.process_engine(config, variations, out_dir,
                                                         remaining_target, max_num)

            results.append(result)

            # Update global statistics
            for variation_result in result.variations:
                self.update_stats(config.name, variation_result)

            logger.info(
                f"Engine {config.name} completed: {result.total_downloaded}/{remaining_target} images")

        return results

    def _calculate_per_engine_target(self, max_num: int) -> int:
        """
        Calculates the target number of images per engine for parallel processing.

        Args:
            max_num (int): The total maximum number of images to download.

        Returns:
            int: The calculated target number of images for each engine.
        """
        base_target = max_num // len(self.engine_configs)
        # Add buffer to ensure we get enough images
        return max(5, int(base_target * 1.3))

    def _process_engine_parallel(self, config: SearchEngineConfig, variations: List[str],
                                 out_dir: str, per_engine_target: int,
                                 total_max: int) -> EngineResult:
        """
        Processes a single engine in parallel mode.

        Args:
            config (SearchEngineConfig): The configuration for the engine to process.
            variations (List[str]): A list of search variations.
            out_dir (str): The output directory for downloaded images.
            per_engine_target (int): The target number of images for this specific engine.
            total_max (int): The overall maximum number of images to download.

        Returns:
            EngineResult: The result of processing the engine.
        """
        engine_processor = SingleEngineProcessor(self.image_downloader, self)
        result = engine_processor.process_engine(config, variations, out_dir,
                                                 per_engine_target, total_max)

        # Update statistics
        for variation_result in result.variations:
            self.update_stats(config.name, variation_result)

        return result

    def _should_stop_processing(self, max_num: int) -> bool:
        """
        Checks if the image downloading process should be stopped.

        Args:
            max_num (int): The maximum number of images targeted for download.

        Returns:
            bool: True if processing should stop, False otherwise.
        """
        return (self.image_downloader.stop_workers or
                self.image_downloader.total_downloaded >= max_num)

    @staticmethod
    def _cancel_remaining_futures(futures_dict: Dict) -> None:
        """
        Cancels all futures that have not yet completed.

        Args:
            futures_dict (Dict): A dictionary of futures, typically from a ThreadPoolExecutor.
        """
        for future in futures_dict.keys():
            if not future.done():
                future.cancel()

    @staticmethod
    def get_crawler_class(engine_name: str) -> Type[
        Union[GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler, Any]]:
        """
        Retrieves the appropriate iCrawler class based on the engine name.

        Args:
            engine_name (str): The name of the search engine (e.g., "google", "bing", "baidu").

        Returns:
            Type[Union[GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler, Any]]: The iCrawler class corresponding to the engine name.
        """
        crawler_map = {
            "google": GoogleImageCrawler,
            "bing": BingImageCrawler,
            "baidu": BaiduImageCrawler
        }
        return crawler_map.get(engine_name)


class SingleEngineProcessor:
    """
    Handles processing of a single search engine with enhanced error handling and monitoring.
    """

    def __init__(self, image_downloader, engine_processor: EngineProcessor):
        self.image_downloader = image_downloader
        self.engine_processor = engine_processor

    def process_engine(self, config: SearchEngineConfig, variations: List[str],
                       out_dir: str, max_num: int, total_max: int) -> EngineResult:
        """
        Processes a single search engine with comprehensive error handling and monitoring.

        Args:
            config (SearchEngineConfig): The configuration for the engine to process.
            variations (List[str]): A list of search variations for the engine.
            out_dir (str): The output directory for downloaded images.
            max_num (int): The maximum number of images to download for this engine.
            total_max (int): The overall maximum number of images to download across all engines.

        Returns:
            EngineResult: The result of processing the engine.
        """
        start_time = time.time()
        downloaded_count = 0
        variation_results = []

        try:
            logger.info(f"Starting {config.name} engine (target: {max_num} images)")

            # Calculate variations to process
            variations_to_process = select_variations(variations, max_num)

            # Process variations with parallel execution
            if self.image_downloader.max_parallel_variations > 1:
                variation_results = self._process_variations_parallel(
                    config, variations_to_process, out_dir, max_num, total_max
                )
            else:
                variation_results = self._process_variations_sequential(
                    config, variations_to_process, out_dir, max_num, total_max
                )

            # Calculate totals
            downloaded_count = sum(
                result.downloaded_count for result in variation_results)

        except (CrawlerInitializationError, CrawlerExecutionError) as ce:
            logger.error(f"Engine {config.name} failed with crawler error: {ce}")
            variation_results.append(VariationResult(
                variation="engine_failure",
                downloaded_count=0,
                success=False,
                error=str(ce)
            ))
        except Exception as e:
            logger.error(f"Engine {config.name} failed with unexpected error: {e}")
            variation_results.append(VariationResult(
                variation="engine_failure",
                downloaded_count=0,
                success=False,
                error=str(e)
            ))

        processing_time = time.time() - start_time
        success_rate = self._calculate_success_rate(variation_results)

        return EngineResult(
            engine_name=config.name,
            total_downloaded=downloaded_count,
            variations_processed=len(variation_results),
            success_rate=success_rate,
            processing_time=processing_time,
            variations=variation_results
        )

    def _process_variations_parallel(self, config: SearchEngineConfig, variations: List[str],
                                     out_dir: str, max_num: int, total_max: int) -> \
    List[VariationResult]:
        """
        Processes multiple search variations in parallel for a given engine.

        Args:
            config (SearchEngineConfig): The configuration for the engine.
            variations (List[str]): A list of search variations to process.
            out_dir (str): The output directory for downloaded images.
            max_num (int): The maximum number of images to download for this engine.
            total_max (int): The overall maximum number of images to download across all engines.

        Returns:
            List[VariationResult]: A list of results for each processed variation.
        """
        results = []
        per_variation_limit = max(2, max_num // len(variations))

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.image_downloader.max_parallel_variations,
            thread_name_prefix=f"{config.name}VariationPool"
        ) as executor:

            # Submit variation tasks
            variation_futures = {
                executor.submit(
                    self._process_single_variation,
                    config, variation, i, out_dir, per_variation_limit, total_max
                ): variation for i, variation in enumerate(variations)
            }

            # Collect results
            for future in concurrent.futures.as_completed(variation_futures):
                if self._should_stop_processing(total_max):
                    break

                try:
                    result = future.result(
                        timeout=120)  # 2 minute timeout per variation
                    results.append(result)
                    self._update_global_counters(result)
                except concurrent.futures.TimeoutError:
                    variation = variation_futures[future]
                    logger.warning(
                        f"Variation '{variation}' timed out for {config.name}")
                    results.append(VariationResult(
                        variation=variation,
                        downloaded_count=0,
                        success=False,
                        error="Timeout"
                    ))
                except (CrawlerInitializationError, CrawlerExecutionError) as ce:
                    variation = variation_futures[future]
                    logger.error(
                        f"Crawler error for variation '{variation}' in {config.name}: {ce}")
                    results.append(VariationResult(
                        variation=variation,
                        downloaded_count=0,
                        success=False,
                        error=str(ce)
                    ))
                except Exception as e:
                    variation = variation_futures[future]
                    logger.error(
                        f"Unexpected error for variation '{variation}' in {config.name}: {e}")
                    results.append(VariationResult(
                        variation=variation,
                        downloaded_count=0,
                        success=False,
                        error=str(e)
                    ))

        return results

    def _process_variations_sequential(self, config: SearchEngineConfig,
                                       variations: List[str],
                                       out_dir: str, max_num: int, total_max: int) -> \
    List[VariationResult]:
        """
        Processes multiple search variations sequentially for a given engine.

        Args:
            config (SearchEngineConfig): The configuration for the engine.
            variations (List[str]): A list of search variations to process.
            out_dir (str): The output directory for downloaded images.
            max_num (int): The maximum number of images to download for this engine.
            total_max (int): The overall maximum number of images to download across all engines.

        Returns:
            List[VariationResult]: A list of results for each processed variation.
        """
        results = []
        downloaded_so_far = 0

        for i, variation in enumerate(variations):
            if self._should_stop_processing(total_max) or downloaded_so_far >= max_num:
                break

            remaining_limit = min(max_num - downloaded_so_far,
                                  max_num // len(variations))
            if remaining_limit <= 0:
                break

            result = self._process_single_variation(
                config, variation, i, out_dir, remaining_limit, total_max
            )

            results.append(result)
            downloaded_so_far += result.downloaded_count
            self._update_global_counters(result)

            # Small delay between variations
            time.sleep(self.image_downloader.delay_between_searches)

        return results

    def _process_single_variation(self, config: SearchEngineConfig, variation: str,
                                  variation_index: int, out_dir: str,
                                  max_num: int, total_max: int) -> VariationResult:
        """
        Processes a single search variation, including crawling and counting downloaded images.

        Args:
            config (SearchEngineConfig): The configuration for the engine.
            variation (str): The specific search variation string.
            variation_index (int): The index of the current variation, used for offset calculation.
            out_dir (str): The output directory for downloaded images.
            max_num (int): The maximum number of images to download for this variation.
            total_max (int): The overall maximum number of images to download across all engines.

        Returns:
            VariationResult: The result of processing this single variation.
        """
        start_time = time.time()

        if self._should_stop_processing(total_max):
            return VariationResult(
                variation=variation,
                downloaded_count=0,
                success=False,
                error="Processing stopped"
            )

        try:
            # Calculate parameters
            current_offset = config.random_offset + (
                    variation_index * config.variation_step)
            actual_limit = min(max_num, self._calculate_remaining_capacity(total_max))

            if actual_limit <= 0:
                return VariationResult(
                    variation=variation,
                    downloaded_count=0,
                    success=False,
                    error="No remaining capacity"
                )

            logger.info(
                f"{config.name}: Processing '{variation}' (limit: {actual_limit}, offset: {current_offset})")

            # Create and configure crawler
            crawler = self._create_enhanced_crawler(config.name, out_dir)
            file_idx_offset = self._get_current_file_offset()

            # Perform crawl
            crawler.crawl(
                keyword=variation,
                max_num=actual_limit,
                min_size=self.image_downloader.min_image_size,
                offset=current_offset,
                file_idx_offset=file_idx_offset
            )

            # Count results
            downloaded_count = self._count_variation_results(out_dir, file_idx_offset)
            processing_time = time.time() - start_time

            logger.info(
                f"{config.name}: '{variation}' completed - {downloaded_count} images in {processing_time:.2f}s")

            return VariationResult(
                variation=variation,
                downloaded_count=downloaded_count,
                success=True,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.warning(
                f"{config.name}: '{variation}' failed after {processing_time:.2f}s - {e}")

            return VariationResult(
                variation=variation,
                downloaded_count=0,
                success=False,
                error=str(e),
                processing_time=processing_time
            )

    def _create_enhanced_crawler(self, engine_name: str, out_dir: str) -> Any:
        """
        Creates a crawler instance with enhanced error handling and applies a safe parser wrapper.

        Args:
            engine_name (str): The name of the engine for which to create the crawler.
            out_dir (str): The output directory for downloaded images.

        Returns:
            Any: An instance of the configured and wrapped crawler.

        Raises:
            ValueError: If no crawler class is found for the given engine name.
        """
        crawler_class = self.engine_processor.get_crawler_class(engine_name)
        if not crawler_class:
            raise CrawlerInitializationError(
                f"No crawler class found for engine: {engine_name}")

        try:
            crawler = self.engine_processor.create_crawler(crawler_class, out_dir)
            self._apply_safe_parser_wrapper(crawler, engine_name)
            return crawler
        except Exception as e:
            raise CrawlerInitializationError(
                f"Failed to initialize crawler for {engine_name}: {e}") from e

    @staticmethod
    def _apply_safe_parser_wrapper(crawler: Any, engine_name: str) -> None:
        """
        Applies an enhanced parser wrapper to the crawler to improve error handling and result validation.

        Args:
            crawler (Any): The crawler instance to wrap.
            engine_name (str): The name of the engine associated with the crawler.
        """
        try:
            original_parse = crawler.parser.parse

            def enhanced_parse_wrapper(*args, **kwargs):
                try:
                    result = original_parse(*args, **kwargs)

                    # Handle None results
                    if result is None:
                        logger.debug(f"Parser for {engine_name} returned None")
                        return []

                    # Ensure result is iterable
                    if not hasattr(result, '__iter__'):
                        logger.warning(
                            f"Parser for {engine_name} returned non-iterable: {type(result)}")
                        return []

                    return result

                except Exception as e:
                    logger.warning(f"Parser exception in {engine_name}: {e}")
                    return []

            crawler.parser.parse = enhanced_parse_wrapper

        except Exception as e:
            logger.error(f"Failed to apply parser wrapper for {engine_name}: {e}")

    def _should_stop_processing(self, total_max: int) -> bool:
        """
        Checks if the image downloading process should be stopped based on global flags or total downloaded count.

        Args:
            total_max (int): The overall maximum number of images to download.

        Returns:
            bool: True if processing should stop, False otherwise.
        """
        return (self.image_downloader.stop_workers or
                self.image_downloader.total_downloaded >= total_max)

    def _calculate_remaining_capacity(self, total_max: int) -> int:
        """
        Calculates the remaining download capacity based on the total maximum and already downloaded images.

        Args:
            total_max (int): The overall maximum number of images to download.

        Returns:
            int: The remaining capacity for downloads.
        """
        with self.image_downloader.lock:
            return max(0, total_max - self.image_downloader.total_downloaded)

    def _get_current_file_offset(self) -> int:
        """
        Retrieves the current file index offset for naming downloaded images.

        Returns:
            int: The current total number of downloaded images, used as an offset.
        """
        with self.image_downloader.lock:
            return self.image_downloader.total_downloaded

    def _count_variation_results(self, out_dir: str, file_idx_offset: int) -> int:
        """
        Counts the number of valid images downloaded in the latest batch for a specific variation.

        Args:
            out_dir (str): The output directory where images are downloaded.
            file_idx_offset (int): The starting file index offset for counting.

        Returns:
            int: The number of valid images found.
        """
        with self.image_downloader.lock:
            return image_validator.count_valid_in_latest_batch(out_dir, file_idx_offset)

    def _update_global_counters(self, result: VariationResult) -> None:
        """
        Updates the global download counters based on the results of a variation.

        Args:
            result (VariationResult): The result object from a processed variation.
        """
        with self.image_downloader.lock:
            self.image_downloader.total_downloaded += result.downloaded_count

    @staticmethod
    def _calculate_success_rate(results: List[VariationResult]) -> float:
        """
        Calculates the success rate from a list of variation results.

        Args:
            results (List[VariationResult]): A list of VariationResult objects.

        Returns:
            float: The success rate as a percentage (0.0 to 100.0).
        """
        if not results:
            return 0.0

        successful = sum(1 for result in results if result.success)
        return (successful / len(results)) * 100
