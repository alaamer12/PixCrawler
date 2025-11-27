"""
Compressor service for the Chunk Worker.

This module handles compressing validated images into a ZIP file.
"""

import zipfile
import os
from pixcrawler.chunk_worker.src.utils.logging import ContextLogger
from pixcrawler.chunk_worker.src.utils.retry import get_retry_strategy

class ChunkCompressor:
    """
    Service responsible for compressing images into a ZIP archive.
    """

    def __init__(self, logger: ContextLogger):
        """
        Initialize the ChunkCompressor.

        Args:
            logger: ContextLogger instance for logging.
        """
        self.logger = logger

    @get_retry_strategy(max_attempts=2)
    def compress_chunk(self, source_dir: str, chunk_id: str, output_dir: str) -> str:
        """
        Compress all files in source_dir into a ZIP file.

        Args:
            source_dir: Directory containing files to compress.
            chunk_id: ID of the chunk (used for naming).
            output_dir: Directory to save the ZIP file.

        Returns:
            str: Path to the created ZIP file.
        """
        zip_filename = f"chunk_{chunk_id}.zip"
        zip_path = os.path.join(output_dir, zip_filename)
        
        self.logger.info(f"Starting compression of {source_dir} to {zip_path}")
        
        if not os.path.exists(source_dir) or not os.listdir(source_dir):
            raise ValueError(f"Source directory {source_dir} is empty or does not exist")

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Store files relative to source_dir
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
                        
            self.logger.info(f"Compression completed: {zip_path}")
            return zip_path
        except Exception as e:
            self.logger.error(f"Compression failed: {e}")
            raise
