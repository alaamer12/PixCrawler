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

from functools import lru_cache
from typing import List, Optional
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'ProjectSettings',
    'get_project_settings'
]


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
    )

    # Development settings
    development_mode: bool = Field(
        default=True,
        description="Enable development mode features"
    )

@lru_cache()
def get_project_settings() -> ProjectSettings:
    """
    Get cached project settings instance.

    Returns:
        ProjectSettings: Configured settings instance
    """
    return ProjectSettings()
