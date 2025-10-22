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
        validate_default=True,
        str_strip_whitespace=True
    )

    config_path: str = Field(
        default="config.json",
        min_length=1,
        max_length=255,
        description="Path to the configuration file",
        examples=["config.json", "datasets/my_config.json", "/path/to/config.json"]
    )
    max_images: int = Field(
        default=10,
        ge=1,
        le=50000,
        description="Maximum number of images to download per keyword",
        examples=[10, 100, 1000, 5000]
    )
    output_dir: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Custom output directory (None uses dataset_name from config)",
        examples=[None, "output", "/path/to/output", "datasets/my_dataset"]
    )
    max_retries: int = Field(
        default=5,
        ge=0,
        le=20,
        description="Maximum number of retry attempts for failed downloads",
        examples=[0, 3, 5, 10]
    )
    continue_from_last: bool = Field(
        default=False,
        description="Whether to continue from previous run",
        examples=[True, False]
    )
    cache_file: str = Field(
        default="download_progress.json",
        min_length=1,
        max_length=255,
        description="Path to cache file for progress tracking",
        examples=["progress.json", "cache/download_progress.json"]
    )
    keyword_generation: KEYWORD_MODE = Field(
        default="auto",
        description="Mode for keyword generation",
        examples=["auto", "enabled", "disabled"]
    )
    ai_model: AI_MODELS = Field(
        default="gpt4-mini",
        description="AI model to use for keyword generation",
        examples=["gpt4", "gpt4-mini"]
    )
    generate_labels: bool = Field(
        default=True,
        description="Whether to generate label files for images",
        examples=[True, False]
    )
    dataset_name: str = Field(
        default="",
        max_length=100,
        description="Name of the dataset (loaded from config file)",
        examples=["", "animal_photos", "car_dataset", "my-dataset-2024"]
    )
    search_variations: Optional[List[str]] = Field(
        default=None,
        max_length=50,
        description="List of search variation templates for image searches",
        examples=[None, ["{keyword} high quality", "{keyword} professional photo"]]
    )

    @field_validator('keyword_generation')
    @classmethod
    def validate_keyword_generation(cls, v: str) -> str:
        """Validate keyword generation mode."""
        valid_modes = ["auto", "disabled", "enabled"]
        if v not in valid_modes:
            raise ValueError(f"keyword_generation must be one of {valid_modes}")
        return v

    @field_validator('ai_model')
    @classmethod
    def validate_ai_model(cls, v: str) -> str:
        """Validate AI model selection."""
        valid_models = ["gpt4", "gpt4-mini"]
        if v not in valid_models:
            raise ValueError(f"ai_model must be one of {valid_models}")
        return v

    @field_validator('search_variations')
    @classmethod
    def validate_search_variations(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate search variations if provided."""
        if v is not None:
            cleaned = []
            for variation in v:
                cleaned_variation = variation.strip()
                if not cleaned_variation:
                    continue
                if "{keyword}" not in cleaned_variation:
                    raise ValueError(f"Search variation '{cleaned_variation}' must contain '{{keyword}}' placeholder")
                if len(cleaned_variation) > 200:
                    raise ValueError(f"Search variation too long: {len(cleaned_variation)} characters (max 200)")
                cleaned.append(cleaned_variation)
            return cleaned if cleaned else None
        return v

    @field_validator('dataset_name')
    @classmethod
    def validate_dataset_name(cls, v: str) -> str:
        """Validate dataset name if provided."""
        if v and not v.replace('_', '').replace('-', '').replace(' ', '').isalnum():
            raise ValueError("Dataset name can only contain alphanumeric characters, spaces, hyphens, and underscores")
        return v
