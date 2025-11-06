"""
API endpoints for system metrics and health checks.
"""
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.metrics import MetricResponse
from app.services.metrics_service import MetricsService

router = APIRouter()


def get_metrics_service(db: Session = Depends(get_db)) -> MetricsService:
    """Dependency for getting the metrics service."""
    return MetricsService(db)


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/metrics/collect", response_model=List[MetricResponse])
async def collect_system_metrics(
    service_name: str = "system",
    metrics_service: MetricsService = Depends(get_metrics_service)
) -> List[MetricResponse]:
    """
    Collect and store system metrics (CPU, memory, disk usage).
    
    Args:
        service_name: Name of the service to associate with the metrics
        
    Returns:
        List of collected metrics
    """
    return await metrics_service.collect_system_metrics(service_name=service_name)


@router.get("/status")
async def system_status() -> Dict[str, Any]:
    """Get current system status and resource usage."""
    import psutil
    
    # Get CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Get memory usage
    memory = psutil.virtual_memory()
    
    # Get disk usage
    disk = psutil.disk_usage('/')
    
    return {
        "status": "operational",
        "cpu": {
            "percent": cpu_percent,
            "cores": psutil.cpu_count(),
            "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        },
        "process": {
            "pid": psutil.Process().pid,
            "memory_info": dict(psutil.Process().memory_info()._asdict()),
            "cpu_percent": psutil.Process().cpu_percent(interval=0.1)
        }
    }
