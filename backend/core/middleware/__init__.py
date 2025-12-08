"""Middleware module for PixCrawler backend.

This module provides custom middleware for FastAPI including:
- Azure Monitor request tracking
- Request ID tracking
- Performance monitoring
- Error tracking

Usage:
    from backend.core.middleware import AzureMonitorMiddleware
    
    app.add_middleware(AzureMonitorMiddleware, monitor_client=monitor)
"""

from backend.core.middleware.azure_monitor import AzureMonitorMiddleware

__all__ = [
    'AzureMonitorMiddleware',
]
