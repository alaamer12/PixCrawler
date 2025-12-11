"""
Request timeout middleware for preventing hanging requests.

This middleware enforces a maximum request processing time to prevent
resource exhaustion from slow or hanging requests.
"""
import asyncio
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

__all__ = ['TimeoutMiddleware']


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Enforce request timeout to prevent hanging requests."""
    
    def __init__(self, app, timeout_seconds: int = 30):
        """
        Initialize timeout middleware.
        
        Args:
            app: FastAPI application
            timeout_seconds: Maximum request processing time in seconds (default: 30)
        """
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request with timeout.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response or raises HTTPException on timeout
        """
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Request timeout after {self.timeout_seconds} seconds"
            )
