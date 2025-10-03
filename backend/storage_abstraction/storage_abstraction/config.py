from __future__ import annotations
import os
from typing import Dict

from .provider_base import ProviderConfig
from .tiers import Tier


DEFAULT_LOCAL_BASE = os.path.join(os.getcwd(), "storage_data")


def env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if v is not None else default


def load_provider_configs() -> Dict[Tier, ProviderConfig]:
    """Build ProviderConfig per tier from environment variables.

    Environment:
    - STORAGE_ENV: dev | test | prod (default: dev)
    - STORAGE_<TIER>_PROVIDER: memory | local | s3
    - LOCAL_BASE_PATH: base path for local provider (default: ./storage_data)
    - LOCAL_PUBLIC_BASE_URL: http url for local server or nginx
    - S3_BUCKET_TEMP/HOT/COLD, S3_REGION, S3_PUBLIC_BASE_URL
    - S3_PREFIX: key prefix to apply to all keys
    """

    storage_env = env("STORAGE_ENV", "dev")

    def pick_default_provider(tier: Tier) -> str:
        if storage_env == "test":
            return "memory"
        if storage_env == "prod":
            return "s3" if tier in (Tier.HOT, Tier.COLD) else "local"
        return "local"  # dev

    cfg: Dict[Tier, ProviderConfig] = {}
    local_base = env("LOCAL_BASE_PATH", DEFAULT_LOCAL_BASE)
    local_public = env("LOCAL_PUBLIC_BASE_URL")

    s3_region = env("S3_REGION")
    s3_public = env("S3_PUBLIC_BASE_URL")
    s3_prefix = env("S3_PREFIX")

    for tier in [Tier.TEMP, Tier.HOT, Tier.COLD]:
        provider = env(f"STORAGE_{tier.name}_PROVIDER", pick_default_provider(tier))
        if provider == "local":
            cfg[tier] = ProviderConfig(
                name="local",
                base_path=os.path.join(local_base or DEFAULT_LOCAL_BASE, tier.value),
                public_base_url=local_public,
                prefix=None,
            )
        elif provider == "memory":
            cfg[tier] = ProviderConfig(name="memory")
        elif provider == "s3":
            bucket = env(f"S3_BUCKET_{tier.name}") or env("S3_BUCKET")
            if not bucket:
                raise ValueError(f"Missing S3 bucket for {tier.name}. Set S3_BUCKET_{tier.name} or S3_BUCKET")
            cfg[tier] = ProviderConfig(
                name="s3",
                bucket=bucket,
                region=s3_region,
                public_base_url=s3_public,
                prefix=s3_prefix,
            )
        else:
            raise ValueError(f"Unknown provider '{provider}' for {tier.name}")

    return cfg
