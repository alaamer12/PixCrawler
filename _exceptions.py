"""
Custom exception classes for the PixCrawler project.
"""


class PixCrawlerError(Exception):
    """Base exception for PixCrawler related errors."""
    pass


class ConfigurationError(PixCrawlerError):
    """Exception raised for errors in configuration settings."""
    pass


class DownloadError(PixCrawlerError):
    """Exception raised for errors during the image download process."""
    pass


class GenerationError(PixCrawlerError):
    """Exception raised for errors during the image generation process."""
    pass


class ArgumentError(PixCrawlerError):
    """Exception raised for errors related to command-line arguments."""
    pass
