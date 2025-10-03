from __future__ import annotations
import os
import pathlib
from typing import Iterable, Optional

from ..interfaces import Storage
from ..provider_base import ProviderConfig


class LocalStorageProvider(Storage):
    """Filesystem-backed storage under a base directory.

    Keys are joined to base_path, normalized to prevent path traversal.
    """

    def __init__(self, config: ProviderConfig):
        if not config.base_path:
            raise ValueError("LocalStorageProvider requires base_path")
        self.base_path = pathlib.Path(config.base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.prefix = config.prefix.strip("/") if config.prefix else ""
        self.public_base_url = config.public_base_url.rstrip("/") if config.public_base_url else None

    def _full_path(self, key: str) -> pathlib.Path:
        safe_key = key.lstrip("/")
        if self.prefix:
            safe_key = f"{self.prefix}/{safe_key}"
        full = (self.base_path / safe_key).resolve()
        # prevent path traversal outside base
        if os.path.commonpath([str(full), str(self.base_path.resolve())]) != str(self.base_path.resolve()):
            raise ValueError("Invalid key resulting in path traversal")
        return full

    def put(self, key: str, data: bytes, *, content_type: Optional[str] = None) -> None:
        path = self._full_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    def get(self, key: str) -> Optional[bytes]:
        path = self._full_path(key)
        if not path.exists():
            return None
        with open(path, "rb") as f:
            return f.read()

    def delete(self, key: str) -> None:
        path = self._full_path(key)
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    def exists(self, key: str) -> bool:
        return self._full_path(key).exists()

    def list(self, prefix: str = "") -> Iterable[str]:
        base = self.base_path
        full_prefix = self.prefix + "/" + prefix.lstrip("/") if self.prefix else prefix.lstrip("/")
        prefix_path = (base / full_prefix).resolve()
        if not prefix_path.exists():
            return []
        keys: list[str] = []
        for path in prefix_path.rglob("*"):
            if path.is_file():
                rel = str(path.resolve().relative_to(base.resolve())).replace("\\", "/")
                # remove prefix when returning keys
                if self.prefix and rel.startswith(self.prefix + "/"):
                    rel = rel[len(self.prefix) + 1 :]
                keys.append(rel)
        return keys

    def url(self, key: str) -> Optional[str]:
        if not self.public_base_url:
            return None
        return f"{self.public_base_url}/{key.lstrip('/')}"
