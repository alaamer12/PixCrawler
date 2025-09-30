"""Image downloading module with multiple search engines and parallel processing.

This module provides various image downloading functionalities, including DuckDuckGo
search integration and a multi-threaded image downloader that leverages different
search engines with robust error handling and rate limiting.

Typical usage example:

    downloader = DuckDuckGoImageDownloader(max_workers=4)
    success, count = downloader.download('cats', '/output/dir', 10)
    
    # Or using the registry system
    registry = DownloaderRegistry
    downloader_class = registry.get_downloader('duckduckgo')
    downloader = downloader_class()
"""

import concurrent.futures
import logging
import os
import random
import threading
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Final, List, Optional, Tuple, Type

import requests
from ddgs import DDGS

from builder._config import get_search_variations
from builder._constants import logger
from builder._engine import EngineProcessor
from builder._exceptions import DownloadError, ImageValidationError
from builder._helpers import progress
from builder._utilities import image_validator, rename_images_sequentially


# Constants to replace magic numbers and improve security
class DownloaderConstants:
    """Constants for downloader configuration and security."""
    # Search result multipliers
    SEARCH_RESULT_MULTIPLIER_HIGH = 3
    SEARCH_RESULT_MULTIPLIER_MEDIUM = 2
    
    # File size limits (bytes)
    MIN_FILE_SIZE = 1000  # 1KB minimum
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB maximum
    
    # Timeout settings
    DEFAULT_TIMEOUT = 20
    MAX_TIMEOUT = 60
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 8
    MAX_RATE_LIMIT = 50
    
    # Thread limits
    DEFAULT_MAX_WORKERS = 4
    MAX_WORKERS = 16
    
    # Retry settings
    DEFAULT_MAX_RETRIES = 3
    MAX_RETRIES = 10
    RETRY_BACKOFF_FACTOR = 0.5
    
    # Security settings
    ENABLE_SSL_VERIFICATION = True
    ALLOW_SSL_FALLBACK = False  # Disabled for security
    
    # Supported content types
    SUPPORTED_CONTENT_TYPES = frozenset([
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
        'image/bmp', 'image/webp', 'image/tiff'
    ])
    
    # Download chunk size
    DOWNLOAD_CHUNK_SIZE = 8192


class ThreadPoolManager:
    """Context manager for proper thread pool cleanup."""
    def __init__(self, max_workers: int):
        self.max_workers = max_workers
        self.executor = None
    
    def __enter__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        return self.executor
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.executor:
            # Cancel pending futures and shutdown gracefully
            self.executor.shutdown(wait=True)
            logger.debug("Thread pool properly cleaned up")


class SecureSession:
    """Secure HTTP session with connection pooling and proper SSL verification."""
    def __init__(self):
        self.session = requests.Session()
        # Configure connection pooling
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=DownloaderConstants.DEFAULT_MAX_RETRIES
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        # Always verify SSL - no fallback
        self.session.verify = DownloaderConstants.ENABLE_SSL_VERIFICATION
    
    def __enter__(self):
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


def standardized_error_handler(func):
    """Decorator for consistent error handling across all methods."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (NetworkError, EngineError, RateLimitError, ImageValidationError) as e:
            logger.warning(f"{func.__name__} failed with known error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise DownloadError(f"Unexpected error in {func.__name__}: {e}") from e
    return wrapper


# Enhanced exception hierarchy for better error context
class NetworkError(DownloadError):
    """Raised when network-related issues occur during download."""
    pass


class EngineError(DownloadError):
    """Raised when search engine-specific issues occur."""
    pass


class RateLimitError(DownloadError):
    """Raised when rate limits are exceeded."""
    pass


class AuthenticationError(DownloadError):
    """Raised when API authentication fails."""
    pass


class QuotaExceededError(DownloadError):
    """Raised when API quota is exceeded."""
    pass

__all__ = [
    'APIDownloader',
    'AioHttpDownloader', 
    'AuthenticationError',
    'DownloaderRegistry',
    'DuckDuckGoImageDownloader',
    'EngineError',
    'IDownloader',
    'ImageDownloader',
    'NetworkError',
    'QuotaExceededError',
    'RateLimitError',
    'RateLimiter',
    'download_images_ddgs',
]

_USER_AGENT: Final[str] = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
)


class RateLimiter:
    """Simple rate limiter to prevent overwhelming servers with requests."""
    
    def __init__(self, max_requests: int = 10, time_window: float = 1.0) -> None:
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window.
            time_window: Time window in seconds.
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self.lock = threading.RLock()
    
    def acquire(self) -> None:
        """Acquire permission to make a request. Blocks if rate limit exceeded."""
        with self.lock:
            current_time = time.time()
            
            # Remove old requests outside the time window
            self.requests = [req_time for req_time in self.requests 
                           if current_time - req_time < self.time_window]
            
            # If we're at the limit, wait
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (current_time - self.requests[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    # Recursively try again
                    return self.acquire()
            # Record this request
            self.requests.append(current_time)


class DownloaderRegistry:
    """Registry for managing image downloader implementations.
    
    Provides a centralized way to register, discover, and instantiate
    different downloader implementations without modifying orchestrators.
    """
    
    _downloaders: Dict[str, Type[IDownloader]] = {}
    _enabled_downloaders: Dict[str, bool] = {}
    
    @classmethod
    def register(cls, name: str, downloader_class: Type[IDownloader], 
                 enabled: bool = True) -> None:
        """Register a new downloader implementation.
        
        Args:
            name: Unique identifier for the downloader.
            downloader_class: The downloader class.
            enabled: Whether the downloader is enabled by default.
            
        Raises:
            ValueError: If downloader_class doesn't implement IDownloader.
        """
        if not issubclass(downloader_class, IDownloader):
            raise ValueError(f"Downloader class {downloader_class} must implement IDownloader")
        
        cls._downloaders[name] = downloader_class
        cls._enabled_downloaders[name] = enabled
        logger.info(f"Registered downloader: {name} ({'enabled' if enabled else 'disabled'})")
    
    @classmethod
    def get_downloader(cls, name: str) -> Optional[Type[IDownloader]]:
        """Get a downloader class by name.
        
        Args:
            name: The downloader name.
            
        Returns:
            The downloader class or None if not found.
        """
        return cls._downloaders.get(name)
    
    @classmethod
    def get_enabled_downloaders(cls) -> Dict[str, Type[IDownloader]]:
        """Get all enabled downloader implementations.
        
        Returns:
            Dictionary of enabled downloaders.
        """
        return {
            name: downloader_class
            for name, downloader_class in cls._downloaders.items()
            if cls._enabled_downloaders.get(name, False)
        }
    
    @classmethod
    def list_downloaders(cls) -> Dict[str, Dict[str, str]]:
        """List all registered downloaders with their status.
        
        Returns:
            Dictionary with downloader info and status.
        """
        result = {}
        for name, downloader_class in cls._downloaders.items():
            # Create a temporary instance to get info (if possible)
            try:
                temp_instance = downloader_class()
                info = temp_instance.get_downloader_info()
            except Exception:
                info = {'name': downloader_class.__name__, 'version': 'unknown', 'description': 'N/A'}
            
            result[name] = {
                **info,
                'enabled': str(cls._enabled_downloaders.get(name, False)),
                'class': downloader_class.__name__
            }
        return result
    
    @classmethod
    def enable_downloader(cls, name: str) -> bool:
        """
        Enable a registered downloader.
        
        Args:
            name (str): The downloader name
            
        Returns:
            bool: True if successfully enabled, False if not found
        """
        if name in cls._downloaders:
            cls._enabled_downloaders[name] = True
            logger.info(f"Enabled downloader: {name}")
            return True
        return False
    
    @classmethod
    def disable_downloader(cls, name: str) -> bool:
        """
        Disable a registered downloader.
        
        Args:
            name (str): The downloader name
            
        Returns:
            bool: True if successfully disabled, False if not found
        """
        if name in cls._downloaders:
            cls._enabled_downloaders[name] = False
            logger.info(f"Disabled downloader: {name}")
            return True
        return False


class IDownloader(ABC):
    """Abstract base class defining the interface for image downloaders.
    
    This ABC establishes a strict contract for all image downloaders, ensuring
    consistent behavior across different implementations.
    
    Contract Requirements:
        - All implementations must handle retries internally
        - All implementations must validate downloaded images
        - All implementations must return consistent tuple format: (success: bool, count: int)
        - All implementations must handle exceptions gracefully and raise DownloadError for failures
        - All implementations must create output directory if it doesn't exist
        - All implementations must respect the max_num parameter as a hard limit
    
    Exception Handling:
        - Must catch and handle network errors, validation errors, and file system errors
        - Must raise DownloadError for unrecoverable failures
        - Must raise ImageValidationError for image-specific validation failures
    
    Return Values:
        - First element (bool): True if at least one image was successfully downloaded, False otherwise
        - Second element (int): Exact count of successfully downloaded and validated images
    """

    @abstractmethod
    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """Downloads images based on the given keyword.
        
        Args:
            keyword: The search term for images. Must not be empty.
            out_dir: The output directory path where images will be saved.
                Directory will be created if it doesn't exist.
            max_num: The maximum number of images to download. Must be > 0.
        
        Returns:
            A tuple where:
                - First element is True if any images were successfully downloaded
                - Second element is the exact count of downloaded images
        
        Raises:
            DownloadError: For unrecoverable download failures.
            ImageValidationError: For image validation failures.
            ValueError: For invalid input parameters.
        """
        pass

    def validate_inputs(self, keyword: str, out_dir: str, max_num: int) -> None:
        """Validates input parameters for the download method.
        
        Args:
            keyword: The search keyword.
            out_dir: The output directory.
            max_num: Maximum number of images.
            
        Raises:
            ValueError: If any parameter is invalid.
        """
        if not keyword or not keyword.strip():
            raise ValueError("Keyword cannot be empty or whitespace")
        if not out_dir:
            raise ValueError("Output directory cannot be empty")
        if max_num <= 0:
            raise ValueError("max_num must be greater than 0")

    def get_downloader_info(self) -> Dict[str, str]:
        """Returns information about this downloader implementation.
        
        Returns:
            Dictionary containing downloader metadata.
        """
        return {
            'name': self.__class__.__name__,
            'version': '1.0',
            'description': 'Base image downloader implementation'
        }


class DuckDuckGoImageDownloader(IDownloader):
    """Downloads images using DuckDuckGo search with parallel processing.

    Uses parallel processing for faster downloads with retry mechanism and rate limiting.
    Includes fallback mechanisms for robust image retrieval.
    """

    def __init__(self, max_workers: int = DownloaderConstants.DEFAULT_MAX_WORKERS, 
                 max_retries: int = DownloaderConstants.DEFAULT_MAX_RETRIES, 
                 rate_limit_requests: int = DownloaderConstants.DEFAULT_RATE_LIMIT) -> None:
        """Initializes the DuckDuckGoImageDownloader with default settings.

        Args:
            max_workers: The maximum number of parallel download workers.
            max_retries: Maximum retry attempts per image.
            rate_limit_requests: Maximum requests per second for rate limiting.
        """
        self.user_agent = _USER_AGENT
        self.timeout = DownloaderConstants.DEFAULT_TIMEOUT
        self.min_file_size = DownloaderConstants.MIN_FILE_SIZE
        self.max_file_size = DownloaderConstants.MAX_FILE_SIZE
        self.delay = 0.2  # seconds between downloads
        self.max_workers = min(max_workers, DownloaderConstants.MAX_WORKERS)
        self.max_retries = min(max_retries, DownloaderConstants.MAX_RETRIES)
        self.lock = threading.RLock()
        self.rate_limiter = RateLimiter(max_requests=rate_limit_requests, time_window=1.0)
        
        # Thread-safe counters
        self._downloaded_count = 0
        self._failed_count = 0

    def _get_image_with_retry(self, image_url: str, file_path: str) -> bool:
        """
        Downloads a single image with retry mechanism and proper error handling.

        Args:
            image_url (str): The URL of the image to download.
            file_path (str): The absolute path where the image should be saved.

        Returns:
            bool: True if the download and validation were successful, False otherwise.
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting
                self.rate_limiter.acquire()
                
                return self._get_image(image_url, file_path)
                
            except NetworkError as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = (attempt + 1) * 0.5  # Exponential backoff
                    logger.debug(f"Network error on attempt {attempt + 1}/{self.max_retries + 1} for {image_url}: {e}. Retrying in {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.info(f"Failed to download {image_url} after {self.max_retries + 1} attempts: {e}")
            except ImageValidationError as e:
                # Don't retry validation errors
                logger.debug(f"Image validation failed for {image_url}: {e}")
                break
            except Exception as e:
                last_exception = e
                logger.debug(f"Unexpected error downloading {image_url}: {e}")
                break
        
        with self.lock:
            self._failed_count += 1
        return False
    
    @standardized_error_handler
    def _get_image(self, image_url: str, file_path: str) -> bool:
        """
        Downloads a single image from a given URL with enhanced security and validation.
        
        Security improvements:
        - Always enforces SSL verification (no fallback)
        - Validates file size before and during download
        - Streams large files to prevent memory issues
        - Validates content type against whitelist

        Args:
            image_url (str): The URL of the image to download.
            file_path (str): The absolute path where the image should be saved.

        Returns:
            bool: True if the download and validation were successful, False otherwise.
            
        Raises:
            NetworkError: For network-related issues including SSL failures
            ImageValidationError: For validation failures
        """
        try:
            # Use secure session with connection pooling
            with SecureSession() as session:
                # First, check file size with HEAD request to avoid downloading large files
                try:
                    head_response = session.head(image_url, timeout=10)
                    content_length = int(head_response.headers.get('content-length', 0))
                    
                    if content_length > self.max_file_size:
                        raise ImageValidationError(f"File too large: {content_length} bytes (max: {self.max_file_size})")
                        
                    # Validate content type from HEAD response
                    content_type = head_response.headers.get('Content-Type', '').lower()
                    if content_type and not any(ct in content_type for ct in DownloaderConstants.SUPPORTED_CONTENT_TYPES):
                        raise ImageValidationError(f"Unsupported content type: {content_type}")
                        
                except requests.exceptions.RequestException:
                    # HEAD request failed, continue with GET but be more careful
                    logger.debug(f"HEAD request failed for {image_url}, proceeding with GET")
                
                # Download with streaming to handle large files efficiently
                response = session.get(
                    image_url,
                    timeout=self.timeout,
                    headers={'User-Agent': self.user_agent},
                    stream=True  # Stream for memory efficiency
                )
                response.raise_for_status()
                
                # Validate content type from actual response
                content_type = response.headers.get('Content-Type', '').lower()
                if not any(ct in content_type for ct in DownloaderConstants.SUPPORTED_CONTENT_TYPES):
                    raise ImageValidationError(f"Invalid content type: {content_type}")
                
                # Download with size validation during streaming
                downloaded_size = 0
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=DownloaderConstants.DOWNLOAD_CHUNK_SIZE):
                        if chunk:  # Filter out keep-alive chunks
                            downloaded_size += len(chunk)
                            
                            # Check size limit during download
                            if downloaded_size > self.max_file_size:
                                # Clean up partial file
                                try:
                                    os.remove(file_path)
                                except OSError:
                                    pass
                                raise ImageValidationError(f"File size exceeded during download: {downloaded_size} bytes")
                            
                            f.write(chunk)
                
                # Validate minimum file size
                if downloaded_size < self.min_file_size:
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
                    raise ImageValidationError(f"File too small: {downloaded_size} bytes (min: {self.min_file_size})")
                
                # Validate the downloaded image integrity
                if not image_validator.validate(file_path):
                    try:
                        os.remove(file_path)
                        logger.warning(f"Removed corrupted image: {file_path}")
                    except OSError as ose:
                        logger.error(f"Error removing corrupted image {file_path}: {ose}")
                    raise ImageValidationError(f"Downloaded image failed validation: {file_path}")
                
                logger.debug(f"Successfully downloaded and validated image: {downloaded_size} bytes")
                return True

        except requests.exceptions.SSLError as e:
            # CRITICAL: No SSL fallback - fail securely
            logger.error(f"SSL verification failed for {image_url}: {e}")
            raise NetworkError(f"SSL verification failed (no fallback allowed): {e}") from e
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Timeout downloading {image_url}: {e}") from e
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error downloading {image_url}: {e}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error downloading {image_url}: {e}") from e
        except ImageValidationError:
            raise  # Re-raise validation errors as-is
        except OSError as e:
            raise DownloadError(f"File system error for {image_url}: {e}") from e

    def _download_single_image(self, result: dict, out_dir: str, index: int) -> bool:
        """
        Downloads a single image from a search result dictionary with retry mechanism.

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

        # Download the image with retry mechanism
        success = self._get_image_with_retry(image_url, file_path)

        # Add small delay between downloads (rate limiter handles this better now)
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
        Fetches image search results from DuckDuckGo with proper error handling.

        Args:
            keyword (str): The search term.
            max_count (int): The maximum number of images needed.

        Returns:
            List[dict]: A list of search result dictionaries.
            
        Raises:
            EngineError: If DuckDuckGo search fails
        """
        try:
            with DDGS() as ddgs:
                # Request more images than needed to account for failures
                search_limit = max_count * DownloaderConstants.SEARCH_RESULT_MULTIPLIER_HIGH
                results = list(ddgs.images(keyword, max_results=search_limit))
                logger.info(f"Found {len(results)} potential images for '{keyword}' (requested {search_limit})")
                return results
        except Exception as e:
            raise EngineError(f"DuckDuckGo search failed for '{keyword}': {e}") from e

    def _execute_parallel_downloads(self, results: List[dict], out_dir: str, max_count: int) -> int:
        """
        Executes parallel downloads with proper resource management and error handling.
        
        This method has been refactored to:
        - Use proper thread pool management with context managers
        - Limit memory usage by controlling concurrent tasks
        - Provide better error reporting and logging
        - Ensure proper cleanup of resources

        Args:
            results (List[dict]): A list of search result dictionaries.
            out_dir (str): The output directory for downloaded images.
            max_count (int): The maximum number of images to download.

        Returns:
            int: The number of successfully downloaded images.
        """
        self._reset_counters()
        
        # Use proper thread pool management with resource cleanup
        with ThreadPoolManager(self.max_workers) as executor:
            futures = self._submit_download_tasks(executor, results, out_dir, max_count)
            return self._process_download_results(futures, max_count)
    
    def _reset_counters(self) -> None:
        """Reset download counters in a thread-safe manner."""
        with self.lock:
            self._downloaded_count = 0
            self._failed_count = 0
    
    def _submit_download_tasks(self, executor, results: List[dict], out_dir: str, max_count: int) -> List:
        """
        Submit download tasks to thread pool with memory usage control.
        
        Args:
            executor: Thread pool executor
            results: Search results to process
            out_dir: Output directory
            max_count: Maximum images to download
            
        Returns:
            List of submitted futures
        """
        futures = []
        # Limit concurrent tasks to prevent memory issues
        task_limit = min(len(results), max_count * DownloaderConstants.SEARCH_RESULT_MULTIPLIER_MEDIUM)
        
        logger.debug(f"Submitting {task_limit} download tasks (max_count: {max_count})")
        
        for i, result in enumerate(results[:task_limit]):
            future = executor.submit(
                self._download_single_image,
                result=result,
                out_dir=out_dir,
                index=i + 1
            )
            futures.append(future)
        
        return futures
    
    def _process_download_results(self, futures: List, max_count: int) -> int:
        """
        Process completed download tasks with proper error handling.
        
        Args:
            futures: List of submitted futures
            max_count: Maximum images needed
            
        Returns:
            Number of successfully downloaded images
        """
        completed_tasks = 0
        
        for future in concurrent.futures.as_completed(futures):
            completed_tasks += 1
            
            # Check if we've reached our target
            with self.lock:
                current_downloaded = self._downloaded_count
            
            if current_downloaded >= max_count:
                logger.debug(f"Target reached ({current_downloaded}/{max_count}), cancelling remaining tasks")
                self._cancel_remaining_futures(futures)
                break
            
            try:
                if future.result():
                    with self.lock:
                        self._downloaded_count += 1
                        current_count = self._downloaded_count
                    
                    if current_count % 5 == 0 or current_count >= max_count:
                        logger.info(f"Downloaded image from DuckDuckGo [{current_count}/{max_count}]")
                else:
                    with self.lock:
                        self._failed_count += 1
                        
            except Exception as e:
                with self.lock:
                    self._failed_count += 1
                logger.debug(f"Download task failed: {e}")
        
        # Log final statistics
        with self.lock:
            final_count = self._downloaded_count
            failed_count = self._failed_count
        
        logger.info(f"DuckDuckGo download completed: {final_count} successful, {failed_count} failed, {completed_tasks} tasks processed")
        return final_count
    
    def _cancel_remaining_futures(self, futures: List[concurrent.futures.Future]) -> None:
        """
        Cancel remaining futures to free up resources.
        
        Args:
            futures: List of futures to check and cancel
        """
        cancelled_count = 0
        for future in futures:
            if not future.done() and future.cancel():
                cancelled_count += 1
        
        if cancelled_count > 0:
            logger.debug(f"Cancelled {cancelled_count} pending download tasks")


    def get_downloader_info(self) -> Dict[str, str]:
        """Returns information about this DuckDuckGo downloader implementation.
        
        Returns:
            Dictionary containing downloader metadata.
        """
        return {
            'name': 'DuckDuckGoImageDownloader',
            'version': '2.0',
            'description': 'Downloads images using DuckDuckGo search with parallel processing and retry logic',
            'source': 'DuckDuckGo Search API',
            'features': 'Parallel downloads, SSL retry, image validation, alternate keywords'
        }

    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """Downloads images using DuckDuckGo search with fallback mechanisms.

        Args:
            keyword: The primary search term for images.
            out_dir: The output directory path where images will be saved.
            max_num: The maximum number of images to download.

        Returns:
            A tuple where the first element is True if any images were downloaded,
            and the second element is the total count of downloaded images.
        """
        # Validate inputs according to ABC contract
        self.validate_inputs(keyword, out_dir, max_num)
        
        logger.info("Using DuckDuckGo image search with parallel downloading")

        try:
            Path(out_dir).mkdir(parents=True, exist_ok=True)

            # Try with the original keyword first
            downloaded_count: int = self._search_and_download_parallel(keyword, out_dir, max_num)

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
    """Downloads images directly using the DuckDuckGo search engine.
    
    This function serves as a wrapper for the DuckDuckGoImageDownloader class.

    Args:
        keyword: The search term for images.
        out_dir: The output directory path where images will be saved.
        max_num: The maximum number of images to download.

    Returns:
        A tuple where the first element is True if any images were downloaded,
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
        _ = ddg_downloader.download(keyword, out_dir, max_num)

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
    """Downloads images using multiple image crawlers in parallel.

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
                 use_all_engines: bool = True) -> None:
        """Initializes the ImageDownloader with configurable parameters.

        Args:
            feeder_threads: Number of feeder threads for crawlers.
            parser_threads: Number of parser threads for crawlers.
            downloader_threads: Number of downloader threads for crawlers.
            min_image_size: Minimum image size as (width, height) tuple.
            delay_between_searches: Delay in seconds between different search terms.
            log_level: Logging level for crawlers (e.g., logging.INFO, logging.WARNING).
            max_parallel_engines: Maximum number of search engines to use in parallel.
            max_parallel_variations: Maximum number of search variations to run in parallel per engine.
            use_all_engines: Whether to use all engines in parallel (True) or fallback mode (False).
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
        
        # Rate limiter for scalability
        self.rate_limiter = RateLimiter(max_requests=15, time_window=1.0)

        # Signal for worker threads
        self.stop_workers = False

        # Thread-safe shared counter for downloaded images
        self._total_downloaded = 0
    
    @property
    def total_downloaded(self) -> int:
        """Thread-safe getter for total downloaded count."""
        with self.lock:
            return self._total_downloaded
    
    def increment_downloaded_count(self, count: int = 1) -> None:
        """Thread-safe increment of downloaded count."""
        with self.lock:
            self._total_downloaded += count

    def get_downloader_info(self) -> Dict[str, str]:
        """Returns information about this multi-engine downloader implementation.
        
        Returns:
            Dictionary containing downloader metadata.
        """
        return {
            'name': 'ImageDownloader',
            'version': '2.0',
            'description': 'Multi-engine image downloader with parallel processing and DuckDuckGo fallback',
            'source': 'Multiple search engines + DuckDuckGo',
            'features': 'Parallel engines, search variations, automatic fallback, image renaming'
        }

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
        # Validate inputs according to ABC contract
        self.validate_inputs(keyword, out_dir, max_num)
        
        try:
            # Ensure output directory exists
            Path(out_dir).mkdir(parents=True, exist_ok=True)

            # Reset counters and flags
            with self.lock:
                self._total_downloaded = 0
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
            with self.lock:
                current_downloaded = self._total_downloaded
            
            if current_downloaded < max_num:
                progress.set_subtask_description(f"Using DuckDuckGo fallback: {keyword}")
                additional_count = self._try_duckduckgo_fallback(
                    keyword=keyword,
                    out_dir=out_dir,
                    max_num=max_num,
                    total_downloaded=current_downloaded
                )
                with self.lock:
                    self._total_downloaded += additional_count

            # Get final count for operations
            with self.lock:
                final_downloaded = self._total_downloaded
            
            # Rename all files sequentially
            if final_downloaded > 0:
                progress.set_subtask_description(f"Renaming images: {keyword}")
                rename_images_sequentially(out_dir)

            # Log engine statistics
            self.engine_processor.log_engine_stats()

            # Update progress with results
            progress.set_subtask_description(f"Downloaded {final_downloaded}/{max_num} images for {keyword}")

            return final_downloaded > 0, final_downloaded

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
            int: The additional count of images downloaded by DuckDuckGo.
        """
        if total_downloaded >= max_num:
            return 0

        logger.info(f"Crawlers downloaded {total_downloaded}/{max_num} images. Trying DuckDuckGo as fallback.")
        ddgs_success, ddgs_count = download_images_ddgs(
            keyword=keyword,
            out_dir=out_dir,
            max_num=max_num - total_downloaded
        )
        return ddgs_count if ddgs_success else 0

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


class APIDownloader(IDownloader):
    """
    Placeholder for API-based image downloader.
    
    This class serves as a template for implementing downloaders that use
    specific APIs (e.g., Unsplash API, Pexels API, etc.) for image retrieval.
    
    To enable this downloader:
    1. Implement the download method with actual API calls
    2. Add necessary API configuration to _config.py
    3. Register the downloader: DownloaderRegistry.register('api', APIDownloader, enabled=True)
    """
    
    def __init__(self, api_key: Optional[str] = None, api_endpoint: Optional[str] = None):
        """
        Initialize API downloader with configuration.
        
        Args:
            api_key (Optional[str]): API key for authentication
            api_endpoint (Optional[str]): Base API endpoint URL
        """
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.enabled = False  # Disabled by default
        
    def get_downloader_info(self) -> Dict[str, str]:
        """
        Returns information about this API downloader implementation.
        
        Returns:
            Dict[str, str]: Dictionary containing downloader metadata
        """
        return {
            'name': 'APIDownloader',
            'version': '1.0',
            'description': 'Template for API-based image downloaders (disabled by default)',
            'source': 'External APIs',
            'features': 'API authentication, rate limiting, high-quality images',
            'status': 'disabled - requires implementation'
        }
    
    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """
        Downloads images using external APIs.
        
        Args:
            keyword (str): The search term for images
            out_dir (str): The output directory path where images will be saved
            max_num (int): The maximum number of images to download
            
        Returns:
            Tuple[bool, int]: A tuple indicating success and count of downloaded images
            
        Raises:
            NotImplementedError: This is a placeholder implementation
        """
        self.validate_inputs(keyword, out_dir, max_num)
        
        if not self.enabled:
            logger.warning("APIDownloader is disabled. Enable it in configuration to use.")
            return False, 0
            
        # TODO: Implement actual API-based downloading
        # Example implementation structure:
        # 1. Authenticate with API using self.api_key
        # 2. Search for images using keyword
        # 3. Download images respecting rate limits
        # 4. Validate downloaded images
        # 5. Return success status and count
        
        raise NotImplementedError(
            "APIDownloader is a placeholder. Implement the download method with actual API calls."
        )


class AioHttpDownloader(IDownloader):
    """
    Placeholder for async HTTP-based image downloader.
    
    This class serves as a template for implementing high-performance async
    downloaders using aiohttp for concurrent image retrieval.
    
    To enable this downloader:
    1. Implement the download method with aiohttp async calls
    2. Add asyncio support and proper session management
    3. Register the downloader: DownloaderRegistry.register('aiohttp', AioHttpDownloader, enabled=True)
    """
    
    def __init__(self, max_concurrent: int = 10, timeout: int = 30):
        """
        Initialize async HTTP downloader with configuration.
        
        Args:
            max_concurrent (int): Maximum concurrent downloads
            timeout (int): Request timeout in seconds
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.enabled = False  # Disabled by default
        
    def get_downloader_info(self) -> Dict[str, str]:
        """
        Returns information about this async HTTP downloader implementation.
        
        Returns:
            Dict[str, str]: Dictionary containing downloader metadata
        """
        return {
            'name': 'AioHttpDownloader',
            'version': '1.0',
            'description': 'Template for async HTTP-based image downloaders (disabled by default)',
            'source': 'HTTP/HTTPS URLs',
            'features': 'Async downloads, high concurrency, session pooling',
            'status': 'disabled - requires implementation'
        }
    
    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """
        Downloads images using async HTTP requests.
        
        Args:
            keyword (str): The search term for images
            out_dir (str): The output directory path where images will be saved
            max_num (int): The maximum number of images to download
            
        Returns:
            Tuple[bool, int]: A tuple indicating success and count of downloaded images
            
        Raises:
            NotImplementedError: This is a placeholder implementation
        """
        self.validate_inputs(keyword, out_dir, max_num)
        
        if not self.enabled:
            logger.warning("AioHttpDownloader is disabled. Enable it in configuration to use.")
            return False, 0
            
        # TODO: Implement actual async HTTP downloading
        # Example implementation structure:
        # 1. Create aiohttp session with proper configuration
        # 2. Generate list of image URLs from search results
        # 3. Download images concurrently using asyncio.gather()
        # 4. Validate downloaded images
        # 5. Return success status and count
        
        raise NotImplementedError(
            "AioHttpDownloader is a placeholder. Implement the download method with aiohttp async calls."
        )


# Register default downloaders
DownloaderRegistry.register('duckduckgo', DuckDuckGoImageDownloader, enabled=True)
DownloaderRegistry.register('multi_engine', ImageDownloader, enabled=True)
DownloaderRegistry.register('api', APIDownloader, enabled=False)
DownloaderRegistry.register('aiohttp', AioHttpDownloader, enabled=False)


"""
=== CUSTOM DOWNLOADER REGISTRATION GUIDE ===

This module provides a registry system for adding new image downloader implementations
without modifying the core orchestrator code. Follow this guide to create and register
custom downloaders.

## Creating a Custom Downloader

1. **Inherit from IDownloader ABC**:
   ```python
   class MyCustomDownloader(IDownloader):
       def __init__(self, custom_param: str = "default"):
           self.custom_param = custom_param
       
       def get_downloader_info(self) -> Dict[str, str]:
           return {
               'name': 'MyCustomDownloader',
               'version': '1.0',
               'description': 'My custom image downloader',
               'source': 'Custom API/Service',
               'features': 'Custom features here'
           }
       
       def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
           # Validate inputs (required by ABC contract)
           self.validate_inputs(keyword, out_dir, max_num)
           
           # Your implementation here
           # Must return (success: bool, count: int)
           return True, downloaded_count
   ```

2. **Follow the ABC Contract**:
   - Always call `self.validate_inputs()` at the start of `download()`
   - Handle retries internally
   - Validate downloaded images using `image_validator.validate()`
   - Create output directory if it doesn't exist
   - Return exact count of successfully downloaded images
   - Raise `DownloadError` for unrecoverable failures
   - Raise `ImageValidationError` for validation failures

3. **Register Your Downloader**:
   ```python
   # Register with the registry
   DownloaderRegistry.register('my_custom', MyCustomDownloader, enabled=True)
   
   # Or register conditionally based on configuration
   if config.get('enable_custom_downloader', False):
       DownloaderRegistry.register('my_custom', MyCustomDownloader, enabled=True)
   ```

## Using Registered Downloaders

1. **Get Available Downloaders**:
   ```python
   # List all registered downloaders
   all_downloaders = DownloaderRegistry.list_downloaders()
   
   # Get only enabled downloaders
   enabled_downloaders = DownloaderRegistry.get_enabled_downloaders()
   ```

2. **Instantiate and Use**:
   ```python
   # Get a specific downloader class
   downloader_class = DownloaderRegistry.get_downloader('my_custom')
   if downloader_class:
       downloader = downloader_class(custom_param="value")
       success, count = downloader.download("cats", "/path/to/output", 10)
   ```

3. **Enable/Disable at Runtime**:
   ```python
   # Enable a disabled downloader
   DownloaderRegistry.enable_downloader('api')
   
   # Disable an enabled downloader
   DownloaderRegistry.disable_downloader('my_custom')
   ```

## Configuration Integration

Add configuration keys to `_config.py` for your custom downloaders:

```python
# In _config.py
CUSTOM_DOWNLOADER_CONFIG = {
    'api_key': 'your_api_key_here',
    'endpoint': 'https://api.example.com/v1',
    'enabled': False,  # Disabled by default
    'max_requests_per_minute': 100
}

def get_custom_downloader_config():
    return CUSTOM_DOWNLOADER_CONFIG
```

## Best Practices

1. **Error Handling**: Always wrap your implementation in try-catch blocks
2. **Logging**: Use the module's logger for consistent logging
3. **Rate Limiting**: Implement appropriate delays for API-based downloaders
4. **Validation**: Always validate downloaded images before counting them
5. **Configuration**: Make your downloader configurable through _config.py
6. **Documentation**: Provide clear docstrings and usage examples
7. **Testing**: Test your downloader thoroughly before registration

## Example: Third-Party API Integration

```python
class UnsplashDownloader(IDownloader):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.unsplash.com"
    
    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        self.validate_inputs(keyword, out_dir, max_num)
        
        # Implementation with proper error handling
        try:
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            
            # Search for images via Unsplash API
            search_results = self._search_images(keyword, max_num)
            
            # Download images with validation
            downloaded = 0
            for result in search_results:
                if downloaded >= max_num:
                    break
                    
                if self._download_image(result['urls']['regular'], out_dir, downloaded):
                    downloaded += 1
            
            return downloaded > 0, downloaded
            
        except Exception as e:
            logger.error(f"Unsplash download failed: {e}")
            raise DownloadError(f"Unsplash API error: {e}") from e

# Register the custom downloader
if config.get('unsplash_api_key'):
    DownloaderRegistry.register(
        'unsplash', 
        lambda: UnsplashDownloader(config['unsplash_api_key']),
        enabled=config.get('enable_unsplash', False)
    )
```

This registry system allows for easy extension without modifying core orchestrator code.
Simply create your downloader class, register it, and it becomes available throughout
the application.
"""