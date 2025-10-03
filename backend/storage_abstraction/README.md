# Storage Abstraction Layer (Python)

Unified interface across storage tiers (temp, hot, cold) with environment-specific providers.

## Features
- Unified `Storage` interface and `StorageManager`
- Tiers: `temp`, `hot`, `cold`
- Providers: In-memory (test), Local filesystem (dev), S3 (prod, optional)
- Configurable via environment variables

## Install
```bash
pip install -r requirements.txt
```

> boto3 is only needed if you use the S3 provider.

## Quick start
```bash
# optional
cp .env.example .env
python examples/demo.py
```

## Environment variables
- **STORAGE_ENV**: `dev` (default) | `test` | `prod`
- **STORAGE_<TIER>_PROVIDER**: `memory` | `local` | `s3`
- **LOCAL_BASE_PATH**: directory for local provider (default: `./storage_data`)
- **LOCAL_PUBLIC_BASE_URL**: base URL for serving local files (optional)
- **S3_BUCKET_TEMP/HOT/COLD** or **S3_BUCKET**: buckets
- **S3_REGION**: region name
- **S3_PUBLIC_BASE_URL**: CDN or website base URL (optional)
- **S3_PREFIX**: common prefix for all keys (optional)

## Code example
```python
from storage_abstraction import StorageManager, Tier

mgr = StorageManager.from_env()

mgr.put(Tier.HOT, "path/to/file.txt", b"data", content_type="text/plain")
print(mgr.exists(Tier.HOT, "path/to/file.txt"))
print(mgr.get(Tier.HOT, "path/to/file.txt"))
for key in mgr.list(Tier.HOT, prefix="path/"):
    print(key)
```

## Provider selection defaults
- dev: all tiers use Local
- test: all tiers use InMemory
- prod: HOT/COLD use S3, TEMP uses Local (override as needed)

## Notes
- Local provider stores data under `LOCAL_BASE_PATH/<tier>/...`
- S3 provider requires AWS credentials in environment or shared config
- `url()` returns a public URL if configured or a presigned URL for S3
