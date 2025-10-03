from __future__ import annotations
from typing import Dict, Iterable, Optional

from ..interfaces import Storage


class InMemoryStorageProvider(Storage):
    def __init__(self):
        self._store: Dict[str, bytes] = {}

    def put(self, key: str, data: bytes, *, content_type: Optional[str] = None) -> None:
        self._store[key] = data

    def get(self, key: str) -> Optional[bytes]:
        return self._store.get(key)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        return key in self._store

    def list(self, prefix: str = "") -> Iterable[str]:
        p = prefix or ""
        return [k for k in self._store.keys() if k.startswith(p)]
