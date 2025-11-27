"""
PixCrawler Utility Package.

Centralized utility system for the PixCrawler monorepo, providing reusable
components for compression, archiving, and logging.

Modules:
    config: Unified configuration system for all utility sub-packages
    compress: Image compression and archiving utilities
    logging_config: Centralized Loguru-based logging configuration

Features:
    - Unified configuration management with Pydantic V2
    - Type-safe configuration with nested composition
    - Environment-based configuration with PIXCRAWLER_UTILITY_ prefix
    - Preset configurations (default, production, development, testing)
    - Cross-package consistency validation
    - Production-ready logging with Loguru
    - High-performance image compression
    - Dataset archiving with Zstandard compression
"""

__version__ = "0.1.0"
__author__ = "PixCrawler Team"

__all__ = ["config", "compress", "logging_config"]
