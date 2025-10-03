# PixCrawler Validator

Comprehensive image validation, integrity checking, and duplicate detection for PixCrawler datasets.

## Overview

The PixCrawler Validator package provides robust validation capabilities for image datasets, including:

- **Image Integrity Validation**: Detect corrupted, invalid, or problematic image files
- **Duplicate Detection**: Advanced duplicate detection using both content and perceptual hashing
- **Configurable Validation**: Multiple validation modes and customizable parameters
- **Batch Processing**: Efficient processing of large datasets
- **Comprehensive Reporting**: Detailed statistics and processing reports

## Features

### Core Validation Components

- **ImageHasher**: Computes content and perceptual hashes for duplicate detection
- **DuplicationManager**: Detects and manages duplicate images with multiple strategies
- **ImageValidator**: Validates image integrity, format, and quality constraints
- **IntegrityProcessor**: Main processor orchestrating all validation workflows

### Advanced Validation Management

- **CheckManager**: Enhanced validation manager with comprehensive tracking
- **ValidationConfig**: Flexible configuration system with presets
- **Detailed Statistics**: Complete tracking of validation operations and results
- **Error Handling**: Robust error handling with configurable failure modes

## Installation

```bash
# Install from workspace root
uv sync

# Or install the validator package specifically
pip install -e validator/
```

## Quick Start

### Basic Usage

```python
from validator import IntegrityProcessor

# Simple validation
processor = IntegrityProcessor()
results = processor.process_dataset("./my_dataset")

print(f"Valid images: {results['validation']['valid_count']}")
print(f"Duplicates removed: {results['duplicates']['removed_count']}")
```

### Advanced Configuration

```python
from validator import CheckManager, ValidationConfig, CheckMode, DuplicateAction

# Create custom configuration
config = ValidationConfig(
    mode=CheckMode.STRICT,
    duplicate_action=DuplicateAction.QUARANTINE,
    min_file_size_bytes=2048,
    min_image_width=100,
    min_image_height=100,
    quarantine_dir="./quarantine"
)

# Initialize validation manager
manager = CheckManager(config)

# Perform comprehensive validation
duplicate_result, integrity_result = manager.check_all("./dataset")

# Get detailed statistics
stats = manager.get_summary_report()
print(f"Success rate: {stats['success_rate']:.2%}")
```

### Validation Modes

```python
from validator.config import get_preset_config

# Use preset configurations
strict_config = get_preset_config('strict')      # Fail on any issues
lenient_config = get_preset_config('lenient')   # Log warnings, continue
default_config = get_preset_config('default')   # Balanced approach
```

## Configuration Options

### Validation Behavior

- **mode**: Validation strictness (`STRICT`, `LENIENT`, `REPORT_ONLY`)
- **duplicate_action**: How to handle duplicates (`REMOVE`, `QUARANTINE`, `REPORT_ONLY`)

### File Constraints

- **supported_extensions**: Allowed image file extensions
- **max_file_size_mb**: Maximum file size in megabytes
- **min_file_size_bytes**: Minimum file size in bytes

### Image Quality Constraints

- **min_image_width**: Minimum image width in pixels
- **min_image_height**: Minimum image height in pixels

### Processing Options

- **batch_size**: Number of images to process in each batch
- **quarantine_dir**: Directory for quarantined files
- **hash_size**: Size of perceptual hash (affects sensitivity)

## API Reference

### Core Classes

#### IntegrityProcessor

Main processor for dataset validation workflows.

```python
processor = IntegrityProcessor()
results = processor.process_dataset(
    directory="./dataset",
    remove_duplicates=True,
    remove_corrupted=True
)
```

#### CheckManager

Enhanced validation manager with comprehensive tracking.

```python
manager = CheckManager(config)

# Check for duplicates only
duplicate_result = manager.check_duplicates("./dataset")

# Check integrity only  
integrity_result = manager.check_integrity("./dataset")

# Comprehensive validation
duplicate_result, integrity_result = manager.check_all("./dataset")
```

#### ValidationConfig

Flexible configuration system.

```python
config = ValidationConfig(
    mode=CheckMode.STRICT,
    duplicate_action=DuplicateAction.REMOVE,
    min_image_width=50,
    min_image_height=50
)
```

### Convenience Functions

```python
from validator import validate_dataset, remove_duplicates, process_integrity

# Quick validation
valid_count, total_count, corrupted = validate_dataset("./dataset")

# Quick duplicate removal
removed_count, originals = remove_duplicates("./dataset")

# Complete integrity processing
results = process_integrity("./dataset")
```

## Integration with Builder

The validator package is designed to work seamlessly with the PixCrawler builder:

```python
from builder import Builder
from validator import IntegrityProcessor

# Generate dataset
builder = Builder("config.json")
builder.generate()

# Validate generated dataset
processor = IntegrityProcessor()
results = processor.process_dataset(builder.config.output_dir)
```

## Performance Considerations

- **Batch Processing**: Large datasets are processed in configurable batches
- **Memory Efficiency**: Streaming processing minimizes memory usage
- **Concurrent Processing**: Configurable concurrency for validation operations
- **Hash Caching**: Intelligent caching of computed hashes

## Error Handling

The validator provides robust error handling with three modes:

- **STRICT**: Fail immediately on any validation error
- **LENIENT**: Log warnings but continue processing
- **REPORT_ONLY**: Only report issues without taking action

## Contributing

1. Follow the existing code style and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for API changes
4. Ensure all validation passes before submitting

## License

This package is part of the PixCrawler project and follows the same licensing terms.