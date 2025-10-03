from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable, Optional


class Storage(ABC):
    """Unified storage interface for a single tier.

    All implementations must be safe for repeated calls and idempotent deletes.
    Keys are opaque paths within the tier namespace; implementations may apply
    prefixes or base paths.
    """

    @abstractmethod
    def put(self, key: str, data: bytes, *, content_type: Optional[str] = None) -> None:
        """Store bytes at key, replacing if exists."""

    @abstractmethod
    def get(self, key: str) -> Optional[bytes]:
        """Retrieve bytes or None if not found."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete key if exists (no error if missing)."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if key exists."""

    @abstractmethod
    def list(self, prefix: str = "") -> Iterable[str]:
        """Yield keys under optional prefix."""

    def url(self, key: str) -> Optional[str]:
        """Optional public URL if supported; default None."""
        return None
