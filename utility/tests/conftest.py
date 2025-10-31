"""
Pytest configuration and fixtures for utility package tests.

This module provides shared fixtures for testing compression, archiving,
and logging functionality.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from PIL import Image


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for tests.

    Yields:
        Path to temporary directory (cleaned up after test)
    """
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


@pytest.fixture
def mock_image_dir(temp_dir: Path) -> Path:
    """
    Create a directory with mock images for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to directory containing mock images
    """
    img_dir = temp_dir / "images"
    img_dir.mkdir()

    # Create mock images with different formats and sizes
    formats = [
        ("test1.jpg", "JPEG", (800, 600)),
        ("test2.png", "PNG", (1024, 768)),
        ("test3.webp", "WEBP", (640, 480)),
        ("subdir/test4.jpg", "JPEG", (1920, 1080)),
        ("subdir/test5.png", "PNG", (512, 512)),
    ]

    for filename, format_type, size in formats:
        file_path = img_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a simple colored image
        img = Image.new("RGB", size, color=(73, 109, 137))
        img.save(file_path, format=format_type)

    return img_dir


@pytest.fixture
def mock_compressed_dir(temp_dir: Path) -> Path:
    """
    Create a directory with mock compressed images.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to directory containing compressed images
    """
    comp_dir = temp_dir / "compressed"
    comp_dir.mkdir()

    # Create smaller mock compressed images
    formats = [
        ("test1.webp", "WEBP", (800, 600)),
        ("test2.webp", "WEBP", (1024, 768)),
        ("test3.webp", "WEBP", (640, 480)),
    ]

    for filename, format_type, size in formats:
        file_path = comp_dir / filename
        img = Image.new("RGB", size, color=(100, 150, 200))
        img.save(file_path, format=format_type, quality=85)

    return comp_dir


@pytest.fixture
def output_dir(temp_dir: Path) -> Path:
    """
    Create an output directory for test results.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path to output directory
    """
    out_dir = temp_dir / "output"
    out_dir.mkdir()
    return out_dir
