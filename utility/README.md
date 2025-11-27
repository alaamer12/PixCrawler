# PixCrawler Utility Package

Centralized utility system for the PixCrawler monorepo with compression, archiving, and logging.

## Features

### Unified Configuration System
- **Centralized management**: Single configuration for all utility sub-packages
- **Environment variables**: Support for `PIXCRAWLER_UTILITY_` prefix
- **Preset configurations**: Default, production, development, and testing presets
- **Type-safe**: Pydantic V2 validation with nested composition
- **Cross-package validation**: Ensures consistency across compression and logging settings

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

### Using Unified Configuration (Recommended)

```python
from utility.config import get_utility_settings, get_preset_config

# Get default settings
settings = get_utility_settings()
print(settings.compression.quality)  # 85
print(settings.logging.environment)  # Environment.DEVELOPMENT

# Use preset configurations
prod_settings = get_preset_config("production")
print(prod_settings.compression.quality)  # 90
print(prod_settings.logging.use_json)  # True

# Access nested settings
print(settings.compression.archive.level)  # 10
print(settings.logging.console_level)  # LogLevel.DEBUG
```

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

## Configuration

### Unified Configuration (.env)

The unified configuration system uses the `PIXCRAWLER_UTILITY_` prefix with nested delimiter `__`:

```ini
# Compression Settings
PIXCRAWLER_UTILITY_COMPRESSION__QUALITY=85
PIXCRAWLER_UTILITY_COMPRESSION__FORMAT=webp
PIXCRAWLER_UTILITY_COMPRESSION__LOSSLESS=false
PIXCRAWLER_UTILITY_COMPRESSION__WORKERS=0

# Archive Settings (nested under compression)
PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__ENABLE=true
PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__TAR=true
PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__TYPE=zstd
PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__LEVEL=10

# Logging Settings
PIXCRAWLER_UTILITY_LOGGING__ENVIRONMENT=development
PIXCRAWLER_UTILITY_LOGGING__LOG_DIR=./logs
PIXCRAWLER_UTILITY_LOGGING__CONSOLE_LEVEL=DEBUG
PIXCRAWLER_UTILITY_LOGGING__FILE_LEVEL=DEBUG
PIXCRAWLER_UTILITY_LOGGING__USE_JSON=false
PIXCRAWLER_UTILITY_LOGGING__USE_COLORS=true
```

### Environment Variable Naming Convention

- **Prefix**: All variables start with `PIXCRAWLER_UTILITY_`
- **Nested Delimiter**: Use double underscore `__` for nested settings
- **Case Insensitive**: Variable names are case-insensitive
- **Examples**:
  - `PIXCRAWLER_UTILITY_COMPRESSION__QUALITY` → `settings.compression.quality`
  - `PIXCRAWLER_UTILITY_LOGGING__ENVIRONMENT` → `settings.logging.environment`
  - `PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__LEVEL` → `settings.compression.archive.level`

### Preset Configurations

The unified configuration system provides four preset configurations:

#### Default Preset
```python
settings = get_preset_config("default")
# compression.quality = 85
# compression.format = "webp"
# logging.environment = "development"
# logging.console_level = "DEBUG"
```

#### Production Preset
```python
settings = get_preset_config("production")
# compression.quality = 90
# compression.archive.level = 15
# logging.environment = "production"
# logging.console_level = "WARNING"
# logging.use_json = True
```

#### Development Preset
```python
settings = get_preset_config("development")
# compression.quality = 80
# compression.archive.level = 8
# logging.environment = "development"
# logging.console_level = "DEBUG"
# logging.use_colors = True
```

#### Testing Preset
```python
settings = get_preset_config("testing")
# compression.quality = 75
# compression.workers = 1
# compression.archive.enable = False
# logging.environment = "testing"
# logging.console_level = "ERROR"
```

### When to Use Each Preset

- **default**: General-purpose development with balanced settings
- **production**: Optimized for production with high quality, JSON logging, and minimal console output
- **development**: Developer-friendly with colored output and verbose logging
- **testing**: Minimal settings for fast test execution with disabled archiving

### Legacy Configuration (Backward Compatible)

The old configuration format is still supported for backward compatibility:

```ini
# Compression Settings (old format)
INPUT_DIR=./images
OUTPUT_DIR=./compressed
FORMAT=webp
QUALITY=85
LOSSLESS=false
WORKERS=0

# Archive Settings (old format)
ARCHIVE_ENABLE=true
ARCHIVE_TAR=true
ARCHIVE_TYPE=zstd
ARCHIVE_LEVEL=10
ARCHIVE_OUTPUT=./dataset.zst

# Logging Settings (old format)
PIXCRAWLER_ENVIRONMENT=development
PIXCRAWLER_LOG_DIR=./logs
PIXCRAWLER_LOG_JSON=false
PIXCRAWLER_LOG_COLORS=true
```

**Note**: New code should use the unified configuration system. The legacy format is maintained for backward compatibility only.

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

## Migration Guide

### Migrating from Old Configs to Unified Config

#### Before (Old Way)
```python
from utility.compress.config import get_compression_settings
from utility.logging_config.config import get_logging_settings

compression_config = get_compression_settings()
logging_config = get_logging_settings()

print(compression_config.quality)
print(logging_config.environment)
```

#### After (New Way - Recommended)
```python
from utility.config import get_utility_settings

settings = get_utility_settings()

print(settings.compression.quality)
print(settings.logging.environment)
```

### Environment Variable Migration

#### Before (Old Format)
```ini
# Compression
QUALITY=85
FORMAT=webp

# Logging
PIXCRAWLER_ENVIRONMENT=development
PIXCRAWLER_LOG_DIR=./logs
```

#### After (New Format)
```ini
# Compression
PIXCRAWLER_UTILITY_COMPRESSION__QUALITY=85
PIXCRAWLER_UTILITY_COMPRESSION__FORMAT=webp

# Logging
PIXCRAWLER_UTILITY_LOGGING__ENVIRONMENT=development
PIXCRAWLER_UTILITY_LOGGING__LOG_DIR=./logs
```

### Code Migration Steps

1. **Update imports**: Replace individual config imports with unified config
2. **Update environment variables**: Add `PIXCRAWLER_UTILITY_` prefix and use `__` delimiter
3. **Update code references**: Access settings through nested structure
4. **Test thoroughly**: Verify all configuration values are loaded correctly

### Backward Compatibility

The old configuration methods still work and will automatically use the unified config if available:

```python
# This still works and uses unified config internally
from utility.compress.config import get_compression_settings
settings = get_compression_settings()  # Returns settings.compression from unified config
```

## Architecture

```
utility/
├── config.py          # Unified configuration system (NEW)
├── compress/          # Image compression and archiving
│   ├── config.py      # Pydantic settings with composition
│   ├── compressor.py  # Multi-threaded batch compression
│   ├── archiver.py    # Archive creation (ZIP, TAR+Zstd)
│   ├── formats.py     # Format-specific compression
│   └── pipeline.py    # High-level API (compress, decompress)
├── logging_config/    # Centralized Loguru logging
│   └── config.py      # Pydantic settings for logging
└── tests/             # Comprehensive test suite
    ├── conftest.py    # Pytest fixtures
    ├── test_config.py # Unified config tests (NEW)
    └── test_compress.py  # Full compression tests
```

## Best Practices

- Use **absolute imports** throughout
- Follow **Pydantic v2** patterns for configuration
- Add **comprehensive docstrings** (Google style)
- Include **inline comments** for complex logic
- Use **type hints** for all functions
- Write **tests** for all new features
