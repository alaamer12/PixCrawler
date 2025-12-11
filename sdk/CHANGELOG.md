# PixCrawler SDK Changelog

## Version 0.2.0 - Updated API Interface (January 2025)

### 🚀 Major Changes

#### New Object-Oriented Interface
- **Added `Dataset` class**: Provides methods for loading, downloading, and getting info
- **Added `Project` class**: Manages project-level operations and dataset access
- **New main functions**: `pix.dataset()`, `pix.project()`, `pix.datasets()`

#### Updated API Endpoints
- **Aligned with backend**: Updated to use actual PixCrawler backend endpoints
- **Export endpoints**: Uses `/datasets/{id}/export/json` and `/datasets/{id}/export/zip`
- **Pagination support**: Proper FastAPI pagination handling
- **Project integration**: Full project-dataset hierarchy support

#### Enhanced Authentication
- **Multiple auth methods**: Programmatic, environment variables, per-request config
- **Updated env vars**: Primary `PIXCRAWLER_SERVICE_KEY`, legacy support maintained
- **Global auth state**: `pix.auth()` sets global authentication for session

### 🔧 API Changes

#### New Interface (Recommended)
```python
import pixcrawler as pix

# Authentication
pix.auth(token="your_api_key")

# Project-based access
project = pix.project("project-id")
datasets = project.datasets()
dataset = project.dataset("dataset-id")

# Direct dataset access
dataset = pix.dataset("dataset-id")
info = dataset.info()
data = dataset.load()
path = dataset.download("./dataset.zip")

# List all datasets
all_datasets = pix.datasets(page=1, size=50)
```

#### Legacy Interface (Backward Compatible)
```python
import pixcrawler as pix

# Legacy functions still work
dataset = pix.load_dataset("dataset-id")
datasets = pix.list_datasets(page=1, size=20)
info = pix.get_dataset_info("dataset-id")
path = pix.download_dataset("dataset-id", "./dataset.zip")
```

### 📋 New Features

1. **Method Chaining**: `dataset.load()` returns self for chaining
2. **Property Access**: `dataset.name`, `dataset.image_count`, `dataset.size_mb`
3. **Memory Safety**: 300MB limit with clear error messages
4. **Better Error Handling**: Specific exceptions for different error types
5. **Streaming Downloads**: Efficient handling of large dataset downloads
6. **Project Management**: Full project-dataset hierarchy support

### 🔄 Backend Endpoint Mapping

| SDK Function | Backend Endpoint | Description |
|--------------|------------------|-------------|
| `pix.datasets()` | `GET /datasets` | List user datasets with pagination |
| `dataset.info()` | `GET /datasets/{id}` | Get dataset metadata |
| `dataset.load()` | `GET /datasets/{id}/export/json` | Load dataset into memory |
| `dataset.download()` | `GET /datasets/{id}/export/zip` | Download dataset archive |
| `project.info()` | `GET /projects/{id}` | Get project metadata |
| `project.datasets()` | `GET /datasets?project_id={id}` | List project datasets |

### 🛡️ Security & Best Practices

1. **Environment Variables**: Primary support for `PIXCRAWLER_SERVICE_KEY`
2. **Token Validation**: Proper Bearer token authentication
3. **Error Handling**: Structured error responses with specific exception types
4. **Memory Limits**: 300MB limit prevents memory exhaustion
5. **Timeout Handling**: Configurable timeouts for different operations

### 🧪 Testing

- **Comprehensive test suite**: 11 test cases covering all major functionality
- **Mock support**: Built-in mocking for development and testing
- **README validation**: Ensures documentation examples work correctly
- **Error scenarios**: Tests for authentication, not found, and rate limiting errors

### 📚 Documentation

- **Updated README**: Complete API reference with examples
- **Demo script**: Interactive demonstration of all features
- **Type hints**: Full type annotation support
- **Docstrings**: Comprehensive documentation for all public methods

### 🔧 Development

- **Updated dependencies**: Modern requests library version
- **Test infrastructure**: pytest-based testing with mocking
- **Code quality**: Type hints, docstrings, and error handling
- **Backward compatibility**: Legacy functions maintained

### 🚨 Breaking Changes

None! All existing code continues to work with legacy function support.

### 📦 Migration Guide

#### From v0.1.0 to v0.2.0

**Old Code:**
```python
import pixcrawler as pix
dataset = pix.load_dataset("dataset-id")
for item in dataset:
    print(item)
```

**New Code (Recommended):**
```python
import pixcrawler as pix
pix.auth(token="your_api_key")
dataset = pix.dataset("dataset-id").load()
for item in dataset:
    print(item)
```

**Or keep using legacy functions:**
```python
import pixcrawler as pix
dataset = pix.load_dataset("dataset-id")  # Still works!
for item in dataset:
    print(item)
```

### 🎯 Next Steps

1. **SDK Publishing**: Ready for PyPI publication
2. **Documentation**: Integration with main PixCrawler docs
3. **Examples**: Additional use case examples
4. **Performance**: Optimization for large dataset handling
5. **Features**: Additional export formats and filtering options