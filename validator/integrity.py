"""
Backend integrity management module for PixCrawler.

This module handles all image integrity validation, duplicate detection,
and quality assurance workflows that were previously in the builder package.

Classes:
    ImageHasher: Computes image hashes for duplicate detection
    DuplicationManager: Detects and manages duplicate images
    ImageValidator: Validates image integrity and quality
    IntegrityProcessor: Main processor for integrity workflows

TypedDict Classes:
    ValidationResults: Type definition for validation results
    DuplicateResults: Type definition for duplicate detection results
    ProcessingResults: Type definition for overall processing results

Functions:
    validate_dataset: Validates an entire dataset
    remove_duplicates: Removes duplicates from a dataset
    process_integrity: Main entry point for integrity processing
"""

import hashlib
import os
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple, TypedDict, Union

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
    'ValidationResults',
    'DuplicateResults',
    'ProcessingResults',
    'validate_dataset',
    'remove_duplicates',
    'process_integrity'
]


def valid_image_ext(file_path) -> bool:
    """Check if a file has a valid image extension."""
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return file_path.suffix.lower() in IMAGE_EXTENSIONS

# TypedDict definitions for enhanced type safety
class ValidationResults(TypedDict):
    """Type definition for validation results."""
    valid_count: int
    total_count: int
    corrupted_count: int
    corrupted_files: List[str]


class DuplicateResults(TypedDict):
    """Type definition for duplicate detection results."""
    removed_count: int
    originals_kept_count: int
    originals_kept: List[str]


class DuplicateDetectionResults(TypedDict):
    """Type definition for duplicate detection results when not removing."""
    detected_count: int
    duplicate_groups: int
    duplicates: Dict[str, List[str]]


class ProcessingResults(TypedDict):
    """Type definition for overall processing results."""
    directory: str
    validation: ValidationResults
    duplicates: Union[DuplicateResults, DuplicateDetectionResults]
    processed_at: float


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

    def build_hashmp(self, image_files: List[str]) -> Tuple[
        Dict[str, List[str]], Dict[str, List[str]]]:
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
            self._process_image_for_maps(img_path, content_hash_map,
                                         perceptual_hash_map)

        return content_hash_map, perceptual_hash_map

    def _prepare_image_for_hashing(self, img: Image.Image) -> Image:
        """
        Prepares an image for perceptual hashing by converting to grayscale and resizing.

        Args:
            img (Image.Image): The input image.

        Returns:
            Image.Image: The processed image ready for hashing.
        """
        return img.convert("L").resize((self.hash_size, self.hash_size),
                                       Image.Resampling.LANCZOS)

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

    def _process_image_for_maps(self, img_path: str,
                                content_hash_map: Dict[str, List[str]],
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
        duplicates = self._process_perceptual_duplicates(perceptual_hash_map,
                                                         duplicates)

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
    def _find_exact_duplicates(content_hash_map: Dict[str, List[str]]) -> Dict[
        str, List[str]]:
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
            logger.info(
                f"Removed duplicate image: {duplicate_path} (duplicate of {original_path})")
            return True
        except (OSError, IOError, PermissionError) as ose:
            logger.warning(f"Failed to remove duplicate {duplicate_path}: {ose}")
            return False
        except Exception as e:
            logger.warning(
                f"An unexpected error occurred while removing duplicate {duplicate_path}: {e}")
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
            logger.error(
                f"An unexpected error occurred during image validation: {image_path} - {str(e)}")
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

        for file_path in tqdm(directory_path.iterdir(), desc="Validating", leave=False,
                              unit="file"):
            if file_path.is_file() and valid_image_ext(file_path):
                total_count += 1
                if self.validate(str(file_path)):
                    valid_count += 1
                else:
                    corrupted_files.append(str(file_path))

        return valid_count, total_count, corrupted_files
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

class IntegrityProcessor:
    """
    Main processor for integrity workflows combining validation and duplicate detection.
    """

    def __init__(self):
        """Initialize the integrity processor with validator and duplication manager."""
        self.validator = ImageValidator()
        self.duplication_manager = DuplicationManager()

    def process_dataset(self, directory: str, remove_duplicates: bool = True,
                        remove_corrupted: bool = True) -> ProcessingResults:
        """
        Process a dataset for integrity issues.

        Args:
            directory: Directory containing the dataset
            remove_duplicates: Whether to remove duplicate images
            remove_corrupted: Whether to remove corrupted images

        Returns:
            ProcessingResults containing processing results
        """
        logger.info(f"Starting integrity processing for {directory}")

        # Validate images
        valid_count, total_count, corrupted_files = self.validator.count_valid(
            directory)

        validation_results: ValidationResults = {
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
                    logger.warning(
                        f"Failed to remove corrupted image {corrupted_file}: {e}")

        # Handle duplicates
        if remove_duplicates:
            removed_count, originals_kept = self.duplication_manager.remove_duplicates(
                directory)
            duplicate_results: DuplicateResults = {
                'removed_count': removed_count,
                'originals_kept_count': len(originals_kept),
                'originals_kept': originals_kept
            }
        else:
            duplicates = self.duplication_manager.detect_duplicates(directory)
            duplicate_results: DuplicateDetectionResults = {
                'detected_count': sum(len(dups) for dups in duplicates.values()),
                'duplicate_groups': len(duplicates),
                'duplicates': duplicates
            }

        results: ProcessingResults = {
            'directory': directory,
            'validation': validation_results,
            'duplicates': duplicate_results,
            'processed_at': time.time()
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


def process_integrity(directory: str, 
                      remove_duplicates: bool = True,
                      remove_corrupted: bool = True) -> ProcessingResults:
    """
    Process a dataset for all integrity issues.

    Args:
        directory: Directory containing the dataset
        remove_duplicates: Whether to remove duplicate images
        remove_corrupted: Whether to remove corrupted images

    Returns:
        ProcessingResults containing processing results
    """
    processor = IntegrityProcessor()
    return processor.process_dataset(directory, remove_duplicates, remove_corrupted)


# Integration Tests
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock


@pytest.fixture
def temp_dataset():
    """Create temporary dataset with mocked images."""
    temp_dir = tempfile.mkdtemp()
    
    # Create valid image files
    valid_files = [
        os.path.join(temp_dir, "valid1.jpg"),
        os.path.join(temp_dir, "valid2.png"),
        os.path.join(temp_dir, "valid3.gif")
    ]
    
    # Create duplicate image files
    duplicate_files = [
        os.path.join(temp_dir, "dup1.jpg"),
        os.path.join(temp_dir, "dup2.jpg")
    ]
    
    # Create corrupted image files
    corrupted_files = [
        os.path.join(temp_dir, "corrupted1.jpg"),
        os.path.join(temp_dir, "corrupted2.png")
    ]
    
    all_files = valid_files + duplicate_files + corrupted_files
    
    for file_path in all_files:
        with open(file_path, 'wb') as f:
            f.write(b'fake_image_data')
    
    yield {
        'dir': temp_dir,
        'valid': valid_files,
        'duplicates': duplicate_files,
        'corrupted': corrupted_files
    }
    
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_hash_mapping():
    """Mock the build_hashmp method to return controlled results"""
    def mock_build_hashmp(image_files):
        content_map = {}
        perceptual_map = {}
        
        for img_path in image_files:
            if 'dup' in img_path:
                content_map.setdefault('duplicate_hash', []).append(img_path)
                perceptual_map.setdefault('perceptual_duplicate', []).append(img_path)
            else:
                unique_hash = f"hash_{os.path.basename(img_path)}"
                content_map.setdefault(unique_hash, []).append(img_path)
                perceptual_map.setdefault(unique_hash, []).append(img_path)
        
        return content_map, perceptual_map
    
    with patch.object(ImageHasher, 'build_hashmp', side_effect=mock_build_hashmp):
        yield

@pytest.fixture
def mock_image_validation():
    """Mock image validation to simulate different image states."""
    def mock_validate(image_path):
        if 'corrupted' in image_path:
            return False
        return True
    
    with patch.object(ImageValidator, 'validate', side_effect=mock_validate):
        yield


@pytest.fixture
def mock_image_hashing():
    """Mock image hashing to simulate duplicate detection."""
    def mock_content_hash(image_path):
        if 'dup1.jpg' in image_path or 'dup2.jpg' in image_path:
            return 'duplicate_hash'
        return f'hash_{os.path.basename(image_path)}'
    
    def mock_perceptual_hash(image_path):
        if 'dup1.jpg' in image_path or 'dup2.jpg' in image_path:
            return 'duplicate_hash'
        return f'hash_{os.path.basename(image_path)}'
    
    with patch.object(ImageHasher, 'compute_content_hash', side_effect=mock_content_hash), \
            patch.object(ImageHasher, 'compute_perceptual_hash', side_effect=mock_perceptual_hash):
        yield


@pytest.fixture
def mock_image_opening():
    """Mock PIL Image.open to prevent actual image processing."""
    mock_img = MagicMock()
    mock_img.width = 100
    mock_img.height = 100
    mock_img.convert.return_value = mock_img
    mock_img.resize.return_value = mock_img
    mock_img.getdata.return_value = [128] * 64
    
    with patch('PIL.Image.open') as mock_open:
        mock_open.return_value.__enter__.return_value = mock_img
        yield mock_open



def test_integrity_workflow_valid_images(temp_dataset, mock_image_validation, mock_image_hashing, mock_image_opening):
    """Verify that valid images pass integrity validation without errors."""
    results = process_integrity(temp_dataset['dir'], remove_duplicates=False, remove_corrupted=False)
    
    assert results['directory'] == temp_dataset['dir']
    assert results['validation']['valid_count'] == 3
    assert results['validation']['total_count'] == 7
    assert results['validation']['corrupted_count'] == 2


def test_integrity_workflow_duplicate_detection(temp_dataset, mock_image_validation, mock_image_hashing, mock_image_opening):
    """Verify that duplicate images are correctly detected using content and perceptual hashing."""
    results = process_integrity(temp_dataset['dir'], remove_duplicates=False, remove_corrupted=False)
    
    duplicates = results['duplicates']
    assert duplicates['detected_count'] >= 1
    assert duplicates['duplicate_groups'] >= 1

def test_integrity_workflow_duplicate_removal(temp_dataset, mock_image_validation, mock_image_hashing, mock_image_opening):
    """Verify that duplicate images are successfully removed while keeping originals."""
    with patch('os.remove') as mock_remove:
        results = process_integrity(temp_dataset['dir'], remove_duplicates=True, remove_corrupted=False)
        
        duplicates = results['duplicates']
        assert duplicates['removed_count'] == 1
        assert duplicates['originals_kept_count'] == 1
        mock_remove.assert_called()


def test_integrity_workflow_corrupted_removal(temp_dataset, mock_image_validation, mock_image_hashing, mock_image_opening):
    """Verify that corrupted images are identified and removed from the dataset."""
    with patch('os.remove') as mock_remove:
        results = process_integrity(temp_dataset['dir'], remove_duplicates=False, remove_corrupted=True)
        
        assert results['validation']['corrupted_count'] == 2
        assert mock_remove.call_count == 2


def test_integrity_workflow_strict_mode(temp_dataset, mock_image_validation, mock_image_hashing, mock_image_opening):
    """Verify that strict mode removes both duplicate and corrupted images."""
    with patch('os.remove') as mock_remove:
        results = process_integrity(temp_dataset['dir'], remove_duplicates=True, remove_corrupted=True)
        
        assert results['validation']['corrupted_count'] == 2
        assert results['duplicates']['removed_count'] == 1
        assert mock_remove.call_count == 3

def test_integrity_workflow_lenient_mode(temp_dataset, mock_image_validation, mock_image_hashing, mock_image_opening):
    """Verify that lenient mode detects issues without removing any files."""
    with patch('os.remove') as mock_remove:
        results = process_integrity(temp_dataset['dir'], remove_duplicates=False, remove_corrupted=False)
        
        assert results['validation']['corrupted_count'] == 2
        assert results['duplicates']['detected_count'] == 1
        mock_remove.assert_not_called()


def test_integrity_workflow_report_only_mode(temp_dataset, mock_image_validation, mock_image_hashing, mock_image_opening):
    """Verify that report-only mode provides validation results without modifications."""
    valid_count, total_count, corrupted_files = validate_dataset(temp_dataset['dir'])
    
    assert valid_count == 3
    assert total_count == 7
    assert len(corrupted_files) == 2


def test_batch_processing_large_dataset(mock_image_validation, mock_image_hashing, mock_image_opening):
    """Verify that large datasets with 100+ images are processed efficiently."""
    temp_dir = tempfile.mkdtemp()
    
    # Create 100 mock image files
    for i in range(1000):
        file_path = os.path.join(temp_dir, f"image_{i}.jpg")
        with open(file_path, 'wb') as f:
            f.write(b'fake_image_data')
    
    try:
        results = process_integrity(temp_dir, remove_duplicates=False, remove_corrupted=False)
        
        assert results['validation']['total_count'] == 1000  
        assert results['validation']['valid_count'] == 1000
        assert results['validation']['corrupted_count'] == 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    
    try:
        results = process_integrity(temp_dir, remove_duplicates=False, remove_corrupted=False)
        
        assert results['validation']['total_count'] == 100
        assert results['validation']['valid_count'] == 100
        assert results['validation']['corrupted_count'] == 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_quarantine_functionality(temp_dataset, mock_image_validation, mock_image_hashing, mock_image_opening):
    """Verify that corrupted files are identified for quarantine processing."""
    results = process_integrity(temp_dataset['dir'], remove_duplicates=False, remove_corrupted=False)
    
    corrupted_files = results['validation']['corrupted_files']
    assert len(corrupted_files) == 2
    assert any('corrupted1.jpg' in f for f in corrupted_files)
    assert any('corrupted2.png' in f for f in corrupted_files)

