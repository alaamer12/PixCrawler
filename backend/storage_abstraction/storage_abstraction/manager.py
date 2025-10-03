from __future__ import annotations
from typing import Dict

from .interfaces import Storage
from .tiers import Tier
from .config import load_provider_configs
from .providers import LocalStorageProvider, InMemoryStorageProvider, S3StorageProvider
from .provider_base import ProviderConfig


class StorageManager:
    """High-level entrypoint routing by tier.

    Example:
        mgr = StorageManager.from_env()
        mgr.put(Tier.HOT, "foo.txt", b"hello")
    """

    def __init__(self, storages: Dict[Tier, Storage]):
        self._storages = storages

    @classmethod
    def from_env(cls) -> "StorageManager":
        cfgs = load_provider_configs()
        storages: Dict[Tier, Storage] = {}
        for tier, cfg in cfgs.items():
            storages[tier] = cls._build_storage(cfg)
        return cls(storages)

    @staticmethod
    def _build_storage(cfg: ProviderConfig) -> Storage:
        if cfg.name == "local":
            return LocalStorageProvider(cfg)
        if cfg.name == "memory":
            return InMemoryStorageProvider()
        if cfg.name == "s3":
            if S3StorageProvider is None:
                raise RuntimeError("S3 provider requested but boto3 is not installed")
            return S3StorageProvider(cfg)
        raise ValueError(f"Unknown provider name: {cfg.name}")

    def storage(self, tier: Tier) -> Storage:
        return self._storages[tier]

    # Convenience proxies
    def put(self, tier: Tier, key: str, data: bytes, **kwargs) -> None:
        self.storage(tier).put(key, data, **kwargs)

    def get(self, tier: Tier, key: str):
        return self.storage(tier).get(key)

    def delete(self, tier: Tier, key: str) -> None:
        self.storage(tier).delete(key)

    def exists(self, tier: Tier, key: str) -> bool:
        return self.storage(tier).exists(key)

    def list(self, tier: Tier, prefix: str = ""):
        return self.storage(tier).list(prefix)

    def url(self, tier: Tier, key: str):
        return self.storage(tier).url(key)
