"""
Logging middleware for request/response logging.

This middleware logs all incoming requests and outgoing responses
for debugging, monitoring, and audit purposes using the centralized
utility.logging_config package.

Features:
- Structured logging with request ID correlation
- Request/response timing
- Client information tracking
- User agent logging
- Error tracking with stack traces
"""
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from utility.logging_config import get_logger

__all__ = ['LoggingMiddleware']

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests and responses using utility.logging_config.
    
    This middleware provides comprehensive request/response logging with:
    - Request ID correlation
    - Timing information
    - Client IP and user agent
    - Status codes and error tracking
    - Structured logging for easy parsing
    """
    
    def __init__(self, app, log_request_body: bool = False, log_response_body: bool = False):
        """
        Initialize logging middleware.
        
        Args:
            app: FastAPI application
            log_request_body: Whether to log request bodies (default: False for security)
            log_response_body: Whether to log response bodies (default: False for performance)
        """
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Log request and response details using utility.logging_config.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response with timing information
        """
        # Start timer
        start_time = time.time()
        
        # Get request ID if available (set by RequestIDMiddleware)
        request_id = getattr(request.state, 'request_id', 'N/A')
        
        # Get client information
        client_host = request.client.host if request.client else 'unknown'
        user_agent = request.headers.get('user-agent', 'unknown')
        
        # Log request with structured data
        logger.info(
            f"→ Request started: {request.method} {request.url.path}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'query_params': str(request.query_params),
                'client_host': client_host,
                'user_agent': user_agent,
            }
        )
        
        # Process request and handle errors
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Determine log level based on status code
            if response.status_code >= 500:
                log_level = logger.error
            elif response.status_code >= 400:
                log_level = logger.warning
            else:
                log_level = logger.info
            
            # Log response with structured data
            log_level(
                f"← Request completed: {request.method} {request.url.path} "
                f"[{response.status_code}] [{duration:.3f}s]",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_seconds': round(duration, 3),
                    'client_host': client_host,
                }
            )
            
            # Add timing header
            response.headers["X-Process-Time"] = f"{duration:.3f}"
            
            return response
            
        except Exception as e:
            # Calculate duration even on error
            duration = time.time() - start_time
            
            # Log error with full context
            logger.error(
                f"✗ Request failed: {request.method} {request.url.path} "
                f"[{duration:.3f}s] - {str(e)}",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_seconds': round(duration, 3),
                    'client_host': client_host,
                    'error': str(e),
                    'error_type': type(e).__name__,
                },
                exc_info=True  # Include stack trace
            )
            
            # Re-raise to let FastAPI handle it
            raise
