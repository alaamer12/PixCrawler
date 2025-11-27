import logging
import psutil
from typing import Optional

logger = logging.getLogger(__name__)

def get_disk_usage_pct(path: str = "/") -> Optional[float]:
    """Get disk usage percentage for the given path."""
    try:
        usage = psutil.disk_usage(path)
        return usage.percent
    except Exception as e:
        logger.error(f"Error getting disk usage for {path}: {e}")
        return None

def get_memory_usage_pct() -> Optional[float]:
    """Get virtual memory usage percentage."""
    try:
        mem = psutil.virtual_memory()
        return mem.percent
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return None
