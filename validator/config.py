"""
Configuration module for the PixCrawler validator package.

This module provides configuration schemas and Pydantic Settings for managing
validation operations. It was separated from the builder package to maintain
clean separation of concerns.

Classes:
    ValidatorConfig: Pydantic Settings for validation configuration with environment variable support

Functions:
    get_default_config: Returns default validation configuration
    load_config_from_dict: Creates config from dictionary

Features:
    - Uses Pydantic V2 Settings for environment-based configuration
    - Comprehensive validation configuration options
    - Schema validation for configuration files
    - Default configuration presets
    - Configuration validation and error handling
"""

from enum import Enum, auto
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from pydantic import Field, field_validator, model_validator
from pydantic.types import PositiveInt, conint
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'CheckMode',
    'DuplicateAction',
    'ValidatorConfig',
    'get_validator_settings',
    'get_default_config',
    'get_strict_config',
    'get_lenient_config',
    'load_config_from_dict',
    'get_preset_config',
    'CONFIG_PRESETS',
]


class CheckMode(Enum):
    """Enumeration of available validation modes"""
    STRICT = auto()  # Fail on any issues
    LENIENT = auto()  # Log warnings but continue
    REPORT_ONLY = auto()  # Only report, no actions


class DuplicateAction(Enum):
    """Actions to take when duplicates are found"""
    REMOVE = auto()  # Remove duplicate files
    REPORT_ONLY = auto()  # Only report duplicates
    QUARANTINE = auto()  # Move duplicates to quarantine directory


class ValidatorConfig(BaseSettings):
    """
    Comprehensive configuration for validator operations.

    This class consolidates all validation-related configuration options
    that were previously scattered across the builder package. Uses Pydantic V2
    Settings for environment variable support with PIXCRAWLER_VALIDATOR_ prefix.

    All validation is handled by Pydantic's type system and validators.
    """

    model_config = SettingsConfigDict(
        env_prefix="PIXCRAWLER_VALIDATOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Validation behavior
    mode: CheckMode = Field(
        default=CheckMode.LENIENT,
        description="Validation mode (STRICT, LENIENT, or REPORT_ONLY)"
    )
    duplicate_action: DuplicateAction = Field(
        default=DuplicateAction.REMOVE,
        description="Action to take for duplicate files"
    )

    # File constraints
    supported_extensions: Tuple[str, ...] = Field(
        default=('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'),
        min_length=1,
        description="Supported image file extensions"
    )
    max_file_size_mb: Optional[PositiveInt] = Field(
        default=10,
        description="Maximum file size in MB (None for no limit)",
    )
    min_file_size_bytes: PositiveInt = Field(
        default=1024,
        description="Minimum file size in bytes"
    )

    # Image dimension constraints
    min_image_width: PositiveInt = Field(
        default=1,
        description="Minimum image width in pixels"
    )
    min_image_height: PositiveInt = Field(
        default=1,
        description="Minimum image height in pixels"
    )

    # Processing options
    batch_size: PositiveInt = Field(
        default=100,
        description="Number of files to process in a batch"
    )
    hash_size: conint(ge=4, le=32) = Field(
        default=8,
        description="Perceptual hash size (between 4 and 32)"
    )
    max_concurrent_validations: PositiveInt = Field(
        default=4,
        description="Maximum number of concurrent validation operations"
    )

    # Quarantine and logging
    quarantine_dir: Optional[Path] = Field(
        default=None,
        description="Directory for quarantined files"
    )
    detailed_logging: bool = Field(
        default=False,
        description="Enable detailed logging output"
    )

    @classmethod
    @field_validator('supported_extensions')
    def validate_extensions(cls, extensions: Tuple[str, ...]) -> Tuple[str, ...]:
        """Ensure all extensions start with a dot."""
        for ext in extensions:
            if not ext.startswith('.'):
                raise ValueError(f"Extension '{ext}' must start with a dot")
        return extensions

    @model_validator(mode='after')
    def validate_quarantine_dir(self) -> 'ValidatorConfig':
        """Create quarantine directory if specified."""
        if self.quarantine_dir:
            try:
                self.quarantine_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(
                    f"Cannot create quarantine directory {self.quarantine_dir}: {e}"
                ) from e
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'mode': self.mode.name,
            'duplicate_action': self.duplicate_action.name,
            'supported_extensions': list(self.supported_extensions),
            'max_file_size_mb': self.max_file_size_mb,
            'min_file_size_bytes': self.min_file_size_bytes,
            'min_image_width': self.min_image_width,
            'min_image_height': self.min_image_height,
            'batch_size': self.batch_size,
            'hash_size': self.hash_size,
            'max_concurrent_validations': self.max_concurrent_validations,
            'quarantine_dir': str(self.quarantine_dir) if self.quarantine_dir else None,
            'detailed_logging': self.detailed_logging,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ValidatorConfig':
        """Create configuration from dictionary."""
        # Convert string enums back to enum values
        if 'mode' in config_dict and isinstance(config_dict['mode'], str):
            config_dict['mode'] = CheckMode[config_dict['mode']]

        if 'duplicate_action' in config_dict and isinstance(
            config_dict['duplicate_action'], str
        ):
            config_dict['duplicate_action'] = DuplicateAction[config_dict['duplicate_action']]

        # Convert list back to tuple for supported_extensions
        if 'supported_extensions' in config_dict and isinstance(
            config_dict['supported_extensions'], list
        ):
            config_dict['supported_extensions'] = tuple(config_dict['supported_extensions'])

        # Convert string to Path for quarantine_dir
        if 'quarantine_dir' in config_dict and isinstance(
            config_dict['quarantine_dir'], str
        ):
            config_dict['quarantine_dir'] = Path(config_dict['quarantine_dir'])

        return cls(**config_dict)


def get_validator_settings() -> ValidatorConfig:
    """
    Get the validator settings instance.

    Returns:
        ValidatorConfig: Configured settings instance
    """
    return ValidatorConfig()


def get_default_config() -> ValidatorConfig:
    """
    Get default validation configuration.

    Returns:
        ValidatorConfig: Default configuration instance
    """
    return ValidatorConfig()


def get_strict_config() -> ValidatorConfig:
    """
    Get strict validation configuration.

    Returns:
        ValidatorConfig: Strict configuration instance
    """
    return ValidatorConfig(
        mode=CheckMode.STRICT,
        duplicate_action=DuplicateAction.REMOVE,
        min_file_size_bytes=2048,  # 2KB minimum
        min_image_width=100,
        min_image_height=100,
        detailed_logging=True
    )


def get_lenient_config() -> ValidatorConfig:
    """
    Get lenient validation configuration.

    Returns:
        ValidatorConfig: Lenient configuration instance
    """
    return ValidatorConfig(
        mode=CheckMode.LENIENT,
        duplicate_action=DuplicateAction.REPORT_ONLY,
        min_file_size_bytes=512,  # 512 bytes minimum
        min_image_width=25,
        min_image_height=25,
        detailed_logging=False
    )


def load_config_from_dict(config_dict: Dict[str, Any]) -> ValidatorConfig:
    """
    Load configuration from dictionary with validation.

    Pydantic handles all validation automatically during instantiation.

    Args:
        config_dict: Dictionary containing configuration options

    Returns:
        ValidatorConfig: Validated configuration instance

    Raises:
        ValueError: If configuration is invalid (raised by Pydantic)
    """
    try:
        return ValidatorConfig.from_dict(config_dict)
    except Exception as e:
        raise ValueError(f"Invalid validator configuration: {e}") from e


# Configuration presets
CONFIG_PRESETS = {
    'default': get_default_config,
    'strict': get_strict_config,
    'lenient': get_lenient_config
}

@lru_cache()
def get_preset_config(preset_name: str) -> ValidatorConfig:
    """
    Get a preset configuration by name.

    Args:
        preset_name: Name of the preset ('default', 'strict', 'lenient')

    Returns:
        ValidatorConfig: Preset configuration instance

    Raises:
        ValueError: If preset name is not recognized
    """
    if preset_name not in CONFIG_PRESETS:
        available = ', '.join(CONFIG_PRESETS.keys())
        raise ValueError(
            f"Unknown preset '{preset_name}'. Available presets: {available}")

    return CONFIG_PRESETS[preset_name]()
