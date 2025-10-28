import concurrent.futures
import os
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, Optional, List, Type, Any, Final

import requests
from ddgs import DDGS

from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler

from _base import ISearchEngineDownloader
from _constants import logger
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


USER_AGENT: Final[
    str] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'


class DDGSImageDownloader(ISearchEngineDownloader):
    """
    A class to download images using DuckDuckGo search.

    Uses parallel processing for faster downloads.
    """

    def __init__(self, max_workers: int = 4):
        """
        Initializes the DuckDuckGo with default settings.

        Args:
            max_workers (int): The maximum number of parallel download workers.
        """
        self.user_agent = USER_AGENT
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
                raise DownloadError(f"Skipping non-image content type: {content_type}")

            if len(response.content) < self.min_file_size:
                raise DownloadError(
                    f"Skipping too small image ({len(response.content)} bytes)")

            with open(file_path, "wb") as f:
                f.write(response.content)

            # Basic validation - check if file exists and has content
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                # Remove empty or missing file
                try:
                    os.remove(file_path)
                    logger.warning(f"Removed corrupted image: {file_path}")
                except OSError as ose:
                    logger.error(f"Error removing corrupted image {file_path}: {ose}")
                raise DownloadError(f"Downloaded image failed validation: {file_path}")
            return True

        except requests.exceptions.RequestException as req_e:
            logger.warning(f"Network or request error downloading {image_url}: {req_e}")
            raise DownloadError(
                f"Network or request error downloading {image_url}: {req_e}") from req_e
        except DownloadError as de:
            logger.warning(f"Download error for {image_url}: {de}")
            raise de
        except Exception as e:
            logger.warning(
                f"An unexpected error occurred while downloading {image_url}: {e}")
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

    def _search_and_download_parallel(self, keyword: str, out_dir: str,
                                      max_count: int) -> int:
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

    def _execute_parallel_downloads(self, results: List[dict], out_dir: str,
                                    max_count: int) -> int:
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
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers) as executor:
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
                            logger.info(
                                f"Downloaded image from DuckDuckGo [{downloaded}/{max_count}]")
                except DownloadError as e:
                    logger.warning(f"Error downloading image: {e}")
                except Exception as e:
                    logger.error(
                        f"An unexpected error occurred during parallel download: {e}")

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

            # Try with the original keyword first
            downloaded_count: int = self._search_and_download_parallel(keyword, out_dir,
                                                                       max_num)

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
            logger.error(
                f"An unexpected error occurred while downloading images for '{keyword}': {e}")
            raise DownloadError(
                f"Unexpected error during download for '{keyword}': {e}") from e



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

