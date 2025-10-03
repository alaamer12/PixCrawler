"""
Base service class with common functionality.
"""

from abc import ABC
from typing import Any

from pixcrawler_logging import get_logger


class BaseService(ABC):
    """Base service class with common functionality."""

    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)

    def log_operation(self, operation: str, **kwargs: Any) -> None:
        """Log service operation with context."""
        self.logger.info(f"Service operation: {operation}", extra=kwargs)
