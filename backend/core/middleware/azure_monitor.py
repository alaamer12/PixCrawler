"""Azure Monitor middleware for FastAPI request tracking.

This middleware automatically tracks HTTP requests, responses, and dependencies
using Azure Application Insights.

Classes:
    AzureMonitorMiddleware: ASGI middleware for request tracking

Features:
    - Automatic request/response tracking
    - Duration measurement
    - Status code tracking
    - Correlation ID propagation
    - Exception tracking
    - Custom properties support
"""

import time
from typing import Callable, Optional
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from utility.logging_config import get_logger
from backend.core.monitoring import AzureMonitorClient

__all__ = ['AzureMonitorMiddleware']

logger = get_logger(__name__)


class AzureMonitorMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking HTTP requests with Azure Application Insights.
    
    Automatically tracks all incoming HTTP requests and their responses,
    including duration, status codes, and custom properties.
    
    Attributes:
        monitor_client: Azure Monitor client instance
        exclude_paths: List of paths to exclude from tracking
    
    Example:
        ```python
        from backend.core.monitoring import setup_azure_monitor
        from backend.core.middleware.azure_monitor import AzureMonitorMiddleware
        
        # Setup monitor
        monitor = setup_azure_monitor(
            connection_string="InstrumentationKey=...",
            sampling_rate=1.0
        )
        
        # Add middleware
        if monitor:
            app.add_middleware(AzureMonitorMiddleware, monitor_client=monitor)
        ```
    """
    
    def __init__(
        self,
        app: ASGIApp,
        monitor_client: AzureMonitorClient,
        exclude_paths: Optional[list[str]] = None,
    ) -> None:
        """Initialize Azure Monitor middleware.
        
        Args:
            app: ASGI application
            monitor_client: Azure Monitor client instance
            exclude_paths: List of paths to exclude from tracking (e.g., ["/health", "/metrics"])
        """
        super().__init__(app)
        self.monitor_client = monitor_client
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/favicon.ico"]
        logger.info(
            f"Initialized Azure Monitor middleware "
            f"(excluding: {', '.join(self.exclude_paths)})"
        )
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and track with Azure Monitor.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler
            
        Returns:
            HTTP response
        """
        # Skip tracking for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        request.state.correlation_id = correlation_id
        
        # Start timing
        start_time = time.time()
        
        # Process request
        response = None
        exception = None
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            exception = e
            # Track exception
            self.monitor_client.track_exception(
                exception=e,
                properties={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                }
            )
            raise
            
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Determine success
            success = exception is None and (response is not None and 200 <= response.status_code < 400)
            
            # Get status code
            status_code = response.status_code if response else 500
            
            # Build properties
            properties = {
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            }
            
            # Add user ID if authenticated
            if hasattr(request.state, "user") and request.state.user:
                properties["user_id"] = str(request.state.user.id)
            
            # Track request
            self.monitor_client.track_request(
                name=f"{request.method} {request.url.path}",
                url=str(request.url),
                duration=duration,
                response_code=status_code,
                success=success,
                properties=properties,
            )
            
            # Add correlation ID to response headers
            if response:
                response.headers["X-Correlation-ID"] = correlation_id
