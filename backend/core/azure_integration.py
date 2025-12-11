"""Azure services integration helper for PixCrawler backend.

This module provides helper functions to integrate Azure services into the
FastAPI application, including Application Insights monitoring and Blob Storage.

Functions:
    setup_azure_monitor_middleware: Setup Azure Monitor middleware
    initialize_azure_services: Initialize all Azure services
    check_azure_services_health: Health check for Azure services

Features:
    - Automatic Azure Monitor setup from settings
    - Graceful degradation when Azure services unavailable
    - Health checks for all Azure services
    - Production vs development behavior
"""

from typing import Optional, Dict, Any

from fastapi import FastAPI

from backend.core.settings import Settings
from backend.core.monitoring import setup_azure_monitor, AzureMonitorClient, AZURE_MONITOR_AVAILABLE
from backend.core.middleware import AzureMonitorMiddleware
from backend.storage.azure_blob import AZURE_AVAILABLE
from utility.logging_config import get_logger

__all__ = [
    'setup_azure_monitor_middleware',
    'initialize_azure_services',
    'check_azure_services_health',
]

logger = get_logger(__name__)


def setup_azure_monitor_middleware(
    app: FastAPI,
    settings: Settings,
) -> Optional[AzureMonitorClient]:
    """Setup Azure Application Insights monitoring middleware.
    
    Automatically configures Azure Monitor based on settings and adds
    middleware to track HTTP requests, dependencies, and exceptions.
    
    Args:
        app: FastAPI application instance
        settings: Application settings
        
    Returns:
        AzureMonitorClient instance if successful, None otherwise
        
    Example:
        ```python
        from backend.core.azure_integration import setup_azure_monitor_middleware
        
        monitor = setup_azure_monitor_middleware(app, settings)
        if monitor:
            logger.info("Azure Monitor enabled")
        ```
    """
    # Check if Azure Monitor is enabled
    if not settings.azure.monitor.enabled:
        logger.info("Azure Monitor is disabled in settings")
        return None
    
    # Check if SDK is available
    if not AZURE_MONITOR_AVAILABLE:
        logger.warning(
            "Azure Monitor SDK not installed. "
            "Install with: pip install opencensus-ext-azure"
        )
        return None
    
    # Get connection string
    connection_string = settings.azure.monitor.get_connection_string()
    if not connection_string:
        logger.warning("Azure Monitor connection string not configured")
        return None
    
    try:
        # Setup Azure Monitor client
        monitor = setup_azure_monitor(
            connection_string=connection_string,
            sampling_rate=settings.azure.monitor.sampling_rate,
            log_level=settings.azure.monitor.log_level,
            track_dependencies=settings.azure.monitor.track_dependencies,
            track_requests=settings.azure.monitor.track_requests,
            track_exceptions=settings.azure.monitor.track_exceptions,
        )
        
        if not monitor:
            logger.warning("Failed to setup Azure Monitor")
            return None
        
        # Add middleware for automatic request tracking
        app.add_middleware(
            AzureMonitorMiddleware,
            monitor_client=monitor,
            exclude_paths=["/health", "/metrics", "/favicon.ico", "/docs", "/redoc", "/openapi.json"]
        )
        
        logger.info(
            f"Azure Monitor enabled: "
            f"sampling={settings.azure.monitor.sampling_rate}, "
            f"log_level={settings.azure.monitor.log_level}"
        )
        
        return monitor
        
    except Exception as e:
        logger.error(f"Failed to setup Azure Monitor: {e}")
        
        # In production, this might be critical
        if settings.environment == "production":
            logger.warning(
                "Azure Monitor setup failed in production. "
                "Application will continue without monitoring."
            )
        
        return None


def initialize_azure_services(settings: Settings) -> Dict[str, Any]:
    """Initialize all Azure services and return status.
    
    Checks availability and configuration of all Azure services:
    - Azure Blob Storage
    - Azure Application Insights
    - Azure App Service (if running in Azure)
    
    Args:
        settings: Application settings
        
    Returns:
        Dictionary with service status and details
        
    Example:
        ```python
        azure_status = initialize_azure_services(settings)
        logger.info(f"Azure services: {azure_status}")
        ```
    """
    status = {
        "blob_storage": {
            "available": False,
            "configured": False,
            "enabled": False,
        },
        "application_insights": {
            "available": False,
            "configured": False,
            "enabled": False,
        },
        "app_service": {
            "detected": False,
            "name": None,
        },
    }
    
    # Check Blob Storage
    status["blob_storage"]["available"] = AZURE_AVAILABLE
    status["blob_storage"]["configured"] = bool(
        settings.azure.blob.connection_string or 
        (settings.azure.blob.account_name and settings.azure.blob.account_key)
    )
    status["blob_storage"]["enabled"] = (
        settings.storage.storage_provider == "azure" and
        status["blob_storage"]["available"] and
        status["blob_storage"]["configured"]
    )
    
    # Check Application Insights
    status["application_insights"]["available"] = AZURE_MONITOR_AVAILABLE
    status["application_insights"]["configured"] = bool(
        settings.azure.monitor.connection_string or
        settings.azure.monitor.instrumentation_key
    )
    status["application_insights"]["enabled"] = (
        settings.azure.monitor.enabled and
        status["application_insights"]["available"] and
        status["application_insights"]["configured"]
    )
    
    # Check if running in Azure App Service
    status["app_service"]["detected"] = settings.azure.is_azure_environment()
    status["app_service"]["name"] = settings.azure.get_service_name()
    
    # Log summary
    logger.info("Azure services initialization:")
    logger.info(f"  - Blob Storage: {'✓' if status['blob_storage']['enabled'] else '✗'}")
    logger.info(f"  - Application Insights: {'✓' if status['application_insights']['enabled'] else '✗'}")
    logger.info(f"  - App Service: {'✓' if status['app_service']['detected'] else '✗'} {status['app_service']['name'] or ''}")
    
    return status


async def check_azure_services_health(settings: Settings) -> Dict[str, Any]:
    """Perform health checks on Azure services.
    
    Tests connectivity and functionality of configured Azure services.
    
    Args:
        settings: Application settings
        
    Returns:
        Dictionary with health check results
        
    Example:
        ```python
        health = await check_azure_services_health(settings)
        if not health["blob_storage"]["healthy"]:
            logger.error("Blob storage unhealthy")
        ```
    """
    health = {
        "blob_storage": {
            "healthy": False,
            "message": "Not configured",
        },
        "application_insights": {
            "healthy": False,
            "message": "Not configured",
        },
    }
    
    # Check Blob Storage
    if settings.storage.storage_provider == "azure" and AZURE_AVAILABLE:
        try:
            from backend.storage.factory import get_storage_provider
            
            provider = get_storage_provider(settings.storage)
            
            # Try to list blobs (lightweight operation)
            await asyncio.to_thread(provider.list_files, prefix="", include_metadata=False)
            
            health["blob_storage"]["healthy"] = True
            health["blob_storage"]["message"] = f"Connected to {settings.azure.blob.container_name}"
            
        except Exception as e:
            health["blob_storage"]["healthy"] = False
            health["blob_storage"]["message"] = f"Connection failed: {str(e)[:100]}"
    
    # Check Application Insights
    if settings.azure.monitor.enabled and AZURE_MONITOR_AVAILABLE:
        try:
            connection_string = settings.azure.monitor.get_connection_string()
            if connection_string:
                health["application_insights"]["healthy"] = True
                health["application_insights"]["message"] = "Configured and available"
            else:
                health["application_insights"]["message"] = "Connection string missing"
        except Exception as e:
            health["application_insights"]["healthy"] = False
            health["application_insights"]["message"] = f"Configuration error: {str(e)[:100]}"
    
    return health


# Import asyncio for async operations
import asyncio
