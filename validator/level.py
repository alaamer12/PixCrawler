from enum import Enum, auto
from pydantic import BaseModel
from typing import List, Dict, Any
from abc import ABC, abstractmethod

class ValidationLevel(Enum):
    """Enumeration of available validation levels.

    Attributes:
        FAST: Quick validation checking file existence and basic image properties.
        MEDIUM: FAST checks plus content/quality metrics.
        SLOW: MEDIUM checks plus deep analysis.
    """
    FAST = auto()
    MEDIUM = auto()
    SLOW = auto()


class ValidationResult(BaseModel):
    """Result of an image validation operation.

    Attributes:
        is_valid: Whether the image passed validation.
        issues_found: List of validation issues encountered.
        metadata: Additional information collected during validation.
        processing_time: Time taken to perform validation in seconds.
        validation_level: The validation level that was applied.
    """
    is_valid: bool
    issues_found: List[str]
    metadata: Dict[str, Any]
    processing_time: float
    validation_level: ValidationLevel


class ImageValidationStrategy(ABC):
    """Abstract base class for image validation strategies.

    Implementations must define the validate method to perform
    validation at their designated level.
    """

    @abstractmethod
    def validate(self, image_path: str) -> ValidationResult:
        """Validate an image file.

        Args:
            image_path: Path to the image file to validate.

        Returns:
            ValidationResult containing validation outcome and metadata.
        """
        pass


def get_validation_strategy(level: ValidationLevel) -> ImageValidationStrategy:
    """Get a validation strategy instance for the specified level.

    Args:
        level: The validation level (FAST, MEDIUM, or SLOW).

    Returns:
        An instance of the appropriate validation strategy.

    Raises:
        ValueError: If the validation level is invalid.
    """
    if level == ValidationLevel.FAST:
        return FastValidation()
    elif level == ValidationLevel.MEDIUM:
        return MediumValidation()
    elif level == ValidationLevel.SLOW:
        return SlowValidation()
    else:
        raise ValueError(f"Invalid validation level: {level}")


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
        ...


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
        raise NotImplementedError("Only Fast Validation Currently Avialble")


class SlowValidation(ImageValidationStrategy):
    """Slow validation strategy.

    Extends medium validation with comprehensive deep analysis.
    Currently includes placeholders for quality and deep content checks.
    """

    def validate(self, image_path: str) -> ValidationResult:
        """Perform slow validation on an image.

        Args:
            image_path: Path to the image file.

        Returns:
            ValidationResult with comprehensive metadata and analysis results.
        """
        raise NotImplementedError("Only Fast Validation Currently Avialble")
