from dataclasses import dataclass
from typing import Literal, Optional

from constants import DEFAULT_CACHE_FILE


CONFIG_SCHEMA = {
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
                }
            }
        }
    }
}


@dataclass
class DatasetGenerationConfig:
    """Configuration for dataset generation."""
    config_path: str
    max_images: int = 10
    output_dir: Optional[str] = None
    integrity: bool = True
    max_retries: int = 5
    continue_from_last: bool = False
    cache_file: str = DEFAULT_CACHE_FILE
    keyword_generation: Literal["disabled", "enabled", "auto"] = "auto"
    ai_model: Literal["gpt4", "gpt4-mini"] = "gpt4-mini"
