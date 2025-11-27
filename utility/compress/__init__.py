"""
Image compression and archiving module.

This module provides utilities for batch image compression and dataset archiving,
with support for multiple formats and compression algorithms.

Classes:
    CompressionSettings: Configuration for compression and archiving
    ArchiveSettings: Archive-specific configuration
    ImageCompressor: Batch image compression with multi-threading
    Archiver: Dataset archiving with compression

Functions:
    run: Execute complete compression and archiving pipeline
    get_compression_settings: Get cached compression settings

Features:
    - Multi-format_ support (WebP, AVIF, PNG, JXL)
    - Multi-threaded compression
    - Zstandard and ZIP archiving
    - Environment-based configuration
    - Progress tracking

Example:
    ```python
    from utility.compress import compress, decompress

    # Simple compression
    compress("./raw_images", "./compressed")

    # With archiving
    archive_path = compress(
        "./raw_images",
        "./compressed",
        format_="webp",
        quality=90,
        archive=True
    )

    # Decompress archive
    decompress("./dataset.zst", "./extracted")

    # Advanced usage with configuration
    from utility.compress import run, get_compression_settings
    run()  # Uses .env configuration
    ```
"""

from utility.compress.archiver import Archiver
from utility.compress.compressor import ImageCompressor
from utility.compress.config import (
    ArchiveSettings,
    CompressionSettings,
    get_compression_settings,
)
from utility.compress.pipeline import compress, decompress, run

__version__ = "0.1.0"
__author__ = "PixCrawler Team"

__all__ = [
    "CompressionSettings",
    "ArchiveSettings",
    "ImageCompressor",
    "Archiver",
    "run",
    "compress",
    "decompress",
    "get_compression_settings",
]
