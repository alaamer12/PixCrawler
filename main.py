import argparse
import concurrent.futures
import contextlib
import json
import logging
import os
import random
import sys
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import g4f
import jsonschema
import requests
from PIL import Image
from duckduckgo_search import DDGS
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler
from jsonschema import validate

from config import DatasetGenerationConfig, CONFIG_SCHEMA
from constants import DEFAULT_CACHE_FILE, DEFAULT_CONFIG_FILE, DEFAULT_LOG_FILE, ENGINES, \
    file_formatter, KEYWORD_MODE, AI_MODELS
from constants import logger, Colors, PIXCRAWLER_ASCII
from helpers import FSRenamer, ReportGenerator, DatasetTracker, ProgressManager
from jupyter_support import is_running_in_notebook, print_help_colored
from utilities import ProgressCache, detect_duplicate_images, \
    is_valid_image_extension, validate_image, count_valid_images, remove_duplicate_images

# Create a global progress manager
progress = ProgressManager()


class LabelGenerator:
    """
    Class to generate label files for images in the dataset.
    
    This class creates structured label files that correspond to the images,
    which can be used for machine learning tasks like classification or object detection.
    It supports multiple output formats (txt, json, csv, yaml) and ensures proper
    organization matching the dataset structure.
    """

    def __init__(self, format_type: str = "txt"):
        """
        Initialize the label generator with specified format type.
        
        Args:
            format_type: The format for label files ('txt', 'json', 'csv', 'yaml')
        """
        self.format_type = format_type.lower()
        self.supported_formats = {"txt", "json", "csv", "yaml"}

        if self.format_type not in self.supported_formats:
            logger.warning(f"Unsupported label format: {format_type}. Defaulting to 'txt'.")
            self.format_type = "txt"

    def generate_dataset_labels(self, dataset_dir: str) -> None:
        """
        Generate label files for all images in the dataset.
        
        Args:
            dataset_dir: Root directory of the dataset
        """
        logger.info(f"Generating {self.format_type} labels for dataset at {dataset_dir}")
        dataset_path = Path(dataset_dir)

        # Create labels directory
        labels_dir = dataset_path / "labels"
        labels_dir.mkdir(parents=True, exist_ok=True)

        # Process each category directory
        category_dirs = [d for d in dataset_path.iterdir() if d.is_dir() and d.name != "labels"]

        # Count total images for progress tracking
        total_images = sum(
            len([f for f in Path(keyword_dir).glob("**/*") if f.is_file() and is_valid_image_extension(f)])
            for category_dir in category_dirs
            for keyword_dir in [d for d in category_dir.iterdir() if d.is_dir()]
        )

        # Create metadata file for the dataset with overall information
        self._generate_dataset_metadata(dataset_path, labels_dir, len(category_dirs), total_images)

        # Create category index file
        self._generate_category_index(labels_dir, [d.name for d in category_dirs])

        # Initialize progress manager for label generation
        progress.start_step("labels", total=total_images)

        # Process each category
        for category_dir in category_dirs:
            category_name = category_dir.name
            progress.start_subtask(f"Category: {category_name}")
            self._process_category(category_dir, category_name, labels_dir, progress)
            progress.close_subtask()

        # Close progress bars
        progress.close()
        logger.info(f"Label generation completed. Labels stored in {labels_dir}")

    def _generate_dataset_metadata(self, dataset_path: Path, labels_dir: Path,
                                   category_count: int, image_count: int) -> None:
        """
        Generate overall dataset metadata.
        
        Args:
            dataset_path: Root path of the dataset
            labels_dir: Directory where labels are stored
            category_count: Number of categories in the dataset
            image_count: Total number of images in the dataset
        """
        dataset_name = dataset_path.name

        metadata = {
            "dataset_name": dataset_name,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "categories_count": category_count,
            "images_count": image_count,
            "label_format": self.format_type
        }

        # Write to appropriate format
        if self.format_type == "json":
            with open(labels_dir / "dataset_metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        elif self.format_type == "yaml":
            try:
                import yaml
                with open(labels_dir / "dataset_metadata.yaml", "w", encoding="utf-8") as f:
                    yaml.dump(metadata, f, default_flow_style=False)
            except ImportError:
                logger.warning("PyYAML not installed, skipping YAML metadata generation")
        else:
            # For txt and csv, use simple format
            with open(labels_dir / "dataset_metadata.txt", "w", encoding="utf-8") as f:
                for key, value in metadata.items():
                    f.write(f"{key}: {value}\n")

    def _generate_category_index(self, labels_dir: Path, categories: List[str]) -> None:
        """
        Generate category index file mapping categories to numeric IDs.
        
        Args:
            labels_dir: Directory where labels are stored
            categories: List of category names
        """
        # Create category to ID mapping
        category_map = {name: idx for idx, name in enumerate(sorted(categories))}

        # Write to appropriate format
        if self.format_type == "json":
            with open(labels_dir / "category_index.json", "w", encoding="utf-8") as f:
                json.dump(category_map, f, indent=2)
        elif self.format_type == "yaml":
            try:
                import yaml
                with open(labels_dir / "category_index.yaml", "w", encoding="utf-8") as f:
                    yaml.dump(category_map, f, default_flow_style=False)
            except ImportError:
                logger.warning("PyYAML not installed, skipping YAML category index generation")
        elif self.format_type == "csv":
            with open(labels_dir / "category_index.csv", "w", encoding="utf-8", newline="") as f:
                f.write("category,id\n")
                for name, idx in category_map.items():
                    f.write(f"{name},{idx}\n")
        else:
            # For txt format
            with open(labels_dir / "category_index.txt", "w", encoding="utf-8") as f:
                for name, idx in category_map.items():
                    f.write(f"{name}: {idx}\n")

    def _process_category(self, category_dir: Path, category_name: str,
                          labels_dir: Path, progress: ProgressManager) -> None:
        """
        Process a single category directory.
        
        Args:
            category_dir: Directory containing the category
            category_name: Name of the category
            labels_dir: Directory to store label files
            progress: Progress manager object
        """
        # Create category label directory
        category_label_dir = labels_dir / category_name
        category_label_dir.mkdir(parents=True, exist_ok=True)

        # Process each keyword directory within the category
        keyword_dirs = [d for d in category_dir.iterdir() if d.is_dir()]
        for keyword_dir in keyword_dirs:
            keyword_name = keyword_dir.name
            progress.set_subtask_description(f"Keyword: {keyword_name}")
            self._process_keyword(keyword_dir, category_name, keyword_name, category_label_dir, progress)

    def _process_keyword(self, keyword_dir: Path, category_name: str, keyword_name: str,
                         category_label_dir: Path, progress: ProgressManager) -> None:
        """
        Process a keyword directory and generate labels for its images.
        
        Args:
            keyword_dir: Directory containing images for the keyword
            category_name: Name of the category
            keyword_name: Name of the keyword
            category_label_dir: Directory to store label files for this category
            progress: Progress manager object
        """
        # Create keyword label directory
        keyword_label_dir = category_label_dir / keyword_name
        keyword_label_dir.mkdir(parents=True, exist_ok=True)

        # Get all image files regardless of naming pattern
        image_files = [
            f for f in keyword_dir.iterdir()
            if f.is_file() and is_valid_image_extension(f)
        ]

        # Generate label for each image
        for image_file in image_files:
            self._generate_label_file(
                image_file=image_file,
                label_dir=keyword_label_dir,
                category=category_name,
                keyword=keyword_name
            )
            progress.update_step(1)  # Update main progress bar

    def _generate_label_file(self, image_file: Path, label_dir: Path, category: str, keyword: str) -> None:
        """
        Generate a label file for a single image.
        
        Args:
            image_file: Path to the image file
            label_dir: Directory to store the label file
            category: Category name
            keyword: Keyword name
        """
        # Create a matching filename but with the appropriate extension
        # Handle any naming pattern by using the stem of the original filename
        label_filename = image_file.stem + "." + self.format_type
        label_file_path = label_dir / label_filename

        try:
            # Try to get image metadata if possible
            image_metadata = self._extract_image_metadata(image_file)

            # Generate label content based on format
            if self.format_type == "txt":
                self._write_txt_label(label_file_path, category, keyword, image_file, image_metadata)
            elif self.format_type == "json":
                self._write_json_label(label_file_path, category, keyword, image_file, image_metadata)
            elif self.format_type == "csv":
                self._write_csv_label(label_file_path, category, keyword, image_file, image_metadata)
            elif self.format_type == "yaml":
                self._write_yaml_label(label_file_path, category, keyword, image_file, image_metadata)

        except PermissionError:
            logger.warning(f"Permission denied when creating label file for {image_file}")
        except IOError as e:
            logger.warning(f"I/O error generating label for {image_file}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error generating label for {image_file}: {e}")

    @staticmethod
    def _extract_image_metadata(image_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from an image if possible.
        
        Args:
            image_path: Path to the image
            
        Returns:
            Dictionary with image metadata
        """
        metadata = {
            "timestamp": time.time(),
            "size": os.path.getsize(image_path) if image_path.exists() else None,
            "filename": image_path.name,
            "parent_dir": image_path.parent.name  # Store parent directory name for context
        }

        # Try to get image dimensions
        try:
            with Image.open(image_path) as img:
                metadata["width"] = img.width
                metadata["height"] = img.height
                metadata["format"] = img.format
                metadata["mode"] = img.mode
        except Exception:
            # If we can't open the image, just continue without dimensions
            pass

        return metadata

    @staticmethod
    def _write_txt_label(label_path: Path, category: str, keyword: str,
                         image_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Write label in TXT format.
        
        Args:
            label_path: Path to write the label file
            category: Category name
            keyword: Keyword name
            image_path: Path to the corresponding image
            metadata: Image metadata
        """
        try:
            with open(label_path, "w", encoding="utf-8") as f:
                f.write(f"category: {category}\n")
                f.write(f"keyword: {keyword}\n")
                f.write(f"image_path: {image_path}\n")
                f.write(f"timestamp: {metadata['timestamp']}\n")
                f.write(f"filename: {metadata['filename']}\n")

                # Add image dimensions if available
                if "width" in metadata and "height" in metadata:
                    f.write(f"width: {metadata['width']}\n")
                    f.write(f"height: {metadata['height']}\n")

                if "format" in metadata:
                    f.write(f"format: {metadata['format']}\n")

            logger.debug(f"Created TXT label: {label_path}")
        except Exception as e:
            logger.warning(f"Failed to write TXT label {label_path}: {e}")
            raise

    @staticmethod
    def _write_json_label(label_path: Path, category: str, keyword: str,
                          image_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Write label in JSON format.
        
        Args:
            label_path: Path to write the label file
            category: Category name
            keyword: Keyword name
            image_path: Path to the corresponding image
            metadata: Image metadata
        """
        try:
            label_data = {
                "category": category,
                "keyword": keyword,
                "image_path": str(image_path),
                **metadata
            }

            with open(label_path, "w", encoding="utf-8") as f:
                json.dump(label_data, f, indent=2)
            logger.debug(f"Created JSON label: {label_path}")
        except Exception as e:
            logger.warning(f"Failed to write JSON label {label_path}: {e}")
            raise

    @staticmethod
    def _write_csv_label(label_path: Path, category: str, keyword: str,
                         image_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Write label in CSV format.
        
        Args:
            label_path: Path to write the label file
            category: Category name
            keyword: Keyword name
            image_path: Path to the corresponding image
            metadata: Image metadata
        """
        try:
            headers = ["category", "keyword", "image_path", "timestamp", "filename", "width", "height", "format",
                       "size"]
            values = [
                category,
                keyword,
                str(image_path),
                metadata.get("timestamp", ""),
                metadata.get("filename", ""),
                metadata.get("width", ""),
                metadata.get("height", ""),
                metadata.get("format", ""),
                metadata.get("size", "")
            ]

            with open(label_path, "w", encoding="utf-8", newline="") as f:
                f.write(",".join(headers) + "\n")
                f.write(",".join(str(v) for v in values) + "\n")

            logger.debug(f"Created CSV label: {label_path}")
        except Exception as e:
            logger.warning(f"Failed to write CSV label {label_path}: {e}")
            raise

    def _write_yaml_label(self, label_path: Path, category: str, keyword: str,
                          image_path: Path, metadata: Dict[str, Any]) -> None:
        """
        Write label in YAML format.
        
        Args:
            label_path: Path to write the label file
            category: Category name
            keyword: Keyword name
            image_path: Path to the corresponding image
            metadata: Image metadata
        """
        try:
            import yaml

            label_data = {
                "category": category,
                "keyword": keyword,
                "image_path": str(image_path),
                **metadata
            }

            with open(label_path, "w", encoding="utf-8") as f:
                yaml.dump(label_data, f, default_flow_style=False)
            logger.debug(f"Created YAML label: {label_path}")
        except ImportError:
            logger.warning("PyYAML not installed, falling back to TXT format")
            self._write_txt_label(label_path, category, keyword, image_path, metadata)
        except Exception as e:
            logger.warning(f"Failed to write YAML label {label_path}: {e}")
            raise


def _apply_config_options(config: DatasetGenerationConfig, options: Dict[str, Any]) -> None:
    """
    Apply configuration options from config file to the configuration object.
    
    This function selectively overrides default configuration values with values
    from the config file, but only when CLI arguments haven't explicitly set them.
    
    Args:
        config: The configuration object to modify
        options: Dictionary containing configuration options from config file
    """
    # Dictionary of CLI argument properties and conditions for applying config values
    # Format: option_name: (condition_to_apply_config_value, getter_function)
    # The condition is True when the CLI argument is using its default value
    config_mappings = {
        'max_images': (config.max_images == 10, lambda: options.get('max_images')),
        'output_dir': (config.output_dir is None, lambda: options.get('output_dir')),
        'integrity': (config.integrity is True, lambda: options.get('integrity')),
        'max_retries': (config.max_retries == 5, lambda: options.get('max_retries')),
        'cache_file': (config.cache_file == DEFAULT_CACHE_FILE, lambda: options.get('cache_file')),
        'keyword_generation': (config.keyword_generation == "auto", lambda: options.get('keyword_generation')),
        'ai_model': (config.ai_model == "gpt4-mini", lambda: options.get('ai_model')),
        'generate_labels': (config.generate_labels is True, lambda: options.get('generate_labels'))
    }

    # Apply each config option if its CLI argument is using the default value
    for option_name, (is_using_default, value_getter) in config_mappings.items():
        if is_using_default and option_name in options and value_getter() is not None:
            new_value = value_getter()
            setattr(config, option_name, new_value)
            logger.info(f"Applied {option_name}={new_value} from config file")
        elif not is_using_default:
            logger.debug(f"CLI argument overriding config file for {option_name}")


class DuckDuckGoImageDownloader:
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


class ImageDownloader:
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

        # Define engine configurations
        self.engines = self._get_engines()

        # Search variations template
        self.search_variations = self._get_search_variations()

        # Thread synchronization
        self.lock = threading.RLock()

        # Signal for worker threads
        self.stop_workers = False

        # Shared counter for downloaded images
        self.total_downloaded = 0

        # Track successful downloads by engine
        self.engine_stats = {}

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
                self.engine_stats = {}

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
                self._download_with_parallel_engines(keyword, variations, out_dir, max_num)
            else:
                # Use engines in sequence with fallbacks (original approach)
                progress.set_subtask_description(f"Downloading sequentially: {keyword}")
                self._download_with_sequential_engines(keyword, variations, out_dir, max_num)

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
            self._log_engine_stats()

            # Update progress with results
            progress.set_subtask_description(f"Downloaded {self.total_downloaded}/{max_num} images for {keyword}")

            return self.total_downloaded > 0, self.total_downloaded

        except Exception as e:
            logger.warning(f"All crawlers failed with error: {e}. Trying DuckDuckGo as fallback.")
            progress.set_subtask_description(f"Error occurred, using final fallback: {keyword}")
            return self._final_duckduckgo_fallback(keyword, out_dir, max_num)

    def _download_with_parallel_engines(self, keyword: str, variations: List[str],
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_engines) as executor:
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
            while completed < len(futures) and self.total_downloaded < max_num:
                # Check if we've reached our download target
                if self.total_downloaded >= max_num:
                    # Signal workers to stop
                    self.stop_workers = True
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
                logger.info(f"Downloaded {self.total_downloaded}/{max_num} images so far")

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
        if self.stop_workers:
            return 0

        engine_name = engine_config['name']
        offset_min, offset_max = engine_config['offset_range']
        variation_step = engine_config['variation_step']

        logger.info(f"Starting parallel download using {engine_name.capitalize()}ImageCrawler")

        # Track engine downloads
        engine_downloaded = 0

        # Use a thread pool for variations
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_variations) as variation_executor:
            variation_futures = []

            # Calculate how many variations to use
            variations_to_use = min(len(variations), max(3, int(max_num / 3)))
            selected_variations = variations[:variations_to_use]

            # Submit tasks for each variation
            for i, variation in enumerate(selected_variations):
                if self.stop_workers:
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
                if self.stop_workers:
                    break

                try:
                    # Get the number of images downloaded by this variation
                    variation_count = future.result()

                    # Update engine downloaded count
                    with self.lock:
                        engine_downloaded += variation_count
                        self.total_downloaded += variation_count

                        # Update engine stats
                        if engine_name not in self.engine_stats:
                            self.engine_stats[engine_name] = 0
                        self.engine_stats[engine_name] += variation_count

                        # Check if we've reached the target
                        if self.total_downloaded >= total_max:
                            self.stop_workers = True
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
        if self.stop_workers:
            return 0

        logger.info(f"{engine_name}: Downloading up to {max_num} images for '{variation}' (offset: {offset})")

        try:
            # Get crawler class
            crawler_class = self._get_crawler_class(engine_name)
            if not crawler_class:
                return 0

            # Create crawler
            crawler = self._create_crawler(crawler_class, out_dir)

            # Calculate file index offset
            with self.lock:
                file_idx_offset = self.total_downloaded + engine_downloaded

            # Crawl for images
            crawler.crawl(
                keyword=variation,
                max_num=max_num,
                min_size=self.min_image_size,
                offset=offset,
                file_idx_offset=file_idx_offset
            )

            # Count valid images
            with self.lock:
                temp_valid_count = count_valid_images_in_latest_batch(
                    out_dir,
                    file_idx_offset
                )

            logger.info(f"{engine_name} downloaded {temp_valid_count} valid images for '{variation}'")
            return temp_valid_count

        except Exception as e:
            logger.warning(f"{engine_name} crawler failed for '{variation}': {e}")
            return 0

    def _download_with_sequential_engines(self, keyword: str, variations: List[str],
                                          out_dir: str, max_num: int) -> None:
        """
        Download images using engines in sequence with fallbacks.
        
        Args:
            keyword: Search term
            variations: List of search variations
            out_dir: Output directory
            max_num: Maximum number of images to download
        """
        # Calculate per-variation limit
        per_variation_limit = max(3, max_num // len(variations))

        # Try each engine in sequence
        for engine_config in self.engines:
            if self.total_downloaded >= max_num:
                break

            # Process this engine
            engine_count = self._process_engine(
                engine_config=engine_config,
                variations=variations,
                out_dir=out_dir,
                max_num=max_num - self.total_downloaded,
                total_max=max_num
            )

            # Update total downloaded
            with self.lock:
                self.total_downloaded += engine_count

                # Update engine stats
                engine_name = engine_config['name']
                if engine_name not in self.engine_stats:
                    self.engine_stats[engine_name] = 0
                self.engine_stats[engine_name] += engine_count

    def _log_engine_stats(self) -> None:
        """Log statistics about downloads from each engine."""
        if not self.engine_stats:
            return

        logger.info("Download statistics by engine:")
        for engine, count in self.engine_stats.items():
            percentage = (count / self.total_downloaded * 100) if self.total_downloaded > 0 else 0
            logger.info(f"  {engine.capitalize()}: {count} images ({percentage:.1f}%)")

    @staticmethod
    def _get_crawler_class(engine_name: str) -> Any:
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

    @staticmethod
    def _get_search_variations() -> List[str]:
        """
        Get the list of search variations.

        Returns:
            List of search variations
        """
        return [
            "{keyword}",
            "{keyword} photo",
            "{keyword} image",
            "{keyword} picture",
            "{keyword} high resolution",
            "{keyword} high quality",
            "{keyword} high quality picture",
            "{keyword} high quality image",
            "{keyword} low quality",
            "{keyword} low quality picture",
            "{keyword} low quality image",
            "{keyword} meme",
            "{keyword} meme image",
            "{keyword} funny {keyword}",
            "{keyword} cute",
            "{keyword} cute picture",
            "{keyword} beautiful",
            "{keyword} beautiful image",
            "{keyword} realistic",
            "{keyword} realistic photo",
            "{keyword} cartoon",
            "{keyword} cartoon image",
            "{keyword} drawing",
            "{keyword} sketch",
            "{keyword} painting",
            "{keyword} artwork",
            "{keyword} digital art",
            "{keyword} 3d render",
            "{keyword} vintage",
            "{keyword} vintage photo",
            "{keyword} modern",
            "{keyword} modern image",
            "{keyword} professional",
            "{keyword} professional photo",
            "{keyword} amateur",
            "{keyword} amateur photo",
            "{keyword} close up",
            "{keyword} close up photo",
            "{keyword} wide shot",
            "{keyword} wide shot photo",
            "{keyword} macro",
            "{keyword} macro photo",
            "{keyword} blurry",
            "{keyword} blurry image",
            "{keyword} sharp",
            "{keyword} sharp image",
            "{keyword} colorful",
            "{keyword} black and white",
            "{keyword} grayscale",
            "{keyword} bright",
            "{keyword} dark",
            "{keyword} sunny",
            "{keyword} cloudy",
            "{keyword} indoor",
            "{keyword} outdoor",
            "{keyword} studio",
            "{keyword} natural light",
            "{keyword} artificial light"
        ]

    @staticmethod
    def _get_engines() -> List[Dict[str, Any]]:
        """
        Get the list of engines with their configurations.

        Returns:
            List of dictionaries containing engine configurations
        """
        return [
            {
                'name': 'google',
                'offset_range': (0, 20),
                'variation_step': 20
            },
            {
                'name': 'bing',
                'offset_range': (0, 30),
                'variation_step': 10
            },
            {
                'name': 'baidu',
                'offset_range': (10, 50),
                'variation_step': 15
            }
        ]

    def _process_engine(self, engine_config: dict, variations: List[str],
                        out_dir: str, max_num: int, total_max: int) -> int:
        """
        Process a search engine to download images (sequential version).
        
        Args:
            engine_config: Engine configuration
            variations: List of search variations
            out_dir: Output directory
            max_num: Maximum images for this engine
            total_max: Overall maximum images
            
        Returns:
            Number of images downloaded
        """
        if self.stop_workers:
            return 0

        engine_name = engine_config['name']
        offset_min, offset_max = engine_config['offset_range']
        random_offset = random.randint(offset_min, offset_max)
        variation_step = engine_config['variation_step']

        logger.info(f"Attempting download using {engine_name.capitalize()}ImageCrawler")

        # Calculate per-variation limit based on variations and max for this engine
        per_variation_limit = max(2, max_num // len(variations))

        engine_downloaded = 0
        try:
            for i, variation in enumerate(variations):
                # Check if we should stop
                if self.stop_workers or self.total_downloaded >= total_max:
                    break

                # Calculate remaining images needed
                with self.lock:
                    if self.total_downloaded >= total_max:
                        break
                    remaining = min(max_num - engine_downloaded, total_max - self.total_downloaded)

                if remaining <= 0:
                    break

                # Calculate limits and offset for this variation
                current_limit = min(remaining, per_variation_limit)
                current_offset = random_offset + (i * variation_step)

                logger.info(
                    f"{engine_name}: Trying to download {current_limit} images with query: '{variation}' (offset: {current_offset})"
                )

                try:
                    crawler = self._create_crawler(
                        self._get_crawler_class(engine_name),
                        out_dir
                    )

                    crawler.crawl(
                        keyword=variation,
                        max_num=current_limit,
                        min_size=self.min_image_size,
                        offset=current_offset,
                        file_idx_offset=self.total_downloaded + engine_downloaded
                    )

                    # Count valid images after this batch download
                    with self.lock:
                        temp_valid_count = count_valid_images_in_latest_batch(
                            out_dir,
                            self.total_downloaded + engine_downloaded
                        )
                        engine_downloaded += temp_valid_count

                    logger.info(
                        f"{engine_name} downloaded {temp_valid_count} valid images for '{variation}', "
                        f"total: {self.total_downloaded + engine_downloaded}/{total_max}"
                    )

                except Exception as e:
                    logger.warning(f"{engine_name} crawler failed for '{variation}': {e}")

                # Break early if we've reached the target
                if self.total_downloaded + engine_downloaded >= total_max:
                    break

                # Small delay between different search terms
                time.sleep(self.delay_between_searches)

        except Exception as e:
            logger.warning(f"{engine_name} engine failed: {e}")

        return engine_downloaded

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


def _generate_alternative_terms(keyword: str, retry_count: int) -> List[str]:
    """
    Generate alternative search terms for retry attempts.
    
    Args:
        keyword: Original search keyword
        retry_count: Current retry count
        
    Returns:
        List of alternative search terms
    """
    # Base variations
    variations = [
        f"{keyword} high resolution",
        f"{keyword} hd image",
        f"{keyword} photo",
        f"{keyword} picture",
        f"{keyword} clear image",
        f"{keyword} best quality",
        f"{keyword} professional",
        f"{keyword} detailed",
        f"{keyword} close-up",
        f"{keyword} high quality"
    ]

    # Add more specific variations for higher retry counts
    if retry_count > 5:
        variations.extend([
            f"{keyword} 4k",
            f"{keyword} ultra hd",
            f"{keyword} stock photo",
            f"{keyword} official image",
            f"{keyword} professional photo"
        ])

    # Shuffle the list to add randomness
    random.shuffle(variations)

    # Always include the original keyword at the beginning
    return [keyword] + variations


def _update_image_count(out_dir: str) -> int:
    """
    Update the count of images in a directory after removing duplicates.
    
    Args:
        out_dir: Directory containing images
        
    Returns:
        Updated count of unique images
    """
    # Get all image files
    image_files = [f for f in os.listdir(out_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    # If there are no images, return 0
    if not image_files:
        return 0

    # If there's only one image, no need to check for duplicates
    if len(image_files) == 1:
        return 1

    # Remove duplicates
    try:
        removed = remove_duplicate_images(out_dir)  # First key is the count
        if removed[0] > 0:
            logger.info(f"Removed {removed} duplicate images")
    except Exception as e:
        logger.warning(f"Error removing duplicates: {str(e)}")

    # Count remaining images
    remaining_images = [f for f in os.listdir(out_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    return len(remaining_images)


def retry_download_images(keyword: str, out_dir: str, max_num: int, max_retries: int = 5) -> Tuple[bool, int]:
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
    # First attempt with parallel downloading
    downloader = ImageDownloader(
        feeder_threads=2,
        parser_threads=2,
        downloader_threads=4,
        max_parallel_engines=3,
        max_parallel_variations=3,
        use_all_engines=True  # Use all engines in parallel for maximum speed
    )

    logger.info(f"Attempting to download {max_num} images for '{keyword}' using parallel processing")
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

        # For retries, use a different approach based on retry number
        if retries % 2 == 0:
            # Even retries: Use sequential mode with specific engines
            retry_engine = ENGINES[retries % len(ENGINES)]
            logger.info(f"Retry #{retries}: Using {retry_engine} sequentially with term '{retry_term}'")

            # Create a sequential downloader
            sequential_downloader = ImageDownloader(use_all_engines=False)
            retry_success, retry_count = sequential_downloader.download(retry_term, out_dir, images_needed)
        else:
            # Odd retries: Use DuckDuckGo directly
            logger.info(f"Retry #{retries}: Using DuckDuckGo directly with term '{retry_term}'")
            retry_success, retry_count = download_images_ddgs(retry_term, out_dir, images_needed)

        # Update count and calculate remaining needed
        if retry_success and retry_count > 0:
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
    """
    Extract keywords from the AI response.
    
    Args:
        response: Raw response text from the AI model
        category: Original category name
        
    Returns:
        List of extracted keywords
    """
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
    """
    Create and configure argument parser with organized argument groups.
    
    Args:
        parser: The argument parser to configure
        
    Returns:
        Configured argument parser
    """
    # Add base configuration arguments
    _add_config_arguments(parser)

    # Add dataset generation control arguments
    _add_dataset_control_arguments(parser)

    # Add keyword generation options
    _add_keyword_generation_arguments(parser)

    # Add logging options
    _add_logging_arguments(parser)

    return parser


def _add_config_arguments(parser: argparse.ArgumentParser) -> None:
    """Add configuration file related arguments."""
    parser.add_argument(
        "-c", "--config",
        default=DEFAULT_CONFIG_FILE,
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_FILE})"
    )
    parser.add_argument(
        "--cache",
        default=DEFAULT_CACHE_FILE,
        help=f"Cache file for progress tracking (default: {DEFAULT_CACHE_FILE})"
    )
    parser.add_argument(
        "--continue",
        dest="continue_last",
        action="store_true",
        help="Continue from last run using the progress cache"
    )


def _add_dataset_control_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments controlling dataset generation behavior."""
    parser.add_argument(
        "-m", "--max-images",
        type=int,
        default=10,
        help="Maximum number of images per keyword (default: 10)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Custom output directory (default: uses dataset_name from config)"
    )
    parser.add_argument(
        "--no-integrity",
        action="store_true",
        help="Skip image integrity checks (faster but may include corrupt images)"
    )
    parser.add_argument(
        "-r", "--max-retries",
        type=int,
        default=5,
        help="Maximum retry attempts for failed downloads (default: 5)"
    )
    parser.add_argument(
        "--no-labels",
        action="store_true",
        help="Disable automatic label file generation"
    )


def _add_keyword_generation_arguments(parser: argparse.ArgumentParser) -> None:
    """Add arguments related to keyword generation."""
    keyword_group = parser.add_argument_group('Keyword Generation')
    generation_mode = keyword_group.add_mutually_exclusive_group()
    generation_mode.add_argument(
        "--keywords-auto",
        action="store_const",
        const="auto",
        dest="keyword_mode",
        help="Generate keywords only if none provided (default)"
    )
    generation_mode.add_argument(
        "--keywords-enabled",
        action="store_const",
        const="enabled",
        dest="keyword_mode",
        help="Always generate additional keywords even when some are provided"
    )
    generation_mode.add_argument(
        "--keywords-disabled",
        action="store_const",
        const="disabled",
        dest="keyword_mode",
        help="Disable keyword generation completely"
    )
    parser.set_defaults(keyword_mode="auto")

    # AI model selection
    keyword_group.add_argument(
        "--ai-model",
        choices=["gpt4", "gpt4-mini"],
        default="gpt4-mini",
        help="AI model to use for keyword generation (default: gpt4-mini)"
    )


def _add_logging_arguments(parser: argparse.ArgumentParser) -> None:
    """Add logging configuration arguments."""
    log_group = parser.add_argument_group('Logging')
    log_group.add_argument(
        "--log-file",
        default=DEFAULT_LOG_FILE,
        help=f"Path to log file (default: {DEFAULT_LOG_FILE})"
    )
    # Remove the verbose option since we're not logging to console anymore
    # log_group.add_argument(
    #     "-v", "--verbose",
    #     action="store_true",
    #     help="Show detailed logs in console (not just warnings/errors)"
    # )


class DatasetGenerator:
    """Class responsible for generating image datasets based on configuration."""

    def __init__(self, config: DatasetGenerationConfig):
        """
        Initialize the dataset generator.
        
        Args:
            config: Dataset generation configuration
        """
        # Create a progress manager instance
        self.downloader_threads: Optional[threading.Thread] = None
        self.feeder_threads: Optional[threading.Thread] = None
        self.parser_threads: Optional[threading.Thread] = None
        self.progress = ProgressManager()
        self.progress.start_step("init")

        self.config = config
        self.dataset_config = self._load_and_validate_config()
        self.dataset_name = self.dataset_config['dataset_name']
        self.categories = self.dataset_config['categories']
        self.root_dir = self._setup_output_directory()
        self.tracker = DatasetTracker()
        self.progress_cache = self._initialize_progress_cache()
        self.report = self._initialize_report()
        self.label_generator = LabelGenerator() if self.config.generate_labels else None

        # Update initialization progress
        self.progress.update_step(1)
        self.progress.close()

    def generate(self) -> None:
        """Generate the dataset based on the provided configuration."""
        # Calculate total work items for progress tracking
        total_keywords = sum(len(keywords) for keywords in self.categories.values())

        # Start the download/generation step
        self.progress.start_step("download", total=total_keywords)

        # Process each category
        for category_name, keywords in self.categories.items():
            logger.info(f"Processing category: {category_name}")
            self.progress.start_subtask(f"Category: {category_name}", total=len(keywords))
            self._process_category(category_name, keywords)
            self.progress.close_subtask()

        # Close download progress
        self.progress.close()

        # Generate labels if enabled
        if self.config.generate_labels and self.label_generator:
            logger.info("Generating labels for the dataset")
            self.label_generator.generate_dataset_labels(str(self.root_dir))

        # Start the report generation step
        self.progress.start_step("report")
        logger.info("Generating dataset report")
        self.report.generate()
        self.progress.update_step(1)
        self.progress.close()

        # Start the finalizing step
        self.progress.start_step("finalizing")

        # Print comprehensive summary (to log file only)
        self.tracker.print_summary()

        logger.info(f"Dataset generation completed. Output directory: {self.root_dir}")
        self.progress.update_step(1)
        self.progress.close()

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

    def _initialize_report(self) -> ReportGenerator:
        """Initialize the report generator with dataset information."""
        report = ReportGenerator(str(self.root_dir))
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
        for keyword in keywords_to_process:
            self._process_keyword(category_name, keyword, category_path)
            # Update main progress
            self.progress.update_step(1)
            # Update subtask description to show completion
            self.progress.set_subtask_description(
                f"Category: {category_name} ({keywords_to_process.index(keyword) + 1}/{len(keywords_to_process)})")

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

    def _process_keyword(self, category_name: str, keyword: str, category_path: Path) -> None:
        """Process a single keyword, downloading images and checking integrity."""
        # Update subtask postfix to show current keyword
        self.progress.set_subtask_postfix(keyword=keyword)

        # Skip if already processed and continuing from last run
        if self.config.continue_from_last and self.progress_cache and self.progress_cache.is_completed(
                category_name, keyword):
            logger.info(f"Skipping already processed: {category_name}/{keyword}")
            return

        # Create keyword directory
        keyword_safe = keyword.replace('/', '_').replace('\\', '_')
        keyword_path = category_path / keyword_safe
        keyword_path.mkdir(parents=True, exist_ok=True)

        # Download images
        download_context = f"{category_name}/{keyword}"

        # Start integrity checking mini-progress
        self.progress.set_subtask_description(f"Downloading: {keyword}")

        success, count = retry_download_images(
            keyword=keyword,
            out_dir=str(keyword_path),
            max_num=self.config.max_images,
            max_retries=self.config.max_retries
        )

        # Track results and record in report
        self._track_download_results(download_context, success, count, category_name, keyword)

        # Check and record duplicates
        self.progress.set_subtask_description(f"Checking duplicates: {keyword}")
        check_duplicates(category_name, keyword, str(keyword_path), self.report)

        # Check integrity if enabled
        if self.config.integrity:
            self.progress.set_subtask_description(f"Checking integrity: {keyword}")
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

        # # Record in report
        # self.report.record_download(
        #     category=category_name,
        #     keyword=keyword,
        #     success=success,
        #     count=count,
        #     attempted=self.config.max_images,
        #     errors=[]
        # )

    def _check_image_integrity(self, download_context: str, keyword_path: str, category_name: str,
                               keyword: str) -> None:
        """Check image integrity and record results."""
        self.progress.set_subtask_description(f"Checking image integrity: {keyword}")

        valid_count, total_count, corrupted_files = count_valid_images(keyword_path)

        if valid_count < total_count:
            self.tracker.record_integrity_failure(
                download_context,
                total_count,
                valid_count,
                corrupted_files
            )
            self.progress.set_subtask_postfix(valid=valid_count, corrupted=total_count - valid_count)
        else:
            self.progress.set_subtask_postfix(valid=valid_count, corrupted=0)

        self.report.record_integrity(
            category=category_name,
            keyword=keyword,
            expected=total_count,
            actual=valid_count,
            corrupted=corrupted_files
        )

    def _log_engine_stats(self) -> None:
        """Log statistics about downloads from each engine."""
        if not self.engine_stats:
            return

        logger.info("Download statistics by engine:")
        for engine, count in self.engine_stats.items():
            percentage = (count / self.total_downloaded * 100) if self.total_downloaded > 0 else 0
            logger.info(f"  {engine.capitalize()}: {count} images ({percentage:.1f}%)")

    @staticmethod
    def _get_crawler_class(engine_name: str) -> Any:
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

    @staticmethod
    def _get_search_variations() -> List[str]:
        """
        Get the list of search variations.

        Returns:
            List of search variations
        """
        return [
            "{keyword}",
            "{keyword} photo",
            "{keyword} image",
            "{keyword} picture",
            "{keyword} high resolution",
            "{keyword} high quality",
            "{keyword} high quality picture",
            "{keyword} high quality image",
            "{keyword} low quality",
            "{keyword} low quality picture",
            "{keyword} low quality image",
            "{keyword} meme",
            "{keyword} meme image",
            "{keyword} funny {keyword}",
            "{keyword} cute",
            "{keyword} cute picture",
            "{keyword} beautiful",
            "{keyword} beautiful image",
            "{keyword} realistic",
            "{keyword} realistic photo",
            "{keyword} cartoon",
            "{keyword} cartoon image",
            "{keyword} drawing",
            "{keyword} sketch",
            "{keyword} painting",
            "{keyword} artwork",
            "{keyword} digital art",
            "{keyword} 3d render",
            "{keyword} vintage",
            "{keyword} vintage photo",
            "{keyword} modern",
            "{keyword} modern image",
            "{keyword} professional",
            "{keyword} professional photo",
            "{keyword} amateur",
            "{keyword} amateur photo",
            "{keyword} close up",
            "{keyword} close up photo",
            "{keyword} wide shot",
            "{keyword} wide shot photo",
            "{keyword} macro",
            "{keyword} macro photo",
            "{keyword} blurry",
            "{keyword} blurry image",
            "{keyword} sharp",
            "{keyword} sharp image",
            "{keyword} colorful",
            "{keyword} black and white",
            "{keyword} grayscale",
            "{keyword} bright",
            "{keyword} dark",
            "{keyword} sunny",
            "{keyword} cloudy",
            "{keyword} indoor",
            "{keyword} outdoor",
            "{keyword} studio",
            "{keyword} natural light",
            "{keyword} artificial light"
        ]

    @staticmethod
    def _get_engines() -> List[Dict[str, Any]]:
        """
        Get the list of engines with their configurations.

        Returns:
            List of dictionaries containing engine configurations
        """
        return [
            {
                'name': 'google',
                'offset_range': (0, 20),
                'variation_step': 20
            },
            {
                'name': 'bing',
                'offset_range': (0, 30),
                'variation_step': 10
            },
            {
                'name': 'baidu',
                'offset_range': (10, 50),
                'variation_step': 15
            }
        ]

    def _process_engine(self, engine_config: dict, variations: List[str],
                        out_dir: str, max_num: int, total_max: int) -> int:
        """
        Process a search engine to download images (sequential version).
        
        Args:
            engine_config: Engine configuration
            variations: List of search variations
            out_dir: Output directory
            max_num: Maximum images for this engine
            total_max: Overall maximum images
            
        Returns:
            Number of images downloaded
        """
        if self.stop_workers:
            return 0

        engine_name = engine_config['name']
        offset_min, offset_max = engine_config['offset_range']
        random_offset = random.randint(offset_min, offset_max)
        variation_step = engine_config['variation_step']

        logger.info(f"Attempting download using {engine_name.capitalize()}ImageCrawler")

        # Calculate per-variation limit based on variations and max for this engine
        per_variation_limit = max(2, max_num // len(variations))

        engine_downloaded = 0
        try:
            for i, variation in enumerate(variations):
                # Check if we should stop
                if self.stop_workers or self.total_downloaded >= total_max:
                    break

                # Calculate remaining images needed
                with self.lock:
                    if self.total_downloaded >= total_max:
                        break
                    remaining = min(max_num - engine_downloaded, total_max - self.total_downloaded)

                if remaining <= 0:
                    break

                # Calculate limits and offset for this variation
                current_limit = min(remaining, per_variation_limit)
                current_offset = random_offset + (i * variation_step)

                logger.info(
                    f"{engine_name}: Trying to download {current_limit} images with query: '{variation}' (offset: {current_offset})"
                )

                try:
                    crawler = self._create_crawler(
                        self._get_crawler_class(engine_name),
                        out_dir
                    )

                    crawler.crawl(
                        keyword=variation,
                        max_num=current_limit,
                        min_size=self.min_image_size,
                        offset=current_offset,
                        file_idx_offset=self.total_downloaded + engine_downloaded
                    )

                    # Count valid images after this batch download
                    with self.lock:
                        temp_valid_count = count_valid_images_in_latest_batch(
                            out_dir,
                            self.total_downloaded + engine_downloaded
                        )
                        engine_downloaded += temp_valid_count

                    logger.info(
                        f"{engine_name} downloaded {temp_valid_count} valid images for '{variation}', "
                        f"total: {self.total_downloaded + engine_downloaded}/{total_max}"
                    )

                except Exception as e:
                    logger.warning(f"{engine_name} crawler failed for '{variation}': {e}")

                # Break early if we've reached the target
                if self.total_downloaded + engine_downloaded >= total_max:
                    break

                # Small delay between different search terms
                time.sleep(self.delay_between_searches)

        except Exception as e:
            logger.warning(f"{engine_name} engine failed: {e}")

        return engine_downloaded

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


def generate_dataset(config: DatasetGenerationConfig) -> None:
    """
    Generate image dataset based on configuration file.
    
    Args:
        config: Dataset generation configuration
    """
    generator = DatasetGenerator(config)
    generator.generate()


def check_duplicates(category_name: str, keyword: str, keyword_path: str, report: ReportGenerator) -> None:
    """Check for and record duplicates in the report."""
    try:
        # Get all image files
        image_files = [
            f for f in Path(keyword_path).iterdir()
            if f.is_file() and is_valid_image_extension(f)
        ]
        total_images = len(image_files)

        logger.info(f"Checking for duplicates in {len(image_files)} images for {category_name}/{keyword}")

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

        logger.info(f"Found and removed {duplicates_count} duplicates out of {total_images} images")

    except Exception as e:
        logger.warning(f"Failed to check duplicates for {category_name}/{keyword}: {e}")
        report.record_error(f"{category_name}/{keyword} duplicates check", str(e))


def check_image_integrity(
        tracker: DatasetTracker,
        download_context: str,
        keyword_path: str,
        max_images: int,
        report: ReportGenerator,
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


def update_logfile(log_file: str) -> None:
    """Update the log file if it's different from the default."""
    if log_file != DEFAULT_LOG_FILE:
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                logger.removeHandler(handler)

        new_file_handler = logging.FileHandler(log_file, encoding='utf-8')
        new_file_handler.setLevel(logging.INFO)
        new_file_handler.setFormatter(file_formatter)
        logger.addHandler(new_file_handler)


def parse_args_safely(parser: argparse.ArgumentParser) -> Optional[argparse.Namespace]:
    """
    Parse command line arguments safely, compatible with Jupyter environments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    # Add help argument manually
    parser.add_argument('-h', '--help', action='store_true', help='Show this help message and exit')

    # First handle the case where we're in a notebook
    if is_running_in_notebook():
        # In Jupyter/Colab, only use sys.argv[0] (script name) and ignore other arguments
        # that might be automatically passed by the notebook environment
        args, unknown = parser.parse_known_args([])

        # If they want help, print it specially formatted
        if args.help:
            print_help_colored(parser)
            return None

        return args

    # In normal terminal environment, parse as usual
    args, unknown = parser.parse_known_args()

    # If they want help, print it specially formatted and exit
    if args.help:
        print_help_colored(parser)
        return None

    # Warning about unknown arguments
    if unknown:
        print(f"{Colors.YELLOW}Warning: Unknown arguments: {unknown}{Colors.ENDC}")

    return args


def run_from_jupyter(config_path: str = DEFAULT_CONFIG_FILE,
                     max_images: int = 10,
                     output_dir: Optional[str] = None,
                     no_integrity: bool = False,
                     max_retries: int = 5,
                     continue_last: bool = False,
                     cache_file: str = DEFAULT_CACHE_FILE,
                     keyword_mode: KEYWORD_MODE = "auto",
                     ai_model: AI_MODELS = "gpt4-mini",
                     no_labels: bool = False) -> None:
    """
    Run PixCrawler directly from a Jupyter notebook or Google Colab.
    
    This function provides an easy way to use PixCrawler in notebook environments
    without dealing with command-line arguments.
    
    Args:
        config_path: Path to configuration file (default: config.json)
        max_images: Maximum images per keyword (default: 10)
        output_dir: Custom output directory (default: derived from config)
        no_integrity: Skip image integrity checks (default: False)
        max_retries: Maximum retry attempts (default: 5)
        continue_last: Continue from last run (default: False)
        cache_file: Path to cache file (default: download_progress.json)
        keyword_mode: Keyword generation mode (auto, enabled, disabled) (default: auto)
        ai_model: AI model for keyword generation (gpt4, gpt4-mini) (default: gpt4-mini)
        no_labels: Disable automatic label generation (default: False)
    """
    # Print ASCII art banner
    print(f"{Colors.CYAN}{PIXCRAWLER_ASCII}{Colors.ENDC}")
    print(f"{Colors.GREEN}PixCrawler: Image Dataset Generator{Colors.ENDC}")
    print(f"{Colors.YELLOW}Running in Jupyter/Colab mode{Colors.ENDC}\n")

    # Create configuration
    config = DatasetGenerationConfig(
        config_path=config_path,
        max_images=max_images,
        output_dir=output_dir,
        integrity=not no_integrity,
        max_retries=max_retries,
        continue_from_last=continue_last,
        cache_file=cache_file,
        keyword_generation=keyword_mode,
        ai_model=ai_model,
        generate_labels=not no_labels
    )

    # Show configuration
    print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
    print(f"  - Config file: {config_path}")
    print(f"  - Max images per keyword: {max_images}")
    print(f"  - Output directory: {output_dir or 'Auto (from config)'}")
    print(f"  - Image integrity checks: {not no_integrity}")
    print(f"  - Max retries: {max_retries}")
    print(f"  - Continue from last run: {continue_last}")
    print(f"  - Cache file: {cache_file}")
    print(f"  - Keyword generation mode: {keyword_mode}")
    print(f"  - AI model: {ai_model}")
    print(f"  - Generate labels: {not no_labels}\n")

    # Generate the dataset
    print(f"{Colors.BOLD}Starting dataset generation...{Colors.ENDC}")
    generate_dataset(config)

    # Print final message to indicate completion
    output_dir = config.output_dir or "dataset"
    print(f"\n{Colors.GREEN}✅ Dataset generation complete!{Colors.ENDC}")
    print(f"   - {Colors.BOLD}Output directory:{Colors.ENDC} {output_dir}")
    print(f"   - {Colors.BOLD}See the REPORT.md file in the output directory for detailed statistics{Colors.ENDC}")


def main():
    """Main function to parse arguments and generate dataset"""
    # Print ASCII art banner
    print(f"{Colors.CYAN}{PIXCRAWLER_ASCII}{Colors.ENDC}")

    # Create the argument parser
    parser = argparse.ArgumentParser(description="PixCrawler: Image Dataset Generator", add_help=False)
    parser = create_arg_parser(parser)

    # Parse arguments safely (works in both scripts and notebooks)
    args = parse_args_safely(parser)

    # If help was requested, we've already printed it
    if args is None:
        if not is_running_in_notebook():
            sys.exit(0)
        return

    # Update log file if specified
    update_logfile(args.log_file)

    config = DatasetGenerationConfig(
        config_path=args.config,
        max_images=args.max_images,
        output_dir=args.output,
        integrity=not args.no_integrity,
        max_retries=args.max_retries,
        continue_from_last=args.continue_last,
        cache_file=args.cache,
        keyword_generation=args.keyword_mode,
        ai_model=args.ai_model,
        generate_labels=not args.no_labels
    )

    # Generate the dataset
    generate_dataset(config)

    # Print final message to indicate completion
    output_dir = config.output_dir or config.dataset_name
    print(f"\n{Colors.GREEN}✅ Dataset generation complete!{Colors.ENDC}")
    print(f"   - {Colors.BOLD}Output directory:{Colors.ENDC} {output_dir}")
    print(f"   - {Colors.BOLD}Log file:{Colors.ENDC} {args.log_file}")
    print(f"   - {Colors.BOLD}See the REPORT.md file in the output directory for detailed statistics{Colors.ENDC}")


if __name__ == "__main__":
    main()


def is_valid_image(file_path: str) -> bool:
    """
    Check if a file is a valid image.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        True if the file is a valid image, False otherwise
    """
    try:
        # Check if file exists and is not empty
        if not os.path.isfile(file_path) or os.path.getsize(file_path) == 0:
            return False

        # Try to open and verify the image
        with Image.open(file_path) as img:
            img.verify()  # Verify that it's an image
            return True
    except Exception:
        return False
