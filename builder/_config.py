"""
This module provides configuration schema definitions and data classes for managing PixCrawler application configuration. It includes JSON schema validation for configuration files and defines the main configuration data structure.

Classes:
    DatasetGenerationConfig: Holds all configuration options for the dataset generation process.

Functions:
    get_search_variations: Returns a list of search variation templates.
    get_engines: Returns a list of engine configurations.

Features:
    - Defines a JSON schema for validating configuration files.
    - Provides a dataclass for structured access to configuration parameters.
    - Manages predefined search variations and engine configurations.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from builder._constants import DEFAULT_CACHE_FILE, KEYWORD_MODE, AI_MODELS

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


@dataclass
class DatasetGenerationConfig:
    """
    Configuration for dataset generation.

    This class holds all configuration options for the dataset generation process,
    including paths, limits, and feature flags.

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
    config_path: str
    max_images: int = 10
    output_dir: Optional[str] = None
    max_retries: int = 5
    continue_from_last: bool = False
    cache_file: str = DEFAULT_CACHE_FILE
    keyword_generation: KEYWORD_MODE = "auto"
    ai_model: AI_MODELS = "gpt4-mini"
    generate_labels: bool = True
    dataset_name: str = ""
    search_variations: list = None
