"""
PixCrawler Logging System using Loguru and Pydantic Settings.

A production-ready logging package that provides consistent logging across the
entire monorepo with type-safe configuration, environment-based settings, and
proper log management - all powered by Loguru.

Classes:
    LoggingSettings: Type-safe logging configuration with Pydantic
    Environment: Environment types enumeration
    LogLevel: Log levels enumeration

Functions:
    setup_logging: Setup logging for the entire application
    get_logger: Get the configured logger instance
    get_logging_settings: Get cached logging settings
    set_log_level: Set global log level
    get_config_info: Get current logging configuration

Features:
    - Environment-based configuration (development, production, testing)
    - Type-safe settings with Pydantic v2
    - JSON logging for production (Azure Monitor compatible)
    - File rotation and retention
    - Colored console output for development
    - Automatic noisy package filtering

Example:
    ```python
    from utility.logging_config import setup_logging, get_logger

    # Setup logging for the application
    setup_logging(environment='development')

    # Get the logger (same instance everywhere)
    logger = get_logger()
    logger.info("Application started")

    # With custom settings
    from utility.logging_config import LoggingSettings
    config = LoggingSettings(environment='production', use_json=True)
    setup_logging(config=config)
    ```
"""

from .config import (
    Environment,
    LogLevel,
    LoggingSettings,
    get_config_info,
    get_logger,
    get_logging_settings,
    set_log_level,
    setup_logging,
)

__version__ = "0.1.0"
__author__ = "PixCrawler Team"

__all__ = [
    'setup_logging',
    'get_logger',
    'get_logging_settings',
    'set_log_level',
    'get_config_info',
    'LogLevel',
    'Environment',
    'LoggingSettings',
]
