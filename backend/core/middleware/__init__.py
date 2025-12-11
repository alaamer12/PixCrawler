"""
Middleware module for PixCrawler backend.

This module provides custom middleware for FastAPI following professional patterns:
- Request ID tracking for debugging and log correlation
- Security headers for protection against common vulnerabilities
- Request size limits to prevent DoS attacks
- Request timeout to prevent hanging requests
- Request/response logging for monitoring
- Azure Monitor integration for production monitoring
- GZip compression for response optimization
- Trusted host validation for production
- HTTPS redirect for production

Usage:
    from backend.core.middleware import setup_middleware
    
    # In main.py after CORS configuration
    setup_middleware(app)
"""
from fastapi import FastAPI
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from backend.core.middleware.request_id import RequestIDMiddleware
from backend.core.middleware.security_headers import SecurityHeadersMiddleware
from backend.core.middleware.request_size import RequestSizeLimitMiddleware
from backend.core.middleware.timeout import TimeoutMiddleware
from backend.core.middleware.logging import LoggingMiddleware
from backend.core.config import get_settings

try:
    from backend.core.middleware.azure_monitor import AzureMonitorMiddleware
    AZURE_MONITOR_AVAILABLE = True
except ImportError:
    AZURE_MONITOR_AVAILABLE = False

try:
    from backend.core.metrics_middleware import MetricsMiddleware
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

__all__ = [
    'AzureMonitorMiddleware',
    'RequestIDMiddleware',
    'SecurityHeadersMiddleware',
    'RequestSizeLimitMiddleware',
    'TimeoutMiddleware',
    'LoggingMiddleware',
    'setup_middleware',
]


def setup_middleware(app: FastAPI, settings=None) -> None:
    """
    Configure all middleware for the application.
    
    Middleware is applied in reverse order (last added = first executed).
    Order matters for security and functionality.
    
    Args:
        app: FastAPI application instance
        settings: Application settings (optional, will be fetched if not provided)
    
    Note:
        Execution order (first to last):
        1. RequestSizeLimitMiddleware - Check request size first
        2. TimeoutMiddleware - Prevent hanging requests
        3. TrustedHostMiddleware - Validate host headers (production only)
        4. HTTPSRedirectMiddleware - Redirect to HTTPS (production only)
        5. SecurityHeadersMiddleware - Add security headers
        6. GZipMiddleware - Compress responses
        7. RequestIDMiddleware - Add request tracking
        8. LoggingMiddleware - Log everything
        9. MetricsMiddleware - Collect metrics (if available)
        10. AzureMonitorMiddleware - Production monitoring (if configured)
        
        CORS middleware should be configured in main.py BEFORE calling this function.
    """
    if settings is None:
        settings = get_settings()
    
    # 1. Request Size Limit - Check request size first (10MB default)
    app.add_middleware(
        RequestSizeLimitMiddleware,
        max_size=10 * 1024 * 1024  # 10MB
    )
    
    # 2. Timeout Middleware - Prevent hanging requests (30s default)
    app.add_middleware(
        TimeoutMiddleware,
        timeout_seconds=30
    )
    
    # 3. Trusted Host Middleware - Validate host headers (production only)
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=getattr(settings, 'allowed_hosts', ['*']),
            www_redirect=True
        )
    
    # 4. HTTPS Redirect - Force HTTPS in production
    if settings.environment == "production" and getattr(settings, 'force_https', False):
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # 5. Security Headers - Add security headers to all responses
    app.add_middleware(
        SecurityHeadersMiddleware,
        environment=settings.environment
    )
    
    # 6. GZip Middleware - Compress responses (minimum size: 500 bytes)
    app.add_middleware(
        GZipMiddleware,
        minimum_size=500,
        compresslevel=6  # Balance between speed and compression
    )
    
    # 7. Request ID Middleware - Add unique request ID for tracking
    app.add_middleware(RequestIDMiddleware)
    
    # 8. Logging Middleware - Log all requests and responses
    app.add_middleware(LoggingMiddleware)
    
    # 9. Metrics Middleware - Collect application metrics (if available)
    if METRICS_AVAILABLE:
        app.add_middleware(MetricsMiddleware)
    
    # 10. Azure Monitor Middleware - Production monitoring (optional)
    # Note: Azure Monitor middleware requires additional configuration
    # and is typically enabled only in production environments
    # Uncomment and configure when Azure Monitor is set up:
    # if AZURE_MONITOR_AVAILABLE and settings.environment == "production":
    #     app.add_middleware(AzureMonitorMiddleware)
