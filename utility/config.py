"""
Unified configuration system for the PixCrawler utility package.

This module provides a centralized, type-safe configuration system that consolidates
compression and logging settings with environment variable support and preset configurations.

Classes:
    UtilitySettings: Main unified configuration class
    
Functions:
    get_utility_settings: Get cached utility settings instance
    get_preset_config: Get preset configuration by name

Features:
    - Centralized configuration management
    - Environment-based configuration with PIXCRAWLER_UTILITY_ prefix
    - Nested composition of compression and logging settings
    - Cross-package consistency validation
    - Preset configurations (default, production, development, testing)
    - Type-safe configuration with Pydantic V2 validation
"""

from functools import lru_cache
from typing import Dict, Any, Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from utility.compress.config import CompressionSettings, ArchiveSettings
from utility.logging_config.config import LoggingSettings, Environment, LogLevel

__all__ = [
    'UtilitySettings',
    'get_utility_settings',
    'get_preset_config',
    'CONFIG_PRESETS'
]

PresetName = Literal["default", "production", "development", "testing"]


class UtilitySettings(BaseSettings):
    """
    Unified configuration for the utility package.
    
    This class consolidates all utility package configuration including
    compression and logging settings with environment variable support
    and cross-package consistency validation.
    
    Attributes:
        compression: Compression and archiving configuration
        logging: Logging configuration
    
    Example:
        >>> # Using default settings
        >>> settings = UtilitySettings()
        >>> 
        >>> # Using environment variables
        >>> # Set PIXCRAWLER_UTILITY_COMPRESSION__QUALITY=90
        >>> settings = UtilitySettings()
        >>> print(settings.compression.quality)  # 90
        >>> 
        >>> # Using preset configurations
        >>> prod_settings = get_preset_config("production")
        >>> print(prod_settings.logging.environment)  # Environment.PRODUCTION
    """
    
    model_config = SettingsConfigDict(
        env_prefix="PIXCRAWLER_UTILITY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        str_strip_whitespace=True,
        env_nested_delimiter="__"
    )
    
    # Nested configuration using composition
    compression: CompressionSettings = Field(
        default_factory=CompressionSettings,
        description="Compression and archiving configuration"
    )
    
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description="Logging configuration"
    )
    
    @model_validator(mode='after')
    def validate_cross_package_consistency(self) -> 'UtilitySettings':
        """
        Validate cross-package configuration consistency.
        
        Ensures that configuration values across different sub-packages
        are consistent and compatible with each other.
        
        Returns:
            Self with validated configuration
            
        Raises:
            ValueError: If configuration inconsistencies are detected
        """
        # Validate compression quality is reasonable for the environment
        if self.logging.environment == Environment.PRODUCTION:
            if self.compression.quality < 70:
                raise ValueError(
                    "Production environment should use compression quality >= 70 "
                    f"(current: {self.compression.quality})"
                )
        
        # Validate archive settings are compatible with compression settings
        if self.compression.archive.enable:
            if self.compression.archive.level > 15 and self.logging.environment == Environment.DEVELOPMENT:
                # Warn about high compression levels in development
                # (we can't use logger here as it might not be configured yet)
                pass
        
        # Validate logging directory exists or can be created for non-production
        if self.logging.environment != Environment.PRODUCTION:
            try:
                self.logging.log_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValueError(
                    f"Cannot create logging directory {self.logging.log_dir}: {e}"
                )
        
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            "compression": self.compression.model_dump(),
            "logging": self.logging.model_dump()
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'UtilitySettings':
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Dictionary with configuration values
            
        Returns:
            UtilitySettings instance
        """
        return cls(**config_dict)


# Preset configurations
CONFIG_PRESETS: Dict[PresetName, Dict[str, Any]] = {
    "default": {
        "compression": {
            "quality": 85,
            "format": "webp",
            "lossless": False,
            "workers": 0,
            "archive": {
                "enable": True,
                "tar": True,
                "type": "zstd",
                "level": 10
            }
        },
        "logging": {
            "environment": "development",
            "console_level": "DEBUG",
            "file_level": "DEBUG",
            "use_json": False,
            "use_colors": True
        }
    },
    "production": {
        "compression": {
            "quality": 90,
            "format": "webp",
            "lossless": False,
            "workers": 0,
            "archive": {
                "enable": True,
                "tar": True,
                "type": "zstd",
                "level": 15
            }
        },
        "logging": {
            "environment": "production",
            "console_level": "WARNING",
            "file_level": "INFO",
            "use_json": True,
            "use_colors": False
        }
    },
    "development": {
        "compression": {
            "quality": 80,
            "format": "webp",
            "lossless": False,
            "workers": 0,
            "archive": {
                "enable": True,
                "tar": True,
                "type": "zstd",
                "level": 8
            }
        },
        "logging": {
            "environment": "development",
            "console_level": "DEBUG",
            "file_level": "DEBUG",
            "use_json": False,
            "use_colors": True
        }
    },
    "testing": {
        "compression": {
            "quality": 75,
            "format": "webp",
            "lossless": False,
            "workers": 1,
            "archive": {
                "enable": False,
                "tar": False,
                "type": "none",
                "level": 1
            }
        },
        "logging": {
            "environment": "testing",
            "console_level": "ERROR",
            "file_level": "WARNING",
            "use_json": False,
            "use_colors": False
        }
    }
}


@lru_cache()
def get_utility_settings() -> UtilitySettings:
    """
    Get cached utility settings instance.
    
    This function returns a singleton instance of UtilitySettings,
    cached for the lifetime of the application.
    
    Returns:
        Cached UtilitySettings instance
        
    Example:
        >>> settings = get_utility_settings()
        >>> print(settings.compression.quality)
        >>> print(settings.logging.environment)
    """
    return UtilitySettings()


def get_preset_config(preset_name: PresetName) -> UtilitySettings:
    """
    Get preset configuration by name.
    
    Args:
        preset_name: Name of the preset (default, production, development, testing)
        
    Returns:
        UtilitySettings instance with preset configuration
        
    Raises:
        ValueError: If preset_name is not valid
        
    Example:
        >>> # Get production preset
        >>> prod_config = get_preset_config("production")
        >>> print(prod_config.compression.quality)  # 90
        >>> 
        >>> # Get development preset
        >>> dev_config = get_preset_config("development")
        >>> print(dev_config.logging.console_level)  # LogLevel.DEBUG
    """
    if preset_name not in CONFIG_PRESETS:
        raise ValueError(
            f"Invalid preset name: {preset_name}. "
            f"Valid presets: {', '.join(CONFIG_PRESETS.keys())}"
        )
    
    preset_dict = CONFIG_PRESETS[preset_name]
    return UtilitySettings(**preset_dict)
