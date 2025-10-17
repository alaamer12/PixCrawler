from typing import List, Dict, Type
from .protocols import KeywordGenerator

class SimpleKeywordGenerator:
    """Basic keyword generator that performs simple expansions."""
    
    def generate(self, base_keywords: List[str]) -> List[str]:
        """Generate additional keywords using basic expansion rules.
        
        Args:
            base_keywords: List of initial keywords to expand upon
            
        Returns:
            List of generated keywords including the original ones
        """
        if not base_keywords:
            return []
            
        # Basic keyword expansion - can be enhanced as needed
        expanded = set(base_keywords)  # Start with original keywords
        
        # Add common variations
        for keyword in base_keywords:
            # Add space-separated parts
            expanded.update(keyword.split())
            # Add variations with common prefixes/suffixes
            for suffix in ['', ' image', ' photo', ' picture', ' art', ' illustration']:
                expanded.add(f"{keyword}{suffix}")
        
        return list(expanded)


class AIKeywordGenerator:
    """AI-powered keyword generator (placeholder implementation)."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
    
    def generate(self, base_keywords: List[str]) -> List[str]:
        """Generate additional keywords using AI.
        
        Args:
            base_keywords: List of initial keywords to expand upon
            
        Returns:
            List of generated keywords including the original ones
        """
        # Placeholder implementation - would call an AI service in reality
        # This is a simplified version that just returns the input for now
        return list(set(base_keywords))  # Remove duplicates


class KeywordGeneratorFactory:
    """Factory for creating keyword generator instances."""
    
    GENERATORS: Dict[str, Type[KeywordGenerator]] = {
        'simple': SimpleKeywordGenerator,
        'ai': AIKeywordGenerator,
    }
    
    @classmethod
    def create_generator(cls, strategy: str = 'simple', **kwargs) -> KeywordGenerator:
        """Create a keyword generator instance based on the specified strategy.
        
        Args:
            strategy: Name of the generation strategy ('simple' or 'ai')
            **kwargs: Additional arguments to pass to the generator's constructor
            
        Returns:
            An instance of the specified keyword generator
            
        Raises:
            ValueError: If the specified strategy is not found
        """
        generator_class = cls.GENERATORS.get(strategy.lower())
        if generator_class is None:
            raise ValueError(f"Unknown keyword generation strategy: {strategy}")
            
        return generator_class(**kwargs)
    
    @classmethod
    def register_generator(cls, name: str, generator_class: Type[KeywordGenerator]) -> None:
        """Register a new keyword generator type.
        
        Args:
            name: Strategy name to register
            generator_class: Class implementing the KeywordGenerator protocol
        """
        if not isinstance(generator_class, type) or not issubclass(generator_class, KeywordGenerator):
            raise TypeError("Generator must be a class implementing KeywordGenerator protocol")
        cls.GENERATORS[name.lower()] = generator_class
