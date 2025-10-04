import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, Optional, List, Type, Any

from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler

from _constants import logger
from _downloader import DDGSImageDownloader
from _exceptions import DownloadError


@dataclass
class SearchEngineConfig:
    """
    Configuration for a search engine.
    """
    name: str
    offset_range: Tuple[int, int]
    variation_step: int

    @property
    def random_offset(self) -> int:
        """
        Generates a random offset within the engine's configured offset range.

        Returns:
            int: A random integer representing the offset.
        """
        return random.randint(*self.offset_range)


@dataclass
class VariationResult:
    """ Represents the result of processing a single search variation. """
    variation: str
    downloaded_count: int
    success: bool
    error: Optional[str] = None
    processing_time: float = 0.0

    def __repr__(self) -> str:
        return (f"VariationResult(variation='{self.variation}', "
                f"downloaded={self.downloaded_count}, "
                f"success={self.success})"
                f"error={self.error})"
                f"processing time={self.processing_time})")


@dataclass
class EngineResult:
    """
    Represents the result of processing a single engine.

    Attributes:
        engine_name (str): The name of the engine.
        total_downloaded (int): The total number of images downloaded by this engine.
        variations_processed (int): The number of variations processed by this engine.
        success_rate (float): The overall success rate of variations processed by this engine.
        processing_time (float): The total time taken to process this engine in seconds.
        variations (List[VariationResult]): A list of results for each variation processed by this engine.
    """
    engine_name: str
    total_downloaded: int
    variations_processed: int
    success_rate: float
    processing_time: float
    variations: List[VariationResult] = field(default_factory=list)


def _download_images_with_crawler(engine_name: str, crawler_class: Type, keyword: str,
                                  variations: List[str], out_dir: str, max_num: int,
                                  config: SearchEngineConfig,
                                  image_downloader: Any) -> EngineResult:
    """Generic function to download images using any crawler."""
    start_time = time.time()
    variation_results = []

    try:
        crawler = crawler_class(
            storage={'root_dir': out_dir},
            log_level=image_downloader.log_level,
            feeder_threads=image_downloader.feeder_threads,
            parser_threads=image_downloader.parser_threads,
            downloader_threads=image_downloader.downloader_threads
        )

        for i, variation in enumerate(variations):
            if image_downloader.stop_workers or image_downloader.total_downloaded >= max_num:
                break

            try:
                current_offset = config.random_offset + (i * config.variation_step)
                file_idx_offset = image_downloader.total_downloaded

                crawler.crawl(
                    keyword=variation,
                    max_num=max_num // len(variations),
                    min_size=image_downloader.min_image_size,
                    offset=current_offset,
                    file_idx_offset=file_idx_offset
                )

                # Basic count of downloaded files - validation moved to validator package
                try:
                    files = [f for f in os.listdir(out_dir) if f.lower().endswith(
                        ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))]
                    downloaded_count = len(files) - file_idx_offset
                except OSError:
                    downloaded_count = 0

                variation_results.append(VariationResult(
                    variation=variation,
                    downloaded_count=downloaded_count,
                    success=True,
                    processing_time=time.time() - start_time
                ))

            except Exception as e:
                variation_results.append(VariationResult(
                    variation=variation,
                    downloaded_count=0,
                    success=False,
                    error=str(e)
                ))

    except Exception as e:
        logger.error(f"{engine_name} engine failed: {e}")

    total_downloaded = sum(r.downloaded_count for r in variation_results)
    success_rate = sum(1 for r in variation_results if r.success) / len(
        variation_results) * 100 if variation_results else 0

    return EngineResult(
        engine_name=engine_name,
        total_downloaded=total_downloaded,
        variations_processed=len(variation_results),
        success_rate=success_rate,
        processing_time=time.time() - start_time,
        variations=variation_results
    )


def download_google_images(keyword: str, variations: List[str], out_dir: str,
                           max_num: int,
                           config: SearchEngineConfig,
                           image_downloader: Any) -> EngineResult:
    """Download images using Google Image Crawler."""
    return _download_images_with_crawler("google", GoogleImageCrawler, keyword,
                                         variations, out_dir, max_num, config,
                                         image_downloader)


def download_bing_images(keyword: str, variations: List[str], out_dir: str,
                         max_num: int,
                         config: SearchEngineConfig,
                         image_downloader: Any) -> EngineResult:
    """Download images using Bing Image Crawler."""
    return _download_images_with_crawler("bing", BingImageCrawler, keyword,
                                         variations, out_dir, max_num, config,
                                         image_downloader)


def download_baidu_images(keyword: str, variations: List[str], out_dir: str,
                          max_num: int,
                          config: SearchEngineConfig,
                          image_downloader: Any) -> EngineResult:
    """Download images using Baidu Image Crawler."""
    return _download_images_with_crawler("baidu", BaiduImageCrawler, keyword,
                                         variations, out_dir, max_num, config,
                                         image_downloader)


def download_images_ddgs(keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
    """
    Downloads images directly using the DuckDuckGo search engine.
    This function serves as a wrapper for the `DuckDuckGo` class.

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
        ddg_downloader = DDGSImageDownloader(max_workers=6)

        # Get the current count of images in the directory
        initial_count = len([f for f in os.listdir(out_dir) if
                             f.lower().endswith(('.jpg', '.jpeg', '.png'))])

        logger.info(
            f"Using DuckDuckGo to download up to {max_num} images for '{keyword}'")

        # Download images
        _ = ddg_downloader.download(keyword, out_dir, max_num)

        # Get the new count of images
        final_count = len([f for f in os.listdir(out_dir) if
                           f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        actual_downloaded = final_count - initial_count

        logger.info(f"DuckDuckGo download complete: {actual_downloaded} new images")

        return True, actual_downloaded
    except DownloadError as de:
        logger.error(f"DuckDuckGo download failed for '{keyword}': {de}")
        return False, 0
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during DuckDuckGo download for '{keyword}': {e}")
        return False, 0
