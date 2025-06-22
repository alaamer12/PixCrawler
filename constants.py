"""
Constants and logging configuration for the PixCrawler dataset generator.

This module defines constants, configurations and sets up logging for the PixCrawler
application. It configures both file and console logging handlers with appropriate
formatting and log levels.
"""

import logging
from typing import Set, List

__all__ = [
    'DEFAULT_CACHE_FILE',
    'DEFAULT_CONFIG_FILE',
    'DEFAULT_LOG_FILE',
    'ENGINES',
    'IMAGE_EXTENSIONS',
    'logger',
    'file_formatter',
    'console_handler'
]

# Default file paths for application data
DEFAULT_CACHE_FILE: str = "download_progress.json"
DEFAULT_CONFIG_FILE: str = "config.json"
DEFAULT_LOG_FILE: str = "pixcrawler.log"

# Supported search engines
ENGINES: List[str] = ["google", "bing", "baidu", "ddgs"]

# Image extensions supported by the application
IMAGE_EXTENSIONS: Set[str] = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

# Configure logging to file and console
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create file handler for detailed logs
file_handler = logging.FileHandler(DEFAULT_LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Create console handler for minimal output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)