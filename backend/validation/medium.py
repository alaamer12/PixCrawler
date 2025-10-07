"""Medium validation strategy implementation.

Performs FAST validation plus placeholder content/quality checks.
"""

import time
from pathlib import Path
from PIL import Image
from .base import ImageValidationStrategy, ValidationResult, ValidationLevel


class MediumValidation(ImageValidationStrategy):
    """Medium validation strategy.
    
    Extends fast validation with additional quality checks.
    Currently includes a placeholder for content/quality metrics.
    """
    
    def validate(self, image_path: str) -> ValidationResult:
        """Perform medium validation on an image.
        
        Args:
            image_path: Path to the image file.
            
        Returns:
            ValidationResult with image metadata and quality indicators.
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
                validation_level=ValidationLevel.MEDIUM
            )
        
        try:
            with Image.open(image_path) as img:
                metadata["format"] = img.format
                metadata["size"] = img.size
                
                # Placeholder content/quality metric stub
                metadata["quality_checked"] = True
        except Exception as e:
            issues_found.append(f"Failed to open image: {str(e)}")
        
        processing_time = time.perf_counter() - start_time
        return ValidationResult(
            is_valid=len(issues_found) == 0,
            issues_found=issues_found,
            metadata=metadata,
            processing_time=processing_time,
            validation_level=ValidationLevel.MEDIUM
        )
