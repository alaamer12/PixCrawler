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

from pydantic import Field, field_validator, model_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'CelerySettings',
    'get_celery_settings'
]


class CelerySettings(BaseSettings):
    """
    Enhanced Pydantic Settings for Celery configuration.

    This class manages environment-based configuration for Celery across
    all PixCrawler packages. Uses PIXCRAWLER_CELERY_ prefix for environment variables.
    Enhanced with comprehensive validation and professional Pydantic V2 features.
    """

    model_config = SettingsConfigDict(
        env_prefix="PIXCRAWLER_CELERY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        str_strip_whitespace=True,
        use_enum_values=True
    )

    # Broker and Result Backend
    broker_url: str = Field(
        default="redis://localhost:6379/0",
        min_length=1,
        description="Celery broker URL",
        examples=["redis://localhost:6379/0", "amqp://guest@localhost//", "sqs://"]
    )
    result_backend: str = Field(
        default="redis://localhost:6379/1",
        min_length=1,
        description="Celery result backend URL",
        examples=["redis://localhost:6379/1", "db+postgresql://user:pass@localhost/celery"]
    )

    # Basic Settings
    timezone: str = Field(
        default="UTC",
        min_length=1,
        max_length=50,
        description="Timezone for Celery",
        examples=["UTC", "America/New_York", "Europe/London"]
    )
    enable_utc: bool = Field(
        default=True,
        description="Enable UTC timezone",
        examples=[True, False]
    )
    task_serializer: str = Field(
        default="json",
        description="Task serialization format_",
        examples=["json", "pickle", "yaml", "msgpack"]
    )
    result_serializer: str = Field(
        default="json",
        description="Result serialization format_",
        examples=["json", "pickle", "yaml", "msgpack"]
    )
    accept_content: List[str] = Field(
        default=["json"],
        min_length=1,
        max_length=10,
        description="Accepted content types",
        examples=[["json"], ["json", "pickle"], ["json", "yaml", "msgpack"]]
    )

    # Task Settings
    task_track_started: bool = Field(
        default=True,
        description="Track when tasks are started",
        examples=[True, False]
    )
    task_time_limit: int = Field(
        default=1800,  # 30 minutes
        ge=60,
        le=86400,  # 24 hours max
        description="Task time limit in seconds",
        examples=[300, 1800, 3600, 7200]
    )
    task_soft_time_limit: int = Field(
        default=1500,  # 25 minutes
        ge=60,
        le=86400,  # 24 hours max
        description="Task soft time limit in seconds",
        examples=[240, 1500, 3300, 6900]
    )
    task_acks_late: bool = Field(
        default=True,
        description="Acknowledge tasks after completion",
        examples=[True, False]
    )
    task_reject_on_worker_lost: bool = Field(
        default=True,
        description="Reject tasks when worker is lost",
        examples=[True, False]
    )

    # Worker Settings
    worker_concurrency: int = Field(
        default=35,
        ge=1,
        le=128,
        description="Number of concurrent worker processes",
        examples=[1, 4, 16, 35, 64]
    )
    worker_prefetch_multiplier: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Worker prefetch multiplier",
        examples=[1, 2, 4]
    )
    worker_max_tasks_per_child: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum tasks per worker child process",
        examples=[100, 500, 1000, 2000]
    )
    worker_max_memory_per_child: int = Field(
        default=200000,  # 200MB in KB
        ge=50000,  # 50MB minimum
        le=2000000,  # 2GB maximum
        description="Maximum memory per worker child process (KB)",
        examples=[100000, 200000, 500000, 1000000]
    )
    worker_autoscale_enabled: bool = Field(
        default=False,
        description="Enable autoscaling for worker pool",
        examples=[True, False]
    )
    worker_autoscale_min: int = Field(
        default=7,
        ge=1,
        le=128,
        description="Minimum concurrency when autoscale is enabled",
        examples=[7, 5, 10]
    )
    worker_autoscale_max: int = Field(
        default=35,
        ge=1,
        le=256,
        description="Maximum concurrency when autoscale is enabled",
        examples=[35, 20, 50]
    )

    # Retry Settings
    task_default_retry_delay: int = Field(
        default=60,
        ge=1,
        le=3600,  # 1 hour max
        description="Default retry delay in seconds",
        examples=[30, 60, 120, 300]
    )
    task_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of task retries",
        examples=[0, 1, 3, 5, 10]
    )

    # Result Settings
    result_expires: int = Field(
        default=3600,  # 1 hour
        ge=60,
        le=604800,  # 1 week max
        description="Result expiration time in seconds",
        examples=[300, 1800, 3600, 86400]
    )
    result_persistent: bool = Field(
        default=True,
        description="Persist results in backend",
        examples=[True, False]
    )

    # Monitoring
    enable_monitoring: bool = Field(
        default=True,
        description="Enable monitoring features",
        examples=[True, False]
    )
    flower_port: int = Field(
        default=5555,
        ge=1024,
        le=65535,
        description="Flower monitoring port",
        examples=[5555, 8080, 9090]
    )
    worker_send_task_events: bool = Field(
        default=True,
        description="Send task events from workers",
        examples=[True, False]
    )
    task_send_sent_event: bool = Field(
        default=True,
        description="Send task sent events",
        examples=[True, False]
    )

    # Security
    worker_hijack_root_logger: bool = Field(
        default=False,
        description="Allow worker to hijack root logger",
        examples=[True, False]
    )
    worker_log_color: bool = Field(
        default=False,
        description="Enable colored logging in workers",
        examples=[True, False]
    )

    # Performance (Production)
    task_compression: Optional[str] = Field(
        default=None,
        description="Task compression algorithm (gzip, bzip2, lzma)",
        examples=[None, "gzip", "bzip2", "lzma"]
    )
    result_compression: Optional[str] = Field(
        default=None,
        description="Result compression algorithm (gzip, bzip2, lzma)",
        examples=[None, "gzip", "bzip2", "lzma"]
    )

    # Queue Configuration
    default_queue: str = Field(
        default="default",
        min_length=1,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_\-]+$',
        description="Default queue name",
        examples=["default", "high_priority", "low_priority", "background"]
    )
    task_default_queue: str = Field(
        default="default",
        min_length=1,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_\-]+$',
        description="Default queue for tasks",
        examples=["default", "tasks", "processing"]
    )
    task_queue_max_priority: int = Field(
        default=10,
        ge=1,
        le=10,
        description="Maximum priority levels supported by task queues (typically 0-9)",
        examples=[10, 9]
    )
    task_default_priority: int = Field(
        default=5,
        ge=0,
        le=9,
        description="Default task priority (0-9, higher means higher priority)",
        examples=[5, 7, 3]
    )

    # Beat Schedule
    beat_schedule_enabled: bool = Field(
        default=False,
        description="Enable Celery Beat scheduler",
        examples=[True, False]
    )

    @field_validator('task_serializer', 'result_serializer')
    @classmethod
    def validate_serializer(cls, v: str) -> str:
        """Validate serializer format_."""
        valid_serializers = ['json', 'pickle', 'yaml', 'msgpack']
        v = v.strip().lower()
        if v not in valid_serializers:
            raise ValueError(f'Serializer must be one of {valid_serializers}')
        return v

    @field_validator('task_compression', 'result_compression')
    @classmethod
    def validate_compression(cls, v: Optional[str]) -> Optional[str]:
        """Validate compression algorithm."""
        if v is None:
            return v
        v = v.strip().lower()
        valid_compression = ['gzip', 'bzip2', 'lzma']
        if v not in valid_compression:
            raise ValueError(f'Compression must be one of {valid_compression}')
        return v

    @field_validator('broker_url', 'result_backend')
    @classmethod
    def validate_urls(cls, v: str) -> str:
        """Validate broker and backend URLs."""
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty")

        # Basic URL validation
        valid_schemes = ['redis', 'amqp', 'sqs', 'db+postgresql', 'db+mysql', 'mongodb']
        if not any(v.startswith(f"{scheme}://") for scheme in valid_schemes):
            raise ValueError(f"URL must start with one of: {', '.join(scheme + '://' for scheme in valid_schemes)}")

        return v

    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone string."""
        v = v.strip()
        if not v:
            raise ValueError("Timezone cannot be empty")

        # Basic timezone validation
        common_timezones = ['UTC', 'GMT', 'EST', 'PST', 'CET']
        if v not in common_timezones and '/' not in v:
            # Allow common formats like America/New_York
            raise ValueError(f"Invalid timezone format_. Use UTC, GMT, or continent/city format_")

        return v

    @field_validator('task_soft_time_limit')
    @classmethod
    def validate_soft_time_limit(cls, v: int, info) -> int:
        """Ensure soft time limit is less than hard time limit."""
        if hasattr(info.data, 'task_time_limit') and v >= info.data['task_time_limit']:
            raise ValueError('task_soft_time_limit must be less than task_time_limit')
        return v

    @field_validator('accept_content')
    @classmethod
    def validate_accept_content(cls, v: List[str]) -> List[str]:
        """Validate accepted content types."""
        valid_content = ['json', 'pickle', 'yaml', 'msgpack']
        cleaned = []
        for content in v:
            content = content.strip().lower()
            if content not in valid_content:
                raise ValueError(f'Content type {content} must be one of {valid_content}')
            if content not in cleaned:
                cleaned.append(content)

        if not cleaned:
            raise ValueError("At least one content type must be specified")
        return cleaned

    @model_validator(mode='after')
    def validate_configuration_consistency(self) -> 'CelerySettings':
        """Validate configuration consistency and relationships."""
        # Validate time limits relationship
        if self.task_soft_time_limit >= self.task_time_limit:
            raise ValueError("task_soft_time_limit must be less than task_time_limit")

        # Validate retry settings
        if self.task_default_retry_delay > self.task_time_limit:
            raise ValueError("task_default_retry_delay should not exceed task_time_limit")

        # Validate result expiration
        if self.result_expires < 60:
            raise ValueError("result_expires should be at least 60 seconds")

        # Validate worker settings
        if self.worker_max_memory_per_child < 50000:  # 50MB
            raise ValueError("worker_max_memory_per_child should be at least 50MB (50000 KB)")
        if self.worker_autoscale_enabled and self.worker_autoscale_min > self.worker_autoscale_max:
            raise ValueError("worker_autoscale_min cannot be greater than worker_autoscale_max")

        # Validate monitoring settings
        if self.enable_monitoring and not (1024 <= self.flower_port <= 65535):
            raise ValueError("flower_port must be between 1024 and 65535 when monitoring is enabled")

        # Validate queue names consistency
        if self.default_queue != self.task_default_queue:
            # Log warning but don't fail
            pass

        return self

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
            'task_queue_max_priority': self.task_queue_max_priority,
            'task_default_priority': self.task_default_priority,
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
            'autoscale': (self.worker_autoscale_max, self.worker_autoscale_min) if self.worker_autoscale_enabled else None,
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
