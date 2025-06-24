"""
Configuration module for PixCrawler dataset generator.

This module provides configuration schema definitions and data classes for
managing application configuration. It includes JSON schema validation for 
configuration files and defines the main configuration data structure.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from constants import DEFAULT_CACHE_FILE, KEYWORD_MODE, AI_MODELS

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
                "integrity": {
                    "type": "boolean",
                    "description": "Whether to check image integrity"
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
        integrity: Whether to perform image integrity checks
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
    integrity: bool = True
    max_retries: int = 5
    continue_from_last: bool = False
    cache_file: str = DEFAULT_CACHE_FILE
    keyword_generation: KEYWORD_MODE = "auto"
    ai_model: AI_MODELS = "gpt4-mini"
    generate_labels: bool = True
    dataset_name: str = ""
    search_variations: list = None
