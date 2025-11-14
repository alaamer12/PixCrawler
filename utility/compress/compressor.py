"""
Image compression module for batch processing.

This module provides the ImageCompressor class for batch compressing images
using multiple worker threads and progress tracking.

Classes:
    ImageCompressor: Batch image compression with multi-threading

Functions:
    _iter_images: Iterator for finding image files recursively

Features:
    - Multi-threaded compression for performance
    - Progress tracking with tqdm
    - Support for multiple image formats
    - Recursive directory scanning
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

from tqdm import tqdm

from utility.compress.config import CompressionSettings
from utility.compress.formats import compress_image

__all__ = ['ImageCompressor']

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif", ".bmp", ".tiff"}


def _iter_images(root: Path) -> Iterable[Path]:
    """
    Recursively iterate over image files in a directory.

    Args:
        root: Root directory to search for images

    Yields:
        Path objects for each image file found
    """
    # Recursively find all files in the directory tree
    for p in root.rglob("*"):
        # Check if it's a file and has a valid image extension
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            yield p


class ImageCompressor:
    """
    Batch image compressor with multi-threading support.

    This class handles batch compression of images from an input directory
    to an output directory, preserving the directory structure and using
    multiple worker threads for performance.

    Attributes:
        cfg: CompressionSettings instance with configuration
    """

    def __init__(self, cfg: CompressionSettings) -> None:
        """
        Initialize the image compressor.

        Args:
            cfg: CompressionSettings instance with compression configuration
        """
        self.cfg = cfg

    def _dst_for(self, src: Path) -> Path:
        """
        Calculate destination path for a source image.

        Args:
            src: Source image path

        Returns:
            Destination path maintaining relative directory structure
        """
        # Get relative path from input directory
        rel = src.relative_to(self.cfg.input_dir)
        # Construct destination path maintaining directory structure
        dst = self.cfg.output_dir / rel
        return dst

    def _compress_one(self, src: Path) -> Path:
        """
        Compress a single image file.

        Args:
            src: Source image path

        Returns:
            Destination path of compressed image
        """
        dst = self._dst_for(src)
        compress_image(src, dst, self.cfg.format, self.cfg.quality, self.cfg.lossless)
        return dst

    def run(self) -> None:
        """
        Run batch compression on all images in input directory.

        This method:
        1. Creates output directory if needed
        2. Finds all images in input directory
        3. Compresses them using multiple worker threads
        4. Shows progress with tqdm
        """
        # Ensure output directory exists
        self.cfg.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all images in input directory
        items = list(_iter_images(self.cfg.input_dir))
        if not items:
            return  # No images found, nothing to do
        
        # Determine number of worker threads
        workers = self.cfg.resolved_workers
        
        # Process images in parallel with progress bar
        with ThreadPoolExecutor(max_workers=workers) as ex:
            # Submit all compression tasks
            futures = [ex.submit(self._compress_one, p) for p in items]
            # Wait for completion with progress tracking
            for _ in tqdm(as_completed(futures), total=len(futures), desc="Compress"):
                pass
