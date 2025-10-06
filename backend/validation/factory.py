"""Factory for creating validation strategy instances.

Provides a single entry point for obtaining the appropriate validation
strategy based on the desired validation level.
"""

from .base import ImageValidationStrategy, ValidationLevel
from .fast import FastValidation
from .medium import MediumValidation
from .slow import SlowValidation


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
