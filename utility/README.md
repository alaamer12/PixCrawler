# PixCrawler Utility Package

Centralized utility system for the PixCrawler monorepo with compression, archiving, and logging.

## Features

### Compression Module
- **Multi-format support**: WebP, AVIF, PNG, JXL
- **Quality control**: 0-100, lossless or lossy
- **Batch processing**: Multi-threaded compression
- **Progress tracking**: Real-time progress bars
- **Archive support**: TAR+Zstandard (1-19) or ZIP
- **Debug mode**: Detailed statistics and metrics

### Logging Module
- **Environment-based**: Development, production, testing
- **Type-safe**: Pydantic v2 configuration
- **JSON logging**: Azure Monitor compatible
- **File rotation**: Automatic log rotation and retention
- **Colored output**: Development-friendly console logs

## Installation

```bash
# Install package
pip install -e .

# Install with test dependencies
pip install -e ".[test]"
```

## Quick Start

### Simple Compression

```python
from utility.compress import compress, decompress

# Compress images
compress("./raw_images", "./compressed")

# With archiving
archive = compress(
  "./raw_images",
  "./compressed",
  format_="webp",
  quality=90,
  archive=True
)

# Decompress
decompress("./dataset.zst", "./extracted")
```

### Debug Mode
```python
# Show detailed statistics
compress(
    "./raw_images",
    "./compressed",
    format="webp",
    quality=85,
    archive=True,
    debug=True  # Shows before/after sizes, compression ratios
)
```

### Advanced Configuration
```python
from utility.compress import CompressionSettings, ImageCompressor

# Custom configuration
cfg = CompressionSettings(
    input_dir="./images",
    output_dir="./compressed",
    format="webp",
    quality=85,
    workers=8
)

compressor = ImageCompressor(cfg)
compressor.run()
```

## Configuration (.env)

```ini
# Compression Settings
INPUT_DIR=./images
OUTPUT_DIR=./compressed
FORMAT=webp
QUALITY=85
LOSSLESS=false
WORKERS=0

# Archive Settings
ARCHIVE_ENABLE=true
ARCHIVE_TAR=true
ARCHIVE_TYPE=zstd
ARCHIVE_LEVEL=10
ARCHIVE_OUTPUT=./dataset.zst

# Logging Settings
PIXCRAWLER_ENVIRONMENT=development
PIXCRAWLER_LOG_DIR=./logs
PIXCRAWLER_LOG_JSON=false
PIXCRAWLER_LOG_COLORS=true
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=utility --cov-report=html

# Run specific test file
pytest tests/test_compress.py

# Run with verbose output
pytest -v
```

## Test Coverage

The test suite provides comprehensive coverage:
- ✅ Configuration validation and defaults
- ✅ Image compression (all formats)
- ✅ Archive creation (ZIP, TAR, Zstandard)
- ✅ Decompression (all archive types)
- ✅ Debug mode output
- ✅ Directory structure preservation
- ✅ Edge cases (empty directories, invalid formats)
- ✅ Full compression/decompression cycle

## Architecture

```
utility/
├── compress/           # Image compression and archiving
│   ├── config.py      # Pydantic settings with composition
│   ├── compressor.py  # Multi-threaded batch compression
│   ├── archiver.py    # Archive creation (ZIP, TAR+Zstd)
│   ├── formats.py     # Format-specific compression
│   └── pipeline.py    # High-level API (compress, decompress)
├── logging_config/    # Centralized Loguru logging
│   └── config.py      # Pydantic settings for logging
└── tests/             # Comprehensive test suite
    ├── conftest.py    # Pytest fixtures
    └── test_compress.py  # Full compression tests
```

## Best Practices

- Use **absolute imports** throughout
- Follow **Pydantic v2** patterns for configuration
- Add **comprehensive docstrings** (Google style)
- Include **inline comments** for complex logic
- Use **type hints** for all functions
- Write **tests** for all new features
