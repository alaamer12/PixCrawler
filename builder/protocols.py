"""
Protocol definitions for PixCrawler builder package.

This module defines protocols (interfaces) for extensible components
in the builder package, enabling strategy pattern implementations
and dependency injection.

Protocols:
    KeywordGenerator: Interface for keyword generation strategies
    
Features:
    - Type-safe protocol definitions using typing.Protocol
    - Extensible keyword generation strategies
    - Compatible with dependency injection patterns
    - Supports multiple implementation strategies
"""

from typing import Protocol, List, Dict, Any, Optional

__all__ = [
    'KeywordGenerator',
]


class KeywordGenerator(Protocol):
    """
    Protocol for keyword generation strategies.
    
    This protocol defines the interface that all keyword generators
    must implement, enabling extensible keyword generation strategies
    such as AI-powered, synonym-based, or domain-specific generators.
    
    Methods:
        generate: Generate keywords based on input parameters
        configure: Configure the generator with specific settings
    """
    
    def generate(
        self,
        category: str,
        base_keywords: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """
        Generate keywords for a given category.
        
        Args:
            category: The category name for keyword generation
            base_keywords: Optional list of base keywords to expand from
            **kwargs: Additional generator-specific parameters
            
        Returns:
            List of generated keywords
            
        Raises:
            GenerationError: If keyword generation fails
        """
        ...
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the keyword generator with specific settings.
        
        Args:
            config: Configuration dictionary with generator-specific settings
        """
        ...
    
    @property
    def name(self) -> str:
        """
        Get the name/identifier of this keyword generator.
        
        Returns:
            String identifier for this generator
        """
        ...
    
    @property
    def description(self) -> str:
        """
        Get a human-readable description of this keyword generator.
        
        Returns:
            Description of the generator's functionality
        """
        ...
