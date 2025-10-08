"""
Global configuration module for the PixCrawler project.

This module provides Pydantic Settings for managing project-level configuration
that applies across all packages. It focuses on high-level settings like
project metadata, workspace configuration, and cross-package coordination.

Classes:
    ProjectSettings: Pydantic Settings for project-level configuration

Functions:
    get_project_settings: Returns project settings instance

Features:
    - Uses Pydantic V2 Settings for environment-based configuration
    - Project metadata and versioning
    - Workspace and monorepo configuration
    - Cross-package coordination settings
    - Development and deployment settings
"""
from enum import Enum
from functools import lru_cache
from typing import List, Optional, Dict, Any
from pathlib import Path

from pydantic import Field, field_validator, model_validator, DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'Environment',
    'LogLevel',
    'ProjectSettings',
    'get_project_settings'
]


class Environment(str, Enum):
    """Project environment enumeration."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ProjectSettings(BaseSettings):
    """
    Pydantic Settings for the PixCrawler project.

    This class manages environment-based configuration for project-level settings
    that apply across all packages in the monorepo. Uses PIXCRAWLER_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="PIXCRAWLER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        str_strip_whitespace=True,
        use_enum_values=True
    )

    # Project metadata
    project_name: str = Field(
        default="PixCrawler",
        min_length=1,
        max_length=50,
        pattern=r'^[a-zA-Z][a-zA-Z0-9_\-]*$',
        description="Project name",
        examples=["PixCrawler", "PixCrawler-Dev"]
    )

    version: str = Field(
        default="1.0.0",
        pattern=r'^\d+\.\d+\.\d+(-[a-zA-Z0-9\-]+)?$',
        description="Project version (semantic versioning)",
        examples=["1.0.0", "1.2.3", "2.0.0-beta.1"]
    )

    description: str = Field(
        default="Automated image dataset builder for machine learning",
        max_length=200,
        description="Project description",
        examples=["Automated image dataset builder for machine learning"]
    )

    # Environment settings
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Current environment",
        examples=[Environment.DEVELOPMENT, Environment.PRODUCTION]
    )

    development_mode: bool = Field(
        default=True,
        description="Enable development mode features",
        examples=[True, False]
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        examples=[True, False]
    )

    # Logging configuration
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Global logging level",
        examples=[LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING]
    )

    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        min_length=10,
        max_length=200,
        description="Log format string",
        examples=["%(asctime)s - %(name)s - %(levelname)s - %(message)s"]
    )

    # Workspace configuration
    workspace_root: Optional[DirectoryPath] = Field(
        default=None,
        description="Workspace root directory (auto-detected if None)",
        examples=[None, Path("/path/to/pixcrawler"), Path("./")]
    )

    temp_dir: Optional[Path] = Field(
        default=None,
        description="Temporary files directory",
        examples=[None, Path("/tmp/pixcrawler"), Path("./temp")]
    )

    cache_dir: Optional[Path] = Field(
        default=None,
        description="Cache directory for shared data",
        examples=[None, Path("./cache"), Path("/var/cache/pixcrawler")]
    )

    # Package coordination
    enabled_packages: List[str] = Field(
        default=["backend", "builder", "validator", "logging_config"],
        min_length=1,
        description="List of enabled packages",
        examples=[["backend", "builder"], ["backend", "builder", "validator"]]
    )

    package_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Package-specific configuration overrides",
        examples=[{}, {"backend": {"debug": True}, "builder": {"max_workers": 8}}]
    )

    # Performance settings
    max_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum number of worker processes/threads",
        examples=[1, 4, 8, 16]
    )

    memory_limit_mb: Optional[int] = Field(
        default=None,
        ge=128,
        le=32768,
        description="Memory limit in MB (None for no limit)",
        examples=[None, 512, 1024, 2048]
    )

    @field_validator('enabled_packages')
    @classmethod
    def validate_enabled_packages(cls, v: List[str]) -> List[str]:
        """Validate enabled packages list."""
        valid_packages = {"backend", "builder", "validator", "logging_config", "frontend"}
        validated = []

        for package in v:
            package = package.strip().lower()
            if not package:
                continue
            if package not in valid_packages:
                raise ValueError(f"Unknown package '{package}'. Valid packages: {', '.join(valid_packages)}")
            if package not in validated:
                validated.append(package)

        if not validated:
            raise ValueError("At least one package must be enabled")

        return validated

    @field_validator('temp_dir', 'cache_dir')
    @classmethod
    def validate_directory_paths(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate directory paths."""
        if v is not None:
            if isinstance(v, str):
                v = Path(v)

            # Check for dangerous paths
            path_str = str(v).lower()
            dangerous_paths = ['/', '\\', 'c:\\windows', '/usr/bin', '/etc']
            if any(path_str.startswith(dp) for dp in dangerous_paths):
                raise ValueError(f"Directory path appears to be in a system location: {v}")

        return v

    @model_validator(mode='after')
    def validate_environment_consistency(self) -> 'ProjectSettings':
        """Validate environment-specific settings consistency."""
        # Production environment validations
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                raise ValueError("Debug mode should not be enabled in production")
            if self.development_mode:
                raise ValueError("Development mode should not be enabled in production")
            if self.log_level == LogLevel.DEBUG:
                raise ValueError("Debug logging should not be used in production")

        # Development environment validations
        if self.environment == Environment.DEVELOPMENT:
            if not self.development_mode:
                # Warning, but not an error
                pass

        # Memory limit validation
        if self.memory_limit_mb and self.memory_limit_mb < 256:
            raise ValueError("Memory limit seems too low (minimum 256MB recommended)")

        return self

    def get_package_config(self, package_name: str) -> Dict[str, Any]:
        """Get configuration for a specific package."""
        return self.package_config.get(package_name, {})

    def is_package_enabled(self, package_name: str) -> bool:
        """Check if a package is enabled."""
        return package_name.lower() in [p.lower() for p in self.enabled_packages]

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "project_name": self.project_name,
            "version": self.version,
            "description": self.description,
            "environment": self.environment.value if hasattr(self.environment, 'value') else str(self.environment),
            "development_mode": self.development_mode,
            "debug": self.debug,
            "log_level": self.log_level.value if hasattr(self.log_level, 'value') else str(self.log_level),
            "log_format": self.log_format,
            "workspace_root": str(self.workspace_root) if self.workspace_root else None,
            "temp_dir": str(self.temp_dir) if self.temp_dir else None,
            "cache_dir": str(self.cache_dir) if self.cache_dir else None,
            "enabled_packages": self.enabled_packages,
            "package_config": self.package_config,
            "max_workers": self.max_workers,
            "memory_limit_mb": self.memory_limit_mb,
        }

@lru_cache()
def get_project_settings() -> ProjectSettings:
    """
    Get cached project settings instance.

    Returns:
        ProjectSettings: Configured settings instance
    """
    return ProjectSettings()
