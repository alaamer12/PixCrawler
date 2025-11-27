"""
Backend logging configuration.

This module provides a centralized logger for the backend package,
integrating with the project's logging_config package.
"""

from logging_config import get_logger

# Create a logger instance for the backend package
logger = get_logger("backend")

__all__ = ["logger"]
