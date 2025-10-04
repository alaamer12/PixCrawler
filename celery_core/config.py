"""
Configuration module for PixCrawler Celery Core.

This module provides Pydantic Settings for managing Celery configuration
across all PixCrawler packages. It includes settings for brokers, workers,
tasks, monitoring, and performance optimization.

Classes:
    CelerySettings: Pydantic Settings for Celery configuration

Functions:
    get_celery_settings: Returns Celery settings instance

Features:
    - Uses Pydantic V2 Settings for environment-based configuration
    - Comprehensive Celery configuration options
    - Environment variable support with PIXCRAWLER_CELERY_ prefix
    - Production-ready defaults with development overrides
    - Monitoring and performance optimization settings
"""

from functools import lru_cache
from typing import List, Dict, Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'CelerySettings',
    'get_celery_settings'
]


class CelerySettings(BaseSettings):
    """
    Pydantic Settings for Celery configuration.
    
    This class manages environment-based configuration for Celery across
    all PixCrawler packages. Uses PIXCRAWLER_CELERY_ prefix for environment variables.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="PIXCRAWLER_CELERY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Broker and Result Backend
    broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    result_backend: str = Field(
        default="redis://localhost:6379/1",
        description="Celery result backend URL"
    )
    
    # Basic Settings
    timezone: str = Field(
        default="UTC",
        description="Timezone for Celery"
    )
    enable_utc: bool = Field(
        default=True,
        description="Enable UTC timezone"
    )
    task_serializer: str = Field(
        default="json",
        description="Task serialization format"
    )
    result_serializer: str = Field(
        default="json",
        description="Result serialization format"
    )
    accept_content: List[str] = Field(
        default=["json"],
        description="Accepted content types"
    )
    
    # Task Settings
    task_track_started: bool = Field(
        default=True,
        description="Track when tasks are started"
    )
    task_time_limit: int = Field(
        default=1800,  # 30 minutes
        ge=60,
        description="Task time limit in seconds"
    )
    task_soft_time_limit: int = Field(
        default=1500,  # 25 minutes
        ge=60,
        description="Task soft time limit in seconds"
    )
    task_acks_late: bool = Field(
        default=True,
        description="Acknowledge tasks after completion"
    )
    task_reject_on_worker_lost: bool = Field(
        default=True,
        description="Reject tasks when worker is lost"
    )
    
    # Worker Settings
    worker_concurrency: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of concurrent worker processes"
    )
    worker_prefetch_multiplier: int = Field(
        default=1,
        ge=1,
        description="Worker prefetch multiplier"
    )
    worker_max_tasks_per_child: int = Field(
        default=1000,
        ge=1,
        description="Maximum tasks per worker child process"
    )
    worker_max_memory_per_child: int = Field(
        default=200000,  # 200MB in KB
        ge=50000,
        description="Maximum memory per worker child process (KB)"
    )
    
    # Retry Settings
    task_default_retry_delay: int = Field(
        default=60,
        ge=1,
        description="Default retry delay in seconds"
    )
    task_max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum number of task retries"
    )
    
    # Result Settings
    result_expires: int = Field(
        default=3600,  # 1 hour
        ge=60,
        description="Result expiration time in seconds"
    )
    result_persistent: bool = Field(
        default=True,
        description="Persist results in backend"
    )
    
    # Monitoring
    enable_monitoring: bool = Field(
        default=True,
        description="Enable monitoring features"
    )
    flower_port: int = Field(
        default=5555,
        ge=1024,
        le=65535,
        description="Flower monitoring port"
    )
    worker_send_task_events: bool = Field(
        default=True,
        description="Send task events from workers"
    )
    task_send_sent_event: bool = Field(
        default=True,
        description="Send task sent events"
    )
    
    # Security
    worker_hijack_root_logger: bool = Field(
        default=False,
        description="Allow worker to hijack root logger"
    )
    worker_log_color: bool = Field(
        default=False,
        description="Enable colored logging in workers"
    )
    
    # Performance (Production)
    task_compression: Optional[str] = Field(
        default=None,
        description="Task compression algorithm (gzip, bzip2, lzma)"
    )
    result_compression: Optional[str] = Field(
        default=None,
        description="Result compression algorithm (gzip, bzip2, lzma)"
    )
    
    # Queue Configuration
    default_queue: str = Field(
        default="default",
        description="Default queue name"
    )
    task_default_queue: str = Field(
        default="default",
        description="Default queue for tasks"
    )
    
    # Beat Schedule
    beat_schedule_enabled: bool = Field(
        default=False,
        description="Enable Celery Beat scheduler"
    )
    
    @field_validator('task_serializer', 'result_serializer')
    @classmethod
    def validate_serializer(cls, v: str) -> str:
        valid_serializers = ['json', 'pickle', 'yaml', 'msgpack']
        if v not in valid_serializers:
            raise ValueError(f'Serializer must be one of {valid_serializers}')
        return v
    
    @field_validator('accept_content')
    @classmethod
    def validate_accept_content(cls, v: List[str]) -> List[str]:
        valid_content = ['json', 'pickle', 'yaml', 'msgpack']
        for content in v:
            if content not in valid_content:
                raise ValueError(f'Content type {content} must be one of {valid_content}')
        return v
    
    @field_validator('task_compression', 'result_compression')
    @classmethod
    def validate_compression(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_compression = ['gzip', 'bzip2', 'lzma']
        if v not in valid_compression:
            raise ValueError(f'Compression must be one of {valid_compression}')
        return v
    
    @field_validator('task_soft_time_limit')
    @classmethod
    def validate_soft_time_limit(cls, v: int, info) -> int:
        # Ensure soft time limit is less than hard time limit
        if hasattr(info.data, 'task_time_limit') and v >= info.data['task_time_limit']:
            raise ValueError('task_soft_time_limit must be less than task_time_limit')
        return v
    
    def get_celery_config(self) -> Dict[str, Any]:
        """
        Generate Celery configuration dictionary.
        
        Returns:
            Dict containing Celery configuration
        """
        config = {
            # Broker and backend
            'broker_url': self.broker_url,
            'result_backend': self.result_backend,
            
            # Serialization
            'task_serializer': self.task_serializer,
            'result_serializer': self.result_serializer,
            'accept_content': self.accept_content,
            
            # Timezone
            'timezone': self.timezone,
            'enable_utc': self.enable_utc,
            
            # Task settings
            'task_track_started': self.task_track_started,
            'task_time_limit': self.task_time_limit,
            'task_soft_time_limit': self.task_soft_time_limit,
            'task_acks_late': self.task_acks_late,
            'task_reject_on_worker_lost': self.task_reject_on_worker_lost,
            'task_default_retry_delay': self.task_default_retry_delay,
            'task_max_retries': self.task_max_retries,
            
            # Worker settings
            'worker_prefetch_multiplier': self.worker_prefetch_multiplier,
            'worker_max_tasks_per_child': self.worker_max_tasks_per_child,
            'worker_max_memory_per_child': self.worker_max_memory_per_child,
            'worker_hijack_root_logger': self.worker_hijack_root_logger,
            'worker_log_color': self.worker_log_color,
            
            # Result settings
            'result_expires': self.result_expires,
            'result_persistent': self.result_persistent,
            
            # Monitoring
            'worker_send_task_events': self.worker_send_task_events,
            'task_send_sent_event': self.task_send_sent_event,
            
            # Queue settings
            'task_default_queue': self.task_default_queue,
        }
        
        # Add compression if enabled
        if self.task_compression:
            config['task_compression'] = self.task_compression
        if self.result_compression:
            config['result_compression'] = self.result_compression
        
        return config
    
    def get_worker_config(self) -> Dict[str, Any]:
        """
        Generate worker-specific configuration.
        
        Returns:
            Dict containing worker configuration
        """
        return {
            'concurrency': self.worker_concurrency,
            'prefetch_multiplier': self.worker_prefetch_multiplier,
            'max_tasks_per_child': self.worker_max_tasks_per_child,
            'max_memory_per_child': self.worker_max_memory_per_child,
            'time_limit': self.task_time_limit,
            'soft_time_limit': self.task_soft_time_limit,
        }
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """
        Generate monitoring configuration.
        
        Returns:
            Dict containing monitoring configuration
        """
        return {
            'enabled': self.enable_monitoring,
            'flower_port': self.flower_port,
            'worker_send_task_events': self.worker_send_task_events,
            'task_send_sent_event': self.task_send_sent_event,
        }


@lru_cache()
def get_celery_settings() -> CelerySettings:
    """
    Get cached Celery settings instance.
    
    Returns:
        CelerySettings: Configured settings instance
    """
    return CelerySettings()