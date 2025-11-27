"""
Cleanup service for the Chunk Worker.

This module handles cleaning up temporary files and directories.
"""

import shutil
import os
from pixcrawler.chunk_worker.src.utils.logging import ContextLogger

class ChunkCleanup:
    """
    Service responsible for cleaning up resources.
    """

    def __init__(self, logger: ContextLogger):
        """
        Initialize the ChunkCleanup.

        Args:
            logger: ContextLogger instance for logging.
        """
        self.logger = logger

    def cleanup(self, *paths: str):
        """
        Remove files or directories.

        Args:
            *paths: Variable number of paths to remove.
        """
        for path in paths:
            if not path:
                continue
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    self.logger.info(f"Removed file: {path}")
                elif os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                    self.logger.info(f"Removed directory: {path}")
            except FileNotFoundError:
                pass
            except PermissionError as pe:
                self.logger.warning(f"Permission denied cleaning up {path}: {pe}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup {path}: {e}")
