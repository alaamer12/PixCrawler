"""
PixCrawler Simplified Logging System using Loguru

A lightweight logging package that provides consistent logging across the entire monorepo
with support for development and production environments, structured logging, and proper
log management - all powered by Loguru.

Functions:
    setup_logging: Setup logging for the entire application
    get_logger: Get the configured logger instance

Example:
    ```python
    from logging_config import setup_logging, get_logger

    # Setup logging for the application
    setup_logging(environment='development')

    # Get the logger (same instance everywhere)
    logger = get_logger()
    logger.info("Application started")
    ```
"""

from logging_config.config import setup_logging, get_logger, LogLevel, Environment

__version__ = "0.1.0"
__author__ = "PixCrawler Team"

__all__ = [
    'setup_logging',
    'get_logger',
    'LogLevel',
    'Environment'
]
