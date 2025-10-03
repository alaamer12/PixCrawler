"""
Backend integrity management module for PixCrawler.

This module handles all image integrity validation, duplicate detection,
and quality assurance workflows that were previously in the builder package.

Classes:
    ImageHasher: Computes image hashes for duplicate detection
    DuplicationManager: Detects and manages duplicate images
    ImageValidator: Validates image integrity and quality
    IntegrityProcessor: Main processor for integrity workflows

Functions:
    validate_dataset: Validates an entire dataset
    remove_duplicates: Removes duplicates from a dataset
    process_integrity: Main entry point for integrity processing
"""

import hashlib
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

from PIL import Image
from tqdm.auto import tqdm

from logging_config import get_logger

logger = get_logger(__name__)

# Image extensions supported
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}

__all__ = [
    'ImageHasher',
    'DuplicationManager', 
    'ImageValidator',
    'IntegrityProcessor',
    'validate_dataset',
    'remove_duplicates',
    'process_integrity'
]


def valid_image_ext(file_path) -> bool:
    """Check if a file has a valid image extension."""
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path.suffix.lower() in IMAGE_EXTENSIONS


class ImageHasher:
    """
    A class responsible for computing and managing image hashes for duplicate detection.

    This class provides functionality to compute both content hashes (for exact duplicates)
    and perceptual hashes (for visually similar images).
    """

    def __init__(self, hash_size: int = 8):
        """
        Initialize the ImageHasher with a specified hash size.

        Args:
            hash_size (int): The size of the perceptual hash. Larger sizes provide more sensitivity.
        """
        self.hash_size = hash_size

    def compute_perceptual_hash(self, image_path: str) -> Optional[str]:
        """
        Computes a perceptual hash for an image to find visually similar images.

        Args:
            image_path (str): The path to the image file.

        Returns:
            Optional[str]: The hexadecimal string representation of the perceptual hash,
                          or None if the image cannot be processed.
        """
        try:
            with Image.open(image_path) as img:
                processed_image = self._prepare_image_for_hashing(img)
                pixels = list(processed_image.getdata())
                avg_pixel_value = self._calculate_average_pixel_value(pixels)
                binary_hash = self._create_binary_hash(pixels, avg_pixel_value)
                return self._convert_to_hex_hash(binary_hash)
        except Exception as e:
            logger.warning(f"Failed to compute perceptual hash for {image_path}: {e}")
            return None

    def compute_content_hash(self, file_path: str) -> Optional[str]:
        """
        Computes the MD5 hash of a file's contents for exact duplicate detection.

        Args:
            file_path (str): The path to the file.

        Returns:
            Optional[str]: The hexadecimal string representation of the MD5 hash,
                          or None if the file cannot be read.
        """
        try:
            file_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                self._update_hash_with_file_chunks(f, file_hash)
            return file_hash.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to compute content hash for {file_path}: {e}")
            return None

    def build_hashmp(self, image_files: List[str]) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
        """
        Builds content hash and perceptual hash maps for a list of image files.

        Args:
            image_files (List[str]): A list of absolute paths to image files.

        Returns:
            Tuple[Dict[str, List[str]], Dict[str, List[str]]]: A tuple containing:
                - Content hash map: maps content hashes to file paths with that hash
                - Perceptual hash map: maps perceptual hashes to file paths with that hash
        """
        content_hash_map: Dict[str, List[str]] = {}
        perceptual_hash_map: Dict[str, List[str]] = {}

        for img_path in image_files:
            self._process_image_for_maps(img_path, content_hash_map, perceptual_hash_map)

        return content_hash_map, perceptual_hash_map

    def _prepare_image_for_hashing(self, img: Image.Image) -> Image:
        """
        Prepares an image for perceptual hashing by converting to grayscale and resizing.

        Args:
            img (Image.Image): The input image.

        Returns:
            Image.Image: The processed image ready for hashing.
        """
        return img.convert("L").resize((self.hash_size, self.hash_size), Image.Resampling.LANCZOS)

    @staticmethod
    def _calculate_average_pixel_value(pixels: List[int]) -> float:
        """Calculates the average pixel value from a list of pixel values."""
        return sum(pixels) / len(pixels)

    @staticmethod
    def _create_binary_hash(pixels: List[int], avg_pixel_value: float) -> str:
        """
        Creates a binary hash string by comparing each pixel to the average.

        Args:
            pixels (List[int]): List of pixel values.
            avg_pixel_value (float): The average pixel value.

        Returns:
            str: Binary hash string.
        """
        return ''.join('1' if px >= avg_pixel_value else '0' for px in pixels)

    def _convert_to_hex_hash(self, binary_hash: str) -> str:
        """
        Converts a binary hash string to a hexadecimal representation.

        Args:
            binary_hash (str): The binary hash string.

        Returns:
            str: The hexadecimal hash string, zero-padded to the expected length.
        """
        hex_hash = hex(int(binary_hash, 2))[2:]
        return hex_hash.zfill(self.hash_size ** 2 // 4)

    @staticmethod
    def _update_hash_with_file_chunks(file_handle, file_hash) -> None:
        """
        Updates the hash object with file contents read in chunks.

        Args:
            file_handle: The file handle to read from.
            file_hash: The hash object to update.
        """
        for chunk in iter(lambda: file_handle.read(4096), b""):
            file_hash.update(chunk)

    def _process_image_for_maps(self, img_path: str, content_hash_map: Dict[str, List[str]],
                                perceptual_hash_map: Dict[str, List[str]]) -> None:
        """
        Processes a single image file and updates both hash maps.

        Args:
            img_path (str): Path to the image file.
            content_hash_map (Dict[str, List[str]]): Content hash map to update.
            perceptual_hash_map (Dict[str, List[str]]): Perceptual hash map to update.
        """
        # Get content hash (exact match)
        content_hash = self.compute_content_hash(img_path)
        if content_hash:
            content_hash_map.setdefault(content_hash, []).append(img_path)

        # Get perceptual hash (similar images)
        perceptual_hash = self.compute_perceptual_hash(img_path)
        if perceptual_hash:
            perceptual_hash_map.setdefault(perceptual_hash, []).append(img_path)


class DuplicationManager:
    """
    A class responsible for detecting and managing duplicate images in a directory.

    This class provides functionality to identify both exact duplicates (using content hashes)
    and visually similar images (using perceptual hashes), and to remove duplicates while
    keeping original copies.
    """

    def __init__(self, hasher: Optional['ImageHasher'] = None):
        """
        Initialize the DuplicationManager with an ImageHasher instance.

        Args:
            hasher (ImageHasher): An instance of ImageHasher for computing hashes.
        """
        self.hasher = hasher or ImageHasher()

    def detect_duplicates(self, directory: str) -> Dict[str, List[str]]:
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
        image_files = self._get_image_files(directory_path)

        # Build hash maps
        content_hash_map, perceptual_hash_map = self.hasher.build_hashmp(image_files)

        # Find exact duplicates first
        duplicates = self._find_exact_duplicates(content_hash_map)

        # Then process perceptual duplicates
        duplicates = self._process_perceptual_duplicates(perceptual_hash_map, duplicates)

        return duplicates

    def remove_duplicates(self, directory: str) -> Tuple[int, List[str]]:
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
        duplicates = self.detect_duplicates(directory)

        # Flatten the dictionary to get all duplicates to remove
        removed_count = 0
        removed_files = []
        originals_kept = []

        for original, dups in duplicates.items():
            # Keep track of originals we're keeping
            originals_kept.append(original)

            # Remove duplicates
            for dup in dups:
                if self.remove_duplicate(dup, original):
                    removed_count += 1
                    removed_files.append(dup)

        logger.info(f"Removed {removed_count} duplicate images from {directory}")
        return removed_count, originals_kept

    @staticmethod
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
            if f.is_file() and valid_image_ext(f)
        ]

    @staticmethod
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

    @staticmethod
    def is_duplicate(img: str, duplicates: Dict[str, List[str]]) -> bool:
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

    def _process_perceptual_duplicates(
            self,
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
                self._find_unmarked_duplicate(file_list, duplicates, kept_file)
        return duplicates

    def _find_unmarked_duplicate(self, file_list, duplicates, kept_file):
        for img in file_list:
            if not self.is_duplicate(img, duplicates):
                if kept_file is None:
                    kept_file = img
                else:
                    # Add to duplicates of kept_file
                    if kept_file in duplicates:
                        duplicates[kept_file].append(img)
                    else:
                        duplicates[kept_file] = [img]

    @staticmethod
    def remove_duplicate(duplicate_path: str, original_path: str) -> bool:
        """
        Removes a single duplicate file and handles any errors that occur.

        Args:
            duplicate_path (str): Path to the duplicate file to remove.
            original_path (str): Path to the original file (for logging purposes).

        Returns:
            bool: True if the file was successfully removed, False otherwise.
        """
        try:
            os.remove(duplicate_path)
            logger.info(f"Removed duplicate image: {duplicate_path} (duplicate of {original_path})")
            return True
        except (OSError, IOError, PermissionError) as ose:
            logger.warning(f"Failed to remove duplicate {duplicate_path}: {ose}")
            return False
        except Exception as e:
            logger.warning(f"An unexpected error occurred while removing duplicate {duplicate_path}: {e}")
            return False


class ImageValidator:
    """
    A class responsible for validating image files and counting valid/invalid images.

    This class provides functionality to validate image integrity, count valid images
    in directories, and handle corrupted image files.
    """

    def __init__(self, min_width: int = 50, min_height: int = 50):
        """
        Initialize the ImageValidator with minimum image dimensions.

        Args:
            min_width (int): Minimum width for valid images.
            min_height (int): Minimum height for valid images.
        """
        self.min_width = min_width
        self.min_height = min_height

    def validate(self, image_path: str) -> bool:
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
                if not self._is_image_size_valid(img, image_path):
                    return False

            return True
        except (Image.UnidentifiedImageError, IOError) as e:
            logger.error(f"Corrupted image detected: {image_path} - {str(e)}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during image validation: {image_path} - {str(e)}")
            return False

    def count_valid(self, directory: str) -> Tuple[int, int, List[str]]:
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
            if file_path.is_file() and valid_image_ext(file_path):
                total_count += 1
                if self.validate(str(file_path)):
                    valid_count += 1
                else:
                    corrupted_files.append(str(file_path))

        return valid_count, total_count, corrupted_files

    def count_valid_in_latest_batch(self, directory: str, previous_count: int) -> int:
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
        image_files = self._get_image_files(directory_path)

        # Sort by creation time to get the latest batch
        image_files = self._sort_by_ctime(image_files)

        # Take only files that were likely created in this batch
        latest_batch = image_files[previous_count:]

        for file_path in latest_batch:
            if self.validate(str(file_path)):
                valid_count += 1
            else:
                # Remove corrupted image
                self._remove_corrupted_image(file_path)

        return valid_count

    def _is_image_size_valid(self, img: Image.Image, image_path: str) -> bool:
        """
        Check if image dimensions meet minimum requirements.

        Args:
            img (Image.Image): The image to check.
            image_path (str): Path to the image file (for logging).

        Returns:
            bool: True if image size is valid, False otherwise.
        """
        if img.width < self.min_width or img.height < self.min_height:
            logger.warning(f"Image too small: {image_path} ({img.width}x{img.height})")
            return False
        return True

    @staticmethod
    def _get_image_files(directory_path: Path) -> List[Path]:
        """
        Get all image files from a directory.

        Args:
            directory_path (Path): The directory to scan.

        Returns:
            List[Path]: List of image file paths.
        """
        return [
            f for f in directory_path.iterdir()
            if f.is_file() and valid_image_ext(f)
        ]

    @staticmethod
    def _sort_by_ctime(image_files: List[Path]) -> List[Path]:
        """
        Sort image files by creation time.

        Args:
            image_files (List[Path]): List of image file paths.

        Returns:
            List[Path]: Sorted list of image file paths.
        """
        return sorted(image_files, key=lambda x: os.path.getctime(x))

    @staticmethod
    def _remove_corrupted_image(file_path: Path) -> None:
        """
        Remove a corrupted image file and handle any errors.

        Args:
            file_path (Path): Path to the corrupted image file.
        """
        try:
            os.remove(file_path)
            logger.warning(f"Removed corrupted image: {file_path}")
        except OSError as ose:
            logger.warning(f"Error removing corrupted image {file_path}: {ose}")
        except Exception as e:
            logger.warning(f"An unexpected error occurred while removing corrupted image {file_path}: {e}")


class IntegrityProcessor:
    """
    Main processor for integrity workflows combining validation and duplicate detection.
    """

    def __init__(self):
        """Initialize the integrity processor with validator and duplication manager."""
        self.validator = ImageValidator()
        self.duplication_manager = DuplicationManager()

    def process_dataset(self, directory: str, remove_duplicates: bool = True, 
                       remove_corrupted: bool = True) -> Dict[str, Any]:
        """
        Process a dataset for integrity issues.

        Args:
            directory: Directory containing the dataset
            remove_duplicates: Whether to remove duplicate images
            remove_corrupted: Whether to remove corrupted images

        Returns:
            Dict containing processing results
        """
        logger.info(f"Starting integrity processing for {directory}")
        
        results = {
            'directory': directory,
            'validation': {},
            'duplicates': {},
            'processed_at': time.time()
        }

        # Validate images
        valid_count, total_count, corrupted_files = self.validator.count_valid(directory)
        results['validation'] = {
            'valid_count': valid_count,
            'total_count': total_count,
            'corrupted_count': len(corrupted_files),
            'corrupted_files': corrupted_files
        }

        # Remove corrupted images if requested
        if remove_corrupted and corrupted_files:
            for corrupted_file in corrupted_files:
                try:
                    os.remove(corrupted_file)
                    logger.info(f"Removed corrupted image: {corrupted_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove corrupted image {corrupted_file}: {e}")

        # Handle duplicates
        if remove_duplicates:
            removed_count, originals_kept = self.duplication_manager.remove_duplicates(directory)
            results['duplicates'] = {
                'removed_count': removed_count,
                'originals_kept_count': len(originals_kept),
                'originals_kept': originals_kept
            }
        else:
            duplicates = self.duplication_manager.detect_duplicates(directory)
            results['duplicates'] = {
                'detected_count': sum(len(dups) for dups in duplicates.values()),
                'duplicate_groups': len(duplicates),
                'duplicates': duplicates
            }

        logger.info(f"Integrity processing completed for {directory}")
        return results


# Convenience functions
def validate_dataset(directory: str) -> Tuple[int, int, List[str]]:
    """
    Validate all images in a dataset directory.

    Args:
        directory: Directory path to validate

    Returns:
        Tuple of (valid_count, total_count, corrupted_files)
    """
    validator = ImageValidator()
    return validator.count_valid(directory)


def remove_duplicates(directory: str) -> Tuple[int, List[str]]:
    """
    Remove duplicate images from a directory.

    Args:
        directory: Directory path to process

    Returns:
        Tuple of (removed_count, originals_kept)
    """
    manager = DuplicationManager()
    return manager.remove_duplicates(directory)


def process_integrity(directory: str, remove_duplicates: bool = True, 
                     remove_corrupted: bool = True) -> Dict[str, Any]:
    """
    Process a dataset for all integrity issues.

    Args:
        directory: Directory containing the dataset
        remove_duplicates: Whether to remove duplicate images
        remove_corrupted: Whether to remove corrupted images

    Returns:
        Dict containing processing results
    """
    processor = IntegrityProcessor()
    return processor.process_dataset(directory, remove_duplicates, remove_corrupted)
