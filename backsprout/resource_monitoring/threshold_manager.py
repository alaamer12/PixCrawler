from typing import Dict, Any, Optional
from .config import settings

def evaluate_thresholds(metrics: Dict[str, Optional[float]]) -> Dict[str, str]:
    """
    Evaluate metrics against configured thresholds.
    Returns a dictionary of statuses: OK, WARN, ALERT.
    """
    statuses = {
        "disk": "OK",
        "memory": "OK",
        "chunks": "OK",
        "overall": "OK"
    }
    
    # Disk
    disk_pct = metrics.get("disk_pct")
    if disk_pct is not None:
        if disk_pct >= settings.DISK_THRESHOLD_ALERT:
            statuses["disk"] = "ALERT"
        elif disk_pct >= settings.DISK_THRESHOLD_WARN:
            statuses["disk"] = "WARN"
            
    # Memory
    mem_pct = metrics.get("memory_pct")
    if mem_pct is not None:
        if mem_pct >= settings.MEMORY_THRESHOLD_ALERT:
            statuses["memory"] = "ALERT"
        elif mem_pct >= settings.MEMORY_THRESHOLD_WARN:
            statuses["memory"] = "WARN"
            
    # Chunks
    active_chunks = metrics.get("active_chunks")
    if active_chunks is not None:
        if active_chunks >= settings.CHUNK_THRESHOLD_ALERT:
            statuses["chunks"] = "ALERT"
        elif active_chunks >= settings.CHUNK_THRESHOLD_WARN:
            statuses["chunks"] = "WARN"
            
    # Overall
    if "ALERT" in statuses.values():
        statuses["overall"] = "ALERT"
    elif "WARN" in statuses.values():
        statuses["overall"] = "WARN"
        
    return statuses
