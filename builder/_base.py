from abc import ABC, abstractmethod
from typing import Tuple


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
