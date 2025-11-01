"""
Image format conversion and compression utilities.

This module provides functions for compressing images to various formats
(WebP, AVIF, PNG) using external tools when available, falling back to PIL.

Functions:
    compress_webp: Compress image to WebP format
    compress_png: Compress image to PNG format
    compress_avif: Compress image to AVIF format
    compress_image: Main compression function with format detection

Features:
    - External tool support (cwebp, pngquant, avifenc) for better quality
    - PIL fallback for portability
    - Configurable quality and lossless modes
    - Automatic parent directory creation
"""

import subprocess
from pathlib import Path

from PIL import Image

__all__ = [
    'compress_webp',
    'compress_png',
    'compress_avif',
    'compress_image'
]


def _run_cmd(cmd: list[str]) -> bool:
    """
    Run external command silently.

    Args:
        cmd: Command and arguments as list

    Returns:
        True if command succeeded, False otherwise
    """
    try:
        # Run command with output suppressed
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        # Command failed or not found
        return False


def _ensure_parent(path: Path) -> None:
    """
    Ensure parent directory exists.

    Args:
        path: File path whose parent directory should exist
    """
    path.parent.mkdir(parents=True, exist_ok=True)


def compress_webp(src: Path, dst: Path, quality: int, lossless: bool) -> None:
    """
    Compress image to WebP format.

    Tries to use cwebp external tool first, falls back to PIL if unavailable.

    Args:
        src: Source image path
        dst: Destination WebP file path
        quality: Compression quality (0-100)
        lossless: Enable lossless compression
    """
    _ensure_parent(dst)
    
    # Build cwebp command arguments
    q = ["-q", str(quality)]
    if lossless:
        q = ["-lossless"]  # Override quality for lossless mode
    
    # Try external cwebp tool first (better quality)
    if _run_cmd(["cwebp", *q, str(src), "-o", str(dst)]):
        return
    
    # Fallback to PIL if cwebp not available
    with Image.open(src) as im:
        im.save(dst, format="WEBP", quality=quality, lossless=lossless, method=6)


def compress_png(src: Path, dst: Path, quality: int, lossless: bool) -> None:
    """
    Compress image to PNG format.

    Tries to use pngquant external tool first, falls back to PIL if unavailable.

    Args:
        src: Source image path
        dst: Destination PNG file path
        quality: Compression quality (0-100)
        lossless: Enable lossless compression (PNG is always lossless)
    """
    _ensure_parent(dst)
    
    # Try pngquant for better compression (quality range with 5-point tolerance)
    if _run_cmd(["pngquant", "--force", "--output", str(dst), "--quality", f"{max(0, quality-5)}-{quality}", str(src)]):
        return
    
    # Fallback to PIL optimization
    with Image.open(src) as im:
        im.save(dst, format="PNG", optimize=True)


def compress_avif(src: Path, dst: Path, quality: int, lossless: bool) -> None:
    """
    Compress image to AVIF format.

    Tries to use avifenc external tool first, falls back to PIL if unavailable.

    Args:
        src: Source image path
        dst: Destination AVIF file path
        quality: Compression quality (0-100)
        lossless: Enable lossless compression
    """
    _ensure_parent(dst)
    
    # Build avifenc command arguments
    cq = ["-Q", str(quality)]
    if lossless:
        # Use lossless encoding parameters
        cq = ["-s", "0", "-a", "end-usage=q", "-a", "cq-level=0"]
    
    # Try external avifenc tool first (better quality)
    if _run_cmd(["avifenc", *cq, str(src), str(dst)]):
        return
    
    # Fallback to PIL if avifenc not available
    with Image.open(src) as im:
        im.save(dst, format="AVIF", quality=quality, lossless=lossless)


def compress_image(src: Path, dst: Path, fmt: str, quality: int, lossless: bool) -> None:
    """
    Compress image to specified format.

    Main compression function that dispatches to format-specific functions.

    Args:
        src: Source image path
        dst: Destination file path
        fmt: Target format ("webp", "avif", "png", "jxl")
        quality: Compression quality (0-100)
        lossless: Enable lossless compression

    Raises:
        ValueError: If format is not supported
    """
    f = fmt.lower()
    
    # Dispatch to format-specific compression function
    if f == "webp":
        # Ensure correct file extension
        if dst.suffix.lower() != ".webp":
            dst = dst.with_suffix(".webp")
        compress_webp(src, dst, quality, lossless)
        return
    
    if f == "png":
        if dst.suffix.lower() != ".png":
            dst = dst.with_suffix(".png")
        compress_png(src, dst, quality, lossless)
        return
    
    if f == "avif":
        if dst.suffix.lower() != ".avif":
            dst = dst.with_suffix(".avif")
        compress_avif(src, dst, quality, lossless)
        return
    
    # Unsupported format
    raise ValueError(f"Unsupported format: {fmt}")
