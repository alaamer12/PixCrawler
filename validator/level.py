"""



ARCHIVED, NOT Now when to use it



"""
import time
from enum import Enum, auto
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
    PositiveFloat,
    NonNegativeInt,
    FilePath
)
from PIL import Image

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# Image extensions supported
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}


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

    Enhanced with Pydantic V2 features for comprehensive validation and metadata handling.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
        frozen=False,
        use_enum_values=False
    )

    is_valid: bool = Field(
        description="Whether the image passed validation",
        examples=[True, False]
    )

    issues_found: List[str] = Field(
        default_factory=list,
        description="List of validation issues encountered",
        examples=[["File not found", "Invalid format"], []],
        max_length=100
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional information collected during validation",
        examples=[{"width": 1920, "height": 1080, "format": "JPEG", "size_bytes": 245760}]
    )

    processing_time: float = Field(
        description="Time taken to perform validation in seconds",
        examples=[0.025, 1.234],
        ge=0.0,
        le=300.0  # Max 5 minutes processing time
    )

    validation_level: ValidationLevel = Field(
        description="The validation level that was applied",
        examples=[ValidationLevel.FAST]
    )

    file_path: Optional[str] = Field(
        default=None,
        description="Path to the validated file",
        examples=["/path/to/image.jpg"]
    )

    file_size_bytes: Optional[NonNegativeInt] = Field(
        default=None,
        description="File size in bytes",
        examples=[245760, 1048576],
        ge=0
    )

    @field_validator('issues_found')
    @classmethod
    def validate_issues_not_empty_strings(cls, v: List[str]) -> List[str]:
        """Ensure no empty strings in issues list."""
        return [issue.strip() for issue in v if issue.strip()]

    @model_validator(mode='after')
    def validate_consistency(self) -> 'ValidationResult':
        """Ensure result consistency."""
        if not self.is_valid and not self.issues_found:
            raise ValueError("Invalid result must have at least one issue")
        if self.is_valid and self.issues_found:
            # Log warning but allow (might be warnings, not errors)
            logger.warning(f"Valid result has issues: {self.issues_found}")
        return self


class ValidationConfig(BaseModel):
    """Configuration for validation strategies with enhanced Pydantic V2 features."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid',
        frozen=True  # Immutable config
    )

    min_width: NonNegativeInt = Field(
        default=1,
        description="Minimum image width in pixels",
        examples=[100, 50, 1],
        ge=1,
        le=10000
    )

    min_height: NonNegativeInt = Field(
        default=1,
        description="Minimum image height in pixels",
        examples=[100, 50, 1],
        ge=1,
        le=10000
    )

    max_file_size_mb: Optional[PositiveFloat] = Field(
        default=None,
        description="Maximum file size in MB (None for no limit)",
        examples=[10.0, 50.0, None],
        gt=0.0,
        le=1000.0
    )

    strict_mode: bool = Field(
        default=False,
        description="Enable strict validation mode",
        examples=[True, False]
    )

    check_transparency: bool = Field(
        default=False,
        description="Check for transparency in images",
        examples=[True, False]
    )

    @field_validator('min_width', 'min_height')
    @classmethod
    def validate_positive_dimensions(cls, v: int) -> int:
        """Ensure dimensions are positive."""
        if v <= 0:
            raise ValueError("Dimensions must be positive")
        return v

    @model_validator(mode='after')
    def validate_dimension_consistency(self) -> 'ValidationConfig':
        """Ensure dimension consistency."""
        if self.min_width > 5000 or self.min_height > 5000:
            logger.warning(f"Very large minimum dimensions: {self.min_width}x{self.min_height}")
        return self


class ImageValidationStrategy(ABC):
    """Abstract base class for image validation strategies.

    Enhanced with configuration support and comprehensive error handling.
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """Initialize strategy with optional configuration."""
        self.config = config or ValidationConfig()

    @abstractmethod
    def validate(self, image_path: str) -> ValidationResult:
        """Validate an image file.

        Args:
            image_path: Path to the image file to validate.

        Returns:
            ValidationResult containing validation outcome and metadata.
        """
        pass

    def _get_file_info(self, image_path: str) -> Tuple[bool, int, List[str]]:
        """Get basic file information."""
        issues = []
        file_size = 0

        try:
            path = Path(image_path)
            if not path.exists():
                issues.append(f"File does not exist: {image_path}")
                return False, 0, issues

            if not path.is_file():
                issues.append(f"Path is not a file: {image_path}")
                return False, 0, issues

            file_size = path.stat().st_size
            if file_size == 0:
                issues.append("File is empty")
                return False, file_size, issues

            # Check file extension
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                issues.append(f"Unsupported file extension: {path.suffix}")
                return False, file_size, issues

            # Check file size limit
            if self.config.max_file_size_mb:
                max_bytes = self.config.max_file_size_mb * 1024 * 1024
                if file_size > max_bytes:
                    issues.append(f"File too large: {file_size} bytes > {max_bytes} bytes")
                    return False, file_size, issues

        except Exception as e:
            issues.append(f"Error accessing file: {str(e)}")
            return False, 0, issues

        return True, file_size, issues


def get_validation_strategy(level: ValidationLevel, config: Optional[ValidationConfig] = None) -> ImageValidationStrategy:
    """Get a validation strategy instance for the specified level.

    Args:
        level: The validation level (FAST, MEDIUM, or SLOW).
        config: Optional configuration for the validation strategy.

    Returns:
        An instance of the appropriate validation strategy.

    Raises:
        ValueError: If the validation level is invalid.
    """
    if level == ValidationLevel.FAST:
        return FastValidation(config)
    elif level == ValidationLevel.MEDIUM:
        return MediumValidation(config)
    elif level == ValidationLevel.SLOW:
        return SlowValidation(config)
    else:
        raise ValueError(f"Invalid validation level: {level}")


class FastValidation(ImageValidationStrategy):
    """Fast validation strategy.

    Validates that the file exists and can be opened as an image.
    Extracts basic metadata (format and size) with minimal processing time.
    Uses existing validation logic from the integrity module.
    """

    def validate(self, image_path: str) -> ValidationResult:
        """Perform fast validation on an image.

        Args:
            image_path: Path to the image file.

        Returns:
            ValidationResult with basic image metadata.
        """
        start_time = time.time()
        issues = []
        metadata = {}
        is_valid = True
        file_size = 0

        try:
            # Basic file checks
            file_exists, file_size, file_issues = self._get_file_info(image_path)
            if not file_exists:
                issues.extend(file_issues)
                is_valid = False
            else:
                # Try to open and verify the image
                try:
                    with Image.open(image_path) as img:
                        # Verify image integrity
                        img.verify()

                        # Re-open for metadata extraction (verify() closes the image)
                        with Image.open(image_path) as img_meta:
                            width, height = img_meta.size
                            format_name = img_meta.format or "Unknown"
                            mode = img_meta.mode

                            # Store metadata
                            metadata.update({
                                "width": width,
                                "height": height,
                                "format": format_name,
                                "mode": mode,
                                "size_bytes": file_size,
                                "aspect_ratio": round(width / height, 2) if height > 0 else 0
                            })

                            # Check minimum dimensions
                            if width < self.config.min_width:
                                issues.append(f"Width {width} < minimum {self.config.min_width}")
                                if self.config.strict_mode:
                                    is_valid = False

                            if height < self.config.min_height:
                                issues.append(f"Height {height} < minimum {self.config.min_height}")
                                if self.config.strict_mode:
                                    is_valid = False

                            # Check for transparency if requested
                            if self.config.check_transparency:
                                has_transparency = (
                                    mode in ('RGBA', 'LA') or
                                    'transparency' in img_meta.info
                                )
                                metadata["has_transparency"] = has_transparency

                            # Additional fast checks
                            if width == 0 or height == 0:
                                issues.append("Image has zero dimensions")
                                is_valid = False

                except Image.UnidentifiedImageError as e:
                    issues.append(f"Cannot identify image format: {str(e)}")
                    is_valid = False
                except IOError as e:
                    issues.append(f"Cannot open image file: {str(e)}")
                    is_valid = False
                except Exception as e:
                    issues.append(f"Image validation error: {str(e)}")
                    is_valid = False

        except Exception as e:
            issues.append(f"Unexpected validation error: {str(e)}")
            is_valid = False

        processing_time = time.time() - start_time

        return ValidationResult(
            is_valid=is_valid,
            issues_found=issues,
            metadata=metadata,
            processing_time=processing_time,
            validation_level=ValidationLevel.FAST,
            file_path=image_path,
            file_size_bytes=file_size
        )


class MediumValidation(ImageValidationStrategy):
    """Medium validation strategy.

    Extends fast validation with additional quality checks.
    Currently includes a placeholder for content/quality metrics.

    Future enhancements will include:
    - Color histogram analysis
    - Basic quality metrics (blur detection, noise analysis)
    - Content-based validation
    """

    def validate(self, image_path: str) -> ValidationResult:
        """Perform medium validation on an image.

        Args:
            image_path: Path to the image file.

        Returns:
            ValidationResult with image metadata and quality indicators.
        """
        # For now, delegate to fast validation and add placeholder metadata
        fast_validator = FastValidation(self.config)
        result = fast_validator.validate(image_path)

        # Update validation level and add placeholder for future enhancements
        result.validation_level = ValidationLevel.MEDIUM
        result.metadata.update({
            "quality_score": None,  # Placeholder for future quality analysis
            "color_analysis": None,  # Placeholder for color histogram
            "content_features": None  # Placeholder for content analysis
        })

        # Add note about current implementation
        if result.is_valid:
            result.issues_found.append("Medium validation not fully implemented - using fast validation")

        return result


class SlowValidation(ImageValidationStrategy):
    """Slow validation strategy.

    Extends medium validation with comprehensive deep analysis.
    Currently includes placeholders for quality and deep content checks.

    Future enhancements will include:
    - Deep quality analysis (sharpness, exposure, composition)
    - Advanced duplicate detection using perceptual hashing
    - Content classification and tagging
    - Metadata extraction and validation
    """

    def validate(self, image_path: str) -> ValidationResult:
        """Perform slow validation on an image.

        Args:
            image_path: Path to the image file.

        Returns:
            ValidationResult with comprehensive metadata and analysis results.
        """
        # For now, delegate to medium validation and add placeholder metadata
        medium_validator = MediumValidation(self.config)
        result = medium_validator.validate(image_path)

        # Update validation level and add placeholder for future enhancements
        result.validation_level = ValidationLevel.SLOW
        result.metadata.update({
            "deep_quality_analysis": None,  # Placeholder for advanced quality metrics
            "perceptual_hash": None,  # Placeholder for perceptual hashing
            "content_classification": None,  # Placeholder for AI-based classification
            "exif_data": None,  # Placeholder for EXIF metadata
            "technical_analysis": None  # Placeholder for technical image analysis
        })

        # Add note about current implementation
        if result.is_valid:
            result.issues_found.append("Slow validation not fully implemented - using medium validation")

        return result
