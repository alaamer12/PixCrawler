"""
Status Manager service for the Chunk Worker.

This module handles updating the status of chunks in the database.
"""

from typing import Any
from pixcrawler.chunk_worker.src.utils.logging import ContextLogger

class StatusManager:
    """
    Service responsible for managing chunk status updates.
    """

    def __init__(self, logger: ContextLogger):
        """
        Initialize the StatusManager.

        Args:
            logger: ContextLogger instance for logging.
        """
        self.logger = logger

    def update_status(self, chunk_id: str, status: str, details: Any = None) -> None:
        """
        Update the status of a chunk.

        Args:
            chunk_id: The ID of the chunk.
            status: The new status (e.g., PROCESSING, COMPLETED, FAILED).
            details: Optional details or metadata to save with the status.
        """
        # In a real implementation, this would write to the database.
        # For now, we log the status change.
        msg = f"Updating chunk status to: {status}"
        if details:
            msg += f" | Details: {details}"
        self.logger.info(msg)
