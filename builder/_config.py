"""
This module provides configuration schema definitions and Pydantic Settings for managing PixCrawler application configuration. It includes JSON schema validation for configuration files and defines the main configuration data structure using Pydantic V2.

Classes:
    DatasetGenerationConfig: Pydantic Settings for dataset generation configuration with environment variable support.

Functions:
    get_search_variations: Returns a list of search variation templates.
    get_engines: Returns a list of engine configurations.

Features:
    - Uses Pydantic V2 Settings for environment-based configuration
    - Defines a JSON schema for validating configuration files.
    - Provides type-safe configuration with validation
    - Manages predefined search variations and engine configurations.
"""

from typing import Optional, Dict, Any, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from builder._constants import KEYWORD_MODE, AI_MODELS

__all__ = [
    'CONFIG_SCHEMA',
    'DatasetGenerationConfig'
]

# JSON schema for configuration file validation
CONFIG_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["dataset_name", "categories"],
    "properties": {
        "dataset_name": {
            "type": "string",
            "description": "Name of the dataset"
        },
        "categories": {
            "type": "object",
            "description": "Map of category names to lists of keywords",
            "additionalProperties": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "options": {
            "type": "object",
            "description": "Optional configuration settings",
            "properties": {
                "max_images": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum number of images per keyword"
                },
                "output_dir": {
                    "type": ["string", "null"],
                    "description": "Custom output directory"
                },

                "max_retries": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Maximum number of retry attempts"
                },
                "cache_file": {
                    "type": "string",
                    "description": "Path to the progress cache file"
                },
                "keyword_generation": {
                    "type": "string",
                    "enum": ["disabled", "enabled", "auto"],
                    "description": "Keyword generation mode: 'disabled', 'enabled', or 'auto' (generate only if none provided)"
                },
                "ai_model": {
                    "type": "string",
                    "enum": ["gpt4", "gpt4-mini"],
                    "description": "AI model to use for keyword generation"
                },
                "generate_labels": {
                    "type": "boolean",
                    "description": "Whether to generate label files for images"
                }
            }
        }
    }
}


def get_engines() -> List[Dict[str, Any]]:
    """
    Get the list of engines with their configurations.

    Returns:
        List of dictionaries containing engine configurations
    """
    return [
        {
            'name': 'google',
            'offset_range': (0, 20),
            'variation_step': 20
        },
        {
            'name': 'bing',
            'offset_range': (0, 30),
            'variation_step': 10
        },
        {
            'name': 'baidu',
            'offset_range': (10, 50),
            'variation_step': 15
        }
    ]


class DatasetGenerationConfig(BaseSettings):
    """
    Configuration for dataset generation.

    This class holds all configuration options for the dataset generation process,
    including paths, limits, and feature flags. Uses Pydantic V2 Settings for
    environment variable support with PIXCRAWLER_BUILDER_ prefix.

    Attributes:
        config_path: Path to the configuration file
        max_images: Maximum number of images to download per keyword
        output_dir: Custom output directory (None uses dataset_name from config)
        max_retries: Maximum number of retry attempts for failed downloads
        continue_from_last: Whether to continue from previous run
        cache_file: Path to cache file for progress tracking
        keyword_generation: Mode for keyword generation
        ai_model: AI model to use for keyword generation
        generate_labels: Whether to generate label files for images
        dataset_name: Name of the dataset (loaded from config file)
        search_variations: List of search variation templates for image searches
    """

    model_config = SettingsConfigDict(
        env_prefix="PIXCRAWLER_BUILDER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    config_path: str = Field(
        default="config.json",
        description="Path to the configuration file"
    )
    max_images: int = Field(
        default=10,
        ge=1,
        description="Maximum number of images to download per keyword"
    )
    output_dir: Optional[str] = Field(
        default=None,
        description="Custom output directory (None uses dataset_name from config)"
    )
    max_retries: int = Field(
        default=5,
        ge=0,
        description="Maximum number of retry attempts for failed downloads"
    )
    continue_from_last: bool = Field(
        default=False,
        description="Whether to continue from previous run"
    )
    cache_file: str = Field(
        default="download_progress.json",
        description="Path to cache file for progress tracking"
    )
    keyword_generation: KEYWORD_MODE = Field(
        default="auto",
        description="Mode for keyword generation"
    )
    ai_model: AI_MODELS = Field(
        default="gpt4-mini",
        description="AI model to use for keyword generation"
    )
    generate_labels: bool = Field(
        default=True,
        description="Whether to generate label files for images"
    )
    dataset_name: str = Field(
        default="",
        description="Name of the dataset (loaded from config file)"
    )
    search_variations: Optional[List[str]] = Field(
        default=None,
        description="List of search variation templates for image searches"
    )
    @classmethod
    @field_validator('keyword_generation')
    def validate_keyword_generation(cls, v: str) -> str:
        valid_modes = ["auto", "disabled", "enabled"]
        if v not in valid_modes:
            raise ValueError(f"keyword_generation must be one of {valid_modes}")
        return v
    @classmethod
    @field_validator('ai_model')
    def validate_ai_model(cls, v: str) -> str:
        valid_models = ["gpt4", "gpt4-mini"]
        if v not in valid_models:
            raise ValueError(f"ai_model must be one of {valid_models}")
        return v
