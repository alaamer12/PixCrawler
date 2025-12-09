"""
PixCrawler SDK
~~~~~~~~~~~~~~

The official Python SDK for PixCrawler.

Usage:
    >>> from pixcrawler import PixCrawler
    >>> client = PixCrawler(api_key="...")
    >>> images = client.crawl("cat", max_images=10)
"""

from .config import get_config
from .exceptions import PixCrawlerError, ConfigurationError, APIError
from .models import Image, CrawlRequest
from .client import PixCrawler

__version__ = "0.1.0"
__all__ = [
    "PixCrawler", 
    "get_config", 
    "PixCrawlerError", 
    "ConfigurationError",
    "APIError",
    "Image", 
    "CrawlRequest"
]
