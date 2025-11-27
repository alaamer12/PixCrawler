"""
Validator service for the Chunk Worker.

This module handles image validation using the validator package's IntegrityProcessor.
It ensures only valid images are processed and handles duplicate removal.
"""

from typing import Tuple
from validator.integrity import IntegrityProcessor, ProcessingResults
from pixcrawler.chunk_worker.src.utils.logging import ContextLogger

class ChunkValidator:
    """
    Service responsible for validating images in a chunk.
    """

    def __init__(self, logger: ContextLogger):
        """
        Initialize the ChunkValidator.

        Args:
            logger: ContextLogger instance for logging.
        """
        self.logger = logger
        self.processor = IntegrityProcessor()

    def validate_chunk(self, directory: str) -> int:
        """
        Validate images in the given directory.
        Removes corrupted images and duplicates.

        Args:
            directory: Directory containing images to validate.

        Returns:
            int: The count of valid images remaining.

        Raises:
            Exception: If no valid images remain after validation.
        """
        self.logger.info(f"Starting validation in {directory}")
        
        # Run integrity processing: remove corrupted and duplicates
        results: ProcessingResults = self.processor.process_dataset(
            directory,
            remove_duplicates=True,
            remove_corrupted=True
        )
        
        valid_count = results['validation']['valid_count']
        corrupted_count = results['validation']['corrupted_count']
        duplicates_removed = results['duplicates'].get('removed_count', 0) if 'removed_count' in results['duplicates'] else 0
        
        self.logger.info(
            f"Validation completed. Valid: {valid_count}, "
            f"Corrupted (removed): {corrupted_count}, "
            f"Duplicates (removed): {duplicates_removed}"
        )
        
        if valid_count == 0:
            msg = "Validation failed: No valid images found after processing."
            self.logger.error(msg)
            # "If no valid images exist, the task should fail without retrying"
            # We raise ValueError which is caught in the task and not retried
            raise ValueError(msg) 
            
        return valid_count
