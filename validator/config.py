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

from pydantic import Field, field_validator, model_validator, ConfigDict
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
        validate_default=True,
        str_strip_whitespace=True
    )

    # Validation behavior
    mode: CheckMode = Field(
        default=CheckMode.LENIENT,
        description="Validation mode (STRICT, LENIENT, or REPORT_ONLY)",
        examples=[CheckMode.STRICT, CheckMode.LENIENT, CheckMode.REPORT_ONLY]
    )
    duplicate_action: DuplicateAction = Field(
        default=DuplicateAction.REMOVE,
        description="Action to take for duplicate files",
        examples=[DuplicateAction.REMOVE, DuplicateAction.REPORT_ONLY, DuplicateAction.QUARANTINE]
    )

    max_file_size_mb: Optional[PositiveInt] = Field(
        default=10,
        le=1000,
        description="Maximum file size in MB (None for no limit)",
        examples=[10, 50, 100, None]
    )
    min_file_size_bytes: PositiveInt = Field(
        default=1024,
        ge=1,
        le=1048576,  # 1MB max
        description="Minimum file size in bytes",
        examples=[512, 1024, 2048]
    )

    supported_extensions: Tuple[str, ...] = Field(
        default=('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'),
        description="Supported image extensions",
        examples=[('.jpg', '.png')]
    )

    # Image dimension constraints
    min_image_width: PositiveInt = Field(
        default=1,
        ge=1,
        le=10000,
        description="Minimum image width in pixels",
        examples=[1, 50, 100, 200]
    )
    min_image_height: PositiveInt = Field(
        default=1,
        ge=1,
        le=10000,
        description="Minimum image height in pixels",
        examples=[1, 50, 100, 200]
    )

    # Processing options
    batch_size: PositiveInt = Field(
        default=100,
        ge=1,
        le=10000,
        description="Number of files to process in a batch",
        examples=[50, 100, 500, 1000]
    )
    hash_size: conint(ge=4, le=32) = Field(
        default=8,
        description="Perceptual hash size (between 4 and 32)",
        examples=[4, 8, 16, 32]
    )
    max_concurrent_validations: PositiveInt = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum number of concurrent validation operations",
        examples=[1, 4, 8, 16]
    )

    # Quarantine and logging
    quarantine_dir: Optional[Path] = Field(
        default=None,
        description="Directory for quarantined files",
        examples=[None, Path("quarantine"), Path("/tmp/quarantine")]
    )
    detailed_logging: bool = Field(
        default=False,
        description="Enable detailed logging output",
        examples=[True, False]
    )

    @field_validator('quarantine_dir')
    @classmethod
    def validate_quarantine_path(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate quarantine directory path."""
        if v is not None:
            # Convert string to Path if needed
            if isinstance(v, str):
                v = Path(v)

            # Validate path is not empty
            if str(v).strip() == '':
                raise ValueError("Quarantine directory path cannot be empty")

            # Check if path is reasonable (not root, not system directories)
            path_str = str(v).lower()
            forbidden_paths = ['c:\\windows', 'c:\\program files', 'c:\\program files (x86)', '/usr', '/bin', '/etc', '/var', '/sys']
            
            # Check for exact root match or system directories
            if path_str in ['/', '\\', 'c:\\']:
                 raise ValueError(f"Quarantine directory cannot be root: {v}")
                 
            if any(path_str.startswith(fp) for fp in forbidden_paths):
                raise ValueError(f"Quarantine directory cannot be in system path: {v}")

        return v

    @model_validator(mode='after')
    def validate_config_consistency(self) -> 'ValidatorConfig':
        """Validate configuration consistency and create quarantine directory if needed."""
        # Validate dimension consistency
        if self.min_image_width > 5000 or self.min_image_height > 5000:
            raise ValueError("Minimum image dimensions seem unreasonably large")

        # Validate file size consistency
        if self.max_file_size_mb and self.min_file_size_bytes > (self.max_file_size_mb * 1024 * 1024):
            raise ValueError("Minimum file size cannot be larger than maximum file size")

        # Validate processing options
        if self.batch_size > 5000:
            raise ValueError("Batch size seems unreasonably large (may cause memory issues)")

        # Create quarantine directory if specified and action requires it
        if self.quarantine_dir and self.duplicate_action == DuplicateAction.QUARANTINE:
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
            'mode': self.mode.name if hasattr(self.mode, 'name') else str(self.mode),
            'duplicate_action': self.duplicate_action.name if hasattr(self.duplicate_action, 'name') else str(self.duplicate_action),
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
        # Make a copy to avoid modifying the original
        config_copy = config_dict.copy()

        # Convert string enums back to enum values
        if 'mode' in config_copy and isinstance(config_copy['mode'], str):
            try:
                config_copy['mode'] = CheckMode[config_copy['mode']]
            except KeyError:
                # Try by value if name lookup fails
                for mode in CheckMode:
                    if mode.name == config_copy['mode']:
                        config_copy['mode'] = mode
                        break

        if 'duplicate_action' in config_copy and isinstance(config_copy['duplicate_action'], str):
            try:
                config_copy['duplicate_action'] = DuplicateAction[config_copy['duplicate_action']]
            except KeyError:
                # Try by value if name lookup fails
                for action in DuplicateAction:
                    if action.name == config_copy['duplicate_action']:
                        config_copy['duplicate_action'] = action
                        break

        # Convert list back to tuple for supported_extensions
        if 'supported_extensions' in config_copy and isinstance(
            config_copy['supported_extensions'], list
        ):
            config_copy['supported_extensions'] = tuple(config_copy['supported_extensions'])

        # Convert string to Path for quarantine_dir
        if 'quarantine_dir' in config_copy and isinstance(
            config_copy['quarantine_dir'], str
        ):
            config_copy['quarantine_dir'] = Path(config_copy['quarantine_dir'])

        return cls(**config_copy)


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
