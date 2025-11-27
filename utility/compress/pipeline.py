"""
Compression and archiving pipeline.

This module provides the main pipeline for compressing images and creating
archives, combining the compressor and archiver modules.

Functions:
    run: Execute the complete compression and archiving pipeline

Features:
    - Batch image compression
    - Optional dataset archiving
    - Configuration from environment variables
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import os
import tarfile
import zipfile
import zstandard as zstd
import tempfile

from utility.compress.archiver import Archiver
from utility.compress.compressor import ImageCompressor
from utility.compress.config import CompressionSettings, get_compression_settings

__all__ = ['run', 'compress', 'decompress']


def run() -> None:
    """
    Execute the complete compression and archiving pipeline.

    This function:
    1. Loads configuration from environment
    2. Compresses all images in input directory
    3. Optionally creates an archive of the compressed images

    The configuration is loaded from .env file or environment variables.
    See CompressionSettings for available options.
    """
    # Load configuration from environment
    cfg = get_compression_settings()

    # Compress all images
    compressor = ImageCompressor(cfg)
    compressor.run()

    # Create archive if enabled
    if cfg.archive.enable:
        archiver = Archiver(cfg.output_dir)
        out = Path(cfg.archive.output)
        kind = cfg.archive.type
        archiver.create(out, cfg.archive.tar, kind, cfg.archive.level)


def compress(
    input_dir: str | Path = "./images",
    output_dir: str | Path = "./compressed",
    format_: str = "webp",
    quality: int = 85,
    lossless: bool = False,
    workers: int = 0,
    archive: bool = False,
    archive_output: Optional[str | Path] = None,
    debug: bool = False,
) -> Path:
    """
    Simple high-level API for compressing images.

    Args:
        input_dir: Directory containing images to compress
        output_dir: Directory for compressed images
        format_: Image format (webp, avif, png, jxl)
        quality: Compression quality (0-100)
        lossless: Enable lossless compression
        workers: Number of worker threads (0 = auto-detect)
        archive: Create archive after compression
        archive_output: Archive output path (default: ./dataset.zst)
        debug: Show detailed statistics (before/after sizes, compression ratio)

    Returns:
        Path to output directory or archive file

    Example:
        ```python
        # Simple compression
        compress("./raw_images", "./compressed")

        # With archiving
        archive_path = compress(
            "./raw_images",
            "./compressed",
            format="webp",
            quality=90,
            archive=True
        )
        ```
    """

    # Create configuration from parameters
    cfg = CompressionSettings(
        input_dir=Path(input_dir),
        output_dir=Path(output_dir),
        format=format_,  # type: ignore
        quality=quality,
        lossless=lossless,
        workers=workers,
    )

    # Calculate input directory size if debug mode
    input_size: Optional[float] = None
    output_size: Optional[float] = None
    if debug:
        input_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(cfg.input_dir)
            for filename in filenames
        )
        input_files = sum(
            len(filenames)
            for _, _, filenames in os.walk(cfg.input_dir)
        )
        print(f"\n{'='*60}")
        print(f"COMPRESSION DEBUG INFO")
        print(f"{'='*60}")
        print(f"Input Directory: {cfg.input_dir}")
        print(f"Input Files: {input_files}")
        print(f"Input Size: {input_size / (1024*1024):.2f} MB")
        print(f"Format: {cfg.format}")
        print(f"Quality: {cfg.quality}")
        print(f"Lossless: {cfg.lossless}")
        print(f"Workers: {cfg.resolved_workers}")
        print(f"{'='*60}\n")

    # Compress images
    compressor = ImageCompressor(cfg)
    compressor.run()

    # Calculate output directory size if debug mode
    if debug:
        output_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(cfg.output_dir)
            for filename in filenames
        )
        output_files = sum(
            len(filenames)
            for _, _, filenames in os.walk(cfg.output_dir)
        )
        compression_ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0
        print(f"\n{'='*60}")
        print(f"COMPRESSION RESULTS")
        print(f"{'='*60}")
        print(f"Output Directory: {cfg.output_dir}")
        print(f"Output Files: {output_files}")
        print(f"Output Size: {output_size / (1024*1024):.2f} MB")
        print(f"Space Saved: {(input_size - output_size) / (1024*1024):.2f} MB")
        print(f"Compression Ratio: {compression_ratio:.2f}%")
        print(f"{'='*60}\n")

    # Create archive if requested
    if archive:
        archiver = Archiver(cfg.output_dir)
        out = Path(archive_output) if archive_output else Path("./dataset.zst")

        if debug:
            print(f"Creating archive: {out}")

        archive_path = archiver.create(out, use_tar=True, kind="zstd", level=10)

        if debug:
            archive_size = os.path.getsize(archive_path)
            archive_ratio = (1 - archive_size / output_size) * 100 if output_size > 0 else 0
            print(f"\n{'='*60}")
            print(f"ARCHIVE RESULTS")
            print(f"{'='*60}")
            print(f"Archive Path: {archive_path}")
            print(f"Archive Size: {archive_size / (1024*1024):.2f} MB")
            print(f"Archive Compression: {archive_ratio:.2f}%")
            print(f"Total Space Saved: {(input_size - archive_size) / (1024*1024):.2f} MB")
            print(f"Total Compression: {(1 - archive_size / input_size) * 100:.2f}%")
            print(f"{'='*60}\n")

        return archive_path

    return cfg.output_dir


def decompress(
    archive_path: str | Path,
    output_dir: str | Path = "./decompressed",
    debug: bool = False,
) -> Path:
    """
    Simple high-level API for decompressing archives.

    Args:
        archive_path: Path to archive file (.zst, .zip, .tar)
        output_dir: Directory to extract files to
        debug: Show detailed extraction statistics

    Returns:
        Path to output directory

    Example:
        ```python
        # Decompress archive
        decompress("./dataset.zst", "./extracted")
        ```
    """

    archive_path = Path(archive_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_size: Optional[float] = None

    # Get archive size if debug mode
    if debug:
        archive_size = os.path.getsize(archive_path)
        print(f"\n{'='*60}")
        print(f"DECOMPRESSION DEBUG INFO")
        print(f"{'='*60}")
        print(f"Archive Path: {archive_path}")
        print(f"Archive Type: {archive_path.suffix}")
        print(f"Archive Size: {archive_size / (1024*1024):.2f} MB")
        print(f"Output Directory: {output_dir}")
        print(f"{'='*60}\n")

    # Handle different archive types based on extension
    if archive_path.suffix == ".zip":
        # Extract ZIP archive
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(output_dir)

    elif archive_path.suffix == ".zst":
        # Decompress zstd, then extract tar
        with tempfile.TemporaryDirectory() as td:
            # Decompress zstd to temporary tar file
            tar_path = Path(td) / "data.tar"
            dctx = zstd.ZstdDecompressor()
            with open(archive_path, "rb") as f_in, open(tar_path, "wb") as f_out:
                dctx.copy_stream(f_in, f_out)

            # Extract tar archive
            with tarfile.open(tar_path, "r") as tf:
                tf.extractall(output_dir)

    elif archive_path.suffix == ".tar":
        # Extract tar archive directly
        with tarfile.open(archive_path, "r") as tf:
            tf.extractall(output_dir)

    else:
        raise ValueError(f"Unsupported archive format_: {archive_path.suffix}")

    # Calculate extracted size if debug mode
    if debug:
        extracted_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, _, filenames in os.walk(output_dir)
            for filename in filenames
        )
        extracted_files = sum(
            len(filenames)
            for _, _, filenames in os.walk(output_dir)
        )
        expansion_ratio = (extracted_size / archive_size) if archive_size > 0 else 0
        print(f"\n{'='*60}")
        print(f"DECOMPRESSION RESULTS")
        print(f"{'='*60}")
        print(f"Extracted Files: {extracted_files}")
        print(f"Extracted Size: {extracted_size / (1024*1024):.2f} MB")
        print(f"Expansion Ratio: {expansion_ratio:.2f}x")
        print(f"Space Saved by Archive: {(extracted_size - archive_size) / (1024*1024):.2f} MB")
        print(f"{'='*60}\n")

    return output_dir


if __name__ == "__main__":
    run()
