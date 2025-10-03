from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderConfig:
    name: str
    base_path: Optional[str] = None  # for local
    bucket: Optional[str] = None     # for s3
    region: Optional[str] = None     # for s3
    public_base_url: Optional[str] = None  # for local hosting or CDN
    prefix: Optional[str] = None     # key prefix within provider
