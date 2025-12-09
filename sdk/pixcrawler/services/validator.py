"""
Validator Service Wrapper

This module wraps the validator package to provide an async interface.
"""
from pathlib import Path
from typing import Tuple

from validator.validation import CheckManager, CheckStats, DuplicateResult, IntegrityResult
from validator.config import ValidatorConfig, CheckMode, DuplicateAction

from .._internal.concurrency import run_in_thread
from ..config import get_config
from ..utils import get_logger

logger = get_logger(__name__)

class ValidationEngine:
    """
    Async wrapper around the PixCrawler Validator engine.
    """
    def __init__(self):
        self.config = get_config()

    async def validate_directory(
        self, 
        directory: Path, 
        strict: bool = False,
        remove_duplicates: bool = True
    ) -> Tuple[DuplicateResult, IntegrityResult]:
        """
        Validate a directory of images asynchronously.
        """
        logger.info(f"Starting validation for {directory}")

        mode = CheckMode.STRICT if strict else CheckMode.LENIENT
        action = DuplicateAction.REMOVE if remove_duplicates else DuplicateAction.REPORT_ONLY

        # Run blocking validation in thread
        return await run_in_thread(
            self._run_validation_sync,
            directory,
            mode,
            action
        )

    def _run_validation_sync(
        self, 
        directory: Path, 
        mode: CheckMode, 
        action: DuplicateAction
    ) -> Tuple[DuplicateResult, IntegrityResult]:
        """
        Internal synchronous validation logic.
        """
        v_config = ValidatorConfig(
            mode=mode,
            duplicate_action=action,
            min_image_width=self.config.MIN_IMAGE_WIDTH,
            min_image_height=self.config.MIN_IMAGE_HEIGHT,
            min_file_size_bytes=self.config.MIN_IMAGE_SIZE_BYTES
        )
        
        manager = CheckManager(v_config)
        return manager.check_all(str(directory))
