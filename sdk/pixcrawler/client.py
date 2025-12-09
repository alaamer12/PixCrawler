"""
PixCrawler Client

This module provides the main entry point for the SDK.
"""
from typing import Optional, List
from pathlib import Path

from .config import get_config
from .models import CrawlRequest
from .services.builder import CrawlerEngine
from .services.validator import ValidationEngine

class PixCrawler:
    """
    Main SDK Client for PixCrawler.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.config = get_config()
        if api_key:
            self.config.API_KEY = api_key
            
        self.crawler = CrawlerEngine()
        self.validator = ValidationEngine()

    async def crawl_local(
        self, 
        keyword: str, 
        max_images: int = 100, 
        output_dir: Optional[str] = None
    ):
        """
        Run a local crawl Job.
        """
        request = CrawlRequest(keyword=keyword, max_images=max_images)
        out = Path(output_dir) if output_dir else None
        
        # Crawl
        crawl_results = await self.crawler.crawl(request, out)
        
        # Validate (optional auto-validation?)
        # For now, just return crawl results
        return crawl_results

    async def validate_local(self, directory: str):
        """
        Run local validation.
        """
        return await self.validator.validate_directory(Path(directory))
