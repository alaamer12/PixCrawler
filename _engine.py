import concurrent.futures
import random
import threading
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Tuple, Optional, List, Dict, Any

from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler

from config import get_engines
from constants import logger
from utilities import count_valid_images_in_latest_batch


def load_engine_configs() -> List["EngineConfig"]:
    """Load and convert engine configurations."""
    raw_engines = get_engines()
    return [
        EngineConfig(
            name=engine['name'],
            offset_range=engine['offset_range'],
            variation_step=engine['variation_step']
        )
        for engine in raw_engines
    ]


def select_variations(variations: List[str], max_num: int) -> List[str]:
    """Select optimal number of variations based on target."""
    # Use more variations for higher targets
    max_variations = min(len(variations), max(3, max_num // 5))
    selected = variations[:max_variations]
    random.shuffle(selected)
    return selected


class EngineMode(StrEnum):
    """Enumeration for different engine processing modes."""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"


@dataclass
class EngineConfig:
    """Configuration for a search engine."""
    name: str
    offset_range: Tuple[int, int]
    variation_step: int

    @property
    def random_offset(self) -> int:
        """Generate a random offset within the engine's range."""
        return random.randint(*self.offset_range)


@dataclass
class VariationResult:
    """Result of processing a single search variation."""
    variation: str
    downloaded_count: int
    success: bool
    error: Optional[str] = None
    processing_time: float = 0.0

    def __repr__(self):
        return (f"VariationResult(variation='{self.variation}', "
                f"downloaded={self.downloaded_count}, "
                f"success={self.success})"
                f"error={self.error})"
                f"processing time={self.processing_time})")


@dataclass
class EngineResult:
    """Result of processing a single engine."""
    engine_name: str
    total_downloaded: int
    variations_processed: int
    success_rate: float
    processing_time: float
    variations: List[VariationResult] = field(default_factory=list)


@dataclass
class EngineStats:
    """Statistics tracking for engine performance."""
    download_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_processing_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total_attempts = self.success_count + self.failure_count
        return (self.success_count / total_attempts * 100) if total_attempts > 0 else 0.0


class EngineProcessor:
    """
    Enhanced engine processor for managing search engines and image downloading.
    Provides both parallel and sequential processing modes with improved error handling.
    """

    def __init__(self, image_downloader):
        """Initialize the EngineProcessor."""
        self.image_downloader = image_downloader
        self.engine_configs = load_engine_configs()
        self.engine_stats: Dict[str, EngineStats] = {}
        self.processing_lock = threading.Lock()

    def reset_stats(self) -> None:
        """Reset all engine statistics."""
        with self.processing_lock:
            self.engine_stats.clear()

    def _get_or_create_stats(self, engine_name: str) -> EngineStats:
        """Get or create statistics for an engine."""
        if engine_name not in self.engine_stats:
            self.engine_stats[engine_name] = EngineStats()
        return self.engine_stats[engine_name]

    def update_stats(self, engine_name: str, result: VariationResult) -> None:
        """Update statistics for a specific engine."""
        with self.processing_lock:
            stats = self._get_or_create_stats(engine_name)
            stats.download_count += result.downloaded_count
            stats.total_processing_time += result.processing_time

            if result.success:
                stats.success_count += 1
            else:
                stats.failure_count += 1

    def log_engine_stats(self) -> None:
        """Log comprehensive statistics about downloads from each engine."""
        if not self.engine_stats:
            logger.info("No engine statistics available")
            return

        logger.info("=" * 60)
        logger.info("ENGINE PERFORMANCE STATISTICS")
        logger.info("=" * 60)

        total_downloaded = self.image_downloader.total_downloaded

        for engine_name, stats in self.engine_stats.items():
            percentage = (stats.download_count / total_downloaded * 100) if total_downloaded > 0 else 0
            avg_time = stats.total_processing_time / (stats.success_count + stats.failure_count) if (
                                                                                                            stats.success_count + stats.failure_count) > 0 else 0

            logger.info(f"{engine_name.upper()}:")
            logger.info(f"  Downloads: {stats.download_count} images ({percentage:.1f}%)")
            logger.info(f"  Success Rate: {stats.success_rate:.1f}%")
            logger.info(f"  Avg Processing Time: {avg_time:.2f}s")
            logger.info(f"  Total Processing Time: {stats.total_processing_time:.2f}s")
            logger.info("-" * 40)

    def download_with_parallel_engines(self, keyword: str, variations: List[str],
                                       out_dir: str, max_num: int) -> List[EngineResult]:
        """
        Download images using all search engines in parallel with improved resource management.
        """
        logger.info(f"Starting parallel engine processing for '{keyword}' (target: {max_num} images)")

        results = []
        per_engine_target = self._calculate_per_engine_target(max_num)

        with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.image_downloader.max_parallel_engines,
                thread_name_prefix="EnginePool"
        ) as executor:

            # Submit engine tasks
            engine_futures = {
                executor.submit(
                    self._process_engine_parallel,
                    config, variations.copy(), out_dir, per_engine_target, max_num
                ): config for config in self.engine_configs
            }

            # Monitor and collect results
            for future in concurrent.futures.as_completed(engine_futures):
                if self._should_stop_processing(max_num):
                    self._cancel_remaining_futures(engine_futures)
                    break

                try:
                    result = future.result(timeout=300)  # 5 minute timeout per engine
                    results.append(result)
                    logger.info(f"Engine {result.engine_name} completed: {result.total_downloaded} images")
                except concurrent.futures.TimeoutError:
                    config = engine_futures[future]
                    logger.warning(f"Engine {config.name} timed out")
                except Exception as e:
                    config = engine_futures[future]
                    logger.error(f"Engine {config.name} failed: {e}")

        return results

    def download_with_sequential_engines(self, keyword: str, variations: List[str],
                                         out_dir: str, max_num: int) -> List[EngineResult]:
        """
        Download images using engines in sequence with enhanced fallback handling.
        """
        logger.info(f"Starting sequential engine processing for '{keyword}' (target: {max_num} images)")

        results = []

        for config in self.engine_configs:
            if self._should_stop_processing(max_num):
                break

            remaining_target = max_num - self.image_downloader.total_downloaded
            if remaining_target <= 0:
                break

            logger.info(f"Processing engine: {config.name} (remaining target: {remaining_target})")

            engine_processor = SingleEngineProcessor(self.image_downloader, self)
            result = engine_processor.process_engine(
                config, variations, out_dir, remaining_target, max_num
            )

            results.append(result)

            # Update global statistics
            for variation_result in result.variations:
                self.update_stats(config.name, variation_result)

            logger.info(f"Engine {config.name} completed: {result.total_downloaded}/{remaining_target} images")

        return results

    def _calculate_per_engine_target(self, max_num: int) -> int:
        """Calculate target images per engine for parallel processing."""
        base_target = max_num // len(self.engine_configs)
        # Add buffer to ensure we get enough images
        return max(5, int(base_target * 1.3))

    def _process_engine_parallel(self, config: EngineConfig, variations: List[str],
                                 out_dir: str, per_engine_target: int, total_max: int) -> EngineResult:
        """Process a single engine in parallel mode."""
        engine_processor = SingleEngineProcessor(self.image_downloader, self)
        result = engine_processor.process_engine(config, variations, out_dir, per_engine_target, total_max)

        # Update statistics
        for variation_result in result.variations:
            self.update_stats(config.name, variation_result)

        return result

    def _should_stop_processing(self, max_num: int) -> bool:
        """Check if processing should stop."""
        return (self.image_downloader.stop_workers or
                self.image_downloader.total_downloaded >= max_num)

    @staticmethod
    def _cancel_remaining_futures(futures_dict: Dict) -> None:
        """Cancel all remaining futures."""
        for future in futures_dict.keys():
            if not future.done():
                future.cancel()

    @staticmethod
    def get_crawler_class(engine_name: str) -> Any:
        """Get the crawler class based on engine name."""
        crawler_map = {
            "google": GoogleImageCrawler,
            "bing": BingImageCrawler,
            "baidu": BaiduImageCrawler
        }
        return crawler_map.get(engine_name)

    def create_crawler(self, crawler_class, out_dir: str):
        """Create a crawler instance with optimized configuration."""
        return crawler_class(
            storage={'root_dir': out_dir},
            log_level=self.image_downloader.log_level,
            feeder_threads=self.image_downloader.feeder_threads,
            parser_threads=self.image_downloader.parser_threads,
            downloader_threads=self.image_downloader.downloader_threads
        )


class SingleEngineProcessor:
    """
    Handles processing of a single search engine with enhanced error handling and monitoring.
    """

    def __init__(self, image_downloader, engine_processor: EngineProcessor):
        self.image_downloader = image_downloader
        self.engine_processor = engine_processor

    def process_engine(self, config: EngineConfig, variations: List[str],
                       out_dir: str, max_num: int, total_max: int) -> EngineResult:
        """
        Process a single search engine with comprehensive error handling and monitoring.
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
            downloaded_count = sum(result.downloaded_count for result in variation_results)

        except Exception as e:
            logger.error(f"Engine {config.name} failed with error: {e}")
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

    def _process_variations_parallel(self, config: EngineConfig, variations: List[str],
                                     out_dir: str, max_num: int, total_max: int) -> List[VariationResult]:
        """Process variations in parallel."""
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
                    result = future.result(timeout=120)  # 2 minute timeout per variation
                    results.append(result)
                    self._update_global_counters(result)
                except concurrent.futures.TimeoutError:
                    variation = variation_futures[future]
                    logger.warning(f"Variation '{variation}' timed out for {config.name}")
                    results.append(VariationResult(
                        variation=variation,
                        downloaded_count=0,
                        success=False,
                        error="Timeout"
                    ))
                except Exception as e:
                    variation = variation_futures[future]
                    logger.error(f"Variation '{variation}' failed for {config.name}: {e}")
                    results.append(VariationResult(
                        variation=variation,
                        downloaded_count=0,
                        success=False,
                        error=str(e)
                    ))

        return results

    def _process_variations_sequential(self, config: EngineConfig, variations: List[str],
                                       out_dir: str, max_num: int, total_max: int) -> List[VariationResult]:
        """Process variations sequentially."""
        results = []
        downloaded_so_far = 0

        for i, variation in enumerate(variations):
            if self._should_stop_processing(total_max) or downloaded_so_far >= max_num:
                break

            remaining_limit = min(max_num - downloaded_so_far, max_num // len(variations))
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

    def _process_single_variation(self, config: EngineConfig, variation: str,
                                  variation_index: int, out_dir: str,
                                  max_num: int, total_max: int) -> VariationResult:
        """Process a single search variation with enhanced error handling."""
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
            current_offset = config.random_offset + (variation_index * config.variation_step)
            actual_limit = min(max_num, self._calculate_remaining_capacity(total_max))

            if actual_limit <= 0:
                return VariationResult(
                    variation=variation,
                    downloaded_count=0,
                    success=False,
                    error="No remaining capacity"
                )

            logger.info(f"{config.name}: Processing '{variation}' (limit: {actual_limit}, offset: {current_offset})")

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

            logger.info(f"{config.name}: '{variation}' completed - {downloaded_count} images in {processing_time:.2f}s")

            return VariationResult(
                variation=variation,
                downloaded_count=downloaded_count,
                success=True,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.warning(f"{config.name}: '{variation}' failed after {processing_time:.2f}s - {e}")

            return VariationResult(
                variation=variation,
                downloaded_count=0,
                success=False,
                error=str(e),
                processing_time=processing_time
            )

    def _create_enhanced_crawler(self, engine_name: str, out_dir: str):
        """Create crawler with enhanced error handling."""
        crawler_class = self.engine_processor.get_crawler_class(engine_name)
        if not crawler_class:
            raise ValueError(f"No crawler class found for engine: {engine_name}")

        crawler = self.engine_processor.create_crawler(crawler_class, out_dir)
        self._apply_safe_parser_wrapper(crawler, engine_name)
        return crawler

    @staticmethod
    def _apply_safe_parser_wrapper(crawler, engine_name: str):
        """Apply enhanced parser wrapper with better error handling."""
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
                        logger.warning(f"Parser for {engine_name} returned non-iterable: {type(result)}")
                        return []

                    return result

                except Exception as e:
                    logger.warning(f"Parser exception in {engine_name}: {e}")
                    return []

            crawler.parser.parse = enhanced_parse_wrapper

        except Exception as e:
            logger.error(f"Failed to apply parser wrapper for {engine_name}: {e}")

    def _should_stop_processing(self, total_max: int) -> bool:
        """Check if processing should stop."""
        return (self.image_downloader.stop_workers or
                self.image_downloader.total_downloaded >= total_max)

    def _calculate_remaining_capacity(self, total_max: int) -> int:
        """Calculate remaining download capacity."""
        with self.image_downloader.lock:
            return max(0, total_max - self.image_downloader.total_downloaded)

    def _get_current_file_offset(self) -> int:
        """Get current file index offset for naming."""
        with self.image_downloader.lock:
            return self.image_downloader.total_downloaded

    def _count_variation_results(self, out_dir: str, file_idx_offset: int) -> int:
        """Count valid images from the latest batch."""
        with self.image_downloader.lock:
            return count_valid_images_in_latest_batch(out_dir, file_idx_offset)

    def _update_global_counters(self, result: VariationResult) -> None:
        """Update global download counters."""
        with self.image_downloader.lock:
            self.image_downloader.total_downloaded += result.downloaded_count

    @staticmethod
    def _calculate_success_rate(results: List[VariationResult]) -> float:
        """Calculate success rate from variation results."""
        if not results:
            return 0.0

        successful = sum(1 for result in results if result.success)
        return (successful / len(results)) * 100
