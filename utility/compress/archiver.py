"""
Dataset archiving module with compression support.

This module provides the Archiver class for creating compressed archives
of datasets, supporting tar+zstd and zip formats.

Classes:
    Archiver: Create compressed archives of directories

Features:
    - Tar archive creation
    - Zstandard compression with configurable levels
    - ZIP archive support
    - Multi-threaded compression
"""

import os
import tarfile
import tempfile
import zipfile
from pathlib import Path

import zstandard as zstd

__all__ = ['Archiver']


class Archiver:
    """
    Create compressed archives of directories.

    This class handles creating compressed archives of datasets,
    supporting tar+zstd and zip formats with configurable compression levels.

    Attributes:
        root: Root directory to archive
    """

    def __init__(self, root: Path) -> None:
        """
        Initialize the archiver.

        Args:
            root: Root directory to archive
        """
        self.root = root

    def _tar_dir(self, tar_path: Path) -> None:
        """
        Create a tar archive of the root directory.

        Args:
            tar_path: Output path for the tar file
        """
        # Open tar file in write mode, following symlinks
        with tarfile.open(tar_path, "w", dereference=True) as tf:
            # Add entire directory tree with "." as archive root
            tf.add(self.root, arcname=".")

    def _compress_zstd(self, src: Path, dst: Path, level: int) -> None:
        """
        Compress a file using Zstandard compression.

        Args:
            src: Source file path
            dst: Destination compressed file path
            level: Compression level (1-19)
        """
        # Configure zstd compression parameters with multi-threading
        cparams = zstd.ZstdCompressionParameters.from_level(level=level, threads=-1)
        compressor = zstd.ZstdCompressor(compression_params=cparams)

        # Stream compress from source to destination
        with open(src, "rb") as f_in, open(dst, "wb") as f_out:
            compressor.copy_stream(f_in, f_out)

    def create(self, output: Path, use_tar: bool, kind: str, level: int) -> Path:
        """
        Create a compressed archive.

        Args:
            output: Output file path
            use_tar: Whether to use tar format_ before compression
            kind: Archive type ("zstd", "zip", "none")
            level: Compression level

        Returns:
            Path to the created archive file
        """
        # Ensure output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)

        # Create ZIP archive (no tar needed)
        if kind == "zip" or not use_tar:
            with zipfile.ZipFile(output.with_suffix(".zip"), "w", compression=zipfile.ZIP_DEFLATED) as zf:
                # Walk directory tree and add all files
                for base, _, files in os.walk(self.root):
                    for name in files:
                        p = Path(base) / name
                        # Add file with relative path as archive name
                        zf.write(p, arcname=str(p.relative_to(self.root)))
            return output.with_suffix(".zip")

        # Create tar+zstd archive
        with tempfile.TemporaryDirectory() as td:
            # First create tar archive in temp directory
            tar_path = Path(td) / "data.tar"
            self._tar_dir(tar_path)

            # Then compress with zstd if requested
            if kind == "zstd":
                out = output if output.suffix else output.with_suffix(".zst")
                self._compress_zstd(tar_path, out, level)
                return out

            # Return uncompressed tar
            return tar_path
