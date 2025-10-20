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
import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Final, Iterator, Union, Set

import jsonschema
from PIL import Image
from icrawler.builtin import GoogleImageCrawler, BingImageCrawler, BaiduImageCrawler
from jsonschema import validate

from _exceptions import PixCrawlerError, ConfigurationError, DownloadError, GenerationError
from config import DatasetGenerationConfig, CONFIG_SCHEMA
from config import get_basic_variations, get_quality_variations, get_generic_quality_variations, get_search_variations, \
    get_lighting_variations, get_location_variations, get_background_variations, get_professional_variations, \
    get_color_variations, get_style_variations, get_meme_culture_variations, get_size_format_variations, \
    get_time_period_variations, get_condition_age_variations, get_emotional_aesthetic_variations, \
    get_quantity_arrangement_variations, get_camera_technique_variations, get_focus_sharpness_variations, \
    get_texture_material_variations
from constants import DEFAULT_CACHE_FILE, DEFAULT_LOG_FILE, ENGINES, \
    file_formatter, logger, IMAGE_EXTENSIONS
from downloader import ImageDownloader, download_images_ddgs
from helpers import ReportGenerator, DatasetTracker, ProgressManager, progress, valid_image_ext
from utilities import ProgressCache, rename_images_sequentially, DuplicationManager, image_validator

__all__ = [
    'retry_download',
    'keyword_stats',
    'validate_keywords',
    'update_logfile',
    'LabelGenerator',
    'KeywordManagement',
    'DatasetGenerator',
    'CheckManager',
    'generate_dataset',
    'ConfigManager',
]

BACKOFF_DELAY: Final[float] = 0.5

duplicate_manager = DuplicationManager()


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

    Raises:
        DownloadError: If the download fails for any reason.
    """
    try:
        if engine_name == "ddgs":
            success, _ = download_images_ddgs(keyword=keyword, out_dir=out_dir, max_num=max_num)
            if not success:
                raise DownloadError(f"DuckDuckGo download failed for {keyword}")
            return success

        # Configure crawler based on engine
        crawler_class = {
            "google": GoogleImageCrawler,
            "bing": BingImageCrawler,
            "baidu": BaiduImageCrawler
        }.get(engine_name)

        if not crawler_class:
            raise DownloadError(f"Unknown engine: {engine_name}")

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
        raise DownloadError(f"{engine_name.capitalize()}ImageCrawler failed for {keyword}: {e}") from e


# noinspection PyArgumentList
class AlternativeTermsGenerator:
    """
    Generates alternative search terms using predefined keywords from config.
    Intelligently combines multiple variations to create more effective search terms.
    """

    def __init__(self):
        """
        Initialize the generator with configuration keywords.
        """

        self.category_functions = self._get_categories()

        # Extract clean terms from each category (remove {keyword} placeholder)
        self.clean_terms = self._extract_clean_terms()

    @staticmethod
    def _get_categories() -> dict:
        return {
            'basic': get_basic_variations,
            'quality': get_quality_variations,
            'style': get_style_variations,
            'time_period': get_time_period_variations,
            'emotional_aesthetic': get_emotional_aesthetic_variations,
            'meme_culture': get_meme_culture_variations,
            'professional': get_professional_variations,
            'camera_technique': get_camera_technique_variations,
            'focus_sharpness': get_focus_sharpness_variations,
            'color': get_color_variations,
            'lighting': get_lighting_variations,
            'location': get_location_variations,
            'background': get_background_variations,
            'size_format': get_size_format_variations,
            'texture_material': get_texture_material_variations,
            'condition_age': get_condition_age_variations,
            'quantity_arrangement': get_quantity_arrangement_variations,
            'generic_quality': get_generic_quality_variations
        }

    def _extract_clean_terms(self) -> Dict[str, List[str]]:
        """Extract clean terms from each category by removing {keyword} placeholder"""
        clean_terms = {}

        for category, func in self.category_functions.items():
            variations = func()
            clean_terms[category] = []

            for variation in variations:
                # Remove {keyword} and clean up the remaining text
                clean_term = variation.replace("{keyword} ", "").replace("{keyword}", "").strip()
                if clean_term and clean_term not in clean_terms[category]:
                    clean_terms[category].append(clean_term)

        return clean_terms

    def _smart_combination_strategy_1(self, keyword: str, retry_count: int) -> str:
        """
        Strategy 1: Quality + Style combination
        Example: "professional 4K realistic cat photo"
        """
        quality_term = random.choice(self.clean_terms['quality'])
        style_term = random.choice(self.clean_terms['style'])

        if retry_count <= 3:
            return f"{style_term} {quality_term} {keyword}"
        else:
            basic_term = random.choice(self.clean_terms['basic'])
            return f"{style_term} {quality_term} {keyword} {basic_term}"

    def _smart_combination_strategy_2(self, keyword: str, retry_count: int) -> str:
        """
        Strategy 2: Multiple quality terms + emotional
        Example: "stunning high resolution 4K detailed cat"
        """
        quality_terms = random.sample(self.clean_terms['quality'], min(2, len(self.clean_terms['quality'])))
        emotional_term = random.choice(self.clean_terms['emotional_aesthetic'])

        if retry_count <= 5:
            return f"{emotional_term} {' '.join(quality_terms)} {keyword}"
        else:
            professional_term = random.choice(self.clean_terms['professional'])
            return f"{emotional_term} {professional_term} {' '.join(quality_terms)} {keyword}"

    def _smart_combination_strategy_3(self, keyword: str, retry_count: int) -> str:
        """
        Strategy 3: Camera technique + lighting + style
        Example: "close up dramatic lighting realistic cat"
        """
        camera_term = random.choice(self.clean_terms['camera_technique'])
        lighting_term = random.choice(self.clean_terms['lighting'])
        style_term = random.choice(self.clean_terms['style'])

        return f"{camera_term} {lighting_term} {style_term} {keyword}"

    def _smart_combination_strategy_4(self, keyword: str, retry_count: int) -> str:
        """
        Strategy 4: Background + color + quality
        Example: "white background colorful high quality cat photo"
        """
        background_term = random.choice(self.clean_terms['background'])
        color_term = random.choice(self.clean_terms['color'])
        quality_term = random.choice(self.clean_terms['quality'])
        basic_term = random.choice(self.clean_terms['basic'])

        return f"{background_term} {color_term} {quality_term} {keyword} {basic_term}"

    def _smart_combination_strategy_5(self, keyword: str, retry_count: int) -> str:
        """
        Strategy 5: Complex multi-category combination
        Example: "professional studio lighting high resolution beautiful detailed cat photograph"
        """
        professional_term = random.choice(self.clean_terms['professional'])
        lighting_term = random.choice(self.clean_terms['lighting'])
        quality_term = random.choice(self.clean_terms['quality'])
        emotional_term = random.choice(self.clean_terms['emotional_aesthetic'])
        focus_term = random.choice(self.clean_terms['focus_sharpness'])
        basic_term = random.choice(self.clean_terms['basic'])

        return f"{professional_term} {lighting_term} {quality_term} {emotional_term} {focus_term} {keyword} {basic_term}"

    def _smart_combination_strategy_6(self, keyword: str, retry_count: int) -> str:
        """
        Strategy 6: Location + time period + style
        Example: "indoor vintage artistic cat"
        """
        location_term = random.choice(self.clean_terms['location'])
        time_term = random.choice(self.clean_terms['time_period'])
        style_term = random.choice(self.clean_terms['style'])

        return f"{location_term} {time_term} {style_term} {keyword}"

    def _smart_combination_strategy_7(self, keyword: str, retry_count: int) -> str:
        """
        Strategy 7: Size + texture + color
        Example: "large textured colorful cat"
        """
        size_term = random.choice(self.clean_terms['size_format'])
        texture_term = random.choice(self.clean_terms['texture_material'])
        color_term = random.choice(self.clean_terms['color'])

        return f"{size_term} {texture_term} {color_term} {keyword}"

    def _smart_combination_strategy_8(self, keyword: str, retry_count: int) -> str:
        """
        Strategy 8: Condition + arrangement + generic quality
        Example: "new organized excellent cat"
        """
        condition_term = random.choice(self.clean_terms['condition_age'])
        arrangement_term = random.choice(self.clean_terms['quantity_arrangement'])
        quality_term = random.choice(self.clean_terms['generic_quality'])

        return f"{condition_term} {arrangement_term} {quality_term} {keyword}"

    @staticmethod
    def _progressive_strategy_selection(retry_count: int) -> int:
        """
        Progressively select more complex strategies as retry count increases
        """
        if retry_count <= 2:
            return random.choice([1, 2])
        elif retry_count <= 4:
            return random.choice([1, 2, 3])
        elif retry_count <= 6:
            return random.choice([2, 3, 4])
        elif retry_count <= 8:
            return random.choice([3, 4, 5])
        elif retry_count <= 10:
            return random.choice([4, 5, 6])
        elif retry_count <= 12:
            return random.choice([5, 6, 7])
        else:
            return random.choice([6, 7, 8])

    def generate(self, keyword: str, retry_count: int = 0) -> List[str]:
        """
        Generate alternative search terms using intelligent combination strategies.

        Args:
            keyword: The original search keyword
            retry_count: Current retry count (influences strategy complexity)

        Returns:
            List of intelligently generated alternative search terms
        """
        if not keyword:
            return []

        # Always start with the original keyword
        alternatives = [keyword]

        # Generate variations using different smart strategies
        strategies = self._get_strategies()

        # Generate multiple alternatives using different strategies
        num_alternatives = min(15, 3 + retry_count)  # More alternatives for higher retry counts

        for i in range(num_alternatives):
            strategy_num = self._progressive_strategy_selection(retry_count + i)
            strategy_func = strategies[strategy_num]

            try:
                alternative = strategy_func(keyword, retry_count + i)
                if alternative and alternative not in alternatives:
                    alternatives.append(alternative)
            except Exception as e:
                logger.warning(f"Strategy {strategy_num} failed: {e}")
                # Fallback to simple combination
                quality_term = random.choice(self.clean_terms['quality'])
                alternatives.append(f"{quality_term} {keyword}")

        # Add some simple fallbacks if we don't have enough alternatives
        if len(alternatives) < 8:
            self._generate_simple_fallback(keyword, alternatives)

        # Shuffle to add randomness while keeping original keyword first
        alternatives_to_shuffle = alternatives[1:]
        random.shuffle(alternatives_to_shuffle)

        return [alternatives[0]] + alternatives_to_shuffle

    def _generate_simple_fallback(self, keyword: str, alternatives: list) -> None:
        simple_combinations = [
            f"{keyword} {random.choice(self.clean_terms['quality'])}",
            f"{random.choice(self.clean_terms['style'])} {keyword}",
            f"{keyword} {random.choice(self.clean_terms['basic'])}",
            f"{random.choice(self.clean_terms['emotional_aesthetic'])} {keyword}",
            f"{random.choice(self.clean_terms['professional'])} {keyword}",
        ]

        for combo in simple_combinations:
            if combo not in alternatives:
                alternatives.append(combo)
                if len(alternatives) >= 15:
                    break

    def _get_strategies(self):
        return {
            1: self._smart_combination_strategy_1,
            2: self._smart_combination_strategy_2,
            3: self._smart_combination_strategy_3,
            4: self._smart_combination_strategy_4,
            5: self._smart_combination_strategy_5,
            6: self._smart_combination_strategy_6,
            7: self._smart_combination_strategy_7,
            8: self._smart_combination_strategy_8
        }

    def next_term(self, keyword: str, retry_count: int) -> str:
        """
        Get the next search term for a specific retry attempt.

        Args:
            keyword: Original keyword
            retry_count: Current retry count

        Returns:
            Next search term to try
        """
        alternatives = self.generate(keyword, retry_count)

        # Return the term at the retry index, or cycle through if we exceed the list
        if retry_count < len(alternatives):
            return alternatives[retry_count]
        else:
            # Cycle through alternatives for very high retry counts
            return alternatives[retry_count % len(alternatives)]


# Global variable
generator = AlternativeTermsGenerator()


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
    max_parallel_engines: int = 3
    max_parallel_variations: int = 3
    use_all_engines: bool = True


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
        Fast image count - no duplicate removal during download.
        Duplicates are removed once at the very end.

        Args:
            out_dir (str): The directory containing images.

        Returns:
            int: The count of images in the directory.
        """
        image_files = self._get_image_files(out_dir)
        return len(image_files)

    def _initial_download(self, max_num: int, keyword: str, out_dir: str) -> int:
        """Direct crawler call - zero overhead, maximum speed"""
        import logging
        from pathlib import Path
        from icrawler.builtin import GoogleImageCrawler, BingImageCrawler
        
        logger.info(f"Downloading {max_num} images for '{keyword}'")
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        
        # Try Google first (fastest from benchmark: 22s/100 images)
        try:
            logger.info("Using Google...")
            google = GoogleImageCrawler(
                storage={'root_dir': out_dir},
                log_level=logging.WARNING,
                feeder_threads=1,
                parser_threads=1,
                downloader_threads=3
            )
            google.crawl(keyword=keyword, max_num=max_num, min_size=(100, 100))
            
            count = len(self._get_image_files(out_dir))
            if count > 0:
                self.stats.total_attempts += 1
                self.stats.successful_attempts += 1
                logger.info(f"Google: Downloaded {count} images")
                return count
        except Exception as e:
            logger.warning(f"Google failed: {e}")
        
        # Fallback to Bing (9s/100 images - even faster!)
        try:
            logger.info("Trying Bing...")
            bing = BingImageCrawler(
                storage={'root_dir': out_dir},
                log_level=logging.WARNING,
                feeder_threads=1,
                parser_threads=1,
                downloader_threads=3
            )
            bing.crawl(keyword=keyword, max_num=max_num, min_size=(100, 100))
            
            count = len(self._get_image_files(out_dir))
            if count > 0:
                self.stats.total_attempts += 1
                self.stats.successful_attempts += 1
                logger.info(f"Bing: Downloaded {count} images")
                return count
        except Exception as e:
            logger.warning(f"Bing failed: {e}")
        
        # Both failed
        self.stats.total_attempts += 1
        self.stats.failed_attempts += 1
        return 0

    def _attempt_retry(self, retries: int, keyword: str, out_dir: str, images_needed: int) -> int:
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
                logger.info(f"Retry #{retries}: Using DuckDuckGo with term '{retry_term}'")
                success, _ = download_images_ddgs(retry_term, out_dir, images_needed)

            elif self.config.strategy == RetryStrategy.ENGINE_ONLY:
                retry_engine = ENGINES[retries % len(ENGINES)]
                logger.info(f"Retry #{retries}: Using {retry_engine} with term '{retry_term}'")
                downloader = ImageDownloader(use_all_engines=False)
                success, _ = downloader.download(retry_term, out_dir, images_needed)

            else:  # ALTERNATING strategy (default)
                if retries % 2 == 0:
                    retry_engine = ENGINES[retries % len(ENGINES)]
                    logger.info(f"Retry #{retries}: Using {retry_engine} with term '{retry_term}'")
                    downloader = ImageDownloader(use_all_engines=False)
                    success, _ = downloader.download(retry_term, out_dir, images_needed)
                else:
                    logger.info(f"Retry #{retries}: Using DuckDuckGo with term '{retry_term}'")
                    success, _ = download_images_ddgs(retry_term, out_dir, images_needed)

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
        # Remove duplicates once at the end (not during download)
        if count > 1:
            try:
                removed = duplicate_manager.remove_duplicates(out_dir)
                if removed[0] > 0:
                    self.stats.duplicates_removed += removed[0]
                    logger.info(f"Removed {removed[0]} duplicate images")
                    count = len(self._get_image_files(out_dir))
            except Exception as e:
                logger.warning(f"Error removing duplicates: {e}")
        
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
def retry_download(keyword: str, out_dir: str, max_num: int, max_retries: int = 5) -> Tuple[bool, int]:
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
        logger.info(f"Configuration from '{self.config_path}' loaded and validated successfully.")
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
            raise ConfigurationError(f"Configuration file not found at: {self.config_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {self.config_path}: {e}")
            raise ConfigurationError(f"Error decoding JSON from {self.config_path}: {e}")

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
            logger.info("Missing 'dataset_name' in config, using 'default_dataset' as default.")

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
            raise KeyError(f"Configuration key '{key}' not found. Available keys are: {list(self.config.keys())}")

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


class CheckMode(Enum):
    """Enumeration of available check modes"""
    STRICT = "strict"  # Fail on any issues
    LENIENT = "lenient"  # Log warnings but continue
    REPORT_ONLY = "report_only"  # Only report, no actions


class DuplicateAction(Enum):
    """Actions to take when duplicates are found"""
    REMOVE = "remove"
    REPORT_ONLY = "report_only"
    QUARANTINE = "quarantine"


@dataclass
class CheckConfig:
    """Configuration for check operations"""
    mode: CheckMode = CheckMode.LENIENT
    duplicate_action: DuplicateAction = DuplicateAction.REMOVE
    supported_extensions: Tuple[str, ...] = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    max_file_size_mb: Optional[int] = None
    min_file_size_bytes: int = 1024  # 1KB minimum
    quarantine_dir: Optional[str] = None
    batch_size: int = 100  # Process images in batches


@dataclass
class DuplicateResult:
    """Result of duplicate checking operation"""
    total_images: int
    duplicates_found: int
    duplicates_removed: int
    unique_kept: int
    duplicate_groups: Dict[str, List[str]] = field(default_factory=dict)
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class IntegrityResult:
    """Result of integrity checking operation"""
    total_images: int
    valid_images: int
    corrupted_images: int
    corrupted_files: List[str] = field(default_factory=list)
    size_violations: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    errors: List[str] = field(default_factory=list)


@dataclass
class CheckStats:
    """Overall statistics for check operations"""
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    total_duplicates_found: int = 0
    total_duplicates_removed: int = 0
    total_corrupted_found: int = 0
    categories_processed: Set[str] = field(default_factory=set)
    keywords_processed: Set[str] = field(default_factory=set)
    processing_history: List[Dict[str, Any]] = field(default_factory=list)


class CheckManager:
    """
    Enhanced manager for checking image duplicates and integrity with comprehensive
    tracking, configurable behavior, and detailed reporting.
    """

    def __init__(self, config: Optional[CheckConfig] = None):
        """
        Initialize the CheckManager.

        Args:
            config: Optional CheckConfig for customizing behavior
        """
        self.config = config or CheckConfig()
        self.stats = CheckStats()

        # Setup quarantine directory if specified
        if (self.config.duplicate_action == DuplicateAction.QUARANTINE and
                self.config.quarantine_dir):
            Path(self.config.quarantine_dir).mkdir(parents=True, exist_ok=True)

    def _is_valid_image_file(self, file_path: Path) -> bool:
        """Check if a file is a valid image file"""
        try:
            if not file_path.is_file():
                return False

            # Check extension
            if not file_path.suffix.lower() in self.config.supported_extensions:
                return False

            # Check file size constraints
            file_size = file_path.stat().st_size
            if file_size < self.config.min_file_size_bytes:
                return False

            if (self.config.max_file_size_mb and
                    file_size > self.config.max_file_size_mb * 1024 * 1024):
                return False

            return True

        except Exception as e:
            logger.warning(f"Error checking file {file_path}: {e}")
            return False

    def _get_image_files(self, directory_path: Path) -> List[Path]:
        """Get all valid image files in a directory"""
        try:
            if not directory_path.exists():
                logger.warning(f"Directory does not exist: {directory_path}")
                return []

            image_files = []
            for file_path in directory_path.iterdir():
                if self._is_valid_image_file(file_path):
                    image_files.append(file_path)

            return image_files

        except Exception as e:
            logger.error(f"Error reading directory {directory_path}: {e}")
            return []

    def _handle_duplicates(self, duplicates: Dict[str, List[str]],
                           keyword_path: str) -> int:
        """Handle duplicate files based on configured action"""
        removed_count = 0

        try:
            if self.config.duplicate_action == DuplicateAction.REPORT_ONLY:
                return 0

            for original, duplicates_list in duplicates.items():
                for duplicate_file in duplicates_list:
                    duplicate_path = Path(keyword_path) / duplicate_file

                    if self.config.duplicate_action == DuplicateAction.REMOVE:
                        removed_count = self._unlink(duplicate_path, removed_count, duplicate_file)

                    elif self.config.duplicate_action == DuplicateAction.QUARANTINE:
                        removed_count = self._unlink_quarantine(duplicate_path, removed_count, duplicate_file)

        except Exception as e:
            logger.error(f"Error handling duplicates: {e}")

        return removed_count

    @staticmethod
    def _unlink(duplicate_path, removed_count, duplicate_file) -> int:
        if duplicate_path.exists():
            duplicate_path.unlink()
            removed_count += 1
            logger.debug(f"Removed duplicate: {duplicate_file}")
        return removed_count

    def _unlink_quarantine(self, duplicate_path, removed_count, duplicate_file) -> int:
        if duplicate_path.exists() and self.config.quarantine_dir:
            quarantine_path = Path(self.config.quarantine_dir) / duplicate_file
            quarantine_path.parent.mkdir(parents=True, exist_ok=True)
            duplicate_path.rename(quarantine_path)
            removed_count += 1
            logger.debug(f"Quarantined duplicate: {duplicate_file}")
        return removed_count

    def duplicates(self, category_name: str, keyword: str,
                   keyword_path: str, report: 'ReportGenerator') -> DuplicateResult:
        """
        Enhanced duplicate checking with comprehensive result tracking.

        Args:
            category_name: Name of the category
            keyword: Keyword being processed
            keyword_path: Path to the keyword directory
            report: ReportGenerator instance for recording results

        Returns:
            DuplicateResult: Detailed results of the duplicate check
        """
        start_time = time.time()
        result = DuplicateResult(total_images=0, duplicates_found=0,
                                 duplicates_removed=0, unique_kept=0)

        try:
            # Get all image files
            keyword_path_obj = Path(keyword_path)
            image_files = self._get_image_files(keyword_path_obj)
            result.total_images = len(image_files)

            if not image_files:
                logger.info(f"No images found in {keyword_path}")
                return result

            logger.info(f"Checking for duplicates in {len(image_files)} images for {category_name}/{keyword}")

            duplicates = duplicate_manager.detect_duplicates(keyword_path)

            result.duplicate_groups = duplicates
            result.duplicates_found = sum(len(dups) for dups in duplicates.values())

            # Handle duplicates based on configuration
            result.duplicates_removed = self._handle_duplicates(duplicates, keyword_path)
            result.unique_kept = result.total_images - result.duplicates_removed

            # Update statistics
            self._update_statistics(result, category_name, keyword)

            # Record in report
            report.record_duplicates(
                category=category_name,
                keyword=keyword,
                total=result.total_images,
                duplicates=result.duplicates_found,
                kept=result.unique_kept
            )

            logger.info(f"Found {result.duplicates_found} duplicates, "
                        f"removed {result.duplicates_removed} out of {result.total_images} images")

        except Exception as e:
            error_msg = f"Failed to check duplicates for {category_name}/{keyword}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            self.stats.failed_checks += 1

            report.record_error(f"{category_name}/{keyword} duplicates check", str(e))

            if self.config.mode == CheckMode.STRICT:
                raise PixCrawlerError(error_msg) from e

        finally:
            result.processing_time = time.time() - start_time
            self.stats.total_checks += 1

            # Record processing history
            self.stats.processing_history.append({
                'operation': 'duplicate_check',
                'category': category_name,
                'keyword': keyword,
                'success': not result.errors,
                'processing_time': result.processing_time,
                'images_processed': result.total_images,
                'duplicates_found': result.duplicates_found
            })

        return result

    def _update_statistics(self, result, category_name, keyword):
        self.stats.total_duplicates_found += result.duplicates_found
        self.stats.total_duplicates_removed += result.duplicates_removed
        self.stats.categories_processed.add(category_name)
        self.stats.keywords_processed.add(keyword)
        self.stats.successful_checks += 1

    def integrity(self, tracker: 'DatasetTracker', download_context: str,
                  keyword_path: str, max_images: int, report: 'ReportGenerator',
                  category_name: str, keyword: str) -> IntegrityResult:
        """
        Enhanced integrity checking with detailed result tracking.

        Args:
            tracker: DatasetTracker instance
            download_context: Context description for the download
            keyword_path: Path to the keyword directory
            max_images: Expected maximum number of images
            report: ReportGenerator instance
            category_name: Name of the category
            keyword: Keyword being processed

        Returns:
            IntegrityResult: Detailed results of the integrity check
        """
        start_time = time.time()
        result = IntegrityResult(total_images=0, valid_images=0, corrupted_images=0)

        try:
            # Count valid images
            valid_count, total_count, corrupted_files = image_validator.count_valid(keyword_path)

            result.total_images = total_count
            result.valid_images = valid_count
            result.corrupted_images = len(corrupted_files)
            result.corrupted_files = corrupted_files

            # Check for size violations if configured
            if self.config.max_file_size_mb or self.config.min_file_size_bytes:
                keyword_path_obj = Path(keyword_path)
                for file_path in self._get_image_files(keyword_path_obj):
                    file_size = file_path.stat().st_size

                    if file_size < self.config.min_file_size_bytes:
                        result.size_violations.append(f"{file_path.name} (too small: {file_size} bytes)")
                    elif (self.config.max_file_size_mb and
                          file_size > self.config.max_file_size_mb * 1024 * 1024):
                        result.size_violations.append(f"{file_path.name} (too large: {file_size} bytes)")

            # Record integrity failure if needed
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

            # Update statistics
            self.stats.total_corrupted_found += result.corrupted_images
            self.stats.categories_processed.add(category_name)
            self.stats.keywords_processed.add(keyword)
            self.stats.successful_checks += 1

            logger.info(f"Integrity check for {category_name}/{keyword}: "
                        f"{valid_count}/{total_count} valid images, "
                        f"{result.corrupted_images} corrupted")

        except Exception as e:
            error_msg = f"Failed to check integrity for {category_name}/{keyword}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            self.stats.failed_checks += 1

            report.record_error(f"{category_name}/{keyword} integrity check", str(e))

            if self.config.mode == CheckMode.STRICT:
                raise PixCrawlerError(error_msg) from e

        finally:
            result.processing_time = time.time() - start_time
            self.stats.total_checks += 1

            # Record processing history
            self.stats.processing_history.append({
                'operation': 'integrity_check',
                'category': category_name,
                'keyword': keyword,
                'success': not result.errors,
                'processing_time': result.processing_time,
                'images_processed': result.total_images,
                'valid_images': result.valid_images,
                'corrupted_images': result.corrupted_images
            })

        return result

    def all(self, tracker: 'DatasetTracker', download_context: str,
            keyword_path: str, max_images: int, report: 'ReportGenerator',
            category_name: str, keyword: str) -> Tuple[DuplicateResult, IntegrityResult]:
        """
        Perform both duplicate and integrity checks in sequence.

        Returns:
            Tuple[DuplicateResult, IntegrityResult]: Results of both checks
        """
        logger.info(f"Starting comprehensive check for {category_name}/{keyword}")

        # Check duplicates first
        duplicate_result = self.duplicates(category_name, keyword, keyword_path, report)

        # Then check integrity
        integrity_result = self.integrity(
            tracker, download_context, keyword_path, max_images,
            report, category_name, keyword
        )

        return duplicate_result, integrity_result

    def reset(self) -> None:
        """Reset check statistics"""
        self.stats = CheckStats()

    def update_config(self, **kwargs) -> None:
        """Update configuration parameters"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Unknown configuration parameter: {key}")

    def get_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of all check operations"""
        return {
            'total_checks': self.stats.total_checks,
            'success_rate': (self.stats.successful_checks / self.stats.total_checks
                             if self.stats.total_checks > 0 else 0),
            'categories_processed': len(self.stats.categories_processed),
            'keywords_processed': len(self.stats.keywords_processed),
            'total_duplicates_found': self.stats.total_duplicates_found,
            'total_duplicates_removed': self.stats.total_duplicates_removed,
            'total_corrupted_found': self.stats.total_corrupted_found,
            'duplicate_removal_rate': (self.stats.total_duplicates_removed /
                                       self.stats.total_duplicates_found
                                       if self.stats.total_duplicates_found > 0 else 0),
            'processing_history': self.stats.processing_history
        }


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


def validate_keywords(keywords: List[str]) -> List[str]:
    """
    Validates a list of keywords, removing invalid or problematic ones.

    Args:
        keywords (List[str]): The list of keywords to validate.

    Returns:
        List[str]: A list of validated keywords.
    """
    valid_keywords = []

    for keyword in keywords:
        # Remove leading/trailing whitespace
        keyword = keyword.strip()

        # Skip empty keywords
        if not keyword:
            continue

        # Skip keywords that are too short or too long
        if len(keyword) < 2 or len(keyword) > 100:
            logger.warning(f"Skipping keyword '{keyword}' - invalid length")
            continue

        # Skip keywords with invalid characters (basic validation)
        if re.search(r'[<>:"/\\|?*]', keyword):
            logger.warning(f"Skipping keyword '{keyword}' - contains invalid characters")
            continue

        valid_keywords.append(keyword)

    return valid_keywords


def keyword_stats(category_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates statistics about keyword generation across all categories.

    Args:
        category_results (Dict[str, Dict[str, Any]]): Results from prepare_keywords for each category.

    Returns:
        Dict[str, Any]: Statistics about keyword generation.
    """
    stats = {
        'total_categories': len(category_results),
        'categories_with_generation': 0,
        'total_original_keywords': 0,
        'total_generated_keywords': 0,
        'total_final_keywords': 0,
        'generation_rate': 0.0
    }

    for category, result in category_results.items():
        stats['total_original_keywords'] += len(result['original_keywords'])
        stats['total_generated_keywords'] += len(result['generated_keywords'])
        stats['total_final_keywords'] += len(result['keywords'])

        if result['generation_occurred']:
            stats['categories_with_generation'] += 1

    if stats['total_categories'] > 0:
        stats['generation_rate'] = stats['categories_with_generation'] / stats['total_categories']

    return stats


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
            len([f for f in Path(keyword_dir).glob("**/*") if f.is_file() and valid_image_ext(f)])
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
            if f.is_file() and valid_image_ext(f)
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

        except PermissionError as pe:
            logger.warning(f"Permission denied when creating label file for {image_file}: {pe}")
            raise GenerationError(f"Permission denied creating label for {image_file}: {pe}") from pe
        except IOError as ioe:
            logger.warning(f"I/O error generating label for {image_file}: {ioe}")
            raise GenerationError(f"I/O error generating label for {image_file}: {ioe}") from ioe
        except Exception as e:
            logger.warning(f"Unexpected error generating label for {image_file}: {e}")
            raise GenerationError(f"Unexpected error generating label for {image_file}: {e}") from e

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
            raise GenerationError(f"Failed to write JSON label {label_path}: {e}") from e

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
            raise GenerationError(f"Failed to write YAML label {label_path}: {e}") from e


class KeywordManagement:
    """
    Class responsible for managing keyword generation and preparation for dataset categories.
    This class handles AI-based keyword generation, keyword validation, and preparation
    of final keyword lists based on configuration settings.
    """

    def __init__(self, ai_model: str = "gpt4-mini", keyword_generation: str = "auto"):
        """
        Initializes the KeywordManagement instance.

        Args:
            ai_model (str): The AI model to use for keyword generation (e.g., "gpt4", "gpt4-mini").
            keyword_generation (str): The keyword generation mode ("auto", "enabled", "disabled").
        """
        self.ai_model = ai_model
        self.keyword_generation = keyword_generation

    def prepare_keywords(self, category_name: str, keywords: List[str]) -> Dict[str, Any]:
        """
        Prepares keywords for processing based on the configuration.
        This includes generating new keywords using an AI model if enabled and necessary.

        Args:
            category_name (str): The name of the category.
            keywords (List[str]): The initial list of keywords provided for the category.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - 'keywords': The final list of keywords to be processed
                - 'original_keywords': The original keywords provided
                - 'generated_keywords': Any keywords generated by AI
                - 'generation_occurred': Boolean indicating if generation took place
        """
        # Record original keywords before any potential generation
        original_keywords = keywords.copy() if keywords else []
        generated_keywords = []
        generation_occurred = False

        if not keywords and self.keyword_generation in ["auto", "enabled"]:
            # No keywords provided and generation enabled
            generated_keywords = self.generate_keywords(category_name)
            keywords = generated_keywords
            generation_occurred = True
            logger.info(f"No keywords provided for category '{category_name}', generated {len(keywords)} keywords")

        elif not keywords and self.keyword_generation == "disabled":
            # No keywords and generation disabled, use category name as keyword
            keywords = [category_name]
            logger.info(
                f"No keywords provided for category '{category_name}' and generation disabled, using category name as keyword"
            )

        elif self.keyword_generation == "enabled" and keywords:
            # Keywords provided and asked to generate more
            generated_keywords = self.generate_keywords(category_name)
            # Add generated keywords to user-provided ones, avoiding duplicates
            original_count = len(keywords)
            keywords = list(set(keywords + generated_keywords))
            generation_occurred = True
            logger.info(
                f"Added {len(keywords) - original_count} generated keywords to {original_count} user-provided ones"
            )

        return {
            'keywords': keywords,
            'original_keywords': original_keywords,
            'generated_keywords': generated_keywords,
            'generation_occurred': generation_occurred
        }

    def generate_keywords(self, category: str) -> List[str]:
        """
        Generates related keywords for a given category using the G4F (GPT-4) API.
        This function attempts to generate diverse and high-quality search terms.

        Args:
            category (str): The category name for which to generate keywords.

        Returns:
            List[str]: A list of generated keywords related to the category.

        Raises:
            GenerationError: If keyword generation fails after retries.
        """
        try:
            # Import g4f here to avoid import issues if not available
            import g4f

            # Select the appropriate model
            provider = None  # Let g4f choose the best available provider
            model = g4f.models.gpt_4 if self.ai_model == "gpt4" else g4f.models.gpt_4o_mini

            # Create the prompt
            prompt = self._get_prompt(category)

            # Make the API call
            logger.info(f"Generating keywords for '{category}' using {self.ai_model}")
            response = g4f.ChatCompletion.create(
                model=model,
                provider=provider,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract keywords from response
            keywords = self._extract_keywords_from_response(response, category)

            logger.info(f"Generated {len(keywords)} keywords for '{category}' using {self.ai_model}")
            return keywords

        except Exception as e:
            logger.warning(f"Failed to generate keywords using {self.ai_model}: {str(e)}")
            raise GenerationError(f"Failed to generate keywords for '{category}' using {self.ai_model}: {e}") from e

    @staticmethod
    def _get_prompt(category: str) -> str:
        return f"""Generate 10-15 search keywords related to "{category}" that would be useful for 
            finding diverse, high-quality images of this concept. 

            Include variations that would work well for image search engines.

            Return ONLY the keywords as a Python list of strings, with no explanation or other text.
            Example format: ["keyword 1", "keyword 2", "keyword 3"]
            """

    def _extract_keywords_from_response(self, response: str, category: str) -> List[str]:
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
            list_pattern = r'\[.*?\]'
            match = re.search(list_pattern, response, re.DOTALL)

            if match:
                # Found a list pattern, try to parse it
                list_str = match.group(0)
                with contextlib.suppress(Exception):
                    # Parse as Python list
                    keywords = eval(list_str)
                    if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
                        return self._clean_and_deduplicate_keywords(keywords, category)

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

            return self._clean_and_deduplicate_keywords(keywords, category)

        except Exception as e:
            logger.warning(f"Error extracting keywords from AI response: {str(e)}")
            # Return at least the category itself
            return [category]

    @staticmethod
    def _clean_and_deduplicate_keywords(keywords: List[str], category: str) -> List[str]:
        """
        Cleans and deduplicates a list of keywords.

        Args:
            keywords (List[str]): The list of keywords to clean.
            category (str): The original category name to ensure it's included.

        Returns:
            List[str]: A cleaned and deduplicated list of keywords.
        """
        # Remove duplicates and empty strings
        keywords = [k.strip() for k in keywords if k and k.strip()]
        keywords = list(dict.fromkeys(keywords))  # Remove duplicates while preserving order

        # Always include the category itself
        if category not in keywords:
            keywords.insert(0, category)

        return keywords


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
        orchestrating keyword processing, image downloading, integrity checks,
        label generation, and report creation.
        """
        # Pre-process all keywords to get accurate totals
        all_keyword_results = {}
        for category_name, keywords in self.categories.items():
            keyword_result = self.keyword_manager.prepare_keywords(category_name, keywords)
            all_keyword_results[category_name] = keyword_result

        # Calculate total work items for progress tracking
        total_keywords = sum(len(result['keywords']) for result in all_keyword_results.values())

        # Generate keyword statistics for reporting
        keyword_stats_ = keyword_stats(all_keyword_results)
        self._record_keyword_statistics(keyword_stats_)

        # Start the download/generation step
        self.progress.start_step("download", total=total_keywords)

        # Process each category with prepared keywords
        for category_name, keyword_result in all_keyword_results.items():
            logger.info(f"Processing category: {category_name}")
            self.progress.start_subtask(f"Category: {category_name}", total=len(keyword_result['keywords']))

            # Record keyword generation in report if any generation occurred
            if keyword_result['generation_occurred']:
                self.report.record_keyword_generation(
                    category_name,
                    keyword_result['original_keywords'],
                    keyword_result['generated_keywords'],
                    self.config.ai_model
                )

            self._process_category(category_name, keyword_result['keywords'])
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

    def _record_keyword_statistics(self, stats: Dict[str, Any]) -> None:
        """
        Records keyword generation statistics in the report.

        Args:
            stats (Dict[str, Any]): Statistics about keyword generation.
        """
        self.report.add_summary(f"Keyword generation statistics:")
        self.report.add_summary(f"  - Total categories: {stats['total_categories']}")
        self.report.add_summary(f"  - Categories with generation: {stats['categories_with_generation']}")
        self.report.add_summary(f"  - Total original keywords: {stats['total_original_keywords']}")
        self.report.add_summary(f"  - Total generated keywords: {stats['total_generated_keywords']}")
        self.report.add_summary(f"  - Total final keywords: {stats['total_final_keywords']}")
        self.report.add_summary(f"  - Generation rate: {stats['generation_rate']:.2%}")

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

        success, count = retry_download(
            keyword=keyword,
            out_dir=str(keyword_path),
            max_num=self.config.max_images,
            max_retries=self.config.max_retries
        )

        # Track results and record in report
        self._track_download_results(download_context, success, count, category_name, keyword)

        # Check and record duplicates
        self.progress.set_subtask_description(f"Checking duplicates: {keyword}")
        check_manager = CheckManager()
        check_manager.duplicates(category_name, keyword, str(keyword_path), self.report)

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

        valid_count, total_count, corrupted_files = image_validator.count_valid(keyword_path)

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


def generate_dataset(config: DatasetGenerationConfig) -> None:
    """
    Generate image dataset based on configuration file.

    Args:
        config: Dataset generation configuration
    """
    generator = DatasetGenerator(config)
    generator.generate()
