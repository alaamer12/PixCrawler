"""
Configuration settings for temporary storage cleanup service.

This module provides Pydantic settings for configuring the temp storage
cleanup service behavior, including thresholds, intervals, and cleanup policies.

Classes:
    TempStorageCleanupSettings: Configuration for temp storage cleanup operations

Features:
    - Environment variable support with TEMP_STORAGE_CLEANUP_ prefix
    - Validation of configuration values
    - Default values optimized for production use
    - Integration with main settings system
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class TempStorageCleanupSettings(BaseSettings):
    """Settings for temporary storage cleanup operations."""
    
    # Storage paths and thresholds
    temp_storage_path: Path = Field(
        default=Path("./temp_storage"),
        description="Path to temporary storage directory"
    )
    
    emergency_cleanup_threshold: float = Field(
        default=95.0,
        ge=50.0,
        le=99.0,
        description="Storage usage percentage that triggers emergency cleanup"
    )
    
    warning_threshold: float = Field(
        default=85.0,
        ge=50.0,
        le=95.0,
        description="Storage usage percentage that triggers warning logs"
    )
    
    # Cleanup batch sizes and limits
    cleanup_batch_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Maximum number of files to process in a single cleanup batch"
    )
    
    max_cleanup_duration_minutes: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Maximum duration for cleanup operations in minutes"
    )
    
    # Orphaned file detection
    max_orphan_age_hours: int = Field(
        default=24,
        ge=1,
        le=168,  # 1 week
        description="Maximum age in hours for files to be considered orphaned"
    )
    
    orphan_detection_enabled: bool = Field(
        default=True,
        description="Enable orphaned file detection and cleanup"
    )
    
    # Scheduled cleanup intervals
    scheduled_cleanup_interval_minutes: int = Field(
        default=60,
        ge=15,
        le=1440,  # 24 hours
        description="Interval in minutes for scheduled cleanup runs"
    )
    
    emergency_check_interval_minutes: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Interval in minutes for emergency threshold checks"
    )
    
    # Cleanup policies
    cleanup_failed_jobs_after_hours: int = Field(
        default=1,
        ge=0,
        le=72,
        description="Hours to wait before cleaning up failed job temp files"
    )
    
    cleanup_completed_chunks_immediately: bool = Field(
        default=True,
        description="Clean up temp files immediately after successful chunk completion"
    )
    
    keep_temp_files_for_debugging: bool = Field(
        default=False,
        description="Keep temp files for debugging (disables most cleanup)"
    )
    
    # Storage monitoring
    enable_storage_monitoring: bool = Field(
        default=True,
        description="Enable continuous storage usage monitoring"
    )
    
    storage_check_interval_seconds: int = Field(
        default=30,
        ge=10,
        le=300,
        description="Interval in seconds for storage usage checks"
    )
    
    # Cleanup statistics and logging
    log_cleanup_stats: bool = Field(
        default=True,
        description="Log detailed cleanup statistics"
    )
    
    cleanup_stats_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to retain cleanup statistics"
    )
    
    # Safety settings
    min_free_space_gb: float = Field(
        default=1.0,
        ge=0.1,
        le=100.0,
        description="Minimum free space in GB to maintain"
    )
    
    max_files_per_cleanup: int = Field(
        default=10000,
        ge=100,
        le=100000,
        description="Maximum number of files to delete in a single cleanup operation"
    )
    
    # Celery task settings
    cleanup_task_priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Priority for cleanup Celery tasks (1=lowest, 10=highest)"
    )
    
    emergency_task_priority: int = Field(
        default=9,
        ge=5,
        le=10,
        description="Priority for emergency cleanup Celery tasks"
    )
    
    # Advanced settings
    use_hard_links_detection: bool = Field(
        default=False,
        description="Use hard link detection for more accurate file cleanup"
    )
    
    parallel_cleanup_workers: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Number of parallel workers for cleanup operations"
    )
    
    cleanup_dry_run: bool = Field(
        default=False,
        description="Run cleanup in dry-run mode (log what would be deleted without deleting)"
    )
    
    @validator('warning_threshold')
    def warning_threshold_must_be_less_than_emergency(cls, v, values):
        """Ensure warning threshold is less than emergency threshold."""
        emergency_threshold = values.get('emergency_cleanup_threshold', 95.0)
        if v >= emergency_threshold:
            raise ValueError('warning_threshold must be less than emergency_cleanup_threshold')
        return v
    
    @validator('temp_storage_path')
    def temp_storage_path_must_be_absolute_or_relative(cls, v):
        """Validate temp storage path."""
        if not isinstance(v, Path):
            v = Path(v)
        return v
    
    @validator('max_files_per_cleanup')
    def max_files_must_be_reasonable(cls, v, values):
        """Ensure max files per cleanup is reasonable compared to batch size."""
        batch_size = values.get('cleanup_batch_size', 1000)
        if v < batch_size:
            raise ValueError('max_files_per_cleanup must be >= cleanup_batch_size')
        return v
    
    model_config = SettingsConfigDict(
        env_prefix="TEMP_STORAGE_CLEANUP_",
        case_sensitive=False
    )


# Default settings instance
def get_temp_storage_cleanup_settings() -> TempStorageCleanupSettings:
    """Get temp storage cleanup settings instance."""
    return TempStorageCleanupSettings()
