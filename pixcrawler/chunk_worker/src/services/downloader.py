"""
Downloader service for the Chunk Worker.

This module handles downloading images using the builder package's ImageDownloader.
It wraps the download process with retry logic and logging.
"""

import os
from typing import Tuple
from builder._downloader import ImageDownloader
from pixcrawler.chunk_worker.src.utils.logging import ContextLogger
from pixcrawler.chunk_worker.src.utils.retry import get_retry_strategy

class ChunkDownloader:
    """
    Service responsible for downloading images for a chunk.
    """

    def __init__(self, logger: ContextLogger):
        """
        Initialize the ChunkDownloader.

        Args:
            logger: ContextLogger instance for logging.
        """
        self.logger = logger
        # Initialize ImageDownloader with reasonable defaults
        # We suppress internal logging to avoid clutter, as we log high-level events
        self.downloader = ImageDownloader(
            feeder_threads=2,
            parser_threads=2,
            downloader_threads=4,
            log_level=30  # WARNING
        )

    @get_retry_strategy(max_attempts=3)
    def download_chunk(self, keyword: str, output_dir: str, target_count: int = 500) -> int:
        """
        Download images for a specific keyword.

        This method wraps the builder package's downloader with retry logic.
        It raises an exception if 0 images are downloaded to trigger a retry.

        Args:
            keyword: The search keyword.
            output_dir: Directory to save downloaded images.
            target_count: Number of images to download (default 500).

        Returns:
            int: The number of images downloaded.

        Raises:
            Exception: If download fails completely (count == 0).
        """
        self.logger.info(f"Starting download for keyword: '{keyword}', target: {target_count}")
        
        # ImageDownloader.download returns (success, count)
        success, count = self.downloader.download(keyword, output_dir, target_count)
        
        if count == 0:
             # If completely failed, raise exception to trigger retry
             msg = f"Download failed for keyword: {keyword}. No images downloaded."
             self.logger.warning(msg)
             raise Exception(msg)
             
        self.logger.info(f"Download completed. Downloaded {count} images.")
        return count
