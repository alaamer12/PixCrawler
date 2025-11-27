"""
Logging utility for the Chunk Worker.

This module provides a context-aware logger that ensures all logs include
task_id, chunk_id, and phase information in a consistent format.
"""

import sys
from typing import Any
from loguru import logger

# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

class ContextLogger:
    """
    A logger wrapper that prepends context information to log messages.
    
    Format: [task_id=XYZ][chunk=81][phase=DOWNLOAD] Message
    """
    
    def __init__(self, task_id: str, chunk_id: Any, phase: str):
        """
        Initialize the ContextLogger.

        Args:
            task_id: The unique ID of the Celery task.
            chunk_id: The ID of the chunk being processed.
            phase: The current processing phase (e.g., DOWNLOAD, VALIDATE).
        """
        self.task_id = task_id
        self.chunk_id = chunk_id
        self.phase = phase
        self.prefix = f"[task_id={task_id}][chunk={chunk_id}][phase={phase}]"
        # Bind context for structured logging backends if needed in future
        self.logger = logger.bind(task_id=task_id, chunk_id=chunk_id, phase=phase)

    def info(self, message: str, **kwargs):
        """Log an info message with context."""
        self.logger.info(f"{self.prefix} {message}", **kwargs)

    def error(self, message: str, **kwargs):
        """Log an error message with context."""
        self.logger.error(f"{self.prefix} {message}", **kwargs)

    def warning(self, message: str, **kwargs):
        """Log a warning message with context."""
        self.logger.warning(f"{self.prefix} {message}", **kwargs)

    def debug(self, message: str, **kwargs):
        """Log a debug message with context."""
        self.logger.debug(f"{self.prefix} {message}", **kwargs)

    def exception(self, message: str, **kwargs):
        """Log an exception with context."""
        self.logger.exception(f"{self.prefix} {message}", **kwargs)

def get_logger(task_id: str, chunk_id: Any, phase: str) -> ContextLogger:
    """
    Factory function to get a ContextLogger instance.

    Args:
        task_id: The unique ID of the Celery task.
        chunk_id: The ID of the chunk being processed.
        phase: The current processing phase.

    Returns:
        ContextLogger: Configured logger instance.
    """
    return ContextLogger(task_id, chunk_id, phase)
