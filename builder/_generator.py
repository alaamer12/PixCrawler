"""Module for generating image datasets.

This module orchestrates the entire process of generating image datasets, including:
- Loading configurations
- Generating keywords (with AI assistance)
- Downloading images from various search engines
- Generating comprehensive reports
- Creating label files for machine learning tasks

Classes:
    LabelGenerator: Generates label files for images in various formats (TXT, JSON, CSV, YAML).
    DatasetGenerator: Manages the end-to-end dataset generation process.

Functions:
    retry_download_images: Attempts to download images with retries and alternative terms.
    load_config: Loads and validates dataset configuration from a JSON file.
    generate_keywords: Generates search keywords using an AI model.
    update_logfile: Updates the logging configuration to a specified file.
    generate_dataset: Main entry point to start the dataset generation process.

Features:
- Multi-engine image downloading (Google, Bing, Baidu, DuckDuckGo)
- AI-powered keyword generation for diverse image collection
- Progress tracking and caching for resuming interrupted runs
- Automatic label file generation in multiple formats (TXT, JSON, CSV, YAML)
- Comprehensive report generation for dataset overview

Note: Image integrity checking and duplicate detection have been moved to the validator package.
Note: Report generation has been moved to the src package.
"""

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Final, Iterator, Union

import jsonschema
from PIL import Image
from jsonschema import validate

from _keywords import KeywordManagement, keyword_stats, AlternativeKeyTermGenerator
from _predefined_variations import get_search_variations
from _search_engines import download_images_ddgs
from builder._config import DatasetGenerationConfig, CONFIG_SCHEMA
from builder._constants import DEFAULT_CACHE_FILE, ENGINES, \
    logger, IMAGE_EXTENSIONS
from builder._downloader import ImageDownloader
from builder._exceptions import ConfigurationError, DownloadError, \
    GenerationError
from builder._helpers import DatasetTracker, ProgressManager, progress, \
    valid_image_ext
from _helpers import rename_images_sequentially

__all__ = [
    'retry_download',
    'update_logfile',
    'LabelGenerator',
    'DatasetGenerator',
    'generate_dataset',
    'ConfigManager',
]

from progress import ProgressCache

BACKOFF_DELAY: Final[float] = 0.5


# Integrity management moved to backend package


def _apply_config_options(config: DatasetGenerationConfig,
                          options: Dict[str, Any]) -> None:
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
        'max_retries': (config.max_retries == 5, lambda: options.get('max_retries')),
        'cache_file': (
            config.cache_file == DEFAULT_CACHE_FILE, lambda: options.get('cache_file')),
        'keyword_generation': (
            config.keyword_generation == "auto",
            lambda: options.get('keyword_generation')),
        'ai_model': (config.ai_model == "gpt4-mini", lambda: options.get('ai_model')),
        'generate_labels': (
            config.generate_labels is True, lambda: options.get('generate_labels'))
    }

    # Apply each config option if its CLI argument is using the default value
    for option_name, (is_using_default, value_getter) in config_mappings.items():
        if is_using_default and option_name in options and value_getter() is not None:
            new_value = value_getter()
            setattr(config, option_name, new_value)
            logger.info(f"Applied {option_name}={new_value} from config file")
        elif not is_using_default:
            logger.debug(f"CLI argument overriding config file for {option_name}")


# Global variable
generator = AlternativeKeyTermGenerator()


class RetryStrategy(Enum):
    """Enumeration of available retry strategies"""
    ALTERNATING = "alternating"
    ENGINE_ONLY = "engine_only"
    DDGS_ONLY = "ddgs_only"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 5
    backoff_delay: float = 2.0
    strategy: RetryStrategy = RetryStrategy.ALTERNATING
    feeder_threads: int = 2
    parser_threads: int = 2
    downloader_threads: int = 4


@dataclass
class RetryStats:
    """Statistics tracking for retry operations"""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    duplicates_removed: int = 0
    images_renamed: int = 0
    retry_history: List[Dict[str, Any]] = field(default_factory=list)


class Retry:
    """
    Enhanced retry mechanism for image downloads with configurable strategies
    and comprehensive tracking.
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize the Retry class.

        Args:
            config: Optional RetryConfig object for customizing retry behavior
        """
        self.config = config or RetryConfig()
        self.stats = RetryStats()
        self._image_extensions = tuple(IMAGE_EXTENSIONS)

    def _get_image_files(self, directory: str) -> List[str]:
        """Get all image files in a directory"""
        try:
            return [f for f in os.listdir(directory)
                    if f.lower().endswith(self._image_extensions)]
        except OSError as e:
            logger.warning(f"Error accessing directory {directory}: {e}")
            return []

    def _update_image_count(self, out_dir: str) -> int:
        """
        Updates the count of images in a directory after removing duplicates.

        Args:
            out_dir (str): The directory containing images.

        Returns:
            int: The updated count of unique images remaining in the directory.
        """
        image_files = self._get_image_files(out_dir)

        if not image_files:
            return 0

        if len(image_files) == 1:
            return 1

        # Duplicate removal moved to validator package
        # Basic duplicate removal can be done post-processing if needed

        # Count remaining images
        remaining_images = self._get_image_files(out_dir)
        return len(remaining_images)

    def _initial_download(self, max_num: int, keyword: str, out_dir: str) -> int:
        """Perform the initial download attempt"""
        logger.info(
            f"Attempting to download {max_num} images for '{keyword}' using sequential processing")

        downloader = ImageDownloader(
            feeder_threads=self.config.feeder_threads,
            parser_threads=self.config.parser_threads,
            downloader_threads=self.config.downloader_threads
        )

        success, count = downloader.download(keyword, out_dir, max_num)
        self.stats.total_attempts += 1

        if success:
            self.stats.successful_attempts += 1
            return self._update_image_count(out_dir) if count > 1 else count
        else:
            self.stats.failed_attempts += 1
            return count

    def _attempt_retry(self, retries: int, keyword: str, out_dir: str,
                       images_needed: int) -> int:
        """Perform a single retry attempt"""
        if self.config.backoff_delay > 0:
            time.sleep(self.config.backoff_delay)

        # Get the next intelligent term combination
        retry_term = generator.next_term(keyword, retries)

        attempt_info = {
            'retry_number': retries,
            'term': retry_term,
            'strategy': self.config.strategy.value,
            'images_needed': images_needed,
            'success': False,
            'images_downloaded': 0
        }

        try:
            success = False

            if self.config.strategy == RetryStrategy.DDGS_ONLY:
                logger.info(
                    f"Retry #{retries}: Using DuckDuckGo with term '{retry_term}'")
                success, _ = download_images_ddgs(retry_term, out_dir, images_needed)

            elif self.config.strategy == RetryStrategy.ENGINE_ONLY:
                retry_engine = ENGINES[retries % len(ENGINES)]
                logger.info(
                    f"Retry #{retries}: Using {retry_engine} with term '{retry_term}'")
                downloader = ImageDownloader()
                success, _ = downloader.download(retry_term, out_dir, images_needed)

            else:  # ALTERNATING strategy (default)
                if retries % 2 == 0:
                    retry_engine = ENGINES[retries % len(ENGINES)]
                    logger.info(
                        f"Retry #{retries}: Using {retry_engine} with term '{retry_term}'")
                    downloader = ImageDownloader()
                    success, _ = downloader.download(retry_term, out_dir, images_needed)
                else:
                    logger.info(
                        f"Retry #{retries}: Using DuckDuckGo with term '{retry_term}'")
                    success, _ = download_images_ddgs(retry_term, out_dir,
                                                      images_needed)

            self.stats.total_attempts += 1
            result = self._update_image_count(out_dir) if success else 0

            if success:
                self.stats.successful_attempts += 1
                attempt_info['success'] = True
                attempt_info['images_downloaded'] = result
            else:
                self.stats.failed_attempts += 1

            return result

        except DownloadError as e:
            logger.warning(f"Retry #{retries} failed: {e}")
            self.stats.failed_attempts += 1
            attempt_info['error'] = str(e)
            return 0
        finally:
            self.stats.retry_history.append(attempt_info)

    def retry_download(self, keyword: str, out_dir: str, max_num: int,
                       max_retries: Optional[int] = None) -> Tuple[bool, int]:
        """
        Attempts to download images for a given keyword, retrying with alternative search terms and engines
        until the desired image count is reached or the maximum number of retries is exceeded.

        Args:
            keyword: The search keyword
            out_dir: Output directory for images
            max_num: Maximum number of images to download
            max_retries: Override the configured max_retries if provided

        Returns:
            Tuple[bool, int]: (success_flag, unique_images_count)

        Raises:
            DownloadError: If no images are successfully downloaded after all retries.
        """
        # Reset stats for new download session
        self.stats = RetryStats()

        # Use provided max_retries or fall back to config
        effective_max_retries = max_retries if max_retries is not None else self.config.max_retries

        # --- Initial Download Phase ---
        count = self._initial_download(max_num, keyword, out_dir)
        if count:
            logger.info(f"After removing duplicates: {count} unique images remain")

        # --- Retry Phase ---
        retries = 0
        while count < max_num and retries < effective_max_retries:
            retries += 1
            images_needed = max(0, max_num - count)
            logger.info(f"Retry #{retries}: Need {images_needed} more images")

            new_count = self._attempt_retry(retries, keyword, out_dir, images_needed)

            if new_count > count:
                count = new_count
                logger.info(f"After retry #{retries}: {count}/{max_num} unique images")

            if count >= max_num:
                break

        # --- Finalization Phase ---
        count = self._update_image_count(out_dir) if count > 1 else count

        if count > 0:
            try:
                renamed = rename_images_sequentially(out_dir)
                self.stats.images_renamed = renamed
                logger.info(f"Final step: Renamed {renamed} images sequentially")
            except Exception as e:
                logger.warning(f"Error renaming images: {e}")

            return True, count

        raise DownloadError(
            f"Failed to download any images for keyword '{keyword}' after {effective_max_retries} retries.")

    def get_stats(self) -> RetryStats:
        """Get current retry statistics"""
        return self.stats

    def reset_stats(self) -> None:
        """Reset retry statistics"""
        self.stats = RetryStats()

    def update_config(self, **kwargs) -> None:
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Unknown configuration parameter: {key}")


# Backward compatibility function
def retry_download(keyword: str, out_dir: str, max_num: int, max_retries: int = 5) -> \
    Tuple[bool, int]:
    """
    Backward compatibility function that maintains the original API.

    Args:
        keyword: The search keyword
        out_dir: Output directory for images
        max_num: Maximum number of images to download
        max_retries: Maximum number of retry attempts

    Returns:
        Tuple[bool, int]: (success_flag, unique_images_count)
    """
    config = RetryConfig(max_retries=max_retries)
    retry_handler = Retry(config)
    return retry_handler.retry_download(keyword, out_dir, max_num)


class ConfigManager:
    """
    Manages loading, validation, and access of dataset configuration from a JSON file.
    Supports dictionary-style access for top-level configuration keys.

    Attributes:
        config_path (str): The absolute path to the configuration file.
        config (Dict[str, Any]): A dictionary holding the validated configuration.
    """

    def __init__(self, config_path: str):
        """
        Initializes the ConfigManager with the path to the configuration file.

        Args:
            config_path (str): The absolute path to the configuration file.
        """
        self.config_path = config_path
        self.config = self._load_and_validate_config()

    def _load_and_validate_config(self) -> Dict[str, Any]:
        """
        Loads the configuration file, validates it against the schema, and sets defaults.

        Returns:
            Dict[str, Any]: The validated and finalized configuration dictionary.

        Raises:
            ConfigurationError: If the file is not found, invalid, or fails validation.
        """
        config = self._load_config_from_file()
        self._validate_config(config)
        self._set_defaults(config)
        logger.info(
            f"Configuration from '{self.config_path}' loaded and validated successfully.")
        return config

    def _load_config_from_file(self) -> Dict[str, Any]:
        """
        Loads the configuration from a JSON file.

        Returns:
            Dict[str, Any]: The loaded configuration dictionary.

        Raises:
            ConfigurationError: If the file cannot be found or decoded.
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found at: {self.config_path}")
            raise ConfigurationError(
                f"Configuration file not found at: {self.config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {self.config_path}: {e}")
            raise ConfigurationError(
                f"Error decoding JSON from {self.config_path}: {e}")

    @staticmethod
    def _validate_config(config: Dict[str, Any]):
        """
        Validates the configuration against the predefined schema.

        Args:
            config (Dict[str, Any]): The configuration dictionary to validate.

        Raises:
            ConfigurationError: If the configuration is invalid.
        """
        try:
            validate(instance=config, schema=CONFIG_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            # Provide a more user-friendly error message
            error_message = f"Configuration validation failed: {e.message} in '{'.'.join(map(str, e.path))}'"
            logger.error(error_message)
            raise ConfigurationError(error_message) from e

    @staticmethod
    def _set_defaults(config: Dict[str, Any]):
        """
        Sets default values for optional fields if they are not present.

        Args:
            config (Dict[str, Any]): The configuration dictionary to set defaults in.
        """
        # Set a default for the top-level 'dataset_name'
        if 'dataset_name' not in config:
            config['dataset_name'] = 'default_dataset'
            logger.info(
                "Missing 'dataset_name' in config, using 'default_dataset' as default.")

        # Ensure 'options' exists before setting defaults within it
        config.setdefault('options', {})

        # Define default options
        default_options = {
            'max_images': 1000,
            'output_dir': f"datasets/{config['dataset_name']}",
            'integrity': True,
            'max_retries': 3,
            'cache_file': f"{config['dataset_name']}_progress.json",
            'generate_keywords': False,
            'generate_labels': True
        }

        # Apply defaults for any missing options
        for key, value in default_options.items():
            if key not in config['options']:
                config['options'][key] = value
                logger.info(f"Missing option '{key}', using default value: {value}")

    # --- Dictionary Magic Methods ---

    def __getitem__(self, key: str) -> Any:
        """
        Allows dictionary-style access to top-level configuration items.
        Example: config_manager['dataset_name']

        Args:
            key (str): The configuration key to retrieve.

        Returns:
            Any: The value associated with the key.

        Raises:
            KeyError: If the key is not found in the configuration.
        """
        try:
            return self.config[key]
        except KeyError:
            raise KeyError(
                f"Configuration key '{key}' not found. Available keys are: {list(self.config.keys())}")

    def __len__(self) -> int:
        """
        Returns the number of top-level configuration items.
        Example: len(config_manager)
        """
        return len(self.config)

    def __iter__(self) -> Iterator[str]:
        """
        Allows iteration over the top-level configuration keys.
        Example: for key in config_manager: ...
        """
        return iter(self.config)

    # --- Getter Methods (still useful for clarity and specific tasks) ---

    def get_dataset_name(self) -> str:
        """Returns the dataset name."""
        return self.config['dataset_name']

    def get_categories(self) -> Dict[str, List[str]]:
        """Returns the categories dictionary."""
        return self.config['categories']

    def get_option(self, option_name: str, default: Any = None) -> Any:
        """
        Returns a specific option value from the configuration.

        Args:
            option_name (str): The name of the option to retrieve.
            default (Any, optional): A default value to return if the option is not found.

        Returns:
            Any: The value of the option or the default value.
        """
        return self.config.get('options', {}).get(option_name, default)

    def get_all_options(self) -> Dict[str, Any]:
        """Returns the entire options dictionary."""
        return self.config.get('options', {})


def update_logfile(log_file: str) -> None:
    """
    Updates the logging configuration to direct output to a specified log file.
    If the provided log file path is different from the default, the existing file handler
    is removed and a new one is added.

    Args:
        log_file (str): The absolute path to the desired log file.
    """
    # if log_file != DEFAULT_LOG_FILE:
    #     for handler in logger.handlers:
    #         if isinstance(handler, logging.FileHandler):
    #             handler.close()
    #             logger.removeHandler(handler)

    # Use centralized logging system - no need to manually configure handlers
    from utility.logging_config import get_logger
    logger = get_logger('builder.generator')


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
            logger.warning(
                f"Unsupported label format: {format_type}. Defaulting to 'txt'.")
            self.format_type = "txt"

    def generate_dataset_labels(self, dataset_dir: str) -> List[str]:
        """
        Generates label files for all images within the specified dataset directory.
        It organizes labels by category and keyword, and creates metadata files for the dataset.

        Args:
            dataset_dir (str): The root directory of the dataset.

        Returns:
            List[str]: List of paths to generated label files.
        """
        logger.info(
            f"Generating {self.format_type} labels for dataset at {dataset_dir}")
        dataset_path = Path(dataset_dir)

        # Create labels directory
        labels_dir = dataset_path / "labels"
        labels_dir.mkdir(parents=True, exist_ok=True)

        # Process each category directory
        category_dirs = [d for d in dataset_path.iterdir() if
                         d.is_dir() and d.name != "labels"]

        # Count total images for progress tracking
        total_images = sum(
            len([f for f in Path(keyword_dir).glob("**/*") if
                 f.is_file() and valid_image_ext(f)])
            for category_dir in category_dirs
            for keyword_dir in [d for d in category_dir.iterdir() if d.is_dir()]
        )

        # Create metadata file for the dataset with overall information
        self._generate_dataset_metadata(dataset_path, labels_dir, len(category_dirs),
                                        total_images)

        # Create category index file
        self._generate_category_index(labels_dir, [d.name for d in category_dirs])

        # Initialize progress manager for label generation
        progress.start_step("labels", total=total_images)

        # Track generated files
        generated_files = []

        # Process each category
        for category_dir in category_dirs:
            category_name = category_dir.name
            progress.start_subtask(f"Category: {category_name}")
            category_files = self._process_category(category_dir, category_name,
                                                    labels_dir, progress)
            generated_files.extend(category_files)
            progress.close_subtask()

        # Close progress bars
        progress.close()
        logger.info(
            f"Label generation completed. {len(generated_files)} labels stored in {labels_dir}")

        return generated_files

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
                with open(labels_dir / "dataset_metadata.yaml", "w",
                          encoding="utf-8") as f:
                    yaml.dump(metadata, f, default_flow_style=False)
            except ImportError:
                logger.warning(
                    "PyYAML not installed, skipping YAML metadata generation")
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
                with open(labels_dir / "category_index.yaml", "w",
                          encoding="utf-8") as f:
                    yaml.dump(category_map, f, default_flow_style=False)
            except ImportError:
                logger.warning(
                    "PyYAML not installed, skipping YAML category index generation")
        elif self.format_type == "csv":
            with open(labels_dir / "category_index.csv", "w", encoding="utf-8",
                      newline="") as f:
                f.write("category,id\n")
                for name, idx in category_map.items():
                    f.write(f"{name},{idx}\n")
        else:
            # For txt format
            with open(labels_dir / "category_index.txt", "w", encoding="utf-8") as f:
                for name, idx in category_map.items():
                    f.write(f"{name}: {idx}\n")

    def _process_category(self, category_dir: Path, category_name: str,
                          labels_dir: Path, progress: ProgressManager) -> List[str]:
        """
        Processes a single category directory, iterating through its keyword subdirectories
        to generate labels for images within them.

        Args:
            category_dir (Path): The directory containing the category's images and keywords.
            category_name (str): The name of the category.
            labels_dir (Path): The base directory where all label files are stored.
            progress (ProgressManager): An instance of the ProgressManager for updating progress bars.

        Returns:
            List[str]: List of paths to generated label files for this category.
        """
        # Create category label directory
        category_label_dir = labels_dir / category_name
        category_label_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Process each keyword directory within the category
        keyword_dirs = [d for d in category_dir.iterdir() if d.is_dir()]
        for keyword_dir in keyword_dirs:
            keyword_name = keyword_dir.name
            progress.set_subtask_description(f"Keyword: {keyword_name}")
            keyword_files = self._process_keyword(keyword_dir, category_name,
                                                  keyword_name,
                                                  category_label_dir, progress)
            generated_files.extend(keyword_files)

        return generated_files

    def _process_keyword(self, keyword_dir: Path, category_name: str, keyword_name: str,
                         category_label_dir: Path, progress: ProgressManager) -> List[
        str]:
        """
        Processes a keyword directory, generating label files for each image within it.

        Args:
            keyword_dir (Path): The directory containing images for the keyword.
            category_name (str): The name of the category.
            keyword_name (str): The name of the keyword.
            category_label_dir (Path): The directory to store label files for this category.
            progress (ProgressManager): An instance of the ProgressManager for updating progress bars.

        Returns:
            List[str]: List of paths to generated label files for this keyword.
        """
        # Create keyword label directory
        keyword_label_dir = category_label_dir / keyword_name
        keyword_label_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # Get all image files regardless of naming pattern
        image_files = [
            f for f in keyword_dir.iterdir()
            if f.is_file() and valid_image_ext(f)
        ]

        # Generate label for each image
        for image_file in image_files:
            label_file = self._generate_label_file(
                image_file=image_file,
                label_dir=keyword_label_dir,
                category=category_name,
                keyword=keyword_name
            )
            if label_file:
                generated_files.append(str(label_file))
            progress.update_step(1)  # Update main progress bar

        return generated_files

    def _generate_label_file(self, image_file: Path, label_dir: Path, category: str,
                             keyword: str) -> Optional[Path]:
        """
        Generates a label file for a single image based on the configured format.
        It extracts image metadata and writes the label content to the specified directory.

        Args:
            image_file (Path): The path to the image file for which to generate a label.
            label_dir (Path): The directory where the label file will be stored.
            category (str): The category name associated with the image.
            keyword (str): The keyword name associated with the image.

        Returns:
            Optional[Path]: Path to the generated label file, or None if generation failed.
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
                self._write_txt_label(label_file_path, category, keyword, image_file,
                                      image_metadata)
            elif self.format_type == "json":
                self._write_json_label(label_file_path, category, keyword, image_file,
                                       image_metadata)
            elif self.format_type == "csv":
                self._write_csv_label(label_file_path, category, keyword, image_file,
                                      image_metadata)
            elif self.format_type == "yaml":
                self._write_yaml_label(label_file_path, category, keyword, image_file,
                                       image_metadata)

            return label_file_path

        except PermissionError as pe:
            logger.warning(
                f"Permission denied when creating label file for {image_file}: {pe}")
            return None
        except IOError as ioe:
            logger.warning(f"I/O error generating label for {image_file}: {ioe}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error generating label for {image_file}: {e}")
            return None

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
            "parent_dir": image_path.parent.name
            # Store parent directory name for context
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
            GenerationError: If there is an error writing the file.
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
            raise GenerationError(f"Failed to write TXT label {label_path}: {e}") from e

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
            GenerationError: If there is an error writing the file.
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
            raise GenerationError(
                f"Failed to write JSON label {label_path}: {e}") from e

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
            GenerationError: If there is an error writing the file.
        """
        try:
            headers = ["category", "keyword", "image_path", "timestamp", "filename",
                       "width", "height", "format",
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
            raise GenerationError(f"Failed to write CSV label {label_path}: {e}") from e

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
            GenerationError: If there is an error writing the file (other than ImportError for PyYAML).
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
            raise GenerationError(
                f"Failed to write YAML label {label_path}: {e}") from e


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
        self.label_generator = LabelGenerator() if self.config.generate_labels else None

        # Initialize KeywordManagement instance
        self.keyword_manager = KeywordManagement(
            ai_model=self.config.ai_model,
            keyword_generation=self.config.keyword_generation
        )

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
        orchestrating keyword processing, image downloading,
        label generation, and report creation.
        """
        # Pre-process all keywords to get accurate totals
        all_keyword_results = {}
        for category_name, keywords in self.categories.items():
            keyword_result = self.keyword_manager.prepare_keywords(category_name,
                                                                   keywords)
            all_keyword_results[category_name] = keyword_result

        # Calculate total work items for progress tracking
        total_keywords = sum(
            len(result['keywords']) for result in all_keyword_results.values())

        # Generate keyword statistics for reporting
        keyword_stats_ = keyword_stats(all_keyword_results)
        # Report generation moved to src package

        # Start the download/generation step
        self.progress.start_step("download", total=total_keywords)

        # Process each category with prepared keywords
        for category_name, keyword_result in all_keyword_results.items():
            logger.info(f"Processing category: {category_name}")
            self.progress.start_subtask(f"Category: {category_name}",
                                        total=len(keyword_result['keywords']))

            # Report generation moved to src package

            self._process_category(category_name, keyword_result['keywords'])
            self.progress.close_subtask()

        # Close download progress
        self.progress.close()

        # Generate labels if enabled
        if self.config.generate_labels and self.label_generator:
            logger.info("Generating labels for the dataset")
            self.label_generator.generate_dataset_labels(str(self.root_dir))

        # Report generation moved to src package
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

    def _load_and_validate_config(self) -> Union[Dict[str, Any], ConfigManager]:
        """
        Loads and validates the dataset configuration from the specified config file.
        It also applies configuration options from the file, giving precedence to CLI arguments.

        Returns:
            Dict[str, Any]: The loaded and validated dataset configuration.
        """
        dataset_config = ConfigManager(self.config.config_path)

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

        # Process each keyword
        for keyword in keywords:
            self._process_keyword(category_name, keyword, category_path)
            # Update main progress
            self.progress.update_step(1)
            # Update subtask description to show completion
            self.progress.set_subtask_description(
                f"Category: {category_name} ({keywords.index(keyword) + 1}/{len(keywords)})")

    def _process_keyword(self, category_name: str, keyword: str,
                         category_path: Path) -> None:
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

        success, count = retry_download(
            keyword=keyword,
            out_dir=str(keyword_path),
            max_num=self.config.max_images,
            max_retries=self.config.max_retries
        )

        # Track results and record in report
        self._track_download_results(download_context, success, count, category_name,
                                     keyword)

        # Validation (duplicates and integrity) moved to validator package
        # Can be performed post-processing if needed using the validator package

        # Update progress cache if continuing from last run
        if self.config.continue_from_last and self.progress_cache:
            metadata = {
                "success": success,
                "downloaded_count": count,
            }
            self.progress_cache.mark_completed(category_name, keyword, metadata)

        # Small delay to be respectful to image services
        time.sleep(0.5)

    def _track_download_results(self, download_context: str, success: bool, count: int,
                                category_name: str,
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
            logger.info(
                f"Successfully downloaded {count} images for {download_context}")
        else:
            error_msg = "Failed to download any valid images after retries"
            self.tracker.record_download_failure(download_context, error_msg)


def generate_dataset(config: DatasetGenerationConfig) -> None:
    """
    Generate image dataset based on configuration file.

    Args:
        config: Dataset generation configuration
    """
    generator = DatasetGenerator(config)
    generator.generate()
