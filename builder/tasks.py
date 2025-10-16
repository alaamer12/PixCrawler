"""
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
from logging_config import get_logger

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
            'generated_keywords': []
        }


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
            'generated_files': []
        }


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
            'total_downloaded': 0
        }


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