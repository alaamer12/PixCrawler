import logging
import datetime
from typing import Dict, Any

logger = logging.getLogger("PixCrawler.resource_monitoring")

def log_alerts(statuses: Dict[str, str], metrics: Dict[str, Any]) -> None:
    """
    Log warnings and errors based on statuses.
    """
    timestamp = datetime.datetime.now().isoformat()
    
    for metric, status in statuses.items():
        if metric == "overall":
            continue
            
        if status == "ALERT":
            value = metrics.get(f"{metric}_pct") if metric != "chunks" else metrics.get("active_chunks")
            logger.error(f"RESOURCE ALERT [{timestamp}] - {metric.upper()}: {value} (Status: {status})")
        elif status == "WARN":
            value = metrics.get(f"{metric}_pct") if metric != "chunks" else metrics.get("active_chunks")
            logger.warning(f"RESOURCE WARNING [{timestamp}] - {metric.upper()}: {value} (Status: {status})")
