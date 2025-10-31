"""
PixCrawler Utility Package.

Centralized utility system for the PixCrawler monorepo, providing reusable
components for compression, archiving, and logging.

Modules:
    compress: Image compression and archiving utilities
    logging_config: Centralized Loguru-based logging configuration

Features:
    - Type-safe configuration with Pydantic Settings
    - Environment-based configuration with .env support
    - Production-ready logging with Loguru
    - High-performance image compression
    - Dataset archiving with Zstandard compression
"""

__version__ = "0.1.0"
__author__ = "PixCrawler Team"

__all__ = ["compress", "logging_config"]
