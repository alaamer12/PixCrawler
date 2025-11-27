"""
Metrics middleware for request monitoring.

This middleware tracks request processing times, status codes, and
resource usage for API endpoints.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.settings import get_settings
from utility.logging_config import get_logger

settings = get_settings()
logger = get_logger("metrics_middleware")


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking request metrics.
    
    Logs request duration, status codes, and path information.
    Can be extended to store metrics in the database asynchronously.
    """
    
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track metrics.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response object
        """
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
            
        except Exception as e:
            status_code = 500
            raise e
            
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log metrics (could be enhanced to write to DB)
            if request.url.path.startswith("/api/"):
                logger.info(
                    "Request metrics",
                    extra={
                        "path": request.url.path,
                        "method": request.method,
                        "status_code": status_code,
                        "duration_ms": round(duration_ms, 2),
                        "client_ip": request.client.host if request.client else None
                    }
                )
