"""
<<<<<<< HEAD
Celery tasks for PixCrawler builder package using celery_core.

This module provides celery-compatible task definitions for background processing
of image crawling, keyword generation, and label creation using the centralized
celery_core package for task management.

Tasks:
    task_build: Main build task for processing datasets
    task_crawl_images: Background task for image crawling
    task_generate_keywords: Background task for AI keyword generation
    task_generate_labels: Background task for label file generation
    task_process_category: Background task for processing a single category
"""

from typing import Dict, List, Any, Optional
from pathlib import Path

from celery_core.base import BaseTask
from celery_core.app import get_celery_app
from utility.logging_config import get_logger

logger = get_logger(__name__)

# Get the shared Celery app from celery_core
app = get_celery_app()

__all__ = [
    'task_build',
    'task_crawl_images',
    'task_generate_keywords',
    'task_generate_labels',
    'task_process_category'
]


def task_build_impl(keyword: str, output_dir: str, max_images: int = 10,
                   engines: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Implementation for the main build task.

    This function performs the core image crawling and dataset building functionality
    using the builder package's internal modules.

    Args:
        keyword: Search keyword for image crawling
        output_dir: Directory to save downloaded images
        max_images: Maximum number of images to download
        engines: List of search engines to use (optional)

    Returns:
        Dict containing build results and metadata
    """
    logger.info(f"Starting build task for keyword: {keyword}")

    try:
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Import builder modules
        from builder._engine import EngineProcessor
        from builder._downloader import ImageDownloader, DuckDuckGoImageDownloader
        from builder._config import get_engines

        # Get available engines
        available_engines = get_engines()
        if not engines:
            engines = [engine['name'] for engine in available_engines]

        results = {
            'keyword': keyword,
            'output_dir': output_dir,
            'max_images': max_images,
            'engines_used': engines,
            'downloads': {},
            'total_downloaded': 0,
            'success': False,
            'errors': []
        }

        total_downloaded = 0

        # Use EngineProcessor for multi-engine support
        image_downloader = ImageDownloader()
        engine_processor = EngineProcessor(image_downloader)

        for engine_name in engines:
            try:
                logger.info(f"Processing engine: {engine_name}")

                if engine_name.lower() == 'duckduckgo':
                    # Use DuckDuckGo downloader as fallback
                    ddg_downloader = DuckDuckGoImageDownloader()
                    success, downloaded = ddg_downloader.download(
                        keyword, output_dir, max_images
                    )

                    results['downloads'][engine_name] = {
                        'success': success,
                        'downloaded': downloaded,
                        'method': 'duckduckgo_direct'
                    }

                    if success:
                        total_downloaded += downloaded

                else:
                    # Use engine processor for other engines (Google, Bing, Baidu)
                    engine_config = next(
                        (e for e in available_engines
                         if e['name'].lower() == engine_name.lower()),
                        None
                    )

                    if engine_config:
                        # Process single engine
                        engine_result = engine_processor.process_single_engine(
                            keyword=keyword,
                            output_dir=output_dir,
                            engine_config=engine_config,
                            max_images=max_images
                        )

                        downloaded = (
                            engine_result.total_downloaded
                            if hasattr(engine_result, 'total_downloaded')
                            else 0
                        )
                        success = downloaded > 0

                        results['downloads'][engine_name] = {
                            'success': success,
                            'downloaded': downloaded,
                            'method': 'engine_processor'
                        }

                        total_downloaded += downloaded
                    else:
                        logger.warning(f"Engine {engine_name} not found in configuration")
                        results['downloads'][engine_name] = {
                            'success': False,
                            'downloaded': 0,
                            'error': 'Engine not found'
                        }

            except Exception as e:
                error_msg = f"Failed to process engine {engine_name}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['downloads'][engine_name] = {
                    'success': False,
                    'downloaded': 0,
                    'error': str(e)
                }

        results['total_downloaded'] = total_downloaded
        results['success'] = total_downloaded > 0

        logger.info(f"Build task completed for {keyword}: {total_downloaded} images downloaded")
        return results

    except Exception as e:
        error_msg = f"Build task failed for {keyword}: {str(e)}"
        logger.error(error_msg)
        return {
            'keyword': keyword,
            'success': False,
            'error': error_msg,
            'total_downloaded': 0
        }


@app.task(bind=True, base=BaseTask, name='builder.task_build')
def task_build(self, keyword: str, output_dir: str, max_images: int = 10,
               engines: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Main build task for processing datasets.

    This is the primary Celery task for building image datasets using the
    builder package functionality.

    Args:
        keyword: Search keyword for image crawling
        output_dir: Directory to save downloaded images
        max_images: Maximum number of images to download
        engines: List of search engines to use (optional)

    Returns:
        Dict containing build results and metadata
    """
    return task_build_impl(keyword, output_dir, max_images, engines)


def task_crawl_images_impl(keyword: str, output_dir: str, max_images: int = 10,
                          engines: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Implementation for crawling images using all available engines.

    Args:
        keyword: Search keyword for image crawling
        output_dir: Directory to save downloaded images
        max_images: Maximum number of images to download
        engines: List of search engines to use (optional)

    Returns:
        Dict containing crawl results and metadata
    """
    logger.info(f"Starting image crawl for keyword: {keyword}")

    try:
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Import builder modules
        from builder._engine import EngineProcessor
        from builder._downloader import ImageDownloader, DuckDuckGoImageDownloader
        from builder._config import get_engines

        # Get available engines
        available_engines = get_engines()
        if not engines:
            engines = [engine['name'] for engine in available_engines]

        results = {
            'keyword': keyword,
            'output_dir': output_dir,
            'max_images': max_images,
            'engines_used': engines,
            'downloads': {},
            'total_downloaded': 0,
            'success': False,
            'errors': []
        }

        total_downloaded = 0

        # Use EngineProcessor for multi-engine support
        image_downloader = ImageDownloader()
        engine_processor = EngineProcessor(image_downloader)

        for engine_name in engines:
            try:
                logger.info(f"Processing engine: {engine_name}")

                if engine_name.lower() == 'duckduckgo':
                    # Use DuckDuckGo downloader as fallback
                    ddg_downloader = DuckDuckGoImageDownloader()
                    success, downloaded = ddg_downloader.download(
                        keyword, output_dir, max_images
                    )

                    results['downloads'][engine_name] = {
                        'success': success,
                        'downloaded': downloaded,
                        'method': 'duckduckgo_direct'
                    }

                    if success:
                        total_downloaded += downloaded

                else:
                    # Use engine processor for other engines
                    engine_config = next(
                        (e for e in available_engines
                         if e['name'].lower() == engine_name.lower()),
                        None
                    )

                    if engine_config:
                        engine_result = engine_processor.process_single_engine(
                            keyword=keyword,
                            output_dir=output_dir,
                            engine_config=engine_config,
                            max_images=max_images
                        )

                        downloaded = (
                            engine_result.total_downloaded
                            if hasattr(engine_result, 'total_downloaded')
                            else 0
                        )
                        success = downloaded > 0

                        results['downloads'][engine_name] = {
                            'success': success,
                            'downloaded': downloaded,
                            'method': 'engine_processor'
                        }

                        total_downloaded += downloaded
                    else:
                        logger.warning(f"Engine {engine_name} not found in configuration")
                        results['downloads'][engine_name] = {
                            'success': False,
                            'downloaded': 0,
                            'error': 'Engine not found'
                        }

            except Exception as e:
                error_msg = f"Failed to process engine {engine_name}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['downloads'][engine_name] = {
                    'success': False,
                    'downloaded': 0,
                    'error': str(e)
                }

        results['total_downloaded'] = total_downloaded
        results['success'] = total_downloaded > 0

        logger.info(f"Crawl completed for {keyword}: {total_downloaded} images downloaded")
        return results

    except Exception as e:
        error_msg = f"Crawl task failed for {keyword}: {str(e)}"
        logger.error(error_msg)
        return {
            'keyword': keyword,
            'success': False,
            'error': error_msg,
            'total_downloaded': 0
        }


@app.task(bind=True, base=BaseTask, name='builder.task_crawl_images')
def task_crawl_images(self, keyword: str, output_dir: str, max_images: int = 10,
                     engines: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Celery task for crawling images using all available engines.

    Args:
        keyword: Search keyword for image crawling
        output_dir: Directory to save downloaded images
        max_images: Maximum number of images to download
        engines: List of search engines to use (optional)

    Returns:
        Dict containing crawl results and metadata
    """
    return task_crawl_images_impl(keyword, output_dir, max_images, engines)


def task_generate_keywords_impl(base_keywords: List[str], ai_model: str = "gpt4-mini",
                               count: int = 10) -> Dict[str, Any]:
    """
    Implementation for AI-powered keyword generation.

    Args:
        base_keywords: List of base keywords to generate variations from
        ai_model: AI model to use for generation
        count: Number of keywords to generate per base keyword

    Returns:
        Dict containing generation results and metadata
    """
    logger.info(f"Starting keyword generation for: {base_keywords}")

    try:
        from builder._generator import KeywordManagement

        keyword_manager = KeywordManagement()

        results = {
            'base_keywords': base_keywords,
            'ai_model': ai_model,
            'requested_count': count,
            'generated_keywords': [],
            'success': False,
            'errors': []
        }

        generated_keywords = []
        for base_keyword in base_keywords:
            try:
                new_keywords = keyword_manager.generate_keywords(
                    base_keyword, ai_model, count
                )
                generated_keywords.extend(new_keywords)

            except Exception as e:
                error_msg = f"Failed to generate keywords for '{base_keyword}': {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        results['generated_keywords'] = list(set(generated_keywords))
        results['success'] = len(generated_keywords) > 0

        logger.info(f"Keyword generation completed: {len(generated_keywords)} keywords generated")
        return results

    except Exception as e:
        error_msg = f"Keyword generation failed: {str(e)}"
        logger.error(error_msg)
        return {
            'base_keywords': base_keywords,
            'success': False,
            'error': error_msg,
=======
Celery tasks for PixCrawler builder package.

This module provides Celery task definitions for background image downloading
using the builder package's real functionality. Each search engine has its own
task for parallel execution.

Tasks:
    task_download_google: Download images using Google Image Search
    task_download_bing: Download images using Bing Image Search
    task_download_baidu: Download images using Baidu Image Search
    task_download_duckduckgo: Download images using DuckDuckGo
    task_generate_keywords: Generate keywords using AI
    task_generate_labels: Generate label files for dataset
    task_build_dataset: Orchestrate complete dataset build

Architecture:
    - One task per search engine for parallel execution
    - Uses real builder functionality (no reimplementation)
    - Follows celery_core patterns (impl + task decorator)
"""

from pathlib import Path
from typing import Dict, List, Any, Optional

from builder._config import get_engines
from builder._downloader import ImageDownloader
from builder._generator import KeywordManagement, LabelGenerator
from builder._predefined_variations import get_search_variations
from builder._search_engines import (
    SearchEngineConfig,
    download_google_images,
    download_bing_images,
    download_baidu_images,
    download_images_ddgs
)
from celery_core.app import get_celery_app
from celery_core.base import BaseTask
from logging_config import get_logger

logger = get_logger(__name__)
app = get_celery_app()

__all__ = [
    'task_download_google',
    'task_download_bing',
    'task_download_baidu',
    'task_download_duckduckgo',
    'task_generate_keywords',
    'task_generate_labels',
    'task_allengines_build_dataset'
]


def task_download_google_impl(
    keyword: str,
    output_dir: str,
    max_images: int = 100,
    variations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Implementation for Google image download task.

    Args:
        keyword: Search keyword
        output_dir: Output directory for images
        max_images: Maximum number of images to download
        variations: Search variations (auto-generated if None)

    Returns:
        Dict with download results
    """
    logger.info(f"Starting Google download for: {keyword}")

    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Get engine config
        engines = get_engines()
        google_config = next((e for e in engines if e['name'].lower() == 'google'),
                             None)

        if not google_config:
            return {
                'success': False,
                'error': 'Google engine not configured',
                'downloaded': 0
            }

        config = SearchEngineConfig(
            name=google_config['name'],
            offset_range=google_config['offset_range'],
            variation_step=google_config['variation_step']
        )

        # Get variations
        if not variations:
            # get_search_variations() returns template strings like "{keyword} photo"
            # We need to format them with the actual keyword
            variation_templates = get_search_variations()
            variations = [template.format(keyword=keyword) for template in
                          variation_templates[:5]]

        # Create downloader
        downloader = ImageDownloader()

        # Download using real builder function
        result = download_google_images(
            keyword=keyword,
            variations=variations,
            out_dir=output_dir,
            max_num=max_images,
            config=config,
            image_downloader=downloader
        )

        logger.info(f"Google download completed: {result.total_downloaded} images")

        return {
            'success': result.total_downloaded > 0,
            'engine': 'google',
            'keyword': keyword,
            'downloaded': result.total_downloaded,
            'variations_processed': result.variations_processed,
            'success_rate': result.success_rate,
            'processing_time': result.processing_time
        }

    except Exception as e:
        logger.error(f"Google download failed for {keyword}: {str(e)}")
        return {
            'success': False,
            'engine': 'google',
            'keyword': keyword,
            'error': str(e),
            'downloaded': 0
        }


@app.task(
    bind=True,
    base=BaseTask,
    name='builder.download_google',
    # Pydantic Support
    typing=True,
    # Retry Configuration
    autoretry_for=(ConnectionError, TimeoutError, IOError),
    max_retries=5,
    default_retry_delay=120,
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    reject_on_worker_lost=True,
    track_started=True,
    # Time Limits (long for network operations)
    soft_time_limit=1800,
    time_limit=3600,
    # Rate Limiting (prevent API abuse)
    rate_limit="10/m",
    # Serialization
    serializer="json",
)
def task_download_google(
    self,
    keyword: str,
    output_dir: str,
    max_images: int = 100,
    variations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Celery task for Google image download."""
    return task_download_google_impl(keyword, output_dir, max_images, variations)


def task_download_bing_impl(
    keyword: str,
    output_dir: str,
    max_images: int = 100,
    variations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Implementation for Bing image download task."""
    logger.info(f"Starting Bing download for: {keyword}")

    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        engines = get_engines()
        bing_config = next((e for e in engines if e['name'].lower() == 'bing'), None)

        if not bing_config:
            return {
                'success': False,
                'error': 'Bing engine not configured',
                'downloaded': 0
            }

        config = SearchEngineConfig(
            name=bing_config['name'],
            offset_range=bing_config['offset_range'],
            variation_step=bing_config['variation_step']
        )

        if not variations:
            # get_search_variations() returns template strings like "{keyword} photo"
            # We need to format them with the actual keyword
            variation_templates = get_search_variations()
            variations = [template.format(keyword=keyword) for template in
                          variation_templates[:5]]

        downloader = ImageDownloader()

        result = download_bing_images(
            keyword=keyword,
            variations=variations,
            out_dir=output_dir,
            max_num=max_images,
            config=config,
            image_downloader=downloader
        )

        logger.info(f"Bing download completed: {result.total_downloaded} images")

        return {
            'success': result.total_downloaded > 0,
            'engine': 'bing',
            'keyword': keyword,
            'downloaded': result.total_downloaded,
            'variations_processed': result.variations_processed,
            'success_rate': result.success_rate,
            'processing_time': result.processing_time
        }

    except Exception as e:
        logger.error(f"Bing download failed for {keyword}: {str(e)}")
        return {
            'success': False,
            'engine': 'bing',
            'keyword': keyword,
            'error': str(e),
            'downloaded': 0
        }


@app.task(
    bind=True,
    base=BaseTask,
    name='builder.download_bing',
    # Pydantic Support
    typing=True,
    # Retry Configuration
    autoretry_for=(ConnectionError, TimeoutError, IOError),
    max_retries=5,
    default_retry_delay=120,
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    reject_on_worker_lost=True,
    track_started=True,
    # Time Limits
    soft_time_limit=1800,
    time_limit=3600,
    # Rate Limiting
    rate_limit="10/m",
    # Serialization
    serializer="json",
)
def task_download_bing(
    self,
    keyword: str,
    output_dir: str,
    max_images: int = 100,
    variations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Celery task for Bing image download."""
    return task_download_bing_impl(keyword, output_dir, max_images, variations)


def task_download_baidu_impl(
    keyword: str,
    output_dir: str,
    max_images: int = 100,
    variations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Implementation for Baidu image download task."""
    logger.info(f"Starting Baidu download for: {keyword}")

    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        engines = get_engines()
        baidu_config = next((e for e in engines if e['name'].lower() == 'baidu'), None)

        if not baidu_config:
            return {
                'success': False,
                'error': 'Baidu engine not configured',
                'downloaded': 0
            }

        config = SearchEngineConfig(
            name=baidu_config['name'],
            offset_range=baidu_config['offset_range'],
            variation_step=baidu_config['variation_step']
        )

        if not variations:
            # get_search_variations() returns template strings like "{keyword} photo"
            # We need to format them with the actual keyword
            variation_templates = get_search_variations()
            variations = [template.format(keyword=keyword) for template in
                          variation_templates[:5]]

        downloader = ImageDownloader()

        result = download_baidu_images(
            keyword=keyword,
            variations=variations,
            out_dir=output_dir,
            max_num=max_images,
            config=config,
            image_downloader=downloader
        )

        logger.info(f"Baidu download completed: {result.total_downloaded} images")

        return {
            'success': result.total_downloaded > 0,
            'engine': 'baidu',
            'keyword': keyword,
            'downloaded': result.total_downloaded,
            'variations_processed': result.variations_processed,
            'success_rate': result.success_rate,
            'processing_time': result.processing_time
        }

    except Exception as e:
        logger.error(f"Baidu download failed for {keyword}: {str(e)}")
        return {
            'success': False,
            'engine': 'baidu',
            'keyword': keyword,
            'error': str(e),
            'downloaded': 0
        }


@app.task(
    bind=True,
    base=BaseTask,
    name='builder.download_baidu',
    # Pydantic Support
    typing=True,
    # Retry Configuration
    autoretry_for=(ConnectionError, TimeoutError, IOError),
    max_retries=5,
    default_retry_delay=120,
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    reject_on_worker_lost=True,
    track_started=True,
    # Time Limits
    soft_time_limit=1800,
    time_limit=3600,
    # Rate Limiting
    rate_limit="10/m",
    # Serialization
    serializer="json",
)
def task_download_baidu(
    self,
    keyword: str,
    output_dir: str,
    max_images: int = 100,
    variations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Celery task for Baidu image download."""
    return task_download_baidu_impl(keyword, output_dir, max_images, variations)


def task_download_duckduckgo_impl(
    keyword: str,
    output_dir: str,
    max_images: int = 100
) -> Dict[str, Any]:
    """Implementation for DuckDuckGo image download task."""
    logger.info(f"Starting DuckDuckGo download for: {keyword}")

    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Use real builder function
        success, downloaded = download_images_ddgs(keyword, output_dir, max_images)

        logger.info(f"DuckDuckGo download completed: {downloaded} images")

        return {
            'success': success,
            'engine': 'duckduckgo',
            'keyword': keyword,
            'downloaded': downloaded
        }

    except Exception as e:
        logger.error(f"DuckDuckGo download failed for {keyword}: {str(e)}")
        return {
            'success': False,
            'engine': 'duckduckgo',
            'keyword': keyword,
            'error': str(e),
            'downloaded': 0
        }


@app.task(
    bind=True,
    base=BaseTask,
    name='builder.download_duckduckgo',
    # Pydantic Support
    typing=True,
    # Retry Configuration
    autoretry_for=(ConnectionError, TimeoutError, IOError),
    max_retries=5,
    default_retry_delay=120,
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    reject_on_worker_lost=True,
    track_started=True,
    # Time Limits
    soft_time_limit=1800,
    time_limit=3600,
    # Rate Limiting
    rate_limit="10/m",
    # Serialization
    serializer="json",
)
def task_download_duckduckgo(
    self,
    keyword: str,
    output_dir: str,
    max_images: int = 100
) -> Dict[str, Any]:
    """Celery task for DuckDuckGo image download."""
    return task_download_duckduckgo_impl(keyword, output_dir, max_images)


# ============================================================================
# Keyword Generation Task
# ============================================================================

def task_generate_keywords_impl(
    base_keywords: List[str],
    ai_model: str = "gpt4-mini",
    count: int = 10
) -> Dict[str, Any]:
    """Implementation for AI-powered keyword generation."""
    logger.info(f"Starting keyword generation for: {base_keywords}")

    try:
        # KeywordManagement.generate_keywords() only takes category parameter
        # The ai_model is set during KeywordManagement initialization
        keyword_manager = KeywordManagement(ai_model=ai_model)

        generated_keywords = []
        errors = []

        for base_keyword in base_keywords:
            try:
                # generate_keywords() only takes category (the keyword itself)
                new_keywords = keyword_manager.generate_keywords(base_keyword)
                generated_keywords.extend(new_keywords)
            except Exception as e:
                error_msg = f"Failed to generate keywords for '{base_keyword}': {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Remove duplicates
        generated_keywords = list(set(generated_keywords))

        logger.info(f"Keyword generation completed: {len(generated_keywords)} keywords")

        return {
            'success': len(generated_keywords) > 0,
            'base_keywords': base_keywords,
            'generated_keywords': generated_keywords,
            'count': len(generated_keywords),
            'errors': errors
        }

    except Exception as e:
        logger.error(f"Keyword generation failed: {str(e)}")
        return {
            'success': False,
            'base_keywords': base_keywords,
            'error': str(e),
>>>>>>> 8396043cf52a68feb519edfac1a9344fe004f208
            'generated_keywords': []
        }


<<<<<<< HEAD
@app.task(bind=True, base=BaseTask, name='builder.task_generate_keywords')
def task_generate_keywords(self, base_keywords: List[str], ai_model: str = "gpt4-mini",
                          count: int = 10) -> Dict[str, Any]:
    """
    Celery task for AI-powered keyword generation.

    Args:
        base_keywords: List of base keywords to generate variations from
        ai_model: AI model to use for generation
        count: Number of keywords to generate per base keyword

    Returns:
        Dict containing generation results and metadata
    """
    return task_generate_keywords_impl(base_keywords, ai_model, count)


def task_generate_labels_impl(dataset_dir: str, formats: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Implementation for generating label files.

    Args:
        dataset_dir: Directory containing the dataset
        formats: List of label formats to generate (optional)

    Returns:
        Dict containing generation results and metadata
    """
    logger.info(f"Starting label generation for: {dataset_dir}")

    try:
        from builder._generator import LabelGenerator

        if not formats:
            formats = ['txt', 'json', 'csv', 'yaml']

        results = {
            'dataset_dir': dataset_dir,
            'formats': formats,
            'generated_files': [],
            'success': False,
            'errors': []
        }

        label_generator = LabelGenerator()
        generated_files = label_generator.generate_dataset_labels(dataset_dir)

        results['generated_files'] = generated_files
        results['success'] = len(generated_files) > 0

        logger.info(f"Label generation completed: {len(generated_files)} files generated")
        return results

    except Exception as e:
        error_msg = f"Label generation failed: {str(e)}"
        logger.error(error_msg)
        return {
            'dataset_dir': dataset_dir,
            'success': False,
            'error': error_msg,
=======
@app.task(
    bind=True,
    base=BaseTask,
    name='builder.generate_keywords',
    # Pydantic Support
    typing=True,
    # Retry Configuration (AI API may fail)
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    track_started=True,
    # Time Limits (AI generation can be slow)
    soft_time_limit=300,
    time_limit=600,
    # Rate Limiting (AI API limits)
    rate_limit="5/m",
    # Serialization
    serializer="json",
)
def task_generate_keywords(
    self,
    base_keywords: List[str],
    ai_model: str = "gpt4-mini",
    count: int = 10
) -> Dict[str, Any]:
    """Celery task for AI-powered keyword generation."""
    return task_generate_keywords_impl(base_keywords, ai_model, count)


def task_generate_labels_impl(
    dataset_dir: str,
    formats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Implementation for generating label files."""
    logger.info(f"Starting label generation for: {dataset_dir}")

    try:
        if not formats:
            formats = ['txt', 'json', 'csv', 'yaml']

        label_generator = LabelGenerator()
        # generate_dataset_labels() now returns list of file paths
        generated_files = label_generator.generate_dataset_labels(dataset_dir)

        logger.info(f"Label generation completed: {len(generated_files)} files")

        return {
            'success': len(generated_files) > 0,
            'dataset_dir': dataset_dir,
            'generated_files': generated_files,
            'count': len(generated_files)
        }

    except Exception as e:
        logger.error(f"Label generation failed: {str(e)}")
        return {
            'success': False,
            'dataset_dir': dataset_dir,
            'error': str(e),
>>>>>>> 8396043cf52a68feb519edfac1a9344fe004f208
            'generated_files': []
        }


<<<<<<< HEAD
@app.task(bind=True, base=BaseTask, name='builder.task_generate_labels')
def task_generate_labels(self, dataset_dir: str, formats: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Celery task for generating label files.

    Args:
        dataset_dir: Directory containing the dataset
        formats: List of label formats to generate (optional)

    Returns:
        Dict containing generation results and metadata
    """
    return task_generate_labels_impl(dataset_dir, formats)


def task_process_category_impl(category: str, keywords: List[str], output_dir: str,
                              max_images: int = 10, generate_labels: bool = True) -> Dict[str, Any]:
    """
    Implementation for processing a complete category.

    Args:
        category: Category name
        keywords: List of keywords to process
        output_dir: Base output directory
        max_images: Maximum images per keyword
        generate_labels: Whether to generate label files

    Returns:
        Dict containing processing results and metadata
    """
    logger.info(f"Starting category processing: {category} with {len(keywords)} keywords")

    try:
        category_dir = Path(output_dir) / category
        category_dir.mkdir(parents=True, exist_ok=True)

        results = {
            'category': category,
            'keywords': keywords,
            'output_dir': str(category_dir),
            'max_images': max_images,
            'keyword_results': {},
            'total_downloaded': 0,
            'success': False,
            'errors': []
        }

        total_downloaded = 0

        for keyword in keywords:
            try:
                keyword_dir = category_dir / keyword.replace(' ', '_')

                # Crawl images for this keyword using all engines
                crawl_result = task_crawl_images_impl(
                    keyword=keyword,
                    output_dir=str(keyword_dir),
                    max_images=max_images
                )

                results['keyword_results'][keyword] = crawl_result
                total_downloaded += crawl_result.get('total_downloaded', 0)

            except Exception as e:
                error_msg = f"Failed to process keyword '{keyword}': {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                results['keyword_results'][keyword] = {
                    'success': False,
                    'error': error_msg,
                    'total_downloaded': 0
                }

        # Generate labels if requested
        if generate_labels and total_downloaded > 0:
            try:
                label_result = task_generate_labels_impl(str(category_dir))
                results['label_generation'] = label_result
            except Exception as e:
                error_msg = f"Failed to generate labels for category '{category}': {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)

        results['total_downloaded'] = total_downloaded
        results['success'] = total_downloaded > 0

        logger.info(f"Category processing completed: {category} - {total_downloaded} images downloaded")
        return results

    except Exception as e:
        error_msg = f"Category processing failed for '{category}': {str(e)}"
        logger.error(error_msg)
        return {
            'category': category,
            'success': False,
            'error': error_msg,
=======
@app.task(
    bind=True,
    base=BaseTask,
    name='builder.generate_labels',
    # Pydantic Support
    typing=True,
    # Retry Configuration
    autoretry_for=(IOError, OSError),
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=300,
    # Result Storage
    ignore_result=False,
    acks_late=True,
    track_started=True,
    # Time Limits
    soft_time_limit=600,
    time_limit=900,
    # Serialization
    serializer="json",
)
def task_generate_labels(
    self,
    dataset_dir: str,
    formats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Celery task for generating label files."""
    return task_generate_labels_impl(dataset_dir, formats)


def task_allengines_build_dataset_impl(
    keyword: str,
    output_dir: str,
    max_images_per_engine: int = 25,
    engines: Optional[List[str]] = None,
    generate_labels: bool = True
) -> Dict[str, Any]:
    """
    Implementation for building complete dataset using parallel engine tasks.

    This orchestrates multiple engine tasks to run in parallel using Celery's
    group primitive for maximum efficiency.

    Args:
        keyword: Search keyword
        output_dir: Output directory
        max_images_per_engine: Max images per engine
        engines: List of engines to use (None = all)
        generate_labels: Whether to generate label files

    Returns:
        Dict with build results
    """
    from celery import group

    logger.info(f"Starting dataset build for: {keyword}")

    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Determine which engines to use
        if not engines:
            engines = ['google', 'bing', 'baidu', 'duckduckgo']

        # Create parallel tasks for each engine
        engine_tasks = []

        if 'google' in engines:
            engine_tasks.append(
                task_download_google.s(keyword, output_dir, max_images_per_engine)
            )
        if 'bing' in engines:
            engine_tasks.append(
                task_download_bing.s(keyword, output_dir, max_images_per_engine)
            )
        if 'baidu' in engines:
            engine_tasks.append(
                task_download_baidu.s(keyword, output_dir, max_images_per_engine)
            )
        if 'duckduckgo' in engines:
            engine_tasks.append(
                task_download_duckduckgo.s(keyword, output_dir, max_images_per_engine)
            )

        # Execute all engine tasks in parallel
        job = group(engine_tasks)
        result = job.apply_async()

        # Wait for all tasks to complete
        engine_results = result.get()

        # Aggregate results
        total_downloaded = sum(r.get('downloaded', 0) for r in engine_results)

        # Generate labels if requested
        label_result = None
        if generate_labels and total_downloaded > 0:
            label_result = task_generate_labels_impl(output_dir)

        logger.info(
            f"Dataset build completed: {total_downloaded} images from {len(engines)} engines")

        return {
            'success': total_downloaded > 0,
            'keyword': keyword,
            'output_dir': output_dir,
            'total_downloaded': total_downloaded,
            'engines_used': engines,
            'engine_results': engine_results,
            'label_generation': label_result
        }

    except Exception as e:
        logger.error(f"Dataset build failed for {keyword}: {str(e)}")
        return {
            'success': False,
            'keyword': keyword,
            'error': str(e),
>>>>>>> 8396043cf52a68feb519edfac1a9344fe004f208
            'total_downloaded': 0
        }


<<<<<<< HEAD
@app.task(bind=True, base=BaseTask, name='builder.task_process_category')
def task_process_category(self, category: str, keywords: List[str], output_dir: str,
                         max_images: int = 10, generate_labels: bool = True) -> Dict[str, Any]:
    """
    Celery task for processing a complete category.

    Args:
        category: Category name
        keywords: List of keywords to process
        output_dir: Base output directory
        max_images: Maximum images per keyword
        generate_labels: Whether to generate label files

    Returns:
        Dict containing processing results and metadata
    """
    return task_process_category_impl(category, keywords, output_dir, max_images, generate_labels)
=======
@app.task(
    bind=True,
    base=BaseTask,
    name='builder.engines_build_dataset',
    # Pydantic Support
    typing=True,
    # Retry Configuration (orchestration task)
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=2,
    default_retry_delay=300,
    retry_backoff=True,
    retry_backoff_max=1800,
    # Result Storage
    ignore_result=False,
    store_errors_even_if_ignored=True,
    acks_late=True,
    reject_on_worker_lost=True,
    track_started=True,
    # Time Limits (very long for orchestration)
    soft_time_limit=7200,
    time_limit=10800,
    # Serialization
    serializer="json",
)
def task_allengines_build_dataset(
    self,
    keyword: str,
    output_dir: str,
    max_images_per_engine: int = 25,
    engines: Optional[List[str]] = None,
    generate_labels: bool = True
) -> Dict[str, Any]:
    """
    Celery task for building complete dataset with parallel engine execution.

    This is the main orchestration task that coordinates multiple engine tasks
    to run in parallel for maximum efficiency.
    """
    return task_allengines_build_dataset_impl(
        keyword, output_dir, max_images_per_engine, engines, generate_labels
    )
>>>>>>> 8396043cf52a68feb519edfac1a9344fe004f208
