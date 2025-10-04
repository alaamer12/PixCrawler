"""
Celery application factory and configuration for PixCrawler.

This module provides the main Celery application factory and configuration
management for all PixCrawler packages. It creates a centralized Celery
instance that can be shared across multiple packages.

Classes:
    CeleryApp: Enhanced Celery application with PixCrawler-specific features

Functions:
    create_celery_app: Factory function for creating Celery applications
    get_celery_app: Get the shared Celery application instance

Features:
    - Centralized Celery application management
    - Automatic configuration from Pydantic Settings
    - Flexible queue and routing setup
    - Enhanced error handling and monitoring
"""

from functools import lru_cache
from typing import Optional, Dict, Any, List
import os

from celery import Celery
from celery.signals import setup_logging
from kombu import Queue

from logging_config import get_logger
from celery_core.config import CelerySettings, get_celery_settings

logger = get_logger(__name__)

__all__ = [
    'CeleryApp',
    'create_celery_app',
    'get_celery_app'
]


class CeleryApp(Celery):
    """
    Enhanced Celery application with PixCrawler-specific features.
    
    This class extends the standard Celery application with additional
    functionality for PixCrawler, including automatic configuration,
    enhanced monitoring, and flexible task management.
    """
    
    def __init__(self, name: str = 'pixcrawler', settings: Optional[CelerySettings] = None):
        """
        Initialize the Celery application.
        
        Args:
            name: Application name
            settings: Optional CelerySettings instance
        """
        super().__init__(name)
        
        self.settings = settings or get_celery_settings()
        self._configure_app()
        
        logger.info(f"Initialized Celery app '{name}' with broker: {self.settings.broker_url}")
    
    def _configure_app(self) -> None:
        """Configure the Celery application with settings."""
        config = self.settings.get_celery_config()
        self.conf.update(config)
        
        # Set basic configuration
        self.conf.update(
            # Default queue setup
            task_default_queue=self.settings.default_queue,
            
            # Error handling
            task_annotations={
                '*': {
                    'rate_limit': '100/m',
                    'time_limit': self.settings.task_time_limit,
                    'soft_time_limit': self.settings.task_soft_time_limit,
                }
            },
        )
    
    def setup_queues(self, queues: List[Queue], routes: Dict[str, Dict[str, str]] = None) -> None:
        """
        Setup task queues and routing for the application.
        
        Args:
            queues: List of Queue objects to configure
            routes: Optional task routing configuration
        """
        self.conf.task_queues = queues
        
        if routes:
            self.conf.task_routes = routes
    
    def setup_includes(self, includes: List[str]) -> None:
        """
        Setup task modules to include for auto-discovery.
        
        Args:
            includes: List of module paths to include
        """
        self.conf.include = includes
    
    def setup_beat_schedule(self, schedule: Dict[str, Dict[str, Any]]) -> None:
        """
        Setup Celery Beat schedule.
        
        Args:
            schedule: Beat schedule configuration
        """
        if self.settings.beat_schedule_enabled:
            self.conf.beat_schedule = schedule
    
    def get_queue_info(self) -> Dict[str, Any]:
        """
        Get information about configured queues.
        
        Returns:
            Dict containing queue information
        """
        queues = getattr(self.conf, 'task_queues', [])
        routes = getattr(self.conf, 'task_routes', {})
        
        return {
            'queues': [q.name for q in queues] if queues else [],
            'default_queue': self.conf.task_default_queue,
            'routing': dict(routes),
        }
    
    def get_worker_info(self) -> Dict[str, Any]:
        """
        Get worker configuration information.
        
        Returns:
            Dict containing worker information
        """
        return self.settings.get_worker_config()
    
    def get_monitoring_info(self) -> Dict[str, Any]:
        """
        Get monitoring configuration information.
        
        Returns:
            Dict containing monitoring information
        """
        return self.settings.get_monitoring_config()


def create_celery_app(name: str = 'pixcrawler', 
                      settings: Optional[CelerySettings] = None) -> CeleryApp:
    """
    Factory function for creating Celery applications.
    
    Args:
        name: Application name
        settings: Optional CelerySettings instance
        
    Returns:
        CeleryApp: Configured Celery application
    """
    return CeleryApp(name=name, settings=settings)


@lru_cache()
def get_celery_app() -> CeleryApp:
    """
    Get the shared Celery application instance.
    
    Returns:
        CeleryApp: Shared Celery application
    """
    return create_celery_app()


# Setup logging configuration
@setup_logging.connect
def config_loggers(*args, **kwargs):
    """Configure logging for Celery workers."""
    # Use our centralized logging configuration
    from logging_config import setup_logging as setup_pixcrawler_logging
    setup_pixcrawler_logging()


# Create the main Celery app instance
app = get_celery_app()

# Export for use by other packages
celery_app = app