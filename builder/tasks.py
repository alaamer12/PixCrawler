"""
Celery tasks for PixCrawler builder package - Refactored with proper design patterns.

This module provides celery-compatible task definitions for background processing
of image crawling, keyword generation, and label creation using proper abstractions.

Classes:
    TaskExecutor: Abstract base for task execution strategies
    CeleryTaskExecutor: Celery-based async task execution
    SyncTaskExecutor: Synchronous fallback execution
    TaskRegistry: Registry for managing task executors
    CrawlerTaskManager: Enhanced task manager with proper abstractions

Tasks:
    crawl_images_task: Background task for image crawling (all engines)
    generate_keywords_task: Background task for AI keyword generation
    generate_labels_task: Background task for label file generation
    process_category_task: Background task for processing a single category
"""

import abc
import functools
from typing import Dict, List, Any, Optional, Callable, Union, Type
import os
from pathlib import Path

from logging_config import get_logger

logger = get_logger(__name__)

# Check celery availability
try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available. Tasks will run synchronously.")

__all__ = [
    'TaskExecutor',
    'CeleryTaskExecutor',
    'SyncTaskExecutor',
    'TaskRegistry',
    'CrawlerTaskManager',
    'crawl_images_task',
    'generate_keywords_task',
    'generate_labels_task',
    'process_category_task'
]


class TaskExecutor(abc.ABC):
    """Abstract base class for task execution strategies."""

    @abc.abstractmethod
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a task function with given arguments."""
        pass

    @abc.abstractmethod
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a task by ID."""
        pass

    @abc.abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task by ID."""
        pass


class CeleryTaskExecutor(TaskExecutor):
    """Celery-based async task executor."""

    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
        self.active_tasks = {}

    def execute(self, func: Callable, *args, **kwargs) -> str:
        """Execute task asynchronously with Celery."""
        # Create celery task from function
        task = self.celery_app.task(func)
        result = task.delay(*args, **kwargs)

        task_id = result.id
        self.active_tasks[task_id] = {
            'task': result,
            'function': func.__name__,
            'args': args,
            'kwargs': kwargs
        }

        logger.info(f"Submitted celery task {task_id} for {func.__name__}")
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get celery task status."""
        if task_id not in self.active_tasks:
            return {'status': 'not_found', 'error': 'Task ID not found'}

        task_info = self.active_tasks[task_id]
        task = task_info['task']

        return {
            'status': task.status,
            'result': task.result if task.ready() else None,
            'info': task.info,
            'function': task_info['function']
        }

    def cancel_task(self, task_id: str) -> bool:
        """Cancel celery task."""
        if task_id not in self.active_tasks:
            return False

        task = self.active_tasks[task_id]['task']
        task.revoke(terminate=True)
        del self.active_tasks[task_id]

        logger.info(f"Cancelled celery task {task_id}")
        return True


class SyncTaskExecutor(TaskExecutor):
    """Synchronous fallback task executor."""

    def __init__(self):
        self.completed_tasks = {}
        self.task_counter = 0

    def execute(self, func: Callable, *args, **kwargs) -> str:
        """Execute task synchronously."""
        self.task_counter += 1
        task_id = f"sync_{func.__name__}_{self.task_counter}"

        logger.info(f"Executing sync task {task_id} for {func.__name__}")

        try:
            result = func(*args, **kwargs)
            self.completed_tasks[task_id] = {
                'status': 'completed',
                'result': result,
                'function': func.__name__
            }
        except Exception as e:
            self.completed_tasks[task_id] = {
                'status': 'failed',
                'error': str(e),
                'function': func.__name__
            }

        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get sync task status."""
        return self.completed_tasks.get(task_id, {
            'status': 'not_found',
            'error': 'Task ID not found'
        })

    def cancel_task(self, task_id: str) -> bool:
        """Cancel sync task (not applicable for completed tasks)."""
        if task_id in self.completed_tasks:
            del self.completed_tasks[task_id]
            return True
        return False


class TaskRegistry:
    """Registry for managing task executors and providing unified interface."""

    def __init__(self, celery_app: Optional[Celery] = None):
        self.executor = self._create_executor(celery_app)

    def _create_executor(self, celery_app: Optional[Celery]) -> TaskExecutor:
        """Create appropriate task executor based on availability."""
        if CELERY_AVAILABLE and celery_app:
            return CeleryTaskExecutor(celery_app)
        else:
            logger.info("Using synchronous task executor")
            return SyncTaskExecutor()

    def task(self, func: Callable) -> Callable:
        """Decorator to register a function as a task."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.executor.execute(func, *args, **kwargs)

        # Add executor methods to wrapper for convenience
        wrapper.get_status = self.executor.get_task_status
        wrapper.cancel = self.executor.cancel_task
        wrapper.executor = self.executor

        return wrapper


# Global task registry (will be configured by application)
_task_registry = TaskRegistry()


def configure_tasks(celery_app: Optional[Celery] = None):
    """Configure task registry with celery app."""
    global _task_registry
    _task_registry = TaskRegistry(celery_app)


# Task implementations using all available engines
def _crawl_images_impl(keyword: str, output_dir: str, max_images: int = 10,
                      engines: Optional[List[str]] = None) -> Dict[str, Any]:
    """Implementation for crawling images using all available engines."""
    from builder._engine import EngineProcessor
    from builder._downloader import ImageDownloader, DuckDuckGoImageDownloader
    from builder._config import get_engines

    logger.info(f"Starting image crawl for keyword: {keyword}")

    try:
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)

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
                    success, downloaded = ddg_downloader.download(keyword, output_dir, max_images)

                    results['downloads'][engine_name] = {
                        'success': success,
                        'downloaded': downloaded,
                        'method': 'duckduckgo_direct'
                    }

                    if success:
                        total_downloaded += downloaded

                else:
                    # Use engine processor for other engines (Google, Bing, Baidu)
                    engine_config = next((e for e in available_engines if e['name'].lower() == engine_name.lower()), None)

                    if engine_config:
                        # Process single engine
                        engine_result = engine_processor.process_single_engine(
                            keyword=keyword,
                            output_dir=output_dir,
                            engine_config=engine_config,
                            max_images=max_images
                        )

                        downloaded = engine_result.total_downloaded if hasattr(engine_result, 'total_downloaded') else 0
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


def _generate_keywords_impl(base_keywords: List[str], ai_model: str = "gpt4-mini",
                           count: int = 10) -> Dict[str, Any]:
    """Implementation for AI-powered keyword generation."""
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


def _generate_labels_impl(dataset_dir: str, formats: Optional[List[str]] = None) -> Dict[str, Any]:
    """Implementation for generating label files."""
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


def _process_category_impl(category: str, keywords: List[str], output_dir: str,
                          max_images: int = 10, generate_labels: bool = True) -> Dict[str, Any]:
    """Implementation for processing a complete category."""
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
                crawl_result = _crawl_images_impl(
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
                label_result = _generate_labels_impl(str(category_dir))
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


@_task_registry.task
def crawl_images_task(keyword: str, output_dir: str, max_images: int = 10,
                     engines: Optional[List[str]] = None) -> Dict[str, Any]:
    """Celery task for crawling images using all available engines."""
    return _crawl_images_impl(keyword, output_dir, max_images, engines)


@_task_registry.task
def generate_keywords_task(base_keywords: List[str], ai_model: str = "gpt4-mini",
                          count: int = 10) -> Dict[str, Any]:
    """Celery task for AI-powered keyword generation."""
    return _generate_keywords_impl(base_keywords, ai_model, count)


@_task_registry.task
def generate_labels_task(dataset_dir: str, formats: Optional[List[str]] = None) -> Dict[str, Any]:
    """Celery task for generating label files."""
    return _generate_labels_impl(dataset_dir, formats)


@_task_registry.task
def process_category_task(category: str, keywords: List[str], output_dir: str,
                         max_images: int = 10, generate_labels: bool = True) -> Dict[str, Any]:
    """Celery task for processing a complete category."""
    return _process_category_impl(category, keywords, output_dir, max_images, generate_labels)


class CrawlerTaskManager:
    """
    Enhanced task manager with proper abstractions and multi-engine support.
    """

    def __init__(self, celery_app: Optional[Celery] = None):
        """Initialize task manager with optional celery app."""
        configure_tasks(celery_app)
        self.registry = _task_registry
        self.active_tasks = {}

    def submit_crawl_task(self, keyword: str, output_dir: str, max_images: int = 10,
                         engines: Optional[List[str]] = None) -> str:
        """Submit a crawl task using all available engines."""
        task_id = crawl_images_task(keyword, output_dir, max_images, engines)

        self.active_tasks[task_id] = {
            'type': 'crawl',
            'keyword': keyword,
            'engines': engines,
            'submitted_at': __import__('time').time()
        }

        logger.info(f"Submitted crawl task {task_id} for keyword: {keyword} with engines: {engines}")
        return task_id

    def submit_category_task(self, category: str, keywords: List[str], output_dir: str,
                           max_images: int = 10, generate_labels: bool = True) -> str:
        """Submit a category processing task."""
        task_id = process_category_task(category, keywords, output_dir, max_images, generate_labels)

        self.active_tasks[task_id] = {
            'type': 'category',
            'category': category,
            'keywords': keywords,
            'submitted_at': __import__('time').time()
        }

        logger.info(f"Submitted category task {task_id} for: {category}")
        return task_id

    def submit_keyword_generation_task(self, base_keywords: List[str],
                                     ai_model: str = "gpt4-mini", count: int = 10) -> str:
        """Submit a keyword generation task."""
        task_id = generate_keywords_task(base_keywords, ai_model, count)

        self.active_tasks[task_id] = {
            'type': 'keywords',
            'base_keywords': base_keywords,
            'ai_model': ai_model,
            'submitted_at': __import__('time').time()
        }

        logger.info(f"Submitted keyword generation task {task_id}")
        return task_id

    def submit_label_generation_task(self, dataset_dir: str,
                                   formats: Optional[List[str]] = None) -> str:
        """Submit a label generation task."""
        task_id = generate_labels_task(dataset_dir, formats)

        self.active_tasks[task_id] = {
            'type': 'labels',
            'dataset_dir': dataset_dir,
            'formats': formats,
            'submitted_at': __import__('time').time()
        }

        logger.info(f"Submitted label generation task {task_id}")
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status using registry."""
        status = self.registry.executor.get_task_status(task_id)

        # Add metadata if available
        if task_id in self.active_tasks:
            status['metadata'] = self.active_tasks[task_id]

        return status

    def cancel_task(self, task_id: str) -> bool:
        """Cancel task using registry."""
        success = self.registry.executor.cancel_task(task_id)

        if success and task_id in self.active_tasks:
            del self.active_tasks[task_id]

        return success

    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all active tasks."""
        active_info = {}

        for task_id, task_info in self.active_tasks.items():
            status = self.get_task_status(task_id)
            active_info[task_id] = {
                'type': task_info['type'],
                'status': status.get('status', 'unknown'),
                'metadata': {k: v for k, v in task_info.items() if k != 'type'}
            }

        return active_info

    def get_available_engines(self) -> List[str]:
        """Get list of available search engines."""
        from builder._config import get_engines
        return [engine['name'] for engine in get_engines()]
