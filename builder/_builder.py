"""Unified Builder class for PixCrawler image dataset generation.

This module provides a single, comprehensive Builder class that encapsulates all
functionality from the builder package, making it easy to use across the monorepo.

The Builder class integrates with the enhanced downloader system, providing:
    - Multiple downloader types with registry system
    - Enhanced error handling with phase-specific exceptions
    - Progress tracking and comprehensive reporting
    - Google-style API with proper type safety

Typical usage example:

    from builder import Builder

    # Simple usage with config file
    builder = Builder("config.json")
    results = builder.generate()

    # Advanced usage with custom configuration
    builder = Builder(
        config_path="config.json",
        max_images=50,
        output_dir="./my_dataset",
        downloader_type="multi_engine",
        rate_limit_requests=10
    )
    
    # Configure and generate
    builder.set_keyword_generation(True)
    builder.set_ai_model("gpt4")
    results = builder.generate()
    
    print(f"Generated {results['total_images']} images in {results['duration']:.2f}s")
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from builder._config import DatasetGenerationConfig, get_engines, get_search_variations
from builder._constants import AI_MODELS, KEYWORD_MODE, logger
from builder._downloader import (
    APIDownloader,
    AioHttpDownloader,
    AuthenticationError,
    DownloaderRegistry,
    DuckDuckGoImageDownloader,
    EngineError,
    ImageDownloader,
    NetworkError,
    QuotaExceededError,
    RateLimiter,
    RateLimitError,
    download_images_ddgs,
)
from builder._engine import EngineProcessor
from builder._exceptions import DownloadError, GenerationError, ImageValidationError


# Constants to replace magic numbers and improve maintainability
class BuilderConstants:
    """Constants for Builder configuration and limits."""
    # Search result multipliers
    SEARCH_RESULT_MULTIPLIER_HIGH = 3
    SEARCH_RESULT_MULTIPLIER_MEDIUM = 2
    
    # Retry and timeout settings
    DEFAULT_MAX_RETRIES = 5
    DEFAULT_TIMEOUT_SECONDS = 30
    
    # Worker and thread limits
    DEFAULT_MAX_WORKERS = 4
    MAX_PARALLEL_ENGINES = 4
    DEFAULT_RATE_LIMIT = 8
    
    # File size limits (in bytes)
    MIN_IMAGE_SIZE = 1000  # 1KB minimum
    MAX_IMAGE_SIZE = 50 * 1024 * 1024  # 50MB maximum
    
    # Progress and reporting
    PROGRESS_UPDATE_INTERVAL = 10  # Update progress every N items
    
    # Security settings
    ENABLE_SSL_VERIFICATION = True
    ALLOW_SSL_FALLBACK = False  # Disabled for security
    
    # Validation settings
    VALIDATION_BATCH_SIZE = 100
    
    # Supported image formats
    SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    SUPPORTED_CONTENT_TYPES = ('image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp')


class BuilderError(Exception):
    """Base exception for Builder-specific errors."""
    pass


class ConfigurationPhaseError(BuilderError):
    """Raised when errors occur during configuration phase."""
    
    def __init__(self, message: str, phase: str, original_error: Optional[Exception] = None) -> None:
        """Initialize ConfigurationPhaseError.
        
        Args:
            message: Error message describing the issue.
            phase: Configuration phase where error occurred.
            original_error: Original exception that caused this error.
        """
        super().__init__(f"Configuration error in {phase}: {message}")
        self.phase = phase
        self.original_error = original_error


class DownloadPhaseError(BuilderError):
    """Raised when errors occur during download phase."""
    
    def __init__(self, message: str, keyword: str, downloader_type: str, 
                 original_error: Optional[Exception] = None) -> None:
        """Initialize DownloadPhaseError.
        
        Args:
            message: Error message describing the issue.
            keyword: Keyword being processed when error occurred.
            downloader_type: Type of downloader that failed.
            original_error: Original exception that caused this error.
        """
        super().__init__(f"Download error for '{keyword}' using {downloader_type}: {message}")
        self.keyword = keyword
        self.downloader_type = downloader_type
        self.original_error = original_error


class ValidationPhaseError(BuilderError):
    """Raised when errors occur during validation phase."""
    
    def __init__(self, message: str, directory: str, 
                 original_error: Optional[Exception] = None) -> None:
        """Initialize ValidationPhaseError.
        
        Args:
            message: Error message describing the issue.
            directory: Directory being validated when error occurred.
            original_error: Original exception that caused this error.
        """
        super().__init__(f"Validation error in '{directory}': {message}")
        self.directory = directory
        self.original_error = original_error


class ReportPhaseError(BuilderError):
    """Raised when errors occur during report generation phase."""
    
    def __init__(self, message: str, dataset_dir: str, 
                 original_error: Optional[Exception] = None) -> None:
        """Initialize ReportPhaseError.
        
        Args:
            message: Error message describing the issue.
            dataset_dir: Dataset directory being processed when error occurred.
            original_error: Original exception that caused this error.
        """
        super().__init__(f"Report generation error for '{dataset_dir}': {message}")
        self.dataset_dir = dataset_dir
        self.original_error = original_error


from builder._generator import DatasetGenerator, ConfigManager


def builder_error_handler(func):
    """Decorator for consistent error handling in Builder methods."""
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (ConfigurationPhaseError, DownloadPhaseError, ValidationPhaseError, ReportPhaseError) as e:
            logger.error(f"Phase-specific error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise BuilderError(f"Unexpected error in {func.__name__}: {e}") from e
    return wrapper


class Builder:
    """Unified Builder class for PixCrawler image dataset generation.

    This class provides a comprehensive interface for generating image datasets,
    combining all functionality from the builder package into a single, easy-to-use class.

    The Builder integrates with the enhanced downloader system, providing multiple
{{ ... }}
        downloader_instance: Current downloader instance.
        dataset_generator: Internal dataset generator instance.
        engine_processor: Engine processor for multi-engine downloads.
        report_generator: Report generator instance.
        progress_manager: Progress tracking manager.
    """

    def __init__(
        self,
        config_path: str,
        max_images: int = 10,
        output_dir: Optional[str] = None,
        integrity: bool = True,
        max_retries: int = BuilderConstants.DEFAULT_MAX_RETRIES,
        continue_from_last: bool = False,
        cache_file: str = "progress_cache.json",
        keyword_generation: KEYWORD_MODE = "auto",
        ai_model: AI_MODELS = "gpt4-mini",
        generate_labels: bool = True,
        downloader_type: str = "multi_engine",
        rate_limit_requests: int = BuilderConstants.DEFAULT_RATE_LIMIT,
        max_workers: int = BuilderConstants.DEFAULT_MAX_WORKERS
    ):
        """Initialize the Builder with configuration options.

        Args:
            config_path: Path to the JSON configuration file.
            max_images: Maximum number of images to download per keyword.
            output_dir: Custom output directory (None uses dataset_name from config).
            integrity: Whether to perform image integrity checks.
            max_retries: Maximum number of retry attempts for failed downloads.
            continue_from_last: Whether to continue from the last incomplete run.
            cache_file: Path to the progress cache file.
            keyword_generation: Keyword generation mode ('disabled', 'enabled', 'auto').
            ai_model: AI model to use for keyword generation ('gpt4', 'gpt4-mini').
            generate_labels: Whether to generate label files for images.
            downloader_type: Type of downloader to use ('duckduckgo', 'multi_engine', 'api', 'aiohttp').
            rate_limit_requests: Maximum requests per second for rate limiting.
            max_workers: Maximum number of parallel download workers.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            ValueError: If configuration parameters are invalid.
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

        # Store downloader configuration
        self.downloader_type = downloader_type
        self.rate_limit_requests = rate_limit_requests
        self.max_workers = max_workers
        
        # Initialize internal components
        self.dataset_generator: Optional[DatasetGenerator] = None
        self.engine_processor: Optional[EngineProcessor] = None
        self.report_generator: Optional[ReportGenerator] = None
        self.progress_manager: Optional[ProgressManager] = None
        self.downloader_instance: Optional[Any] = None
        
        # Initialize downloader registry and create downloader instance
        self._setup_downloader()

        # Load and validate configuration
        self._load_config()

        logger.info(f"Builder initialized with config: {config_path}")

    @builder_error_handler
    def _setup_downloader(self) -> None:
        """Setup the downloader instance based on configuration with enhanced error handling."""
        try:
            # Get downloader class from registry
            downloader_class = DownloaderRegistry.get_downloader(self.downloader_type)
            
            if not downloader_class:
                logger.warning(f"Downloader '{self.downloader_type}' not found in registry, using DuckDuckGo as fallback")
                downloader_class = DuckDuckGoImageDownloader
                self.downloader_type = "duckduckgo"
            
            # Create downloader instance with appropriate parameters
            if self.downloader_type == "duckduckgo":
                self.downloader_instance = downloader_class(
                    max_workers=self.max_workers,
                    max_retries=self.config.max_retries,
                    rate_limit_requests=self.rate_limit_requests
                )
            elif self.downloader_type == "multi_engine":
                self.downloader_instance = downloader_class(
                    downloader_threads=self.max_workers,
                    max_parallel_engines=BuilderConstants.MAX_PARALLEL_ENGINES,
                    use_all_engines=True
                )
            else:
                # For API and AioHttp downloaders (placeholders)
                self.downloader_instance = downloader_class()
            
            logger.info(f"Downloader setup completed: {self.downloader_type}")
            
        except Exception as e:
            logger.error(f"Failed to setup downloader: {e}")
            # Fallback to DuckDuckGo downloader
            self.downloader_instance = DuckDuckGoImageDownloader(
                max_workers=self.max_workers,
                max_retries=self.config.max_retries,
                rate_limit_requests=self.rate_limit_requests
            )
            self.downloader_type = "duckduckgo"
            logger.info("Using DuckDuckGo downloader as fallback")

    @builder_error_handler
    def _load_config(self) -> None:
        """Load and validate the dataset configuration with comprehensive error handling."""
        try:
            config_manager = ConfigManager(self.config.config_path)
            self.dataset_config = config_manager

            # Update config with dataset name from file
            if 'dataset_name' in config_manager:
                self.config.dataset_name = config_manager['dataset_name']

            logger.info(f"Configuration loaded successfully: {self.config.dataset_name}")
        except FileNotFoundError as e:
            raise ConfigurationPhaseError(
                f"Configuration file not found: {self.config.config_path}",
                "config_loading",
                e
            ) from e
        except Exception as e:
            raise ConfigurationPhaseError(
                f"Failed to parse configuration file: {str(e)}",
                "config_parsing",
                e
            ) from e

    @builder_error_handler
    def generate(self) -> Dict[str, Any]:
        """Generate the complete image dataset with enhanced progress tracking and error recovery.

        This is the main entry point that orchestrates the entire dataset generation process:
        1. Initialize progress tracking and reporting
        2. Initialize the dataset generator
        3. Process all categories and keywords with progress updates
        4. Perform integrity checks (if enabled)
        5. Generate labels (if enabled)
        6. Create comprehensive reports

        Returns:
            Dictionary containing generation results and statistics.

        Raises:
            ConfigurationPhaseError: If configuration setup fails.
            GenerationError: If dataset generation fails.
        """
        generation_start_time = time.time()
        results = {
            'success': False,
            'total_images': 0,
            'categories_processed': 0,
            'keywords_processed': 0,
            'errors': [],
            'duration': 0,
            'report_path': None
        }
        
        try:
            logger.info("Starting dataset generation with enhanced tracking...")

            # Initialize progress manager
            dataset_info = self.dataset_info()
            total_keywords = dataset_info.get('total_keywords', 0)
            
            if total_keywords == 0:
                raise ConfigurationPhaseError(
                    "No keywords found in configuration",
                    "dataset_validation"
                )
            
            self.progress_manager = ProgressManager(
                total_items=total_keywords,
                description="Dataset Generation"
            )
            
            # Initialize dataset generator with progress callback
            try:
                self.dataset_generator = DatasetGenerator(self.config)
                logger.info(f"Dataset generator initialized for {dataset_info['dataset_name']}")
            except Exception as e:
                raise ConfigurationPhaseError(
                    f"Failed to initialize dataset generator: {str(e)}",
                    "generator_initialization",
                    e
                ) from e

            # Start generation process with progress tracking
            try:
                self.progress_manager.start()
                generation_results = self.dataset_generator.generate()
                
                # Update results
                results.update({
                    'success': True,
                    'total_images': generation_results.get('total_downloaded', 0),
                    'categories_processed': len(dataset_info.get('categories', [])),
                    'keywords_processed': total_keywords
                })
                
            except Exception as e:
                results['errors'].append(f"Generation failed: {str(e)}")
                raise GenerationError(f"Dataset generation failed: {e}") from e
            finally:
                if self.progress_manager:
                    self.progress_manager.finish()

            # Generate comprehensive report
            if self.config.output_dir:
                try:
                    report_path = self.generate_report(self.config.output_dir)
                    results['report_path'] = report_path
                    logger.info(f"Generation report created: {report_path}")
                except Exception as e:
                    results['errors'].append(f"Report generation failed: {str(e)}")
                    logger.warning(f"Failed to generate report: {e}")

            # Calculate duration
            results['duration'] = time.time() - generation_start_time
            
            logger.info(f"Dataset generation completed successfully in {results['duration']:.2f}s!")
            logger.info(f"Results: {results['total_images']} images, {results['categories_processed']} categories")
            
            return results

        except (ConfigurationPhaseError, GenerationError):
            results['duration'] = time.time() - generation_start_time
            raise
        except Exception as e:
            results['duration'] = time.time() - generation_start_time
            results['errors'].append(f"Unexpected error: {str(e)}")
            logger.error(f"Dataset generation failed: {e}")
            raise GenerationError(f"Failed to generate dataset: {e}") from e

    @builder_error_handler
    def download(
        self,
        keyword: str,
        output_dir: str,
        max_count: int = None,
        use_fallback: bool = True
    ) -> int:
        """Download images for a specific keyword with enhanced security and error handling.

        Args:
            keyword: Search keyword.
            output_dir: Output directory for downloaded images.
            max_count: Maximum number of images to download (uses config default if None).
            use_fallback: Whether to use DuckDuckGo as fallback if primary downloader fails.

        Returns:
            Number of images successfully downloaded.

        Raises:
            DownloadError: If download process fails.
        """
        try:
            max_count = max_count or self.config.max_images
            
            # Enhanced input validation with security checks
            if not keyword or not keyword.strip():
                raise ValueError("Keyword cannot be empty")
            if max_count <= 0:
                raise ValueError("max_count must be greater than 0")
            if max_count > 1000:  # Prevent excessive downloads
                logger.warning(f"Large download request: {max_count} images for '{keyword}'")
                max_count = min(max_count, 1000)
            
            # Validate output directory path for security
            output_path = Path(output_dir).resolve()
            if not str(output_path).startswith(str(Path.cwd().resolve())):
                logger.warning(f"Output directory outside current working directory: {output_dir}")

            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading {max_count} images for '{keyword}' using {self.downloader_type} downloader")

            try:
                # Use the configured downloader instance
                success, downloaded = self.downloader_instance.download(keyword, output_dir, max_count)
                
                if success and downloaded > 0:
                    logger.info(f"Successfully downloaded {downloaded} images for '{keyword}' (requested: {max_count})")
                    
                    # Rename images sequentially for better organization
                    if downloaded > 1:
                        try:
                            rename_images_sequentially(output_dir)
                            logger.info(f"Renamed {downloaded} images sequentially")
                        except Exception as e:
                            logger.warning(f"Failed to rename images sequentially: {e}")
                    
                    return downloaded
                else:
                    logger.warning(f"Primary downloader failed for '{keyword}', downloaded: {downloaded}")
                    
                    # Try fallback if enabled and primary failed
                    if use_fallback and self.downloader_type != "duckduckgo":
                        return self._fallback_download(keyword, output_dir, max_count)
                    
                    return downloaded
                    
            except (NetworkError, EngineError, RateLimitError) as e:
                logger.warning(f"Downloader error for '{keyword}': {e}")
                
                # Try fallback on specific errors if enabled
                if use_fallback and self.downloader_type != "duckduckgo":
                    return self._fallback_download(keyword, output_dir, max_count)
                else:
                    raise DownloadPhaseError(
                        f"Primary downloader failed: {str(e)}",
                        keyword,
                        self.downloader_type,
                        e
                    ) from e

        except ValueError as e:
            raise DownloadPhaseError(
                f"Invalid parameters: {str(e)}",
                keyword,
                self.downloader_type,
                e
            ) from e
        except Exception as e:
            logger.error(f"Image download failed for '{keyword}': {e}")
            raise DownloadPhaseError(
                f"Unexpected download error: {str(e)}",
                keyword,
                self.downloader_type,
                e
            ) from e
    
    def _fallback_download(self, keyword: str, output_dir: str, max_count: int) -> int:
        """Fallback download using DuckDuckGo downloader.
        
        Args:
            keyword: Search keyword.
            output_dir: Output directory for downloaded images.
            max_count: Maximum number of images to download.
            
        Returns:
            Number of images successfully downloaded.
        """
        try:
            logger.info(f"Using DuckDuckGo fallback for '{keyword}'")
            
            # Use the direct function for fallback
            success, downloaded = download_images_ddgs(keyword, output_dir, max_count)
            
            if success and downloaded > 0:
                logger.info(f"Fallback download successful: {downloaded} images for '{keyword}'")
                
                # Rename images sequentially
                if downloaded > 1:
                    rename_images_sequentially(output_dir)
                
                return downloaded
            else:
                logger.warning(f"Fallback download also failed for '{keyword}'")
                return 0
                
        except Exception as e:
            logger.error(f"Fallback download failed for '{keyword}': {e}")
            return 0

    @staticmethod
    def validate(directory: str, remove_invalid: bool = True) -> Dict[str, Any]:
        """Validate integrity of images in a directory.

        Args:
            directory: Directory containing images to validate.
            remove_invalid: Whether to remove invalid images.

        Returns:
            Validation results with statistics.

        Raises:
            ValidationPhaseError: If validation process fails.
        """
        try:
            if not os.path.exists(directory):
                raise ValidationPhaseError(
                    f"Directory does not exist: {directory}",
                    directory
                )
            
            logger.info(f"Validating images in: {directory}")

            results = image_validator(directory, remove_invalid=remove_invalid)

            logger.info(f"Validation completed: {results}")
            return results

        except ValidationPhaseError:
            raise
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            raise ValidationPhaseError(
                f"Validation process failed: {str(e)}",
                directory,
                e
            ) from e

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
        """Generate a comprehensive report for the dataset.

        Args:
            dataset_dir: Directory containing the dataset.

        Returns:
            Path to the generated report file.

        Raises:
            ReportPhaseError: If report generation fails.
        """
        try:
            if not os.path.exists(dataset_dir):
                raise ReportPhaseError(
                    f"Dataset directory does not exist: {dataset_dir}",
                    dataset_dir
                )
            
            logger.info(f"Generating report for dataset: {dataset_dir}")

            self.report_generator = ReportGenerator(dataset_dir)
            self.report_generator.generate()
            report_path = self.report_generator.report_file

            logger.info(f"Report generated: {report_path}")
            return report_path

        except ReportPhaseError:
            raise
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise ReportPhaseError(
                f"Report generation process failed: {str(e)}",
                dataset_dir,
                e
            ) from e

    def set_ai_model(self, model: AI_MODELS) -> None:
        """Set the AI model for keyword generation.

        Args:
            model: AI model to use ('gpt4', 'gpt4-mini').
        """
        self.config.ai_model = model
        logger.info(f"AI model set to: {model}")

    def set_keyword_generation(self, mode: Union[KEYWORD_MODE, bool]) -> None:
        """Configure AI-powered keyword generation.

        Args:
            mode: Keyword generation mode. Can be:
                - KEYWORD_MODE: 'enabled', 'auto', 'disabled'
                - bool: True for 'enabled', False for 'disabled'
                
        Raises:
            ValueError: If mode is invalid.
        """
        if isinstance(mode, bool):
            mode = "enabled" if mode else "disabled"
        
        if mode not in ["enabled", "auto", "disabled"]:
            raise ValueError(f"Invalid keyword generation mode: {mode}")
        
        self.config.keyword_generation = mode
        logger.info(f"Keyword generation set to: {mode}")

    def set_max_images(self, max_images: int) -> None:
        """Set the maximum number of images per keyword.

        Args:
            max_images: Maximum number of images to download per keyword.
            
        Raises:
            ValueError: If max_images is not positive.
        """
        if max_images <= 0:
            raise ValueError("max_images must be greater than 0")

        self.config.max_images = max_images
        logger.info(f"Max images per keyword set to: {max_images}")

    def set_output_directory(self, output_dir: str) -> None:
        """Set the output directory for the dataset.

        Args:
            output_dir: Path to the output directory.
            
        Raises:
            ValueError: If output_dir is empty or invalid.
        """
        if not output_dir or not output_dir.strip():
            raise ValueError("Output directory cannot be empty")
        
        self.config.output_dir = output_dir
        logger.info(f"Output directory set to: {output_dir}")

    def set_integrity_checking(self, enabled: bool) -> None:
        """Configure image integrity checking.

        Args:
            enabled: Whether to enable integrity checking.
        """
        self.config.integrity = enabled
        logger.info(f"Image integrity checking: {'enabled' if enabled else 'disabled'}")

    def set_label_generation(self, enabled: bool) -> None:
        """Configure label file generation.

        Args:
            enabled: Whether to enable label generation.
        """
        self.config.generate_labels = enabled
        logger.info(f"Label generation: {'enabled' if enabled else 'disabled'}")

    def switch_downloader(self, downloader_type: str) -> None:
        """Switch to a different downloader type.
        
        Args:
            downloader_type: Type of downloader ('duckduckgo', 'multi_engine', 'api', 'aiohttp').
            
        Raises:
            ValueError: If downloader type is invalid.
        """
        if downloader_type not in ['duckduckgo', 'multi_engine', 'api', 'aiohttp']:
            raise ValueError(f"Invalid downloader type: {downloader_type}")
        
        old_type = self.downloader_type
        self.downloader_type = downloader_type
        
        try:
            self._setup_downloader()
            logger.info(f"Switched from {old_type} to {downloader_type} downloader")
        except Exception as e:
            # Rollback on failure
            self.downloader_type = old_type
            self._setup_downloader()
            logger.error(f"Failed to switch downloader: {e}")
            raise ValueError(f"Failed to switch to {downloader_type}: {e}") from e

    def get_downloader_info(self) -> Dict[str, Any]:
        """Get information about the current downloader.
        
        Returns:
            Dictionary containing downloader information and capabilities.
        """
        if not self.downloader_instance:
            return {'error': 'No downloader instance available'}
        
        try:
            info = self.downloader_instance.get_downloader_info()
            info.update({
                'type': self.downloader_type,
                'max_workers': self.max_workers,
                'rate_limit_requests': self.rate_limit_requests,
                'max_retries': self.config.max_retries
            })
            return info
        except Exception as e:
            return {'error': f'Failed to get downloader info: {e}'}

    def list_available_downloaders(self) -> Dict[str, Dict[str, str]]:
        """List all available downloaders in the registry.
        
        Returns:
            Dictionary of available downloaders with their information.
        """
        return DownloaderRegistry.list_downloaders()

    def get_downloader_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of the current downloader.
        
        Returns:
            Dictionary containing downloader capabilities.
        """
        info = self.get_downloader_info()
        return {
            'current_downloader': self.downloader_type,
            'max_workers': self.max_workers,
            'rate_limit': self.rate_limit_requests,
            'max_retries': self.config.max_retries,
            'supports_fallback': True,
            'supports_retry': True,
            'supports_rate_limiting': True,
            'downloader_info': info
        }

    def batch_download(
        self, 
        keywords: List[str], 
        base_output_dir: str, 
        max_count_per_keyword: int = None
    ) -> Dict[str, int]:
        """Download images for multiple keywords in batch.
        
        Args:
            keywords: List of search keywords.
            base_output_dir: Base output directory (subdirectories created per keyword).
            max_count_per_keyword: Maximum images per keyword (uses config default if None).
            
        Returns:
            Dictionary mapping keywords to number of downloaded images.
        """
        max_count_per_keyword = max_count_per_keyword or self.config.max_images
        results = {}
        
        logger.info(f"Starting batch download for {len(keywords)} keywords")
        
        for i, keyword in enumerate(keywords, 1):
            try:
                # Create keyword-specific output directory
                keyword_dir = Path(base_output_dir) / keyword.replace(' ', '_').replace('/', '_')
                
                logger.info(f"Processing keyword {i}/{len(keywords)}: '{keyword}'")
                
                downloaded = self.download(keyword, str(keyword_dir), max_count_per_keyword)
                results[keyword] = downloaded
                
                logger.info(f"Completed '{keyword}': {downloaded} images")
                
            except Exception as e:
                logger.error(f"Failed to download for '{keyword}': {e}")
                results[keyword] = 0
        
        total_downloaded = sum(results.values())
        logger.info(f"Batch download completed: {total_downloaded} total images across {len(keywords)} keywords")
        
        return results

    def configure_rate_limiting(self, requests_per_second: int) -> None:
        """Configure rate limiting for the downloader.
        
        Args:
            requests_per_second: Maximum requests per second.
        """
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be greater than 0")
        
        self.rate_limit_requests = requests_per_second
        
        # Recreate downloader instance with new rate limit
        self._setup_downloader()
        
        logger.info(f"Rate limiting configured to {requests_per_second} requests/second")

    def configure_workers(self, max_workers: int) -> None:
        """Configure maximum number of parallel workers.
        
        Args:
            max_workers: Maximum number of parallel workers.
        """
        if max_workers <= 0:
            raise ValueError("max_workers must be greater than 0")
        
        self.max_workers = max_workers
        
        # Recreate downloader instance with new worker count
        self._setup_downloader()
        
        logger.info(f"Max workers configured to {max_workers}")

    def dataset_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded dataset configuration.
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