import argparse
import hashlib
import json
import logging
import os
import random
import shutil
import signal
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any, Tuple, Union

import jsonschema
import requests
from PIL import Image
from duckduckgo_search import DDGS
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler
from jsonschema import validate
from tqdm.auto import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CACHE_FILE = "download_progress.json"
DEFAULT_CONFIG_FILE = "config.json"

# Image extensions supported
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

# JSON Schema for config validation
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["dataset_name", "categories"],
    "properties": {
        "dataset_name": {
            "type": "string",
            "description": "Name of the dataset"
        },
        "categories": {
            "type": "object",
            "description": "Map of category names to lists of keywords",
            "additionalProperties": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "options": {
            "type": "object",
            "description": "Optional configuration settings",
            "properties": {
                "max_images": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum number of images per keyword"
                },
                "output_dir": {
                    "type": ["string", "null"],
                    "description": "Custom output directory"
                },
                "integrity": {
                    "type": "boolean",
                    "description": "Whether to check image integrity"
                },
                "max_retries": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Maximum number of retry attempts"
                },
                "cache_file": {
                    "type": "string",
                    "description": "Path to the progress cache file"
                },
                "generate_keywords": {
                    "type": "boolean",
                    "description": "Whether to generate additional keywords"
                },
                "disable_keyword_generation": {
                    "type": "boolean",
                    "description": "Whether to disable automatic keyword generation"
                }
            }
        }
    }
}


class ProgressCache:
    """
    Tracks and manages progress for dataset generation to enable continuing from where we left off.
    """

    def __init__(self, cache_file: str = DEFAULT_CACHE_FILE):
        self.cache_file = cache_file
        self.completed_paths = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load progress cache from file if it exists."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load progress cache: {e}")
                return {}
        return {}

    def save_cache(self) -> None:
        """Save current progress to cache file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.completed_paths, f, indent=2)
            logger.debug(f"Progress cache saved to {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to save progress cache: {e}")

    def is_completed(self, category: str, keyword: str) -> bool:
        """Check if a specific path has been completed."""
        path_key = f"{category}/{keyword}"
        return path_key in self.completed_paths

    def mark_completed(self, category: str, keyword: str,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark a path as completed with optional metadata."""
        path_key = f"{category}/{keyword}"
        self.completed_paths[path_key] = {
            "timestamp": time.time(),
            "category": category,
            "keyword": keyword,
            "metadata": metadata or {}
        }
        # Save after each update to ensure progress is not lost
        self.save_cache()

    def get_completion_stats(self) -> Dict[str, int]:
        """Get statistics about completion progress."""
        return {
            "total_completed": len(self.completed_paths),
            "categories": len(set(item["category"] for item in self.completed_paths.values()))
        }


def get_image_hash(image_path: str, hash_size: int = 8) -> Optional[str]:
    """
    Compute a perceptual hash for an image to find visually similar images.
    
    Args:
        image_path: Path to the image file
        hash_size: Size of the hash (larger = more sensitive)
        
    Returns:
        str: Perceptual hash string or None if image can't be processed
    """
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale and resize
            img = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)

            # Calculate mean pixel value
            # noinspection PyTypeChecker
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)

            # Create hash
            binary_hash = ''.join('1' if px >= avg else '0' for px in pixels)
            hex_hash = hex(int(binary_hash, 2))[2:]

            return hex_hash.zfill(hash_size ** 2 // 4)
    except Exception as e:
        logger.warning(f"Failed to compute hash for {image_path}: {e}")
        return None


def get_file_hash(file_path: str) -> Optional[str]:
    """
    Compute a regular MD5 hash of file contents.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MD5 hash string or None if file can't be read
    """
    try:
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            # Read in chunks in case of large files
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    except Exception as e:
        logger.warning(f"Failed to compute file hash for {file_path}: {e}")
        return None


def _get_image_files(directory_path: Path) -> List[str]:
    """Get all valid image files from directory."""
    return [
        str(f) for f in directory_path.iterdir()
        if f.is_file() and is_valid_image_extension(f)
    ]


def _build_hash_maps(image_files: List[str]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build content and perceptual hash maps for all images."""
    content_hash_map: Dict[str, List[str]] = {}
    perceptual_hash_map: Dict[str, List[str]] = {}

    for img_path in image_files:
        # Get content hash (exact match)
        content_hash = get_file_hash(img_path)
        if content_hash:
            content_hash_map.setdefault(content_hash, []).append(img_path)

        # Get perceptual hash (similar images)
        perceptual_hash = get_image_hash(img_path)
        if perceptual_hash:
            perceptual_hash_map.setdefault(perceptual_hash, []).append(img_path)

    return content_hash_map, perceptual_hash_map


def _find_exact_duplicates(content_hash_map: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Find exact duplicates based on content hash."""
    duplicates: Dict[str, List[str]] = {}

    for file_list in content_hash_map.values():
        if len(file_list) > 1:
            # Keep the first as original, others as duplicates
            original = file_list[0]
            dups = file_list[1:]
            duplicates[original] = dups

    return duplicates


def _is_file_duplicate(img: str, duplicates: Dict[str, List[str]]) -> bool:
    """Check if a file is already marked as a duplicate."""
    for dups in duplicates.values():
        if img in dups:
            return True
    return False


# noinspection t
def _process_perceptual_duplicates(
        perceptual_hash_map: Dict[str, List[str]],
        existing_duplicates: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """Process perceptual duplicates and merge with existing duplicates."""
    duplicates = existing_duplicates.copy()

    for file_list in perceptual_hash_map.values():
        if len(file_list) > 1:
            kept_file = None

            # Find an image not already marked as duplicate
            for img in file_list:
                if not _is_file_duplicate(img, duplicates):
                    if kept_file is None:
                        kept_file = img
                    else:
                        # Add to duplicates of kept_file
                        if kept_file in duplicates:
                            duplicates[kept_file].append(img)
                        else:
                            duplicates[kept_file] = [img]

    return duplicates


def detect_duplicate_images(directory: str) -> Dict[str, List[str]]:
    """
    Detect duplicate images in a directory using both content hash and perceptual hash.
    
    Args:
        directory: Directory path to check for duplicates
        
    Returns:
        Dict mapping original images to lists of their duplicates
    """
    directory_path = Path(directory)

    # Get all image files
    image_files = _get_image_files(directory_path)

    # Build hash maps
    content_hash_map, perceptual_hash_map = _build_hash_maps(image_files)

    # Find exact duplicates first
    duplicates = _find_exact_duplicates(content_hash_map)

    # Then process perceptual duplicates
    duplicates = _process_perceptual_duplicates(perceptual_hash_map, duplicates)

    return duplicates


def remove_duplicate_images(directory: str) -> Tuple[int, List[str]]:
    """
    Remove duplicate images from a directory.
    
    Args:
        directory: Directory path to clean
        
    Returns:
        Tuple of (number of removed duplicates, list of original images kept)
    """
    duplicates = detect_duplicate_images(directory)

    # Flatten the dictionary to get all duplicates to remove
    removed_count = 0
    removed_files = []
    originals_kept = []

    for original, dups in duplicates.items():
        # Keep track of originals we're keeping
        originals_kept.append(original)

        # Remove duplicates
        for dup in dups:
            try:
                os.remove(dup)
                removed_count += 1
                removed_files.append(dup)
                logger.info(f"Removed duplicate image: {dup} (duplicate of {original})")
            except Exception as e:
                logger.warning(f"Failed to remove duplicate {dup}: {e}")

    logger.info(f"Removed {removed_count} duplicate images from {directory}")
    return removed_count, originals_kept


class TimeoutException(Exception):
    """Custom exception for timeout operations"""
    pass


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


def download_images(keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
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

        # Define search variations to try
        variations = [
            keyword,
            f"{keyword} photo",
            f"{keyword} high resolution"
        ]

        total_downloaded = 0
        per_variation_limit = max(3, max_num // len(variations))

        # Define the engines to try in order of preference
        engines = [
            ("google", _download_with_google, random.randint(0, 20)),
            ("bing", _download_with_bing, random.randint(0, 30)),
            ("baidu", _download_with_baidu, random.randint(10, 50))
        ]

        # Try each engine in sequence
        for engine_name, download_func, random_offset in engines:
            if total_downloaded >= max_num:
                break

            total_downloaded = _try_engine(
                engine_name=engine_name,
                download_func=download_func,
                variations=variations,
                out_dir=out_dir,
                max_num=max_num,
                per_variation_limit=per_variation_limit,
                total_downloaded=total_downloaded,
                offset=random_offset
            )

        # Fallback to DuckDuckGo if needed
        if total_downloaded < max_num:
            total_downloaded = _try_duckduckgo_fallback(
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
        return _final_duckduckgo_fallback(keyword, out_dir, max_num)


def _try_engine(engine_name: str, download_func: Callable, variations: List[str],
                out_dir: str, max_num: int, per_variation_limit: int,
                total_downloaded: int, offset: int) -> int:
    """
    Try downloading images using the specified engine.
    
    Args:
        engine_name: Name of the engine for logging
        download_func: Function to use for downloading
        variations: List of search term variations
        out_dir: Output directory
        max_num: Maximum number of images to download
        per_variation_limit: Maximum images per variation
        total_downloaded: Current download count
        offset: Random offset for search results
        
    Returns:
        Updated total downloaded count
    """
    logger.info(f"Attempting download using {engine_name.capitalize()}ImageCrawler")
    try:
        total_downloaded = download_func(
            variations=variations,
            out_dir=out_dir,
            max_num=max_num - total_downloaded,
            per_variation_limit=per_variation_limit,
            total_downloaded=total_downloaded,
            offset=offset
        )
    except Exception as e:
        logger.warning(f"{engine_name.capitalize()}ImageCrawler failed: {e}")

    return total_downloaded


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


def _download_with_google(variations: List[str], out_dir: str, max_num: int,
                          per_variation_limit: int, total_downloaded: int = 0, offset: int = 0) -> int:
    """Helper function to download images using Google Image Crawler"""
    for i, variation in enumerate(variations):
        if total_downloaded >= max_num:
            break

        # Calculate remaining images needed
        remaining = max_num - total_downloaded

        # Limit for this variation
        current_limit = min(remaining, per_variation_limit)

        # Use different offset for each variation
        current_offset = offset + (i * 20)

        logger.info(
            f"Google: Trying to download {current_limit} images with query: '{variation}' (offset: {current_offset})")

        try:
            crawler = GoogleImageCrawler(
                storage={'root_dir': out_dir},
                log_level=logging.WARNING,
                feeder_threads=1,
                parser_threads=1,
                downloader_threads=3
            )

            crawler.crawl(
                keyword=variation,
                max_num=current_limit,
                min_size=(100, 100),
                offset=current_offset,
                file_idx_offset=total_downloaded
            )

            # Count valid images after this batch download
            temp_valid_count = count_valid_images_in_latest_batch(out_dir, total_downloaded)
            total_downloaded += temp_valid_count

            logger.info(
                f"Google downloaded {temp_valid_count} valid images for '{variation}', total: {total_downloaded}/{max_num}")

            # Small delay between different search terms
            time.sleep(1)

        except Exception as e:
            logger.warning(f"Google crawler failed with query '{variation}': {e}")

    return total_downloaded


def _download_with_bing(variations: List[str], out_dir: str, max_num: int,
                        per_variation_limit: int, total_downloaded: int = 0, offset: int = 0) -> int:
    """Helper function to download images using Bing Image Crawler"""
    for i, variation in enumerate(variations):
        if total_downloaded >= max_num:
            break

        # Calculate remaining images needed
        remaining = max_num - total_downloaded

        # Limit for this variation
        current_limit = min(remaining, per_variation_limit)

        # Use different offset for each variation to get more diverse results
        current_offset = offset + (i * 10)

        logger.info(
            f"Bing: Trying to download {current_limit} images with query: '{variation}' (offset: {current_offset})")

        try:
            crawler = BingImageCrawler(
                storage={'root_dir': out_dir},
                log_level=logging.WARNING,
                feeder_threads=1,
                parser_threads=1,
                downloader_threads=3
            )

            crawler.crawl(
                keyword=variation,
                max_num=current_limit,
                min_size=(100, 100),
                offset=current_offset,
                file_idx_offset=total_downloaded
            )

            # Count valid images after this batch download
            temp_valid_count = count_valid_images_in_latest_batch(out_dir, total_downloaded)
            total_downloaded += temp_valid_count

            logger.info(
                f"Bing downloaded {temp_valid_count} valid images for '{variation}', total: {total_downloaded}/{max_num}")

            # Small delay between different search terms
            time.sleep(1)

        except Exception as e:
            logger.warning(f"Bing crawler failed with query '{variation}': {e}")

    return total_downloaded


def _download_with_baidu(variations: List[str], out_dir: str, max_num: int,
                         per_variation_limit: int, total_downloaded: int = 0, offset: int = 0) -> int:
    """Helper function to download images using Baidu Image Crawler"""
    for i, variation in enumerate(variations):
        if total_downloaded >= max_num:
            break

        # Calculate remaining images needed
        remaining = max_num - total_downloaded

        # Limit for this variation
        current_limit = min(remaining, per_variation_limit)

        # Use different offset for each variation to get more diverse results
        current_offset = offset + (i * 15)

        logger.info(
            f"Baidu: Trying to download {current_limit} images with query: '{variation}' (offset: {current_offset})")

        try:
            crawler = BaiduImageCrawler(
                storage={'root_dir': out_dir},
                log_level=logging.WARNING,
                feeder_threads=1,
                parser_threads=1,
                downloader_threads=3
            )

            crawler.crawl(
                keyword=variation,
                max_num=current_limit,
                min_size=(100, 100),
                offset=current_offset,
                file_idx_offset=total_downloaded
            )

            # Count valid images after this batch download
            temp_valid_count = count_valid_images_in_latest_batch(out_dir, total_downloaded)
            total_downloaded += temp_valid_count

            logger.info(
                f"Baidu downloaded {temp_valid_count} valid images for '{variation}', total: {total_downloaded}/{max_num}")

            # Small delay between different search terms
            time.sleep(1)

        except Exception as e:
            logger.warning(f"Baidu crawler failed with query '{variation}': {e}")

    return total_downloaded


def rename_images_sequentially(directory: str) -> int:
    """
    Rename all image files in a directory to a sequential, zero-padded format.
    
    Args:
        directory: Directory containing images to rename
        
    Returns:
        int: Number of renamed files
    """
    directory_path = Path(directory)

    if not _validate_directory_exists(directory_path):
        return 0

    image_files = _get_sorted_image_files(directory_path)

    if not image_files:
        logger.warning(f"No image files found in {directory}")
        return 0

    temp_dir = _create_temp_directory(directory_path)
    padding_width = _calculate_padding_width(len(image_files))

    renamed_count = _copy_files_to_temp_with_new_names(
        image_files, temp_dir, padding_width
    )

    _delete_original_files(image_files)
    _move_files_from_temp_to_original(temp_dir, directory_path)
    _cleanup_temp_directory(temp_dir)

    logger.info(f"Renamed {renamed_count} images in {directory} with sequential numbering")
    return renamed_count


def _validate_directory_exists(directory_path: Path) -> bool:
    """Validate that the directory exists."""
    if not directory_path.exists():
        logger.warning(f"Directory {directory_path} does not exist")
        return False
    return True


def _get_sorted_image_files(directory_path: Path) -> List[Path]:
    """Get all image files sorted by creation time."""
    image_files = [
        f for f in directory_path.iterdir()
        if f.is_file() and is_valid_image_extension(f)
    ]
    image_files.sort(key=lambda x: os.path.getctime(x))
    return image_files


def _create_temp_directory(directory_path: Path) -> Path:
    """Create a temporary directory for renaming operations."""
    temp_dir = directory_path / ".temp_rename"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


def _calculate_padding_width(file_count: int) -> int:
    """Calculate the padding width for sequential numbering."""
    return max(3, len(str(file_count)))


def _copy_files_to_temp_with_new_names(
        image_files: List[Path], temp_dir: Path, padding_width: int
) -> int:
    """Copy files to temp directory with new sequential names."""
    renamed_count = 0

    for i, file_path in enumerate(image_files, 1):
        extension = file_path.suffix.lower()
        new_filename = f"{i:0{padding_width}d}{extension}"
        temp_path = temp_dir / new_filename

        try:
            shutil.copy2(file_path, temp_path)
            renamed_count += 1
        except Exception as e:
            logger.error(f"Failed to copy {file_path} to temp directory: {e}")

    return renamed_count


def _delete_original_files(image_files: List[Path]) -> None:
    """Delete original image files."""
    for file_path in image_files:
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Failed to delete original file {file_path}: {e}")


def _move_files_from_temp_to_original(temp_dir: Path, directory_path: Path) -> None:
    """Move files from temp directory back to original directory."""
    for file_path in temp_dir.iterdir():
        if file_path.is_file():
            try:
                shutil.move(str(file_path), str(directory_path / file_path.name))
            except Exception as e:
                logger.error(f"Failed to move {file_path} from temp directory: {e}")


def _cleanup_temp_directory(temp_dir: Path) -> None:
    """Remove the temporary directory."""
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        logger.error(f"Failed to remove temp directory: {e}")


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
    success, count = download_images(keyword, out_dir, max_num)

    # Remove any duplicates after initial download
    if count > 1:
        count = _update_image_count(out_dir)
        logger.info(f"After removing duplicates: {count} unique images remain")

    # Calculate how many more images we need
    images_needed = max(0, max_num - count)
    retries = 0

    # List of available engines to cycle through
    engines = ["google", "bing", "baidu", "ddgs"]

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
        engine_index = (retries - 1) % len(engines)
        current_engine = engines[engine_index]
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


@dataclass
class DatasetGenerationConfig:
    """Configuration for dataset generation."""
    config_path: str
    max_images: int = 10
    output_dir: Optional[str] = None
    integrity: bool = True
    max_retries: int = 5
    continue_from_last: bool = False
    cache_file: str = DEFAULT_CACHE_FILE
    generate_keywords: bool = False
    disable_keyword_generation: bool = False


def generate_dataset(config: DatasetGenerationConfig) -> None:
    """
    Generate image dataset based on configuration file.
    
    Args:
        config: Dataset generation configuration
    """
    # Load and validate config
    dataset_config = _load_and_validate_config(config)
    dataset_name = dataset_config['dataset_name']
    categories = dataset_config['categories']

    # Set output directory
    root_dir = _setup_output_directory(config.output_dir, dataset_name)

    # Initialize tracker and progress cache
    tracker, progress_cache = _initialize_tracking(config.continue_from_last, config.cache_file)

    # Process each category
    for category_name, keywords in tqdm(categories.items(), desc="Processing Categories", leave=True):
        logger.info(f"Processing category: {category_name}")

        # Create category directory
        category_path = root_dir / category_name
        category_path.mkdir(parents=True, exist_ok=True)

        # Handle keywords based on configuration
        keywords = _process_keywords(
            category_name,
            keywords,
            config.generate_keywords,
            config.disable_keyword_generation
        )

        # Process each keyword
        _process_keywords_for_category(
            category_name,
            keywords,
            category_path,
            config,
            tracker,
            progress_cache
        )

    # Print comprehensive summary
    tracker.print_summary()

    logger.info(f"Dataset generation completed. Output directory: {root_dir}")


def _load_and_validate_config(config: DatasetGenerationConfig) -> Dict[str, Any]:
    """Load and validate the dataset configuration, applying config file options."""
    dataset_config = load_config(config.config_path)

    # Extract options from config if available, with CLI arguments taking precedence
    if 'options' in dataset_config and isinstance(dataset_config['options'], dict):
        options = dataset_config['options']

        # Apply config file options if CLI arguments weren't explicitly provided
        _apply_config_options(config, options)

    return dataset_config


def _apply_config_options(config: DatasetGenerationConfig, options: Dict[str, Any]) -> None:
    """Apply options from config file to the configuration object."""
    # Only use config values if CLI arguments weren't explicitly provided
    if config.max_images == 10 and 'max_images' in options:
        config.max_images = options.get('max_images')
        logger.info(f"Using max_images={config.max_images} from config file")

    if config.output_dir is None and 'output_dir' in options:
        config.output_dir = options.get('output_dir')
        logger.info(f"Using output_dir={config.output_dir} from config file")

    if config.integrity is True and 'integrity' in options:
        config.integrity = options.get('integrity')
        logger.info(f"Using integrity={config.integrity} from config file")

    if config.max_retries == 5 and 'max_retries' in options:
        config.max_retries = options.get('max_retries')
        logger.info(f"Using max_retries={config.max_retries} from config file")

    if config.cache_file == DEFAULT_CACHE_FILE and 'cache_file' in options:
        config.cache_file = options.get('cache_file')
        logger.info(f"Using cache_file={config.cache_file} from config file")

    if config.generate_keywords is False and 'generate_keywords' in options:
        config.generate_keywords = options.get('generate_keywords')
        logger.info(f"Using generate_keywords={config.generate_keywords} from config file")

    if config.disable_keyword_generation is False and 'disable_keyword_generation' in options:
        config.disable_keyword_generation = options.get('disable_keyword_generation')
        logger.info(f"Using disable_keyword_generation={config.disable_keyword_generation} from config file")


def _setup_output_directory(output_dir: Optional[str], dataset_name: str) -> Path:
    """Set up and create the output directory."""
    root_dir = output_dir or dataset_name
    root_path = Path(root_dir)
    root_path.mkdir(parents=True, exist_ok=True)
    return root_path


def _initialize_tracking(continue_from_last: bool, cache_file: str) -> Tuple[DatasetTracker, Optional[ProgressCache]]:
    """Initialize the dataset tracker and progress cache."""
    tracker = DatasetTracker()
    progress_cache = ProgressCache(cache_file) if continue_from_last else None

    if continue_from_last and progress_cache:
        stats = progress_cache.get_completion_stats()
        logger.info(
            f"Continuing from previous run. Already completed: {stats['total_completed']} items across {stats['categories']} categories.")

    return tracker, progress_cache


def _process_keywords(
        category_name: str,
        keywords: List[str],
        generate_keywords: bool,
        disable_keyword_generation: bool
) -> List[str]:
    """Process keywords based on configuration options."""
    if not keywords and not disable_keyword_generation:
        # No keywords provided and generation not disabled, generate keywords
        keywords = generate_keywords_for_category(category_name)
        logger.info(f"No keywords provided for category '{category_name}', generated {len(keywords)} keywords")
    elif not keywords and disable_keyword_generation:
        # No keywords and generation disabled, use category name as keyword
        keywords = [category_name]
        logger.info(
            f"No keywords provided for category '{category_name}' and generation disabled, using category name as keyword")
    elif generate_keywords and not disable_keyword_generation:
        # Keywords provided and asked to generate more
        generated_keywords = generate_keywords_for_category(category_name)
        # Add generated keywords to user-provided ones, avoiding duplicates
        original_count = len(keywords)
        keywords = list(set(keywords + generated_keywords))
        logger.info(
            f"Added {len(keywords) - original_count} generated keywords to {original_count} user-provided ones")

    return keywords


def _process_keywords_for_category(
        category_name: str,
        keywords: List[str],
        category_path: Path,
        config: DatasetGenerationConfig,
        tracker: DatasetTracker,
        progress_cache: Optional[ProgressCache]
) -> None:
    """Process all keywords for a specific category."""
    for keyword in tqdm(keywords, desc=f"Keywords in {category_name}", leave=False):
        # Skip if already processed and continuing from last run
        if config.continue_from_last and progress_cache and progress_cache.is_completed(category_name, keyword):
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
            max_num=config.max_images,
            max_retries=config.max_retries
        )

        # Track results
        _track_download_results(tracker, download_context, success, count)

        # Check integrity if enabled
        if config.integrity:
            _check_image_integrity(tracker, download_context, str(keyword_path), config.max_images)

        # Update progress cache if continuing from last run
        if config.continue_from_last and progress_cache:
            metadata = {
                "success": success,
                "downloaded_count": count,
            }
            progress_cache.mark_completed(category_name, keyword, metadata)

        # Small delay to be respectful to image services
        time.sleep(0.5)


def _track_download_results(
        tracker: DatasetTracker,
        download_context: str,
        success: bool,
        count: int
) -> None:
    """Track the results of image downloads."""
    if success:
        tracker.record_download_success(download_context)
        logger.info(f"Successfully downloaded {count} images for {download_context}")
    else:
        error_msg = "Failed to download any valid images after retries"
        tracker.record_download_failure(download_context, error_msg)
        logger.warning(f"Failed to download images for: {download_context}")


def _check_image_integrity(
        tracker: DatasetTracker,
        download_context: str,
        keyword_path: str,
        max_images: int
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
    parser.add_argument("--generate-keywords", action="store_true", help="Generate additional keywords for categories")
    parser.add_argument("--no-generate-keywords", action="store_true",
                        help="Disable keyword generation even if no keywords provided")
    return parser


def generate_keywords_for_category(category: str) -> List[str]:
    """
    Generate related keywords for a category using predefined patterns.
    This is a simple implementation that doesn't use external AI services,
    but creates meaningful variations for the given category.
    
    Args:
        category: The category name to generate keywords for
    
    Returns:
        List of generated keywords related to the category
    """
    # Basic variations that work for most categories
    variations = [
        category,
        f"{category} example",
        f"{category} in detail",
        f"{category} high quality",
        f"{category} closeup",
    ]

    # Domain-specific variations (add more based on use case)
    domain_variations = []

    # Check for specific category types and add relevant keywords
    if any(term in category.lower() for term in ["animal", "bird", "mammal", "insect", "fish"]):
        domain_variations.extend([
            f"{category} in wild",
            f"{category} natural habitat",
            f"{category} wildlife",
        ])

    elif any(term in category.lower() for term in ["food", "dish", "meal", "fruit", "vegetable"]):
        domain_variations.extend([
            f"{category} meal",
            f"{category} on plate",
            f"{category} cuisine",
            f"fresh {category}",
        ])

    elif any(term in category.lower() for term in ["landscape", "place", "location", "country", "city"]):
        domain_variations.extend([
            f"{category} view",
            f"{category} landscape",
            f"{category} scenic",
            f"{category} travel",
        ])

    elif any(term in category.lower() for term in ["object", "tool", "device", "machine"]):
        domain_variations.extend([
            f"{category} isolated",
            f"{category} on white background",
            f"{category} in use",
        ])

    # Add domain-specific variations if we found any
    variations.extend(domain_variations)

    # Add some randomization to ensure diversity
    if len(variations) > 5:
        additional = [
            f"{category} professional photo",
            f"{category} detailed",
            f"high resolution {category}",
            f"{category} photography"
        ]
        variations.extend(random.sample(additional, min(2, len(additional))))

    # Remove any duplicates that might have been created
    return list(set(variations))


def main():
    """Main function to parse arguments and generate dataset"""

    parser = argparse.ArgumentParser(description="PixCrawler: Image Dataset Generator")
    parser = create_arg_parser(parser)

    args = parser.parse_args()

    config = DatasetGenerationConfig(
        config_path=args.config,
        max_images=args.max_images,
        output_dir=args.output,
        integrity=not args.no_integrity,
        max_retries=args.max_retries,
        continue_from_last=args.continue_last,
        cache_file=args.cache,
        generate_keywords=args.generate_keywords,
        disable_keyword_generation=args.no_generate_keywords
    )

    generate_dataset(config)


if __name__ == "__main__":
    main()
