"""
Overview:
    This module provides various utility functions and classes for the PixCrawler project.
    It includes functionalities for managing download progress caching, image hashing,
    duplicate detection and removal, image integrity validation, and sequential file renaming.

Classes:
    TimeoutException: Custom exception for operation timeouts.
    ProgressCache: Manages the caching of progress for dataset generation.

Functions:
    get_image_hash: Computes a perceptual hash for an image.
    get_file_hash: Computes the MD5 hash of a file's contents.
    _get_image_files: Retrieves a list of all valid image files within a directory.
    _build_hash_maps: Builds content hash and perceptual hash maps for image files.
    _find_exact_duplicates: Identifies exact duplicate images based on content hashes.
    _is_file_duplicate: Checks if a file is already marked as a duplicate.
    _process_perceptual_duplicates: Processes perceptual duplicates and merges them with exact duplicates.
    detect_duplicate_images: Detects duplicate images within a directory.
    remove_duplicate_images: Removes duplicate images from a directory.
    validate_image: Validates if an image file is not corrupted.
    count_valid_images: Counts valid and invalid images in a directory.
    rename_images_sequentially: Renames all image files in a directory to a sequential format.
    count_valid_images_in_latest_batch: Counts valid images in the latest batch.

Features:
    - Progress caching for resuming interrupted dataset generation.
    - Image hashing (perceptual and content) for duplicate detection.
    - Robust duplicate image detection and removal.
    - Image integrity validation using Pillow.
    - Sequential renaming of image files.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

from PIL import Image
from tqdm.auto import tqdm

from constants import DEFAULT_CACHE_FILE, logger
from helpers import is_valid_image_extension, FSRenamer
from _exceptions import PixCrawlerError, DownloadError, GenerationError

__all__ = [
    'TimeoutException',
    'ProgressCache',
    'get_image_hash',
    'get_file_hash',
    'detect_duplicate_images',
    'remove_duplicate_images',
    'validate_image',
    'count_valid_images',
    'rename_images_sequentially',
    'count_valid_images_in_latest_batch'
]


class TimeoutException(Exception):
    """
    Custom exception raised when a timeout occurs during an operation.
    """
    pass


class ProgressCache:
    """
    Manages the caching of progress for dataset generation, allowing the process
    to be resumed from where it left off in case of interruption.
    """

    def __init__(self, cache_file: str = DEFAULT_CACHE_FILE):
        """
        Initializes the ProgressCache.

        Args:
            cache_file (str): The path to the JSON file used for caching progress.
        """
        self.cache_file: str = cache_file
        self.completed_paths: Dict[str, Dict[str, Any]] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """
        Loads the progress cache from the specified cache file.
        If the file does not exist or an error occurs during loading, an empty dictionary is returned.

        Returns:
            Dict[str, Dict[str, Any]]: A dictionary representing the loaded cache.
        """
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load progress cache: {e}")
                raise PixCrawlerError(f"Failed to load progress cache: {e}") from e
        return {}

    def save_cache(self) -> None:
        """
        Saves the current progress cache to the cache file.
        """
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.completed_paths, f, indent=2)
            logger.debug(f"Progress cache saved to {self.cache_file}")
        except IOError as ioe:
            logger.error(f"Failed to save progress cache: {ioe}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while saving progress cache: {e}")

    def is_completed(self, category: str, keyword: str) -> bool:
        """
        Checks if a specific category/keyword combination has already been marked as completed.

        Args:
            category (str): The category name.
            keyword (str): The keyword name.

        Returns:
            bool: True if the combination is found in the completed paths, False otherwise.
        """
        path_key = f"{category}/{keyword}"
        return path_key in self.completed_paths

    def mark_completed(self, category: str, keyword: str,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Marks a specific category/keyword combination as completed and stores optional metadata.
        The cache is saved immediately after marking to ensure persistence.

        Args:
            category (str): The category name.
            keyword (str): The keyword name.
            metadata (Optional[Dict[str, Any]]): Optional dictionary of metadata to store with the completion record.
        """
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
        """
        Retrieves statistics about the completion progress.

        Returns:
            Dict[str, int]: A dictionary containing 'total_completed' (number of completed items)
                            and 'categories' (number of unique categories completed).
        """
        return {
            "total_completed": len(self.completed_paths),
            "categories": len(set(item["category"] for item in self.completed_paths.values()))
        }


def get_image_hash(image_path: str, hash_size: int = 8) -> Optional[str]:
    """
    Computes a perceptual hash for an image, which can be used to find visually similar images.

    Args:
        image_path (str): The path to the image file.
        hash_size (int): The size of the hash (e.g., 8, 16). A larger size results in more sensitivity.

    Returns:
        Optional[str]: The hexadecimal string representation of the perceptual hash, or None if the image cannot be processed.

    Raises:
        GenerationError: If the image cannot be processed.
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
        raise GenerationError(f"Failed to compute hash for {image_path}: {e}") from e


def get_file_hash(file_path: str) -> Optional[str]:
    """
    Computes the MD5 hash of a file's contents.

    Args:
        file_path (str): The path to the file.

    Returns:
        Optional[str]: The hexadecimal string representation of the MD5 hash, or None if the file cannot be read.

    Raises:
        PixCrawlerError: If the file cannot be read.
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
        raise PixCrawlerError(f"Failed to compute file hash for {file_path}: {e}") from e


def _get_image_files(directory_path: Path) -> List[str]:
    """
    Retrieves a list of all valid image files within a specified directory.

    Args:
        directory_path (Path): The path to the directory to scan.

    Returns:
        List[str]: A list of absolute paths to the image files.
    """
    return [
        str(f) for f in directory_path.iterdir()
        if f.is_file() and is_valid_image_extension(f)
    ]


def _build_hash_maps(image_files: List[str]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Builds content hash and perceptual hash maps for a list of image files.

    Args:
        image_files (List[str]): A list of absolute paths to image files.

    Returns:
        Tuple[Dict[str, List[str]], Dict[str, List[str]]]: A tuple containing two dictionaries:
            - The first dictionary maps content hashes to a list of file paths with that hash.
            - The second dictionary maps perceptual hashes to a list of file paths with that hash.
    """
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
    """
    Identifies exact duplicate images based on their content hashes.

    Args:
        content_hash_map (Dict[str, List[str]]): A dictionary mapping content hashes to lists of file paths.

    Returns:
        Dict[str, List[str]]: A dictionary where keys are the paths to original images
                              and values are lists of their exact duplicate file paths.
    """
    duplicates: Dict[str, List[str]] = {}

    for file_list in content_hash_map.values():
        if len(file_list) > 1:
            # Keep the first as original, others as duplicates
            original = file_list[0]
            dups = file_list[1:]
            duplicates[original] = dups

    return duplicates


def _is_file_duplicate(img: str, duplicates: Dict[str, List[str]]) -> bool:
    """
    Checks if a given image file path is already marked as a duplicate in the provided dictionary.

    Args:
        img (str): The path to the image file.
        duplicates (Dict[str, List[str]]): A dictionary of duplicate image mappings.

    Returns:
        bool: True if the file is a duplicate, False otherwise.
    """
    for dups in duplicates.values():
        if img in dups:
            return True
    return False


# noinspection t
def _process_perceptual_duplicates(
        perceptual_hash_map: Dict[str, List[str]],
        existing_duplicates: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """
    Processes perceptual duplicates and merges them with a dictionary of existing exact duplicates.
    It identifies visually similar images and adds them to the duplicates list, ensuring that
    already marked exact duplicates are not re-processed.

    Args:
        perceptual_hash_map (Dict[str, List[str]]): A dictionary mapping perceptual hashes to lists of file paths.
        existing_duplicates (Dict[str, List[str]]): A dictionary of already identified exact duplicates.

    Returns:
        Dict[str, List[str]]: An updated dictionary of duplicates, including both exact and perceptual duplicates.
    """
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
    Detects duplicate images within a specified directory using both content hashing for exact matches
    and perceptual hashing for visually similar images.

    Args:
        directory (str): The path to the directory to check for duplicates.

    Returns:
        Dict[str, List[str]]: A dictionary where keys are the paths to original images
                              and values are lists of their duplicate file paths.
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
    Removes duplicate images from a specified directory.
    It identifies duplicates using both content and perceptual hashing and deletes them,
    keeping one original copy.

    Args:
        directory (str): The path to the directory to clean.

    Returns:
        Tuple[int, List[str]]: A tuple containing:
            - The number of duplicate images removed.
            - A list of paths to the original images that were kept.
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
            except OSError as ose:
                logger.warning(f"Failed to remove duplicate {dup}: {ose}")
            except Exception as e:
                logger.warning(f"An unexpected error occurred while removing duplicate {dup}: {e}")

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
    except (Image.UnidentifiedImageError, IOError) as e:
        logger.error(f"Corrupted image detected: {image_path} - {str(e)}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during image validation: {image_path} - {str(e)}")
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


def rename_images_sequentially(directory: str) -> int:
    """
    Rename all image files in a directory to a sequential, zero-padded format.

    Args:
        directory: Directory containing images to rename

    Returns:
        int: Number of renamed files
    """
    renamer = FSRenamer(directory)
    return renamer.rename_sequentially()


def count_valid_images_in_latest_batch(directory: str, previous_count: int) -> int:
    """
    Count valid images in the latest batch, starting from previous_count index.

    Args:
        directory: Directory path to check
        previous_count: Number of images that existed before this batch

    Returns:
        int: Number of valid images in the latest batch
    """
    valid_count = 0

    directory_path = Path(directory)
    if not directory_path.exists():
        return 0

    # Get all image files
    image_files = [
        f for f in directory_path.iterdir()
        if f.is_file() and is_valid_image_extension(f)
    ]

    # Sort by creation time to get the latest batch
    image_files.sort(key=lambda x: os.path.getctime(x))

    # Take only files that were likely created in this batch
    latest_batch = image_files[previous_count:]

    for file_path in latest_batch:
        if validate_image(str(file_path)):
            valid_count += 1
        else:
            # Remove corrupted image
            try:
                os.remove(file_path)
                logger.warning(f"Removed corrupted image: {file_path}")
            except OSError as ose:
                logger.warning(f"Error removing corrupted image {file_path}: {ose}")
            except Exception as e:
                logger.warning(f"An unexpected error occurred while removing corrupted image {file_path}: {e}")

    return valid_count
