"""
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
            'generated_keywords': []
        }


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
            'generated_files': []
        }


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
