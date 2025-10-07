"""Base classes and types for image validation strategy system.

This module defines the core abstractions for implementing multi-tier
image validation with FAST, MEDIUM, and SLOW levels.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List, Any
from pydantic import BaseModel


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
