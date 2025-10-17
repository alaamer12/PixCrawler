from typing import Protocol, List, runtime_checkable

@runtime_checkable
class KeywordGenerator(Protocol):
    """Protocol for keyword generation strategies."""
    def generate(self, base_keywords: List[str]) -> List[str]:
        """Generate additional keywords based on the provided base keywords.
        
        Args:
            base_keywords: List of initial keywords to expand upon
            
        Returns:
            List of generated keywords
        """
        ...
