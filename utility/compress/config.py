"""
Compression and archiving configuration using Pydantic Settings.

This module provides type-safe configuration management for image compression
and archiving operations, supporting environment-based configuration with
validation and sensible defaults.

Classes:
    ArchiveSettings: Archive-specific configuration settings
    CompressionSettings: Main compression and archive configuration

Functions:
    get_compression_settings: Get cached compression settings instance

Features:
    - Environment-based configuration with .env file support
    - Type-safe configuration with Pydantic v2 validation
    - Support for multiple compression formats (WebP, AVIF, PNG, JXL)
    - Archive support (Zstandard, ZIP)
    - Automatic worker count detection
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    'FormatLiteral',
    'ArchiveTypeLiteral',
    'ArchiveSettings',
    'CompressionSettings',
    'get_compression_settings'
]

FormatLiteral = Literal["webp", "avif", "png", "jxl"]
ArchiveTypeLiteral = Literal["zstd", "zip", "none"]


class ArchiveSettings(BaseSettings):
    """
    Archive-specific configuration settings.

    This class defines configuration options for dataset archiving,
    including compression type, level, and output settings.

    Attributes:
        enable: Whether to enable archiving
        tar: Whether to use tar format_ before compression
        type: Archive compression type (zstd, zip, none)
        level: Compression level (1-19 for zstd)
        output: Output file path for the archive
    """

    model_config = SettingsConfigDict(
        env_prefix="ARCHIVE_",
        validate_default=True,
        str_strip_whitespace=True,
        extra="ignore"
    )

    enable: bool = Field(
        default=True,
        description="Enable dataset archiving",
        examples=[True, False]
    )
    tar: bool = Field(
        default=True,
        description="Use tar format_ before compression",
        examples=[True, False]
    )
    type: ArchiveTypeLiteral = Field(
        default="zstd",
        description="Archive compression type",
        examples=["zstd", "zip", "none"]
    )
    level: int = Field(
        default=10,
        ge=1,
        le=19,
        description="Compression level (1-19)",
        examples=[1, 10, 19]
    )
    output: Path = Field(
        default=Path("./dataset.zst"),
        description="Output file path for archive",
        examples=[Path("./dataset.zst"), Path("./output/archive.tar.zst")]
    )

    @field_validator("level")
    @classmethod
    def validate_compression_level(cls, v: int) -> int:
        """
        Validate compression level is within valid range.

        Args:
            v: Compression level value

        Returns:
            Validated compression level

        Raises:
            ValueError: If level is not between 1 and 19
        """
        if v < 1 or v > 19:
            raise ValueError("archive.level must be between 1 and 19")
        return v


class CompressionSettings(BaseSettings):
    """
    Main compression and archive configuration.

    This class defines all configuration options for image compression
    and archiving, including input/output directories, compression format_,
    quality settings, and archive options.

    Attributes:
        input_dir: Input directory containing images to compress
        output_dir: Output directory for compressed images
        format: Image compression format_ (webp, avif, png, jxl)
        quality: Compression quality (0-100)
        lossless: Enable lossless compression
        workers: Number of worker threads (0 = auto-detect)
        archive__enable: Override archive enable setting
        archive__tar: Override archive tar setting
        archive__type: Override archive type setting
        archive__level: Override archive compression level
        archive__output: Override archive output path
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        str_strip_whitespace=True
    )

    # Compression settings
    input_dir: Path = Field(
        default=Path("./images"),
        description="Input directory containing images",
        examples=[Path("./images"), Path("/data/raw_images")]
    )
    output_dir: Path = Field(
        default=Path("./compressed"),
        description="Output directory for compressed images",
        examples=[Path("./compressed"), Path("/data/processed")]
    )
    format: FormatLiteral = Field(
        default="webp",
        description="Image compression format_",
        examples=["webp", "avif", "png", "jxl"]
    )
    quality: int = Field(
        default=85,
        ge=0,
        le=100,
        description="Compression quality (0-100)",
        examples=[75, 85, 95]
    )
    lossless: bool = Field(
        default=False,
        description="Enable lossless compression",
        examples=[True, False]
    )
    workers: int = Field(
        default=0,
        ge=0,
        description="Number of worker threads (0 = auto-detect)",
        examples=[0, 4, 8]
    )

    # Nested archive settings using composition
    archive: ArchiveSettings = Field(
        default_factory=ArchiveSettings,
        description="Archive configuration settings"
    )

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v: int) -> int:
        """
        Validate compression quality is within valid range.

        Args:
            v: Quality value

        Returns:
            Validated quality value

        Raises:
            ValueError: If quality is not between 0 and 100
        """
        if v < 0 or v > 100:
            raise ValueError("quality must be between 0 and 100")
        return v

    @computed_field
    @property
    def resolved_workers(self) -> int:
        """
        Get resolved worker count with auto-detection.

        Returns:
            Number of worker threads to use
        """
        import multiprocessing

        if self.workers and self.workers > 0:
            return self.workers
        try:
            return max(1, multiprocessing.cpu_count() or 1)
        except Exception:
            return 1


@lru_cache()
def get_compression_settings() -> CompressionSettings:
    """
    Get cached compression settings instance.

    Returns:
        Cached CompressionSettings instance
    """
    return CompressionSettings()
