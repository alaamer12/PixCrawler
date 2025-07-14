"""Module for generating image datasets.

This module orchestrates the entire process of generating image datasets, including:
- Loading configurations
- Generating keywords (with AI assistance)
- Downloading images from various search engines
- Performing integrity checks on downloaded images
- Generating comprehensive reports
- Creating label files for machine learning tasks

Classes:
    LabelGenerator: Generates label files for images in various formats (TXT, JSON, CSV, YAML).
    DatasetGenerator: Manages the end-to-end dataset generation process.

Functions:
    retry_download_images: Attempts to download images with retries and alternative terms.
    load_config: Loads and validates dataset configuration from a JSON file.
    generate_keywords: Generates search keywords using an AI model.
    check_duplicates: Checks for and removes duplicate images.
    check_image_integrity: Verifies the integrity of downloaded images.
    update_logfile: Updates the logging configuration to a specified file.
    generate_dataset: Main entry point to start the dataset generation process.

Features:
- Multi-engine image downloading (Google, Bing, Baidu, DuckDuckGo)
- AI-powered keyword generation for diverse image collection
- Duplicate image detection and removal
- Image integrity checking
- Progress tracking and caching for resuming interrupted runs
- Automatic label file generation in multiple formats (TXT, JSON, CSV, YAML)
- Comprehensive report generation for dataset overview
"""

import contextlib
import json
import logging
import os
import random
import sys
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union, Type

import g4f
import jsonschema
from PIL import Image
from icrawler import Crawler
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler
from jsonschema import validate

from config import DatasetGenerationConfig, CONFIG_SCHEMA, get_search_variations
from constants import DEFAULT_CACHE_FILE, DEFAULT_LOG_FILE, ENGINES, \
    file_formatter
from constants import logger
from downloader import ImageDownloader, download_images_ddgs
from helpers import ReportGenerator, DatasetTracker, ProgressManager, progress, is_valid_image_extension
from utilities import ProgressCache, detect_duplicate_images, \
    count_valid_images, remove_duplicate_images, rename_images_sequentially

__all__ = [
    '_apply_config_options',
    '_download_with_engine',
    '_generate_alternative_terms',
    '_update_image_count',
    'retry_download_images',
    'load_config',
    'generate_keywords',
    '_extract_keywords_from_response',
    'check_duplicates',
    'check_image_integrity',
    'update_logfile',
    'LabelGenerator',
    'DatasetGenerator',
    'generate_dataset'
]


def _apply_config_options(config: DatasetGenerationConfig, options: Dict[str, Any]) -> None:
    """
    Applies configuration options from a loaded config file to the DatasetGenerationConfig object.
    This function selectively overrides default configuration values with values from the config file,
    but only when CLI arguments haven't explicitly set them.

    Args:
        config (DatasetGenerationConfig): The configuration object to modify.
        options (Dict[str, Any]): A dictionary containing configuration options from the config file.
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


def _download_with_engine(engine_name: str, keyword: str, out_dir: str, max_num: int,
                          offset: int = 0, file_idx_offset: int = 0) -> bool:
    """
    Downloads images using a specific search engine.

    Args:
        engine_name (str): Name of the search engine to use ("google", "bing", "baidu", "ddgs").
        keyword (str): Search term for images.
        out_dir (str): Output directory path.
        max_num (int): Maximum number of images to download.
        offset (int): Search offset to avoid duplicate results (default is 0).
        file_idx_offset (int): Starting index for file naming (default is 0).

    Returns:
        bool: True if download was successful, False otherwise.
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
    Generates alternative search terms for retry attempts based on the original keyword and retry count.
    This helps in finding more diverse images if initial attempts are not successful.

    Args:
        keyword (str): The original search keyword.
        retry_count (int): The current retry count, which influences the diversity of generated terms.

    Returns:
        List[str]: A list of alternative search terms, with the original keyword included at the beginning.
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
    Updates the count of images in a directory after removing duplicates.

    Args:
        out_dir (str): The directory containing images.

    Returns:
        int: The updated count of unique images remaining in the directory.
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
    Attempts to download images for a given keyword, retrying with alternative search terms and engines
    until the desired image count is reached or the maximum number of retries is exceeded.

    Args:
        keyword (str): The primary search term for images.
        out_dir (str): The output directory path where images will be downloaded.
        max_num (int): The maximum number of images to download.
        max_retries (int): The maximum number of retry attempts (default is 5).

    Returns:
        Tuple[bool, int]: A tuple where the first element is True if at least one image was downloaded,
                         and the second element is the total count of unique images downloaded.
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
    Loads dataset configuration from a JSON file and validates it against a predefined schema.

    Args:
        config_path (str): The absolute path to the configuration file.

    Returns:
        Dict[str, Any]: A dictionary containing the validated dataset configuration.

    Raises:
        ValueError: If the configuration file is invalid or missing required fields.
        jsonschema.exceptions.ValidationError: If the configuration does not conform to the schema.
        Exception: For other file loading or parsing errors.
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
    Generates related keywords for a given category using the G4F (GPT-4) API.
    This function attempts to generate diverse and high-quality search terms.

    Args:
        category (str): The category name for which to generate keywords.
        ai_model (str): The AI model to use for keyword generation (e.g., "gpt4", "gpt4-mini").

    Returns:
        List[str]: A list of generated keywords related to the category.

    Raises:
        SystemExit: If keyword generation fails after retries, the system will exit.
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
    Extracts a list of keywords from the raw AI model response string.
    It attempts to parse a Python list structure first, then falls back to line-by-line extraction.

    Args:
        response (str): The raw response text received from the AI model.
        category (str): The original category name, which is always included in the returned list.

    Returns:
        List[str]: A cleaned and deduplicated list of extracted keywords.
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


def check_duplicates(category_name: str, keyword: str, keyword_path: str, report: ReportGenerator) -> None:
    """
    Checks for and records duplicate images within a specified keyword directory.
    Duplicate images are removed, and the process is logged in the report.

    Args:
        category_name (str): The name of the category the keyword belongs to.
        keyword (str): The specific keyword being processed.
        keyword_path (str): The absolute path to the directory containing images for the keyword.
        report (ReportGenerator): An instance of the ReportGenerator to record findings.
    """
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
    """
    Checks the integrity of downloaded images within a specified keyword directory.
    It counts valid and corrupted images and records the results in the dataset tracker and report.

    Args:
        tracker (DatasetTracker): An instance of the DatasetTracker to record integrity failures.
        download_context (str): A string describing the context of the download (e.g., "category/keyword").
        keyword_path (str): The absolute path to the directory containing images for the keyword.
        max_images (int): The maximum number of images expected for this keyword.
        report (ReportGenerator): An instance of the ReportGenerator to record integrity results.
        category_name (str): The name of the category the keyword belongs to.
        keyword (str): The specific keyword being processed.
    """
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
    """
    Updates the logging configuration to direct output to a specified log file.
    If the provided log file path is different from the default, the existing file handler
    is removed and a new one is added.

    Args:
        log_file (str): The absolute path to the desired log file.
    """
    if log_file != DEFAULT_LOG_FILE:
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                logger.removeHandler(handler)

        new_file_handler = logging.FileHandler(log_file, encoding='utf-8')
        new_file_handler.setLevel(logging.INFO)
        new_file_handler.setFormatter(file_formatter)
        logger.addHandler(new_file_handler)


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
        Initializes the LabelGenerator with a specified output format for label files.

        Args:
            format_type (str): The desired format for label files ('txt', 'json', 'csv', 'yaml').
                                If an unsupported format is provided, it defaults to 'txt'.
        """
        self.format_type = format_type.lower()
        self.supported_formats = {"txt", "json", "csv", "yaml"}

        if self.format_type not in self.supported_formats:
            logger.warning(f"Unsupported label format: {format_type}. Defaulting to 'txt'.")
            self.format_type = "txt"

    def generate_dataset_labels(self, dataset_dir: str) -> None:
        """
        Generates label files for all images within the specified dataset directory.
        It organizes labels by category and keyword, and creates metadata files for the dataset.

        Args:
            dataset_dir (str): The root directory of the dataset.
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
        Generates an overall metadata file for the dataset.

        Args:
            dataset_path (Path): The root path of the dataset.
            labels_dir (Path): The directory where label files are stored.
            category_count (int): The number of categories in the dataset.
            image_count (int): The total number of images in the dataset.
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
        Generates a category index file that maps category names to numeric IDs.

        Args:
            labels_dir (Path): The directory where label files are stored.
            categories (List[str]): A list of category names in the dataset.
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
        Processes a single category directory, iterating through its keyword subdirectories
        to generate labels for images within them.

        Args:
            category_dir (Path): The directory containing the category's images and keywords.
            category_name (str): The name of the category.
            labels_dir (Path): The base directory where all label files are stored.
            progress (ProgressManager): An instance of the ProgressManager for updating progress bars.
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
        Processes a keyword directory, generating label files for each image within it.

        Args:
            keyword_dir (Path): The directory containing images for the keyword.
            category_name (str): The name of the category.
            keyword_name (str): The name of the keyword.
            category_label_dir (Path): The directory to store label files for this category.
            progress (ProgressManager): An instance of the ProgressManager for updating progress bars.
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
        Generates a label file for a single image based on the configured format.
        It extracts image metadata and writes the label content to the specified directory.

        Args:
            image_file (Path): The path to the image file for which to generate a label.
            label_dir (Path): The directory where the label file will be stored.
            category (str): The category name associated with the image.
            keyword (str): The keyword name associated with the image.
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
        Extracts metadata (e.g., dimensions, size, format) from an image file.

        Args:
            image_path (Path): The path to the image file.

        Returns:
            Dict[str, Any]: A dictionary containing extracted image metadata.
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
        Writes a label file in plain text (TXT) format.

        Args:
            label_path (Path): The path to write the label file.
            category (str): The category name.
            keyword (str): The keyword name.
            image_path (Path): The path to the corresponding image.
            metadata (Dict[str, Any]): A dictionary containing image metadata.

        Raises:
            Exception: If there is an error writing the file.
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
        Writes a label file in JSON format.

        Args:
            label_path (Path): The path to write the label file.
            category (str): The category name.
            keyword (str): The keyword name.
            image_path (Path): The path to the corresponding image.
            metadata (Dict[str, Any]): A dictionary containing image metadata.

        Raises:
            Exception: If there is an error writing the file.
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
        Writes a label file in CSV format.

        Args:
            label_path (Path): The path to write the label file.
            category (str): The category name.
            keyword (str): The keyword name.
            image_path (Path): The path to the corresponding image.
            metadata (Dict[str, Any]): A dictionary containing image metadata.

        Raises:
            Exception: If there is an error writing the file.
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
        Writes a label file in YAML format.

        Args:
            label_path (Path): The path to write the label file.
            category (str): The category name.
            keyword (str): The keyword name.
            image_path (Path): The path to the corresponding image.
            metadata (Dict[str, Any]): A dictionary containing image metadata.

        Raises:
            Exception: If there is an error writing the file (other than ImportError for PyYAML).
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


class DatasetGenerator:
    """
    Class responsible for generating image datasets based on a provided configuration.
    It orchestrates the entire process, including setting up directories, managing
    progress, downloading images, checking integrity, and generating reports and labels.
    """

    def __init__(self, config: DatasetGenerationConfig):
        """
        Initializes the DatasetGenerator.

        Args:
            config (DatasetGenerationConfig): The configuration object for dataset generation.
        """
        # Create a progress manager instance
        self.downloader_threads: Optional[threading.Thread] = None
        self.feeder_threads: Optional[threading.Thread] = None
        self.parser_threads: Optional[threading.Thread] = None
        self.progress = ProgressManager()
        self.progress.start_step("init")

        self.config = config
        self.dataset_config = self._load_and_validate_config()

        # Set dataset_name from the loaded config
        self.config.dataset_name = self.dataset_config['dataset_name']
        self.dataset_name = self.config.dataset_name

        self.categories = self.dataset_config['categories']
        self.root_dir = self._setup_output_directory()
        self.tracker = DatasetTracker()
        self.progress_cache = self._initialize_progress_cache()
        self.report = self._initialize_report()
        self.label_generator = LabelGenerator() if self.config.generate_labels else None

        # Add missing attributes that are referenced in methods but not initialized
        self.engine_stats = {}
        self.total_downloaded = 0
        self.stop_workers = False
        self.log_level = logging.WARNING
        self.lock = threading.RLock()
        self.min_image_size = (100, 100)
        self.delay_between_searches = 0.5

        # Initialize search_variations
        self.config.search_variations = get_search_variations()
        self.search_variations = self.config.search_variations

        # Update initialization progress
        self.progress.update_step(1)
        self.progress.close()

    def generate(self) -> None:
        """
        Generates the dataset based on the provided configuration.
        This is the main entry point for the dataset generation process,
        orchestrating keyword processing, image downloading, integrity checks,
        label generation, and report creation.
        """
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
        """
        Sets up and creates the root output directory for the dataset.

        Returns:
            Path: The Path object representing the created root directory.
        """
        root_dir = self.config.output_dir or self.dataset_name
        root_path = Path(root_dir)
        root_path.mkdir(parents=True, exist_ok=True)
        return root_path

    def _initialize_progress_cache(self) -> Optional[ProgressCache]:
        """
        Initializes the progress cache if the `continue_from_last` option is enabled.
        This allows the generator to resume from a previous incomplete run.

        Returns:
            Optional[ProgressCache]: An instance of ProgressCache if enabled, otherwise None.
        """
        if not self.config.continue_from_last:
            return None

        progress_cache = ProgressCache(self.config.cache_file)
        stats = progress_cache.get_completion_stats()
        logger.info(
            f"Continuing from previous run. Already completed: {stats['total_completed']} items across {stats['categories']} categories.")
        return progress_cache

    def _initialize_report(self) -> ReportGenerator:
        """
        Initializes the ReportGenerator and populates it with initial dataset information.

        Returns:
            ReportGenerator: An instance of the ReportGenerator.
        """
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
        """
        Loads and validates the dataset configuration from the specified config file.
        It also applies configuration options from the file, giving precedence to CLI arguments.

        Returns:
            Dict[str, Any]: The loaded and validated dataset configuration.
        """
        dataset_config = load_config(self.config.config_path)

        # Extract options from config if available, with CLI arguments taking precedence
        if 'options' in dataset_config and isinstance(dataset_config['options'], dict):
            options = dataset_config['options']
            # Apply config file options if CLI arguments weren't explicitly provided
            _apply_config_options(self.config, options)

        return dataset_config

    def _process_category(self, category_name: str, keywords: List[str]) -> None:
        """
        Processes a single category, creating its directory and handling its keywords.

        Args:
            category_name (str): The name of the category.
            keywords (List[str]): A list of keywords associated with this category.
        """
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
        """
        Prepares keywords for processing based on the configuration.
        This includes generating new keywords using an AI model if enabled and necessary.

        Args:
            category_name (str): The name of the category.
            keywords (List[str]): The initial list of keywords provided for the category.

        Returns:
            List[str]: The final list of keywords to be processed for the category.
        """
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
        """
        Processes a single keyword, including downloading images, checking for duplicates,
        and performing integrity checks.

        Args:
            category_name (str): The name of the category the keyword belongs to.
            keyword (str): The specific keyword to process.
            category_path (Path): The path to the category's directory.
        """
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
        """
        Tracks the results of image downloads, updating the dataset tracker and report.

        Args:
            download_context (str): A string describing the context of the download (e.g., "category/keyword").
            success (bool): True if the download was successful, False otherwise.
            count (int): The number of images downloaded.
            category_name (str): The name of the category.
            keyword (str): The keyword associated with the download.
        """
        if success:
            self.tracker.record_download_success(download_context)
            logger.info(f"Successfully downloaded {count} images for {download_context}")
        else:
            error_msg = "Failed to download any valid images after retries"
            self.tracker.record_download_failure(download_context, error_msg)
            self.report.record_error(f"{category_name}/{keyword} download", error_msg)

    def _check_image_integrity(self, download_context: str, keyword_path: str, category_name: str,
                               keyword: str) -> None:
        """
        Checks image integrity for a given keyword directory and records the results.

        Args:
            download_context (str): A string describing the context of the download.
            keyword_path (str): The path to the keyword's image directory.
            category_name (str): The name of the category.
            keyword (str): The keyword being processed.
        """
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
        """
        Logs statistics about image downloads from each engine.
        """
        if not self.engine_stats:
            return

        logger.info("Download statistics by engine:")
        for engine, count in self.engine_stats.items():
            percentage = (count / self.total_downloaded * 100) if self.total_downloaded > 0 else 0
            logger.info(f"  {engine.capitalize()}: {count} images ({percentage:.1f}%)")

    @staticmethod
    def _get_crawler_class(engine_name: str) -> Type[Crawler]:
        """
        Retrieves the appropriate iCrawler class based on the engine name.

        Args:
            engine_name (str): The name of the search engine.

        Returns:
            Type[Union[GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler, Any]]: The iCrawler class.
        """
        crawler_map = {
            "google": GoogleImageCrawler,
            "bing": BingImageCrawler,
            "baidu": BaiduImageCrawler
        }
        return crawler_map.get(engine_name)

    def _create_crawler(self, crawler_class: Type[Any], out_dir: str) -> Any:
        """
        Creates an instance of a crawler with the configured parameters.

        Args:
            crawler_class (Type[Any]): The class of the crawler to instantiate.
            out_dir (str): The output directory for the crawler.

        Returns:
            Any: A configured crawler instance.
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
