"""
Overview:
    This module provides utility functions for the PixCrawler builder package.
    It focuses on file system operations and helper utilities for image processing.

Classes:
    TimeoutException: Custom exception for operation timeouts.

Functions:
    rename_images_sequentially: Renames all image files in a directory to a sequential format.

Features:
    - Sequential renaming of image files.
    - File system utilities for image processing.
"""

from typing import Optional

from builder._helpers import FSRenamer

__all__ = [
    'TimeoutException',
    'rename_images_sequentially',
]


class TimeoutException(Exception):
    """
    Custom exception raised when a timeout occurs during an operation.
    """
    pass


def rename_images_sequentially(directory: str, padding_width: Optional[int] = 4) -> int:
    """
    Rename all image files in a directory to a sequential, zero-padded format.

    Args:
        directory: Directory containing images to rename
        padding_width: The desired width for zero-padding sequential filenames. Defaults to 4.

    Returns:
        int: Number of renamed files
    """
    renamer = FSRenamer(directory, padding_width)
    return renamer.rename_sequentially()
