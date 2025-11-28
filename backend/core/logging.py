import sys
from loguru import logger
from backend.core.config import get_settings

def setup_logging():
    """Configure logging for the application."""
    settings = get_settings()
    
    # Remove default handler
    logger.remove()
    
    # Add stdout handler
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    return logger
