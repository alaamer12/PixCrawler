"""
PixCrawler Builder Package

This package provides unified Builder classes for generating image datasets with
AI-powered keyword generation, multi-engine downloading, and label generation.
Integrity management has been moved to the backend package.

Classes:
    Builder: Main synchronous builder class
    AsyncBuilder: Async-compatible builder for background processing
    BuilderConfig: Configuration for async operations
    CrawlerTaskManager: Task manager for celery integration

Example:
    ```python
    from builder import Builder

    # Simple synchronous usage
    builder = Builder("config.json")
    builder.generate()

    # Async usage with celery
    from builder import AsyncBuilder, BuilderConfig

    config = BuilderConfig("config.json", max_images=50)
    async_builder = AsyncBuilder(config, celery_app)
    task_ids = await async_builder.generate_dataset_async()
    ```

Features:
    - Multi-engine image downloading (Google, Bing, Baidu, DuckDuckGo)
    - AI-powered keyword generation for diverse image collection
    - Automatic label file generation in multiple formats
    - Celery-compatible background processing
    - Progress tracking and task management
    - Customizable configuration and search parameters

Note: Image integrity checking and duplicate removal moved to backend package.
"""

from builder._builder import Builder
from builder.tasks import CrawlerTaskManager

__version__ = "0.1.1"
__author__ = "PixCrawler Team"
__email__ = "team@pixcrawler.com"

__all__ = ["Builder", "AsyncBuilder", "BuilderConfig", "CrawlerTaskManager"]
