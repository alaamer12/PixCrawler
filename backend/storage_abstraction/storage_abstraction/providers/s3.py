from __future__ import annotations
from typing import Iterable, Optional
import boto3
from botocore.client import Config as BotoConfig

from ..interfaces import Storage
from ..provider_base import ProviderConfig


class S3StorageProvider(Storage):
    def __init__(self, config: ProviderConfig):
        if not config.bucket:
            raise ValueError("S3StorageProvider requires bucket")
        self.bucket = config.bucket
        self.prefix = (config.prefix or "").strip("/")
        self.public_base_url = config.public_base_url.rstrip("/") if config.public_base_url else None
        session = boto3.session.Session()
        self.client = session.client(
            "s3",
            region_name=config.region,
            config=BotoConfig(signature_version="s3v4"),
        )

    def _key(self, key: str) -> str:
        key = key.lstrip("/")
        return f"{self.prefix}/{key}" if self.prefix else key

    def put(self, key: str, data: bytes, *, content_type: Optional[str] = None) -> None:
        extra = {"ContentType": content_type} if content_type else {}
        self.client.put_object(Bucket=self.bucket, Key=self._key(key), Body=data, **extra)

    def get(self, key: str) -> Optional[bytes]:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=self._key(key))
            return obj["Body"].read()
        except self.client.exceptions.NoSuchKey:
            return None
        except Exception:
            # fallback: check existence
            if not self.exists(key):
                return None
            raise

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=self._key(key))

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=self._key(key))
            return True
        except Exception:
            return False

    def list(self, prefix: str = "") -> Iterable[str]:
        full_prefix = self._key(prefix)
        paginator = self.client.get_paginator("list_objects_v2")
        keys: list[str] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=full_prefix):
            for item in page.get("Contents", []) or []:
                k = item["Key"]
                # strip provider prefix
                if self.prefix and k.startswith(self.prefix + "/"):
                    k = k[len(self.prefix) + 1 :]
                keys.append(k)
        return keys

    def url(self, key: str) -> Optional[str]:
        if self.public_base_url:
            return f"{self.public_base_url}/{key.lstrip('/')}"
        # presigned fallback
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": self._key(key)},
            ExpiresIn=3600,
        )
