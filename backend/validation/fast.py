"""Fast validation strategy implementation.

Performs basic validation: file existence check and image format/size extraction.
"""

import time
from pathlib import Path
from PIL import Image
from .base import ImageValidationStrategy, ValidationResult, ValidationLevel


class FastValidation(ImageValidationStrategy):
    """Fast validation strategy.
    
    Validates that the file exists and can be opened as an image.
    Extracts basic metadata (format and size) with minimal processing time.
    """
    
    def validate(self, image_path: str) -> ValidationResult:
        """Perform fast validation on an image.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            ValidationResult with basic image metadata.
        """
        start_time = time.perf_counter()
        issues_found = []
        metadata = {}
        
        if not Path(image_path).exists():
            processing_time = time.perf_counter() - start_time
            return ValidationResult(
                is_valid=False,
                issues_found=["File does not exist"],
                metadata=metadata,
                processing_time=processing_time,
                validation_level=ValidationLevel.FAST
            )
        
        try:
            with Image.open(image_path) as img:
                metadata["format"] = img.format
                metadata["size"] = img.size
        except Exception as e:
            issues_found.append(f"Failed to open image: {str(e)}")
        
        processing_time = time.perf_counter() - start_time
        return ValidationResult(
            is_valid=len(issues_found) == 0,
            issues_found=issues_found,
            metadata=metadata,
            processing_time=processing_time,
            validation_level=ValidationLevel.FAST
        )
