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
    validate_config: Validates configuration parameters

Features:
    - Uses Pydantic V2 Settings for environment-based configuration
    - Comprehensive validation configuration options
    - Schema validation for configuration files
    - Default configuration presets
    - Configuration validation and error handling
"""

from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from validator.validation import CheckMode, DuplicateAction

__all__ = [
    'ValidatorConfig',
    'get_default_config',
    'load_config_from_dict',
    'validate_config'
]


class ValidatorConfig(BaseSettings):
    """
    Comprehensive configuration for validator operations.

    This class consolidates all validation-related configuration options
    that were previously scattered across the builder package. Uses Pydantic V2
    Settings for environment variable support with PIXCRAWLER_VALIDATOR_ prefix.
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
        description="Validation mode (STRICT or LENIENT)"
    )
    duplicate_action: DuplicateAction = Field(
        default=DuplicateAction.REMOVE,
        description="Action to take for duplicate files"
    )

    # File constraints
    supported_extensions: Tuple[str, ...] = Field(
        default=('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'),
        description="Supported image file extensions"
    )
    max_file_size_mb: Optional[int] = Field(
        default=10,
        ge=1,
        description="Maximum file size in MB (None for no limit)",
    )
    min_file_size_bytes: int = Field(
        default=1024,
        ge=1,
        description="Minimum file size in bytes"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'mode': self.mode.name,
            'duplicate_action': self.duplicate_action.name,
            'supported_extensions': list(self.supported_extensions),
            'max_file_size_mb': self.max_file_size_mb,
            'min_file_size_bytes': self.min_file_size_bytes,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ValidatorConfig':
        """Create configuration from dictionary"""
        # Convert string enums back to enum values
        if 'mode' in config_dict and isinstance(config_dict['mode'], str):
            config_dict['mode'] = CheckMode[config_dict['mode']]

        if 'duplicate_action' in config_dict and isinstance(
            config_dict['duplicate_action'], str):
            config_dict['duplicate_action'] = DuplicateAction[
                config_dict['duplicate_action']]

        # Convert list back to tuple for supported_extensions
        if 'supported_extensions' in config_dict and isinstance(
            config_dict['supported_extensions'], list):
            config_dict['supported_extensions'] = tuple(
                config_dict['supported_extensions'])

        return cls(**config_dict)


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

    Args:
        config_dict: Dictionary containing configuration options

    Returns:
        ValidatorConfig: Validated configuration instance

    Raises:
        ValueError: If configuration is invalid
    """
    try:
        config = ValidatorConfig.from_dict(config_dict)
        validate_config(config)
        return config
    except Exception as e:
        raise ValueError(f"Invalid validator configuration: {e}") from e


def validate_config(config: ValidatorConfig) -> None:
    """
    Validate configuration parameters.

    Args:
        config: Configuration to validate

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate file size constraints
    if config.min_file_size_bytes < 0:
        raise ValueError("min_file_size_bytes must be non-negative")

    if config.max_file_size_mb is not None and config.max_file_size_mb <= 0:
        raise ValueError("max_file_size_mb must be positive")

    # Validate image dimension constraints
    if config.min_image_width < 1:
        raise ValueError("min_image_width must be positive")

    if config.min_image_height < 1:
        raise ValueError("min_image_height must be positive")

    # Validate processing options
    if config.batch_size < 1:
        raise ValueError("batch_size must be positive")

    if config.hash_size < 4 or config.hash_size > 32:
        raise ValueError("hash_size must be between 4 and 32")

    if config.max_concurrent_validations < 1:
        raise ValueError("max_concurrent_validations must be positive")

    # Validate quarantine directory if specified
    if config.quarantine_dir:
        quarantine_path = Path(config.quarantine_dir)
        try:
            quarantine_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(
                f"Cannot create quarantine directory {config.quarantine_dir}: {e}") from e

    # Validate supported extensions
    if not config.supported_extensions:
        raise ValueError("supported_extensions cannot be empty")

    for ext in config.supported_extensions:
        if not ext.startswith('.'):
            raise ValueError(f"Extension '{ext}' must start with a dot")


# Configuration presets
CONFIG_PRESETS = {
    'default': get_default_config,
    'strict': get_strict_config,
    'lenient': get_lenient_config
}


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
