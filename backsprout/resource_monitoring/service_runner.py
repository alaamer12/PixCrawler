import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager

from .config import settings
from .metrics_endpoint import app, update_state
from .chunk_tracker import count_active_chunks
from .threshold_manager import evaluate_thresholds
from .alerting import log_alerts

# Configure logging
logging.basicConfig(level=logging.INFO, format=settings.log_format if hasattr(settings, 'log_format') else "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PixCrawler.resource_monitoring")

# Global flag for shutdown
running = True

async def poll_metrics():
    """
    Main polling loop.
    """
    logger.info(f"Starting metrics polling loop. Mode: {settings.MODE}, Interval: {settings.POLL_INTERVAL_SECONDS}s")
    
    while running:
        try:
            metrics = {}
            
            # 1. Get System Metrics (Disk/Memory)
            if settings.MODE == "local":
                from .monitoring_local import get_disk_usage_pct, get_memory_usage_pct
                metrics["disk_pct"] = get_disk_usage_pct()
                metrics["disk_pct"] = get_disk_usage_pct()
                metrics["memory_pct"] = get_memory_usage_pct()
            elif settings.MODE == "azure":
                from .monitoring_azure import query_metrics
                
                if settings.AZURE_RESOURCE_ID:
                    az_metrics = query_metrics(
                        settings.AZURE_RESOURCE_ID, 
                        settings.AZURE_METRIC_NAMES
                    )
                    
                    if az_metrics:
                        # Map Azure metrics to our internal keys
                        # This mapping assumes standard Azure metric names. 
                        # Adjust config.AZURE_METRIC_NAMES and this mapping as needed.
                        metrics["memory_pct"] = az_metrics.get("MemoryPercentage")
                        
                        # DiskQueueLength is not a percentage, so we might need a different metric or logic
                        # For now, we just log it or map it if it makes sense. 
                        # If using 'Disk Usage', map it here.
                        # metrics["disk_pct"] = az_metrics.get("DiskUsage") 
                        pass
                else:
                    logger.warning("Azure mode enabled but AZURE_RESOURCE_ID not set.")
            
            # 2. Get Application Metrics (Chunks)
            metrics["active_chunks"] = await count_active_chunks()
            
            # 3. Evaluate Thresholds
            statuses = evaluate_thresholds(metrics)
            
            # 4. Log Alerts
            log_alerts(statuses, metrics)
            
            # 5. Update Endpoint State
            update_state(metrics, statuses)
            
        except Exception as e:
            logger.error(f"Error in polling loop: {e}")
            
        # Wait for next poll
        # Check running flag frequently during wait if needed, or just wait
        if running:
            await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app):
    # Startup
    global running
    running = True
    task = asyncio.create_task(poll_metrics())
    yield
    # Shutdown
    logger.info("Shutting down resource monitoring service...")
    running = False
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

# Attach lifespan to app
app.router.lifespan_context = lifespan

def main():
    """
    Entry point for the service.
    """
    # Run uvicorn
    # Uvicorn handles signals (SIGINT, SIGTERM) automatically
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()
