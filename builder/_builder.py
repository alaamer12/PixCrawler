"""
Unified Builder class for PixCrawler image dataset generation.

This module provides a single, comprehensive Builder class that encapsulates all
functionality from the builder package, making it easy to use across the monorepo.

Classes:
    Builder: Main class that provides a unified interface for all dataset generation functionality.

Example:
    ```python
    from builder import Builder

    # Simple usage with config file
    builder = Builder("config.json")
    builder.generate()

    # Advanced usage with custom configuration
    builder = Builder(
        config_path="config.json",
        max_images=50,
        output_dir="./my_dataset",
        integrity=True,
        generate_labels=True
    )
    builder.generate()

    # Custom keyword generation
    builder.set_ai_model("gpt4")
    builder.enable_keyword_generation()
    builder.generate()
    ```
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from builder._config import DatasetGenerationConfig, get_engines, get_search_variations
from builder._constants import logger, KEYWORD_MODE, AI_MODELS
from builder._downloader import DuckDuckGoImageDownloader
from builder._engine import EngineProcessor
from builder._exceptions import (
    DownloadError,
    ImageValidationError,
    GenerationError
)
from builder._generator import DatasetGenerator, ConfigManager
from builder._helpers import ReportGenerator, ProgressManager
from builder._utilities import image_validator

__all__ = ['Builder']


class Builder:
    """
    Unified Builder class for PixCrawler image dataset generation.

    This class provides a comprehensive interface for generating image datasets,
    combining all functionality from the builder package into a single, easy-to-use class.

    Features:
        - Dataset generation with multiple search engines
        - AI-powered keyword generation
        - Image integrity checking
        - Label file generation
        - Progress tracking and resumption
        - Comprehensive reporting
        - Customizable configuration

    Attributes:
        config (DatasetGenerationConfig): Configuration object for dataset generation
        dataset_generator (DatasetGenerator): Internal dataset generator instance
        engine_processor (EngineProcessor): Engine processor for multi-engine downloads
        report_generator (ReportGenerator): Report generator instance
        progress_manager (ProgressManager): Progress tracking manager
    """

    def __init__(
        self,
        config_path: str,
        max_images: int = 10,
        output_dir: Optional[str] = None,
        integrity: bool = True,
        max_retries: int = 5,
        continue_from_last: bool = False,
        cache_file: str = "progress_cache.json",
        keyword_generation: KEYWORD_MODE = "auto",
        ai_model: AI_MODELS = "gpt4-mini",
        generate_labels: bool = True
    ):
        """
        Initialize the Builder with configuration options.

        Args:
            config_path (str): Path to the JSON configuration file
            max_images (int): Maximum number of images to download per keyword
            output_dir (Optional[str]): Custom output directory (None uses dataset_name from config)
            integrity (bool): Whether to perform image integrity checks
            max_retries (int): Maximum number of retry attempts for failed downloads
            continue_from_last (bool): Whether to continue from the last incomplete run
            cache_file (str): Path to the progress cache file
            keyword_generation (KEYWORD_MODE): Keyword generation mode ('disabled', 'enabled', 'auto')
            ai_model (AI_MODELS): AI model to use for keyword generation ('gpt4', 'gpt4-mini')
            generate_labels (bool): Whether to generate label files for images

        Raises:
            FileNotFoundError: If the config file doesn't exist
            ValueError: If configuration parameters are invalid
        """
        # Validate config file exists
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Create configuration object
        self.config = DatasetGenerationConfig(
            config_path=config_path,
            max_images=max_images,
            output_dir=output_dir,
            integrity=integrity,
            max_retries=max_retries,
            continue_from_last=continue_from_last,
            cache_file=cache_file,
            keyword_generation=keyword_generation,
            ai_model=ai_model,
            generate_labels=generate_labels
        )

        # Initialize internal components
        self.dataset_generator: Optional[DatasetGenerator] = None
        self.engine_processor: Optional[EngineProcessor] = None
        self.report_generator: Optional[ReportGenerator] = None
        self.progress_manager: Optional[ProgressManager] = None

        # Load and validate configuration
        self._load_config()

        logger.info(f"Builder initialized with config: {config_path}")

    def _load_config(self) -> None:
        """Load and validate the dataset configuration."""
        try:
            config_manager = ConfigManager(self.config.config_path)
            self.dataset_config = config_manager

            # Update config with dataset name from file
            if 'dataset_name' in config_manager:
                self.config.dataset_name = config_manager['dataset_name']

            logger.info(f"Configuration loaded successfully: {self.config.dataset_name}")
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}") from e

    def generate(self) -> None:
        """
        Generate the complete image dataset.

        This is the main entry point that orchestrates the entire dataset generation process:
        1. Initialize the dataset generator
        2. Process all categories and keywords
        3. Download images from multiple search engines
        4. Perform integrity checks (if enabled)
        5. Generate labels (if enabled)
        6. Create comprehensive reports

        Raises:
            GenerationError: If dataset generation fails
        """
        try:
            logger.info("Starting dataset generation...")

            # Initialize dataset generator
            self.dataset_generator = DatasetGenerator(self.config)

            # Start generation process
            self.dataset_generator.generate()

            logger.info("Dataset generation completed successfully!")

        except Exception as e:
            logger.error(f"Dataset generation failed: {e}")
            raise GenerationError(f"Failed to generate dataset: {e}") from e

    def download(
        self,
        keyword: str,
        output_dir: str,
        max_count: int = None,
        engines: List[str] = None
    ) -> int:
        """
        Download images for a specific keyword using multiple search engines.

        Args:
            keyword (str): Search keyword
            output_dir (str): Output directory for downloaded images
            max_count (int): Maximum number of images to download (uses config default if None)
            engines (List[str]): List of engines to use (uses all available if None)

        Returns:
            int: Number of images successfully downloaded

        Raises:
            DownloadError: If download process fails
        """
        try:
            max_count = max_count or self.config.max_images
            engines = engines or [engine['name'] for engine in get_engines()]

            # Initialize engine processor if not already done
            if not self.engine_processor:
                # Create a dummy image downloader for the engine processor
                from builder._downloader import ImageDownloader
                image_downloader = ImageDownloader()
                self.engine_processor = EngineProcessor(image_downloader)

            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading {max_count} images for '{keyword}' using engines: {engines}")

            total_downloaded = 0
            for engine in engines:
                try:
                    # Use DuckDuckGo downloader for now (can be extended for other engines)
                    if engine.lower() == 'duckduckgo':
                        downloader = DuckDuckGoImageDownloader()
                        success, downloaded = downloader.download(keyword, output_dir, max_count)
                        if success:
                            total_downloaded += downloaded
                            logger.info(f"Downloaded {downloaded} images from {engine}")
                        else:
                            logger.warning(f"Failed to download from {engine}")
                except Exception as e:
                    logger.warning(f"Failed to download from {engine}: {e}")
                    continue

            logger.info(f"Total downloaded: {total_downloaded} images for '{keyword}'")
            return total_downloaded

        except Exception as e:
            logger.error(f"Image download failed: {e}")
            raise DownloadError(f"Failed to download images for '{keyword}': {e}") from e

    @staticmethod
    def validate(directory: str, remove_invalid: bool = True) -> Dict[str, Any]:
        """
        Validate integrity of images in a directory.

        Args:
            directory (str): Directory containing images to validate
            remove_invalid (bool): Whether to remove invalid images

        Returns:
            Dict[str, Any]: Validation results with statistics

        Raises:
            ImageValidationError: If validation process fails
        """
        try:
            logger.info(f"Validating images in: {directory}")

            results = image_validator(directory, remove_invalid=remove_invalid)

            logger.info(f"Validation completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            raise ImageValidationError(f"Failed to validate images: {e}") from e

    @staticmethod
    def generate_labels(dataset_dir: str, formats: List[str] = None) -> None:
        """
        Generate label files for the dataset.

        Args:
            dataset_dir (str): Directory containing the dataset
            formats (List[str]): List of label formats to generate ('txt', 'json', 'csv', 'yaml')

        Raises:
            GenerationError: If label generation fails
        """
        try:
            from builder._generator import LabelGenerator

            formats = formats or ['txt', 'json', 'csv', 'yaml']

            logger.info(f"Generating labels in formats: {formats}")

            label_generator = LabelGenerator()
            label_generator.generate_dataset_labels(dataset_dir)

            logger.info("Label generation completed successfully!")

        except Exception as e:
            logger.error(f"Label generation failed: {e}")
            raise GenerationError(f"Failed to generate labels: {e}") from e

    def generate_report(self, dataset_dir: str) -> str:
        """
        Generate a comprehensive report for the dataset.

        Args:
            dataset_dir (str): Directory containing the dataset

        Returns:
            str: Path to the generated report file

        Raises:
            GenerationError: If report generation fails
        """
        try:
            logger.info(f"Generating report for dataset: {dataset_dir}")

            self.report_generator = ReportGenerator(dataset_dir)
            self.report_generator.generate()
            report_path = self.report_generator.report_file

            logger.info(f"Report generated: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise GenerationError(f"Failed to generate report: {e}") from e

    def set_ai_model(self, model: AI_MODELS) -> None:
        """
        Set the AI model for keyword generation.

        Args:
            model (AI_MODELS): AI model to use ('gpt4', 'gpt4-mini')
        """
        self.config.ai_model = model
        logger.info(f"AI model set to: {model}")

    def enable_kwgen(self, mode: KEYWORD_MODE = "enabled") -> None:
        """
        Enable AI-powered keyword generation.

        Args:
            mode (KEYWORD_MODE): Keyword generation mode ('enabled', 'auto', 'disabled')
        """
        self.config.keyword_generation = mode
        logger.info(f"Keyword generation set to: {mode}")

    def disable_keyword_generation(self) -> None:
        """Disable AI-powered keyword generation."""
        self.config.keyword_generation = "disabled"
        logger.info("Keyword generation disabled")

    def set_maxi(self, max_images: int) -> None:
        """
        Set the maximum number of images per keyword.

        Args:
            max_images (int): Maximum number of images to download per keyword
        """
        if max_images <= 0:
            raise ValueError("max_images must be greater than 0")

        self.config.max_images = max_images
        logger.info(f"Max images per keyword set to: {max_images}")

    def set_outdir(self, output_dir: str) -> None:
        """
        Set the output directory for the dataset.

        Args:
            output_dir (str): Path to the output directory
        """
        self.config.output_dir = output_dir
        logger.info(f"Output directory set to: {output_dir}")

    def enable_integrity(self, enabled: bool = True) -> None:
        """
        Enable or disable image integrity checking.

        Args:
            enabled (bool): Whether to enable integrity checking
        """
        self.config.integrity = enabled
        logger.info(f"Image integrity checking: {'enabled' if enabled else 'disabled'}")

    def enable_label_generation(self, enabled: bool = True) -> None:
        """
        Enable or disable label file generation.

        Args:
            enabled (bool): Whether to enable label generation
        """
        self.config.generate_labels = enabled
        logger.info(f"Label generation: {'enabled' if enabled else 'disabled'}")

    def dataset_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded dataset configuration.

        Returns:
            Dict[str, Any]: Dataset information including name, categories, etc.
        """
        if not hasattr(self, 'dataset_config'):
            return {}

        return {
            'dataset_name': self.dataset_config['dataset_name'] if 'dataset_name' in self.dataset_config else '',
            'categories': list(self.dataset_config['categories'].keys()) if 'categories' in self.dataset_config else [],
            'category_count': len(self.dataset_config['categories']) if 'categories' in self.dataset_config else 0,
            'total_keywords': sum(
                len(keywords) for keywords in self.dataset_config['categories'].values()
            ) if 'categories' in self.dataset_config else 0
        }

    @staticmethod
    def available_engines() -> List[str]:
        """
        Get list of available search engines.

        Returns:
            List[str]: List of available engine names
        """
        return [engine['name'] for engine in get_engines()]

    @staticmethod
    def search_variations() -> List[str]:
        """
        Get list of available search variations.

        Returns:
            List[str]: List of search variation templates
        """
        return get_search_variations()

    def __str__(self) -> str:
        """String representation of the Builder."""
        info = self.dataset_info()
        return (
            f"Builder(dataset='{info.get('dataset_name', 'Unknown')}', "
            f"categories={info.get('category_count', 0)}, "
            f"max_images={self.config.max_images})"
        )

    def __repr__(self) -> str:
        """Detailed representation of the Builder."""
        return (
            f"Builder(config_path='{self.config.config_path}', "
            f"max_images={self.config.max_images}, "
            f"output_dir='{self.config.output_dir}', "
            f"integrity={self.config.integrity}, "
            f"keyword_generation='{self.config.keyword_generation}', "
            f"ai_model='{self.config.ai_model}', "
            f"generate_labels={self.config.generate_labels})"
        )
