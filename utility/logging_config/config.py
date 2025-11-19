"""
Logging configuration using Loguru and Pydantic Settings.

This module provides centralized logging configuration for the PixCrawler
monorepo using Loguru with Pydantic Settings for type-safe configuration
management.

Classes:
    Environment: Environment types enumeration
    LogLevel: Log levels enumeration
    LoggingSettings: Main logging configuration with Pydantic Settings

Functions:
    setup_logging: Setup Loguru logging for the application
    get_logger: Get configured logger instance
    set_log_level: Set global log level
    get_config_info: Get current logging configuration
    get_logging_settings: Get cached logging settings instance

Features:
    - Environment-based configuration with .env file support
    - Type-safe configuration with Pydantic v2 validation
    - Support for development, production, and testing environments
    - JSON logging for production (Azure Monitor compatible)
    - File rotation and retention
    - Colored console output for development
"""

from functools import lru_cache
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

from loguru import logger
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'Environment',
    'LogLevel',
    'LoggingSettings',
    'setup_logging',
    'get_logger',
    'set_log_level',
    'get_config_info',
    'get_logging_settings'
]


NOISY_PACKAGES = [
    'urllib3.connectionpool',
    'requests.packages.urllib3',
    'PIL.PngImagePlugin',
    'matplotlib.font_manager'
]

class Environment(Enum):
    """Environment types for logging configuration."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(Enum):
    """Log levels with their string values."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"


class LoggingSettings(BaseSettings):
    """
    Logging configuration using Pydantic Settings.

    This class defines all configuration options for Loguru-based logging,
    including environment-specific defaults, file paths, and formatting options.

    Attributes:
        environment: Environment type (development, production, testing)
        log_dir: Directory for log files
        log_filename: Main log file name
        error_filename: Error-only log file name
        max_file_size: Maximum file size before rotation
        backup_count: Number of backup files to retain
        console_level: Console output log level
        file_level: File output log level
        use_json: Enable JSON formatting
        use_colors: Enable colored console output
    """

    model_config = SettingsConfigDict(
        env_prefix="PIXCRAWLER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        str_strip_whitespace=True
    )

    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Environment type",
        examples=[Environment.DEVELOPMENT, Environment.PRODUCTION, Environment.TESTING]
    )
    log_dir: Path = Field(
        default=Path("logs"),
        description="Directory for log files",
        examples=[Path("logs"), Path("/var/log/pixcrawler")]
    )
    log_filename: str = Field(
        default="pixcrawler.log",
        min_length=1,
        description="Main log file name",
        examples=["pixcrawler.log", "app.log"]
    )
    error_filename: str = Field(
        default="errors.log",
        min_length=1,
        description="Error-only log file name",
        examples=["errors.log", "error.log"]
    )
    max_file_size: str = Field(
        default="10 MB",
        description="Maximum file size before rotation",
        examples=["10 MB", "50 MB", "100 MB"]
    )
    backup_count: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of backup files to retain",
        examples=[5, 10, 20]
    )
    console_level: LogLevel = Field(
        default=LogLevel.DEBUG,
        description="Console output log level",
        examples=[LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING]
    )
    file_level: LogLevel = Field(
        default=LogLevel.DEBUG,
        description="File output log level",
        examples=[LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING]
    )
    use_json: bool = Field(
        default=False,
        description="Enable JSON formatting",
        examples=[True, False]
    )
    use_colors: bool = Field(
        default=True,
        description="Enable colored console output",
        examples=[True, False]
    )

    @field_validator("environment", mode="before")
    @classmethod
    def parse_environment(cls, v: Any) -> Environment:
        """
        Parse environment from string or enum.

        Args:
            v: Input value (string or Environment)

        Returns:
            Environment enum value
        """
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    @field_validator("console_level", "file_level", mode="before")
    @classmethod
    def parse_log_level(cls, v: Any) -> LogLevel:
        """
        Parse log level from string or enum.

        Args:
            v: Input value (string or LogLevel)

        Returns:
            LogLevel enum value
        """
        if isinstance(v, str):
            return LogLevel(v.upper())
        return v

    def model_post_init(self, __context: Any) -> None:
        """
        Apply environment-specific defaults after initialization.

        Args:
            __context: Pydantic context (unused)
        """
        # Apply environment-specific defaults if not explicitly set
        if self.environment == Environment.PRODUCTION:
            if self.console_level == LogLevel.DEBUG:
                self.console_level = LogLevel.WARNING
            if self.file_level == LogLevel.DEBUG:
                self.file_level = LogLevel.INFO
            if not self.use_json:
                self.use_json = True
            if self.use_colors:
                self.use_colors = False
        elif self.environment == Environment.TESTING:
            if self.console_level == LogLevel.DEBUG:
                self.console_level = LogLevel.ERROR
            if self.file_level == LogLevel.DEBUG:
                self.file_level = LogLevel.WARNING
            if self.use_colors:
                self.use_colors = False


def setup_logging(environment: Optional[str] = None,
                  config: Optional[LoggingSettings] = None,
                  **kwargs: Any) -> None:
    """
    Setup Loguru logging for the PixCrawler monorepo.

    Args:
        environment: Environment type (development, production, testing)
        config: Custom LoggingSettings instance
        **kwargs: Additional configuration options to override
    """
    # Remove default handler
    logger.remove()

    # Create or get config
    if config is None:
        if environment:
            config = LoggingSettings(environment=environment)
        else:
            config = get_logging_settings()

    # Apply kwargs overrides
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Ensure log directory exists (only for non-production)
    if config.environment != Environment.PRODUCTION:
        config.log_dir.mkdir(parents=True, exist_ok=True)

    # Console handler (always present)
    console_format = _get_console_format(config)
    logger.add(
        sys.stderr,
        level=config.console_level.value,
        format=console_format,
        colorize=config.use_colors,
        filter=_package_filter
    )

    # File handlers (only for development and testing)
    # Production uses stdout for Azure Monitor
    if config.environment == Environment.PRODUCTION:
        # Production: JSON to stdout for Azure Monitor
        logger.add(
            sys.stdout,
            level=config.file_level.value,
            format="{message}",
            serialize=True,  # JSON format
            filter=_package_filter
        )
    elif config.environment != Environment.TESTING:
        # Development: File handlers with rotation
        file_format = _get_file_format(config)
        config.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            config.log_dir / config.log_filename,
            level=config.file_level.value,
            format=file_format,
            rotation=config.max_file_size,
            retention=config.backup_count,
            serialize=config.use_json,
            filter=_package_filter
        )

        # Error-only file handler
        logger.add(
            config.log_dir / config.error_filename,
            level="ERROR",
            format=file_format,
            rotation=config.max_file_size,
            retention=config.backup_count,
            serialize=config.use_json,
            filter=lambda record: record["level"].no >= 40  # ERROR and above
        )

    # Log the configuration
    logger.info(f"Logging configured for {config.environment.value} environment")
    logger.debug(f"Log directory: {config.log_dir}")


def _get_console_format(config: LoggingSettings) -> str:
    """Get console format string based on configuration."""
    if config.environment == Environment.DEVELOPMENT:
        return "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    elif config.use_json:
        return "{message}"  # JSON serialization handles formatting
    else:
        return "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"


def _get_file_format(config: LoggingSettings) -> str:
    """Get file format string based on configuration."""
    if config.use_json:
        return "{message}"  # JSON serialization handles formatting
    else:
        return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"


def _package_filter(record: Dict[str, Any]) -> bool:
    """Filter noisy packages."""
    name = record.get("name", "")

    # Suppress noisy third-party packages
    for package in NOISY_PACKAGES:
        if name.startswith(package):
            return record["level"].no >= 30  # WARNING and above only

    return True


def get_logger(name: Optional[str] = None):
    """
    Get the configured Loguru logger instance.

    Args:
        name: Logger name (for compatibility, but Loguru uses a single logger)

    Returns:
        The configured Loguru logger
    """
    # Loguru uses a single global logger instance
    # We can bind context if name is provided
    if name:
        return logger.bind(logger_name=name)
    return logger


def set_log_level(level: str) -> None:
    """
    Set the global log level.

    Args:
        level: Log level to set
    """
    # Remove existing handlers and re-add with new level
    # This is a simplified approach - in practice you might want more granular control
    logger.remove()
    logger.add(sys.stderr, level=level.upper())


def get_config_info() -> Dict[str, Any]:
    """
    Get current logging configuration information.

    Returns:
        Dictionary with configuration details
    """
    return {
        "status": "configured",
        "library": "loguru",
        "note": "Using Loguru - check logger._core.handlers for detailed info"
    }


@lru_cache()
def get_logging_settings() -> LoggingSettings:
    """
    Get cached logging settings instance.

    Returns:
        Cached LoggingSettings instance
    """
    return LoggingSettings()
