# Utility Package: Compression Pipeline

## Features
- Multiple formats: WebP, AVIF, PNG
- Quality control 0-100, lossless or lossy
- Batch processing with multi-threading
- Progress tracking
- TAR archive with ZSTD (1-19) or ZIP fallback

## Install
```bash
pip install -e .
```

## Configuration (.env)
```ini
INPUT_DIR=./images
OUTPUT_DIR=./compressed
FORMAT=webp
QUALITY=85
LOSSLESS=false
WORKERS=0
ARCHIVE__ENABLE=true
ARCHIVE__TAR=true
ARCHIVE__TYPE=zstd
ARCHIVE__LEVEL=19
ARCHIVE__OUTPUT=./dataset.zst
```

## Usage
```bash
python -m utility.compress.pipeline
# or
utility-compress
```

## Defaults
- WebP: cwebp -q 85 if available, otherwise Pillow WebP
- Archiving: tar + zstd -10 using multi-threaded zstd
