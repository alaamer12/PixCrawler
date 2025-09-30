from abc import ABC, abstractmethod
from typing import List, Optional

class StorageProvider(ABC):
    @abstractmethod
    def upload(self, file_path: str, destination_path: str) -> None:
        pass

    @abstractmethod
    def download(self, file_path: str, destination_path: str) -> None:
        pass

    @abstractmethod
    def delete(self, file_path: str) -> None:
        pass

    @abstractmethod
    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        pass

    @abstractmethod
    def generate_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        pass
