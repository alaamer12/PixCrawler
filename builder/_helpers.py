"""
This module provides helper classes and utilities for the PixCrawler dataset generator. It includes functionalities for tracking dataset generation progress, generating comprehensive reports, handling file system operations like sequential renaming of images, and managing interactive progress bars for a better user experience.

Classes:
    DatasetTracker: Tracks the progress and various outcomes of the dataset generation process.
    FSRenamer: Renames image files sequentially within a specified directory.
    ProgressManager: Manages centralized progress bars for the dataset generation process.

Functions:
    is_valid_image_extension: Checks if a file has a valid image extension.

Features:
    - Comprehensive tracking of download successes and failures.
    - Robust file system operations for renaming and organizing image files.
    - Interactive progress bars for real-time feedback during long-running operations.

Note: Image integrity checking and duplicate detection have been moved to the validator package.
Note: Report generation has been moved to the src package.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Any, Union, Callable

from tqdm.auto import tqdm

from builder._constants import logger, IMAGE_EXTENSIONS
from builder._exceptions import PixCrawlerError

__all__ = [
    'DatasetTracker',
    'FSRenamer',
    'ProgressManager',
    'valid_image_ext'
]


def valid_image_ext(file_path: Union[str, Path]) -> bool:
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


class DatasetTracker:
    """
    A class to track the progress and various outcomes of the dataset generation process.
    It records successful and failed downloads. Integrity checking has been moved to the validator package.
    """

    def __init__(self):
        """
        Initializes the DatasetTracker with counters for download successes and failures,
        and lists to store details of failed downloads.
        """
        self.download_successes: int = 0
        self.download_failures: int = 0
        self.failed_downloads: List[str] = []

    def record_download_success(self, context: str) -> None:
        """
        Records a successful image download.

        Args:
            context (str): A string describing the context of the successful download (e.g., keyword).
        """
        self.download_successes += 1

    def record_download_failure(self, context: str, error: str) -> None:
        """
        Records a failed image download.

        Args:
            context (str): A string describing the context of the failed download.
            error (str): The error message associated with the failure.
        """
        self.download_failures += 1
        self.failed_downloads.append(f"{context}: {error}")

    def print_summary(self) -> None:
        """
        Prints a comprehensive summary of the dataset generation process,
        including download statistics. Integrity checking has been moved to the validator package.
        """
        self._print_header()

        # Download statistics
        self.print_statistics()

        if self.failed_downloads:
            logger.info(f"\n  📋 Download Failures:")
            self._print_failed_downloads()

        # Overall success rate
        total_operations = self.download_successes + self.download_failures
        if total_operations > 0:
            success_rate = (self.download_successes / total_operations) * 100
            logger.info(f"\n📊 OVERALL SUCCESS RATE: {success_rate:.1f}%")

        logger.info("=" * 60)

    @staticmethod
    def _print_header() -> None:
        logger.info("\n" + "=" * 60)
        logger.info("DATASET GENERATION SUMMARY")
        logger.info("=" * 60)

    def print_statistics(self) -> None:
        logger.info(f"\n📥 IMAGE DOWNLOAD STATISTICS:")
        logger.info(f"  ✅ Successful downloads: {self.download_successes}")
        logger.info(f"  ❌ Failed downloads: {self.download_failures}")

    def _print_failed_downloads(self) -> None:
        for failure in self.failed_downloads:
            logger.info(f"    • {failure}")


class FSRenamer:
    """
    A self-encapsulated class for renaming image files sequentially within a specified directory.
    It handles the complete process of renaming image files to a sequential, zero-padded format_
    while maintaining data integrity through temporary directory operations.
    """

    def __init__(self, directory: str, padding_width: Optional[int] = None):
        """
        Initializes the FSRenamer with the target directory.

        Args:
            directory (str): The path to the directory containing images to rename.
            padding_width (Optional[int]): The desired width for zero-padding sequential filenames.
                                          If None, it will be calculated based on the number of files (min 3).
        """
        self.directory_path = Path(directory)
        self.temp_dir: Optional[Path] = None
        self.image_files: List[Path] = []
        self._user_defined_padding_width = padding_width
        self.padding_width: int = 0

    def rename_sequentially(self) -> int:
        """
        Renames all image files in the initialized directory to a sequential, zero-padded format_.
        This process involves copying files to a temporary directory with new names, deleting
        original files, moving the renamed files back, and cleaning up the temporary directory.

        Returns:
            int: The number of files successfully renamed.
        """
        if not self._validate_directory_exists():
            return 0

        self.image_files = self._get_sorted_image_files()

        if not self.image_files:
            logger.warning(f"No image files found in {self.directory_path}")
            return 0

        self.temp_dir = self._create_temp_directory()
        self.padding_width = self._user_defined_padding_width if self._user_defined_padding_width is not None else self._calculate_padding_width(
            len(self.image_files))

        renamed_count = self._copy_files_to_temp_with_new_names()

        self._delete_original_files()
        self._move_files_from_temp_to_original()
        self._cleanup_temp_directory()

        logger.info(
            f"Renamed {renamed_count} images in {self.directory_path} with sequential numbering")
        return renamed_count

    def _validate_directory_exists(self) -> bool:
        """
        Validates that the target directory for renaming exists.

        Returns:
            bool: True if the directory exists, False otherwise.
        """
        if not self.directory_path.exists():
            logger.warning(f"Directory {self.directory_path} does not exist")
            return False
        return True

    def _get_sorted_image_files(self) -> List[Path]:
        """
        Retrieves a sorted list of image files within the target directory.
        Files are sorted by their creation time.

        Returns:
            List[Path]: A list of Path objects representing the image files.
        """
        image_files = [
            f for f in self.directory_path.iterdir()
            if f.is_file() and valid_image_ext(f)
        ]
        # Sort by filename to maintain any existing sequential order
        image_files.sort(key=lambda x: x.name)
        return image_files

    def _create_temp_directory(self) -> Path:
        """
        Creates a temporary directory within the target directory for renaming operations.

        Returns:
            Path: The path to the created temporary directory.
        """
        temp_dir = self.directory_path / ".temp_rename"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir

    @staticmethod
    def _calculate_padding_width(file_count: int) -> int:
        """
        Calculates the necessary padding width for sequential numbering based on the total file count.

        Args:
            file_count (int): The total number of files to be renamed.

        Returns:
            int: The calculated padding width (e.g., 3 for up to 999 files, 4 for up to 9999 files).
        """
        return max(3, len(str(file_count)))

    def _copy_files_to_temp_with_new_names(self) -> int:
        """
        Copies image files from the original directory to the temporary directory with new sequential names.

        Returns:
            int: The number of files successfully copied and renamed.
        """
        renamed_count = 0

        for i, file_path in enumerate(self.image_files, 1):
            extension = file_path.suffix.lower()
            new_filename = f"{i:0{self.padding_width}d}{extension}"
            temp_path = self.temp_dir / new_filename

            try:
                shutil.copy2(file_path, temp_path)
                renamed_count += 1
                # Log progress every 10 files
                if renamed_count % 10 == 0 or renamed_count == len(self.image_files):
                    logger.debug(
                        f"Renamed {renamed_count}/{len(self.image_files)} images")
            except IOError as ioe:
                logger.error(f"Failed to copy {file_path} to temp directory: {ioe}")
                raise PixCrawlerError(
                    f"Failed to copy {file_path} to temp directory: {ioe}") from ioe
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred while copying {file_path} to temp directory: {e}")
                raise PixCrawlerError(
                    f"Unexpected error copying {file_path} to temp directory: {e}") from e

        return renamed_count

    def _delete_original_files(self) -> None:
        """
        Deletes the original image files from the target directory after they have been copied and renamed.
        """
        for file_path in self.image_files:
            try:
                os.remove(file_path)
            except OSError as ose:
                logger.error(f"Failed to delete original file {file_path}: {ose}")
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred while deleting original file {file_path}: {e}")

    def _move_files_from_temp_to_original(self) -> None:
        """
        Moves the sequentially renamed files from the temporary directory back to the original directory.
        """
        if not self.temp_dir:
            return

        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                try:
                    shutil.move(str(file_path),
                                str(self.directory_path / file_path.name))
                except IOError as ioe:
                    logger.error(
                        f"Failed to move {file_path} from temp directory: {ioe}")
                except Exception as e:
                    logger.error(
                        f"An unexpected error occurred while moving {file_path} from temp directory: {e}")

    def _cleanup_temp_directory(self) -> None:
        """
        Removes the temporary directory created during the renaming process.
        """
        if not self.temp_dir:
            return

        try:
            shutil.rmtree(self.temp_dir)
        except OSError as ose:
            logger.error(f"Failed to remove temp directory: {ose}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while removing temp directory: {e}")


class ProgressManager:
    """
    Centralized progress bar manager for the dataset generation process.
    This class provides a consistent interface for displaying progress bars
    across different steps of the dataset generation pipeline, ensuring clear
    visibility of the current stage while removing terminal logging.
    """

    def __init__(self):
        """
        Initializes the ProgressManager, setting up tqdm for progress bars
        or a dummy fallback if tqdm is not available. Defines main steps and their colors.
        """
        try:
            # Import here to handle potential import errors gracefully
            self.tqdm = tqdm
        except ImportError:
            # Fallback to a simple progress indicator if tqdm is not available
            self.tqdm = self._dummy_tqdm
            logger.warning("tqdm not available, using simple progress indicators")

        self.current_progress = None
        self.nested_progress = None

        # Step definitions with descriptions
        self.steps = {
            "init": "Initializing PixCrawler",
            "download": "Downloading Images",
            "integrity": "Checking integrity",
            "labels": "Generating labels",
            "report": "Generating report",
            "finalizing": "Finalizing"
        }

        # Step colors (if terminal supports it)
        self.colors = {
            "init": "blue",
            "download": "green",
            "integrity": "yellow",
            "labels": "magenta",
            "report": "cyan",
            "finalizing": "white"
        }

    def start_step(self, step: str, total: Optional[int] = None) -> None:
        """
        Starts a new main progress step with a description and an optional total count.

        Args:
            step (str): The identifier for the current step (e.g., 'download', 'integrity').
            total (Optional[int]): The total number of units for this step. If None, defaults to 1.
        """
        if step not in self.steps:
            logger.warning(f"Unknown progress step: {step}")
            desc = f"Processing {step}"
        else:
            desc = f"[{step.upper()}] {self.steps[step]}"

        # Close any existing progress bars
        self.close()

        # Ensure we have a valid total (use 1 as default if None is provided)
        # This prevents the TypeError when checking if self.current_progress evaluates to True
        if total is None:
            total = 1

        # Create new progress bar
        self.current_progress = self.tqdm(
            total=total,
            desc=desc,
            colour=self.colors.get(step, "white"),
            leave=True,
            position=0,
            dynamic_ncols=True
        )

    def update_step(self, n: int = 1) -> None:
        """
        Updates the current main progress step by incrementing its progress.

        Args:
            n (int): The number of units to increment the progress by (default is 1).
        """
        if self.current_progress is not None and hasattr(self.current_progress,
                                                         'update'):
            self.current_progress.update(n)

    def set_step_description(self, desc: str) -> None:
        """
        Updates the description of the current main progress step.

        Args:
            desc (str): The new description text for the step.
        """
        if self.current_progress is not None and hasattr(self.current_progress,
                                                         'set_description_str'):
            self.current_progress.set_description_str(desc)

    def set_step_postfix(self, **kwargs: Any) -> None:
        """
        Updates the postfix text of the current main progress step.

        Args:
            **kwargs (Any): Arbitrary keyword arguments to display as postfix (e.g., count=10, total=100).
        """
        if self.current_progress is not None and hasattr(self.current_progress,
                                                         'set_postfix'):
            self.current_progress.set_postfix(**kwargs)

    def start_subtask(self, desc: str, total: Optional[int] = None) -> None:
        """
        Starts a nested progress bar for subtasks, displayed below the main progress bar.

        Args:
            desc (str): The description of the subtask.
            total (Optional[int]): The total number of units for this subtask. If None, defaults to 1.
        """
        # Close any existing nested progress bar
        if self.nested_progress:
            self.nested_progress.close()

        # Ensure we have a valid total (use 1 as default if None is provided)
        if total is None:
            total = 1

        # Create new nested progress bar
        self.nested_progress = self.tqdm(
            total=total,
            desc=f"  └─ {desc}",
            leave=False,
            position=1,
            dynamic_ncols=True
        )

    def update_subtask(self, n: int = 1) -> None:
        """
        Updates the current subtask progress by incrementing its progress.

        Args:
            n (int): The number of units to increment the progress by (default is 1).
        """
        if self.nested_progress is not None and hasattr(self.nested_progress, 'update'):
            self.nested_progress.update(n)

    def set_subtask_description(self, desc: str) -> None:
        """
        Updates the description of the current subtask.

        Args:
            desc (str): The new description text for the subtask.
        """
        if self.nested_progress is not None and hasattr(self.nested_progress,
                                                        'set_description_str'):
            self.nested_progress.set_description_str(f"  └─ {desc}")

    def set_subtask_postfix(self, **kwargs: Any) -> None:
        """
        Updates the postfix text of the current subtask.

        Args:
            **kwargs (Any): Arbitrary keyword arguments to display as postfix.
        """
        if self.nested_progress is not None and hasattr(self.nested_progress,
                                                        'set_postfix'):
            self.nested_progress.set_postfix(**kwargs)

    def close_subtask(self) -> None:
        """
        Closes the current subtask progress bar.
        """
        if self.nested_progress is not None and hasattr(self.nested_progress, 'close'):
            self.nested_progress.close()
            self.nested_progress = None

    def close(self) -> None:
        """
        Closes all active progress bars (both main and nested).
        """
        self.close_subtask()
        if self.current_progress is not None and hasattr(self.current_progress,
                                                         'close'):
            self.current_progress.close()
            self.current_progress = None

    def _dummy_tqdm(self, *args: Any, **kwargs: Any) -> Any:
        """
        A dummy tqdm implementation used as a fallback when the `tqdm` library is not available.
        It provides basic progress indication to the console.

        Args:
            *args (Any): Positional arguments passed to tqdm.
            **kwargs (Any): Keyword arguments passed to tqdm.

        Returns:
            Any: An instance of DummyTqdm that mimics tqdm's behavior.
        """

        class DummyTqdm:
            """
            A simple dummy class that mimics the behavior of tqdm for basic progress indication.
            Used when the `tqdm` library is not installed.
            """

            def __init__(self):
                """
                Initializes the DummyTqdm instance.
                """
                self.n = 0
                self.total = kwargs.get('total', 100)  # Default total

            def update(self, n: int = 1) -> None:
                """
                Updates the progress by incrementing the counter.

                Args:
                    n (int): The number of units to increment by (default is 1).
                """
                self.n += n
                print(f"{kwargs.get('desc', 'Progress')}: {self.n}/{self.total}",
                      end="")

            @staticmethod
            def set_description_str(desc: str) -> None:
                """
                Sets the description string for the progress indicator.

                Args:
                    desc (str): The description text.
                """
                print(f"{desc}", end="")

            def set_postfix(self, **kwargs: Any) -> None:
                """
                Sets the postfix text for the progress indicator.

                Args:
                    **kwargs (Any): Arbitrary keyword arguments to display as postfix.
                """
                postfix = ' '.join(f"{k}={v}" for k, v in kwargs.items())
                print(
                    f"{kwargs.get('desc', 'Progress')}: {self.n}/{self.total} {postfix}",
                    end="")

            @staticmethod
            def close() -> None:
                """
                Closes the progress indicator, printing a newline.
                """
                print()

            def __bool__(self) -> bool:
                """
                Returns True to ensure the DummyTqdm instance is treated as truthy.
                """
                # Always return True to avoid TypeError in bool() check
                return True

        return DummyTqdm()

    def iterate(self, iterable: Any, desc: Optional[str] = None,
                total: Optional[int] = None,
                subtask: bool = False, unit: str = "it") -> Any:
        """
        Iterates over an iterable while displaying a progress bar.

        Args:
            iterable (Any): The iterable object to iterate over.
            desc (Optional[str]): A description for the progress bar.
            total (Optional[int]): The total number of items in the iterable. If None, it's inferred.
            subtask (bool): If True, uses a nested progress bar for a subtask.
            unit (str): The unit label for the progress bar (e.g., "it", "files").

        Returns:
            Any: An iterator that yields items from the iterable while updating the progress bar.
        """
        progress_method: Union[Callable[
            [int], None], bool] = self.update_subtask if subtask else self.update_step
        tqdm_instance = self.nested_progress if subtask else self.current_progress

        # If we have an active progress bar, use it
        if tqdm_instance:
            if desc:
                if subtask:
                    self.set_subtask_description(desc)
                else:
                    self.set_step_description(desc)

            # Yield from the iterable and update progress
            for item in iterable:
                yield item
                progress_method(1)
        else:
            # Create a new progress bar for this iteration
            with self.tqdm(iterable, desc=desc, total=total, unit=unit) as pbar:
                for item in pbar:
                    yield item


# Create a global progress manager
progress = ProgressManager()


def rename_images_sequentially(directory: str, padding_width: Optional[int] = 4) -> int:
    """
    Rename all image files in a directory to a sequential, zero-padded format_.

    Args:
        directory: Directory containing images to rename
        padding_width: The desired width for zero-padding sequential filenames. Defaults to 4.

    Returns:
        int: Number of renamed files
    """
    renamer = FSRenamer(directory, padding_width)
    return renamer.rename_sequentially()
