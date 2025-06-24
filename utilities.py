import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple, Union

from PIL import Image
from tqdm.auto import tqdm

from constants import DEFAULT_CACHE_FILE, logger, IMAGE_EXTENSIONS


class TimeoutException(Exception):
    """Custom exception for timeout operations"""
    pass


def is_valid_image_extension(file_path: Union[str, Path]) -> bool:
    """
    Check if a file has a valid image extension.

    Args:
        file_path: Path to check

    Returns:
        bool: True if valid image extension, False otherwise
    """
    if isinstance(file_path, str):
        file_path = Path(file_path)

    return file_path.suffix.lower() in IMAGE_EXTENSIONS


class ProgressCache:
    """
    Tracks and manages progress for dataset generation to enable continuing from where we left off.
    """

    def __init__(self, cache_file: str = DEFAULT_CACHE_FILE):
        self.cache_file = cache_file
        self.completed_paths = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load progress cache from file if it exists."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load progress cache: {e}")
                return {}
        return {}

    def save_cache(self) -> None:
        """Save current progress to cache file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.completed_paths, f, indent=2)
            logger.debug(f"Progress cache saved to {self.cache_file}")
        except Exception as e:
            logger.error(f"Failed to save progress cache: {e}")

    def is_completed(self, category: str, keyword: str) -> bool:
        """Check if a specific path has been completed."""
        path_key = f"{category}/{keyword}"
        return path_key in self.completed_paths

    def mark_completed(self, category: str, keyword: str,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark a path as completed with optional metadata."""
        path_key = f"{category}/{keyword}"
        self.completed_paths[path_key] = {
            "timestamp": time.time(),
            "category": category,
            "keyword": keyword,
            "metadata": metadata or {}
        }
        # Save after each update to ensure progress is not lost
        self.save_cache()

    def get_completion_stats(self) -> Dict[str, int]:
        """Get statistics about completion progress."""
        return {
            "total_completed": len(self.completed_paths),
            "categories": len(set(item["category"] for item in self.completed_paths.values()))
        }


def get_image_hash(image_path: str, hash_size: int = 8) -> Optional[str]:
    """
    Compute a perceptual hash for an image to find visually similar images.
    
    Args:
        image_path: Path to the image file
        hash_size: Size of the hash (larger = more sensitive)
        
    Returns:
        str: Perceptual hash string or None if image can't be processed
    """
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale and resize
            img = img.convert("L").resize((hash_size, hash_size), Image.Resampling.LANCZOS)

            # Calculate mean pixel value
            # noinspection PyTypeChecker
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)

            # Create hash
            binary_hash = ''.join('1' if px >= avg else '0' for px in pixels)
            hex_hash = hex(int(binary_hash, 2))[2:]

            return hex_hash.zfill(hash_size ** 2 // 4)
    except Exception as e:
        logger.warning(f"Failed to compute hash for {image_path}: {e}")
        return None


def get_file_hash(file_path: str) -> Optional[str]:
    """
    Compute a regular MD5 hash of file contents.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MD5 hash string or None if file can't be read
    """
    try:
        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            # Read in chunks in case of large files
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    except Exception as e:
        logger.warning(f"Failed to compute file hash for {file_path}: {e}")
        return None


def _get_image_files(directory_path: Path) -> List[str]:
    """Get all valid image files from directory."""
    return [
        str(f) for f in directory_path.iterdir()
        if f.is_file() and is_valid_image_extension(f)
    ]


def _build_hash_maps(image_files: List[str]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Build content and perceptual hash maps for all images."""
    content_hash_map: Dict[str, List[str]] = {}
    perceptual_hash_map: Dict[str, List[str]] = {}

    for img_path in image_files:
        # Get content hash (exact match)
        content_hash = get_file_hash(img_path)
        if content_hash:
            content_hash_map.setdefault(content_hash, []).append(img_path)

        # Get perceptual hash (similar images)
        perceptual_hash = get_image_hash(img_path)
        if perceptual_hash:
            perceptual_hash_map.setdefault(perceptual_hash, []).append(img_path)

    return content_hash_map, perceptual_hash_map


def _find_exact_duplicates(content_hash_map: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Find exact duplicates based on content hash."""
    duplicates: Dict[str, List[str]] = {}

    for file_list in content_hash_map.values():
        if len(file_list) > 1:
            # Keep the first as original, others as duplicates
            original = file_list[0]
            dups = file_list[1:]
            duplicates[original] = dups

    return duplicates


def _is_file_duplicate(img: str, duplicates: Dict[str, List[str]]) -> bool:
    """Check if a file is already marked as a duplicate."""
    for dups in duplicates.values():
        if img in dups:
            return True
    return False


# noinspection t
def _process_perceptual_duplicates(
        perceptual_hash_map: Dict[str, List[str]],
        existing_duplicates: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """Process perceptual duplicates and merge with existing duplicates."""
    duplicates = existing_duplicates.copy()

    for file_list in perceptual_hash_map.values():
        if len(file_list) > 1:
            kept_file = None

            # Find an image not already marked as duplicate
            for img in file_list:
                if not _is_file_duplicate(img, duplicates):
                    if kept_file is None:
                        kept_file = img
                    else:
                        # Add to duplicates of kept_file
                        if kept_file in duplicates:
                            duplicates[kept_file].append(img)
                        else:
                            duplicates[kept_file] = [img]

    return duplicates


def detect_duplicate_images(directory: str) -> Dict[str, List[str]]:
    """
    Detect duplicate images in a directory using both content hash and perceptual hash.
    
    Args:
        directory: Directory path to check for duplicates
        
    Returns:
        Dict mapping original images to lists of their duplicates
    """
    directory_path = Path(directory)

    # Get all image files
    image_files = _get_image_files(directory_path)

    # Build hash maps
    content_hash_map, perceptual_hash_map = _build_hash_maps(image_files)

    # Find exact duplicates first
    duplicates = _find_exact_duplicates(content_hash_map)

    # Then process perceptual duplicates
    duplicates = _process_perceptual_duplicates(perceptual_hash_map, duplicates)

    return duplicates


def remove_duplicate_images(directory: str) -> Tuple[int, List[str]]:
    """
    Remove duplicate images from a directory.
    
    Args:
        directory: Directory path to clean
        
    Returns:
        Tuple of (number of removed duplicates, list of original images kept)
    """
    duplicates = detect_duplicate_images(directory)

    # Flatten the dictionary to get all duplicates to remove
    removed_count = 0
    removed_files = []
    originals_kept = []

    for original, dups in duplicates.items():
        # Keep track of originals we're keeping
        originals_kept.append(original)

        # Remove duplicates
        for dup in dups:
            try:
                os.remove(dup)
                removed_count += 1
                removed_files.append(dup)
                logger.info(f"Removed duplicate image: {dup} (duplicate of {original})")
            except Exception as e:
                logger.warning(f"Failed to remove duplicate {dup}: {e}")

    logger.info(f"Removed {removed_count} duplicate images from {directory}")
    return removed_count, originals_kept


def validate_image(image_path: str) -> bool:
    """
    Validate if an image file is not corrupted using Pillow.

    Args:
        image_path: Path to the image file

    Returns:
        bool: True if image is valid, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            img.verify()  # Verify image integrity

            # Additional check for very small or empty images
            if img.width < 50 or img.height < 50:
                logger.warning(f"Image too small: {image_path} ({img.width}x{img.height})")
                return False

        return True
    except Exception as e:
        logger.error(f"Corrupted image detected: {image_path} - {str(e)}")
        return False


def count_valid_images(directory: str) -> Tuple[int, int, List[str]]:
    """
    Count valid and invalid images in a directory.

    Args:
        directory: Directory path to check

    Returns:
        Tuple of (valid_count, total_count, corrupted_files)
    """
    valid_count = 0
    total_count = 0
    corrupted_files = []

    directory_path = Path(directory)
    if not directory_path.exists():
        return 0, 0, []

    for file_path in tqdm(directory_path.iterdir(), desc="Validating", leave=False, unit="file"):
        if file_path.is_file() and is_valid_image_extension(file_path):
            total_count += 1
            if validate_image(str(file_path)):
                valid_count += 1
            else:
                corrupted_files.append(str(file_path))

    return valid_count, total_count, corrupted_files
