"""
PixCrawler SDK Utilities

Shared utilities for the SDK.
"""
import sys
from loguru import logger
from .config import get_config

def setup_logging():
    """
    Configure Loguru logging based on SDK settings.
    """
    config = get_config()
    logger.remove()
    
    # Add stderr handler
    logger.add(
        sys.stderr,
        level=config.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

    # Optional: disk logging?
    if config.DEBUG:
         logger.add("pixcrawler_sdk_debug.log", rotation="10 MB", retention="1 day", level="DEBUG")

# Initialize logging on import
setup_logging()

def get_logger(name: str):
    """
    Get a logger instance with bound name context.
    """
    return logger.bind(name=name)
