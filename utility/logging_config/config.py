"""
Simplified logging configuration using Loguru for PixCrawler monorepo.
"""

import os
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger


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


class LoguruConfig:
    """Simple configuration for Loguru-based logging."""

    def __init__(self, environment: Environment = Environment.DEVELOPMENT):
        self.environment = environment
        self.log_dir = Path("logs")
        self.log_filename = "pixcrawler.log"
        self.error_filename = "errors.log"
        self.max_file_size = "10 MB"
        self.backup_count = 5

        # Environment-specific defaults
        if environment == Environment.PRODUCTION:
            self.console_level = LogLevel.WARNING
            self.file_level = LogLevel.INFO
            self.use_json = True
            self.use_colors = False
        elif environment == Environment.DEVELOPMENT:
            self.console_level = LogLevel.DEBUG
            self.file_level = LogLevel.DEBUG
            self.use_json = False
            self.use_colors = True
        else:  # TESTING
            self.console_level = LogLevel.ERROR
            self.file_level = LogLevel.WARNING
            self.use_json = False
            self.use_colors = False

    # noinspection PyCompatibility
    @classmethod
    def from_env(cls) -> 'LoguruConfig':
        """Create config from environment variables."""
        env_name = os.getenv('PIXCRAWLER_ENVIRONMENT', 'development').lower()
        environment = Environment(env_name)

        config = cls(environment=environment)

        # Override with environment variables if present
        if log_dir := os.getenv('PIXCRAWLER_LOG_DIR'):
            config.log_dir = Path(log_dir)

        if json_format := os.getenv('PIXCRAWLER_LOG_JSON'):
            config.use_json = json_format.lower() in ('true', '1', 'yes')

        if use_colors := os.getenv('PIXCRAWLER_LOG_COLORS'):
            config.use_colors = use_colors.lower() in ('true', '1', 'yes')

        return config


def setup_logging(environment: Optional[str] = None,
                  config: Optional[LoguruConfig] = None,
                  **kwargs) -> None:
    """
    Setup Loguru logging for the PixCrawler monorepo.

    Args:
        environment: Environment type (development, production, testing)
        config: Custom LoguruConfig instance
        **kwargs: Additional configuration options
    """
    # Remove default handler
    logger.remove()

    # Create or get config
    if config is None:
        if environment:
            env = Environment(environment.lower())
            config = LoguruConfig(environment=env)
        else:
            config = LoguruConfig.from_env()

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


def _get_console_format(config: LoguruConfig) -> str:
    """Get console format string based on configuration."""
    if config.environment == Environment.DEVELOPMENT:
        return "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    elif config.use_json:
        return "{message}"  # JSON serialization handles formatting
    else:
        return "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"


def _get_file_format(config: LoguruConfig) -> str:
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
