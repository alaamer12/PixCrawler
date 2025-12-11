"""Monitoring and observability module for PixCrawler backend.

This module provides monitoring integrations for production environments:
- Azure Application Insights
- Custom metrics and events
- Request/response tracking
- Dependency tracking
- Exception logging

Usage:
    from backend.core.monitoring import setup_azure_monitor
    
    monitor = setup_azure_monitor(
        connection_string="InstrumentationKey=...",
        sampling_rate=0.5
    )
    
    if monitor:
        monitor.track_event("user_signup", {"user_id": "123"})
        monitor.track_metric("images_processed", 100)
"""

from .azure_monitor import (
    AzureMonitorClient,
    AZURE_MONITOR_AVAILABLE,
    setup_azure_monitor,
)

__all__ = [
    'AzureMonitorClient',
    'AZURE_MONITOR_AVAILABLE',
    'setup_azure_monitor',
]
