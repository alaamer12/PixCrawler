import os
import shutil
from typing import List, Optional
from .base import StorageProvider
from urllib.parse import quote
import time

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_directory: str = "local_storage"):
        self.base_directory = base_directory
        os.makedirs(self.base_directory, exist_ok=True)

    def _full_path(self, file_path: str) -> str:
        return os.path.join(self.base_directory, file_path)

    def upload(self, file_path: str, destination_path: str) -> None:
        full_path = self._full_path(destination_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        shutil.copy(file_path, full_path)

    def download(self, file_path: str, destination_path: str) -> None:
        full_path = self._full_path(file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"{file_path} not found in local storage")
        shutil.copy(full_path, destination_path)

    def delete(self, file_path: str) -> None:
        full_path = self._full_path(file_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        files = []
        for root, _, filenames in os.walk(self.base_directory):
            for filename in filenames:
                relative_path = os.path.relpath(os.path.join(root, filename), self.base_directory)
                if not prefix or relative_path.startswith(prefix):
                    files.append(relative_path)
        return files

    def generate_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        timestamp = int(time.time())
        expires_at = timestamp + expires_in
        return f"file://{quote(self._full_path(file_path))}?expires_at={expires_at}"
