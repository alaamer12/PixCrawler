"""
Request size limit middleware for preventing large request attacks.

This middleware validates request size before processing to prevent
memory exhaustion and DoS attacks.
"""
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

__all__ = ['RequestSizeLimitMiddleware']


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size to prevent DoS attacks."""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        """
        Initialize request size limit middleware.
        
        Args:
            app: FastAPI application
            max_size: Maximum request size in bytes (default: 10MB)
        """
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Check request size before processing.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response or raises HTTPException if size exceeds limit
        """
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request body too large. Maximum size: {self.max_size} bytes"
                )
        
        return await call_next(request)
