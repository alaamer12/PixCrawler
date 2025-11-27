"""
Tests for unified utility configuration system.

This module tests the unified configuration system including default settings,
environment variable loading, nested configuration, validation, and presets.
"""

import os
import pytest
from pathlib import Path
from pydantic import ValidationError

from utility.config import (
    UtilitySettings,
    get_utility_settings,
    get_preset_config,
    CONFIG_PRESETS
)
from utility.logging_config.config import Environment, LogLevel


class TestDefaultSettings:
    """Test default settings initialization."""
    
    def test_default_settings_initialization(self):
        """Test that default settings initialize correctly."""
        settings = UtilitySettings()
        
        # Check compression defaults
        assert settings.compression.quality == 85
        assert settings.compression.format == "webp"
        assert settings.compression.lossless is False
        assert settings.compression.workers == 0
        
        # Check archive defaults
        assert settings.compression.archive.enable is True
        assert settings.compression.archive.tar is True
        assert settings.compression.archive.type == "zstd"
        assert settings.compression.archive.level == 10
        
        # Check logging defaults
        assert settings.logging.environment == Environment.DEVELOPMENT
        assert settings.logging.console_level == LogLevel.DEBUG
        assert settings.logging.file_level == LogLevel.DEBUG
        assert settings.logging.use_json is False
        assert settings.logging.use_colors is True
    
    def test_default_paths(self):
        """Test that default paths are set correctly."""
        settings = UtilitySettings()
        
        assert settings.compression.input_dir == Path("./images")
        assert settings.compression.output_dir == Path("./compressed")
        assert settings.logging.log_dir == Path("logs")
        assert settings.logging.log_filename == "pixcrawler.log"
        assert settings.logging.error_filename == "errors.log"


class TestEnvironmentVariableLoading:
    """Test environment variable loading with PIXCRAWLER_UTILITY_ prefix."""
    
    def test_compression_quality_from_env(self, monkeypatch):
        """Test loading compression quality from environment variable."""
        monkeypatch.setenv("PIXCRAWLER_UTILITY_COMPRESSION__QUALITY", "95")
        settings = UtilitySettings()
        assert settings.compression.quality == 95
    
    def test_compression_format_from_env(self, monkeypatch):
        """Test loading compression format from environment variable."""
        monkeypatch.setenv("PIXCRAWLER_UTILITY_COMPRESSION__FORMAT", "avif")
        settings = UtilitySettings()
        assert settings.compression.format == "avif"
    
    def test_logging_environment_from_env(self, monkeypatch):
        """Test loading logging environment from environment variable."""
        monkeypatch.setenv("PIXCRAWLER_UTILITY_LOGGING__ENVIRONMENT", "production")
        settings = UtilitySettings()
        assert settings.logging.environment == Environment.PRODUCTION
    
    def test_logging_console_level_from_env(self, monkeypatch):
        """Test loading logging console level from environment variable."""
        monkeypatch.setenv("PIXCRAWLER_UTILITY_LOGGING__CONSOLE_LEVEL", "INFO")
        settings = UtilitySettings()
        assert settings.logging.console_level == LogLevel.INFO
    
    def test_archive_settings_from_env(self, monkeypatch):
        """Test loading archive settings from environment variable."""
        monkeypatch.setenv("PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__ENABLE", "false")
        monkeypatch.setenv("PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__LEVEL", "15")
        settings = UtilitySettings()
        assert settings.compression.archive.enable is False
        assert settings.compression.archive.level == 15
    
    def test_nested_delimiter_parsing(self, monkeypatch):
        """Test that nested delimiter (__) works correctly."""
        monkeypatch.setenv("PIXCRAWLER_UTILITY_COMPRESSION__WORKERS", "8")
        monkeypatch.setenv("PIXCRAWLER_UTILITY_LOGGING__USE_JSON", "true")
        settings = UtilitySettings()
        assert settings.compression.workers == 8
        assert settings.logging.use_json is True


class TestNestedConfigurationComposition:
    """Test nested configuration composition."""
    
    def test_compression_settings_nested(self):
        """Test that compression settings are properly nested."""
        settings = UtilitySettings()
        assert hasattr(settings, 'compression')
        assert hasattr(settings.compression, 'quality')
        assert hasattr(settings.compression, 'archive')
    
    def test_logging_settings_nested(self):
        """Test that logging settings are properly nested."""
        settings = UtilitySettings()
        assert hasattr(settings, 'logging')
        assert hasattr(settings.logging, 'environment')
        assert hasattr(settings.logging, 'console_level')
    
    def test_archive_settings_nested(self):
        """Test that archive settings are nested within compression."""
        settings = UtilitySettings()
        assert hasattr(settings.compression, 'archive')
        assert hasattr(settings.compression.archive, 'enable')
        assert hasattr(settings.compression.archive, 'level')
    
    def test_nested_modification(self):
        """Test that nested settings can be modified."""
        settings = UtilitySettings(
            compression={"quality": 90, "format": "png"},
            logging={"environment": "production"}
        )
        assert settings.compression.quality == 90
        assert settings.compression.format == "png"
        assert settings.logging.environment == Environment.PRODUCTION


class TestFieldValidationRules:
    """Test field validation rules."""
    
    def test_quality_validation_min(self):
        """Test that quality below 0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UtilitySettings(compression={"quality": -1})
        assert "quality" in str(exc_info.value).lower()
    
    def test_quality_validation_max(self):
        """Test that quality above 100 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UtilitySettings(compression={"quality": 101})
        assert "quality" in str(exc_info.value).lower()
    
    def test_quality_validation_valid_range(self):
        """Test that quality within 0-100 is valid."""
        for quality in [0, 50, 100]:
            settings = UtilitySettings(compression={"quality": quality})
            assert settings.compression.quality == quality
    
    def test_compression_level_validation_min(self):
        """Test that compression level below 1 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UtilitySettings(compression={"archive": {"level": 0}})
        assert "level" in str(exc_info.value).lower()
    
    def test_compression_level_validation_max(self):
        """Test that compression level above 19 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UtilitySettings(compression={"archive": {"level": 20}})
        assert "level" in str(exc_info.value).lower()
    
    def test_compression_level_validation_valid_range(self):
        """Test that compression level within 1-19 is valid."""
        for level in [1, 10, 19]:
            settings = UtilitySettings(compression={"archive": {"level": level}})
            assert settings.compression.archive.level == level
    
    def test_format_validation(self):
        """Test that only valid formats are accepted."""
        valid_formats = ["webp", "avif", "png", "jxl"]
        for fmt in valid_formats:
            settings = UtilitySettings(compression={"format": fmt})
            assert settings.compression.format == fmt
    
    def test_format_validation_invalid(self):
        """Test that invalid format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            UtilitySettings(compression={"format": "invalid"})
        assert "format" in str(exc_info.value).lower()
    
    def test_archive_type_validation(self):
        """Test that only valid archive types are accepted."""
        valid_types = ["zstd", "zip", "none"]
        for archive_type in valid_types:
            settings = UtilitySettings(compression={"archive": {"type": archive_type}})
            assert settings.compression.archive.type == archive_type
    
    def test_backup_count_validation(self):
        """Test that backup count is within valid range."""
        with pytest.raises(ValidationError) as exc_info:
            UtilitySettings(logging={"backup_count": 0})
        assert "backup_count" in str(exc_info.value).lower()
        
        with pytest.raises(ValidationError) as exc_info:
            UtilitySettings(logging={"backup_count": 101})
        assert "backup_count" in str(exc_info.value).lower()


class TestPresetConfigurations:
    """Test preset configurations."""
    
    def test_default_preset(self):
        """Test default preset configuration."""
        settings = get_preset_config("default")
        assert settings.compression.quality == 85
        assert settings.compression.format == "webp"
        assert settings.logging.environment == Environment.DEVELOPMENT
        assert settings.logging.console_level == LogLevel.DEBUG
    
    def test_production_preset(self):
        """Test production preset configuration."""
        settings = get_preset_config("production")
        assert settings.compression.quality == 90
        assert settings.compression.archive.level == 15
        assert settings.logging.environment == Environment.PRODUCTION
        assert settings.logging.console_level == LogLevel.WARNING
        assert settings.logging.use_json is True
        assert settings.logging.use_colors is False
    
    def test_development_preset(self):
        """Test development preset configuration."""
        settings = get_preset_config("development")
        assert settings.compression.quality == 80
        assert settings.compression.archive.level == 8
        assert settings.logging.environment == Environment.DEVELOPMENT
        assert settings.logging.console_level == LogLevel.DEBUG
        assert settings.logging.use_json is False
        assert settings.logging.use_colors is True
    
    def test_testing_preset(self):
        """Test testing preset configuration."""
        settings = get_preset_config("testing")
        assert settings.compression.quality == 75
        assert settings.compression.workers == 1
        assert settings.compression.archive.enable is False
        assert settings.logging.environment == Environment.TESTING
        assert settings.logging.console_level == LogLevel.ERROR
        assert settings.logging.use_colors is False
    
    def test_invalid_preset_name(self):
        """Test that invalid preset name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_preset_config("invalid")
        assert "Invalid preset name" in str(exc_info.value)
    
    def test_all_presets_exist(self):
        """Test that all defined presets can be loaded."""
        for preset_name in CONFIG_PRESETS.keys():
            settings = get_preset_config(preset_name)
            assert isinstance(settings, UtilitySettings)


class TestCrossPackageConsistencyValidation:
    """Test cross-package consistency validation."""
    
    def test_production_quality_validation(self):
        """Test that production environment enforces minimum quality."""
        with pytest.raises(ValidationError) as exc_info:
            UtilitySettings(
                compression={"quality": 60},
                logging={"environment": "production"}
            )
        assert "compression quality >= 70" in str(exc_info.value)
    
    def test_production_quality_valid(self):
        """Test that production environment accepts quality >= 70."""
        settings = UtilitySettings(
            compression={"quality": 70},
            logging={"environment": "production"}
        )
        assert settings.compression.quality == 70
        assert settings.logging.environment == Environment.PRODUCTION
    
    def test_development_quality_no_restriction(self):
        """Test that development environment has no quality restriction."""
        settings = UtilitySettings(
            compression={"quality": 50},
            logging={"environment": "development"}
        )
        assert settings.compression.quality == 50
    
    def test_logging_directory_creation(self, tmp_path):
        """Test that logging directory is created for non-production."""
        log_dir = tmp_path / "test_logs"
        settings = UtilitySettings(
            logging={"log_dir": str(log_dir), "environment": "development"}
        )
        assert log_dir.exists()
    
    def test_logging_directory_invalid_path(self):
        """Test that invalid logging directory raises ValueError."""
        import platform
        
        # Use platform-specific invalid paths
        if platform.system() == "Windows":
            # On Windows, use a path with invalid characters
            invalid_path = "C:\\invalid<>path\\with|invalid*chars"
        else:
            # On Unix-like systems, use a path that requires root permissions
            invalid_path = "/root/invalid_path_that_cannot_be_created"
        
        with pytest.raises(ValidationError) as exc_info:
            UtilitySettings(
                logging={"log_dir": invalid_path, "environment": "development"}
            )
        assert "Cannot create logging directory" in str(exc_info.value)


class TestInvalidConfigurationValues:
    """Test that invalid configuration values raise ValidationError."""
    
    def test_invalid_quality_type(self):
        """Test that non-integer quality raises ValidationError."""
        with pytest.raises(ValidationError):
            UtilitySettings(compression={"quality": "invalid"})
    
    def test_invalid_workers_type(self):
        """Test that non-integer workers raises ValidationError."""
        with pytest.raises(ValidationError):
            UtilitySettings(compression={"workers": "invalid"})
    
    def test_invalid_environment_type(self):
        """Test that invalid environment raises ValidationError."""
        with pytest.raises(ValidationError):
            UtilitySettings(logging={"environment": "invalid"})
    
    def test_invalid_log_level(self):
        """Test that invalid log level raises ValidationError."""
        with pytest.raises(ValidationError):
            UtilitySettings(logging={"console_level": "INVALID"})
    
    def test_invalid_boolean_type(self):
        """Test that non-boolean values for boolean fields raise ValidationError."""
        with pytest.raises(ValidationError):
            UtilitySettings(compression={"lossless": "not_a_bool"})


class TestFactoryFunctions:
    """Test factory functions."""
    
    def test_get_utility_settings_returns_instance(self):
        """Test that get_utility_settings returns UtilitySettings instance."""
        settings = get_utility_settings()
        assert isinstance(settings, UtilitySettings)
    
    def test_get_utility_settings_cached(self):
        """Test that get_utility_settings returns cached instance."""
        settings1 = get_utility_settings()
        settings2 = get_utility_settings()
        assert settings1 is settings2
    
    def test_get_preset_config_returns_instance(self):
        """Test that get_preset_config returns UtilitySettings instance."""
        settings = get_preset_config("default")
        assert isinstance(settings, UtilitySettings)
    
    def test_get_preset_config_not_cached(self):
        """Test that get_preset_config returns new instance each time."""
        settings1 = get_preset_config("default")
        settings2 = get_preset_config("default")
        # They should have same values but be different instances
        assert settings1 is not settings2
        assert settings1.compression.quality == settings2.compression.quality


class TestSerialization:
    """Test configuration serialization."""
    
    def test_to_dict(self):
        """Test converting configuration to dictionary."""
        settings = UtilitySettings()
        config_dict = settings.to_dict()
        
        assert isinstance(config_dict, dict)
        assert "compression" in config_dict
        assert "logging" in config_dict
        assert "quality" in config_dict["compression"]
        assert "environment" in config_dict["logging"]
    
    def test_from_dict(self):
        """Test creating configuration from dictionary."""
        config_dict = {
            "compression": {"quality": 95, "format": "png"},
            "logging": {"environment": "production"}
        }
        settings = UtilitySettings.from_dict(config_dict)
        
        assert settings.compression.quality == 95
        assert settings.compression.format == "png"
        assert settings.logging.environment == Environment.PRODUCTION
    
    def test_round_trip_serialization(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = UtilitySettings(
            compression={"quality": 88, "format": "avif"},
            logging={"environment": "development"}
        )
        config_dict = original.to_dict()
        restored = UtilitySettings.from_dict(config_dict)
        
        assert restored.compression.quality == original.compression.quality
        assert restored.compression.format == original.compression.format
        assert restored.logging.environment == original.logging.environment
