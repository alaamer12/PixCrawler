from abc import ABC, abstractmethod
from typing import Tuple, Protocol, Optional, List, Dict, Any


class IDownloader(ABC):
    """
    Abstract base class for image downloaders.

    Contract:
    - Must handle retries internally
    - Must validate downloaded images
    - Must return (success: bool, count: int)
    - Must raise DownloadError for unrecoverable failures
    """

    @abstractmethod
    def download(self, keyword: str, out_dir: str, max_num: int) -> Tuple[bool, int]:
        """
        Downloads images for the given keyword.

        Args:
            keyword: Search term for images
            out_dir: Output directory path
            max_num: Maximum number of images to download

        Returns:
            Tuple[bool, int]: (success, downloaded_count)

        Raises:
            DownloadError: For download and validation failures
        """
        pass

class ISearchEngineDownloader(ABC):
    ...


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
