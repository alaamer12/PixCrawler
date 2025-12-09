"""
Builder Service Wrapper

This module wraps the legacy synchronous builder package to provide an async interface.
"""
from pathlib import Path
from typing import List, Optional

from builder._downloader import ImageDownloader
from builder._engine import EngineProcessor
from builder._search_engines import EngineResult

from .._internal.concurrency import run_in_thread
from ..config import get_config
from ..models import CrawlRequest
from ..utils import get_logger

logger = get_logger(__name__)

class CrawlerEngine:
    """
    Async wrapper around the PixCrawler Builder engine.
    """
    def __init__(self):
        self.config = get_config()

    async def crawl(self, request: CrawlRequest, output_dir: Optional[Path] = None) -> List[EngineResult]:
        """
        Execute a crawl operation asynchronously.

        Args:
            request: Crawl configuration.
            output_dir: Directory to save images. Defaults to config default.
        """
        out = output_dir or self.config.DEFAULT_OUTPUT_DIR
        out = Path(out) / request.keyword.replace(" ", "_")
        
        # Ensure output directory exists (blocking I/O, but fast)
        out.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting crawl for '{request.keyword}' output_to='{out}'")

        # Run the heavy blocking crawler in a thread
        results = await run_in_thread(
            self._run_crawler_sync,
            request,
            str(out)
        )
        
        return results

    def _run_crawler_sync(self, request: CrawlRequest, out_dir: str) -> List[EngineResult]:
        """
        Internal synchronous method to run the actual builder logic.
        """
        # Initialize Downloader
        downloader = ImageDownloader(
            process_id=f"sdk-crawl-{request.keyword}",
            storage={'root_dir': out_dir},
            feeder_threads=self.config.DEFAULT_FEEDER_THREADS,
            parser_threads=self.config.DEFAULT_PARSER_THREADS,
            downloader_threads=self.config.DEFAULT_DOWNLOADER_THREADS
        )

        # Initialize Processor
        processor = EngineProcessor(downloader)

        # Configure Engines (hacky injection if needed, or rely on defaults)
        # For now, we assume _config.py in builder handles defaults, 
        # but ideally we should inject config here.
        
        # Override variations if not requested
        variations = [request.keyword] # TODO: Add variations logic if needed
        if request.use_variations:
             # Basic variations for now, or fetch from builder's logic
             variations = [request.keyword] # Placeholder

        # Execute
        results = processor.download_with_sequential_engines(
            keyword=request.keyword,
            variations=variations,
            out_dir=out_dir,
            max_num=request.max_images
        )
        
        # Cleanup
        downloader.signal_workers_to_stop()
        
        return results
