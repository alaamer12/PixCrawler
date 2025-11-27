# PixCrawler Logging System

A centralized logging package powered by Loguru that provides consistent logging across the entire PixCrawler monorepo with environment-aware configuration and structured output.

## Features

- **Environment-aware configuration**: Automatic setup for development, production, and testing environments
- **Structured logging**: Built-in JSON format support for production environments
- **Automatic file rotation**: Configurable log file rotation with size limits
- **Colored console output**: Enhanced readability during development
- **Error separation**: Dedicated error log files for critical issues
- **Thread-safe operation**: Built-in thread safety through Loguru
- **High performance**: Optimized logging with lazy evaluation

## Installation

```bash
pip install loguru>=0.7.0
```

## Quick Start

### Basic Usage

```python
from utility.logging_config import setup_logging, get_logger

# Setup logging for your environment
setup_logging(environment='development')

# Get the logger
logger = get_logger()

# Use the logger
logger.info("Application started")
logger.debug("Debug information")
logger.error("An error occurred")
```

### Environment-Specific Setup

```python
from utility.logging_config import setup_logging

# Development environment (colored console, debug level)
setup_logging(environment='development')

# Production environment (JSON format_, file logging)
setup_logging(environment='production')

# Testing environment (minimal output)
setup_logging(environment='testing')
```

### Environment Variables

Configure logging using environment variables:

```bash
export PIXCRAWLER_ENVIRONMENT=production
export PIXCRAWLER_LOG_DIR=logs
export PIXCRAWLER_LOG_JSON=true
export PIXCRAWLER_LOG_COLORS=false
```

## Configuration

### LoguruConfig Parameters

| Parameter        | Description                                       | Default               |
|------------------|---------------------------------------------------|-----------------------|
| `environment`    | Environment type (development/production/testing) | `development`         |
| `log_dir`        | Directory for log files                           | `logs`                |
| `log_filename`   | Main log file name                                | `pixcrawler.log`      |
| `error_filename` | Error log file name                               | `errors.log`          |
| `max_file_size`  | Max size before rotation                          | `10 MB`               |
| `backup_count`   | Number of backup files                            | `5`                   |
| `use_json`       | Enable JSON formatting                            | Environment-dependent |
| `use_colors`     | Enable colored console output                     | Environment-dependent |

## Package Integration

### Builder Package

```python
from utility.logging_config import get_logger

logger = get_logger()
logger.info("Starting download process")
logger.debug("Processing image: {}", image_url)
```

### Backend Package

```python
from utility.logging_config import get_logger

logger = get_logger()
logger.bind(endpoint='/api/generate', method='POST', user_id='user123').info("API request received")
```

## Log Formats

### Development Format (Colored Console)
```
14:30:15 | INFO     | builder.downloader:download_images:45 - Starting image download
14:30:16 | DEBUG    | builder.engine:search:123 - Processing search results  
14:30:17 | ERROR    | builder.validator:validate:67 - Image validation failed
```

### Production Format (JSON)
```json
{
  "text": "2024-01-15T14:30:15.123456+00:00 | INFO | Starting image download\n",
  "record": {
    "elapsed": {"repr": "0:00:00.006401", "seconds": 0.006401},
    "level": {"name": "INFO", "no": 20},
    "message": "Starting image download",
    "module": "downloader", 
    "name": "builder.downloader",
    "time": {"repr": "2024-01-15T14:30:15.123456+00:00", "timestamp": 1705327815.123456}
  }
}
```

## Advanced Usage

### Custom Configuration

```python
from utility.logging_config import LoguruConfig, setup_logging

config = LoguruConfig(environment='production')
config.log_dir = Path("custom_logs")
config.max_file_size = "50 MB"
config.use_json = True

setup_logging(config=config)
```

### Context Binding

```python
from utility.logging_config import get_logger

logger = get_logger()

# Bind context that will appear in all subsequent logs
context_logger = logger.bind(user_id="user123", request_id="req-456")
context_logger.info("Processing request")
context_logger.error("Request failed")
```

### Runtime Configuration

```python
from loguru import logger

# Add custom handler at runtime
logger.add("debug.log", level="DEBUG", filter=lambda record: "debug" in record["message"])

# Remove handlers
logger.remove()  # Remove all handlers
```

## File Structure

The logging system creates the following file structure:

```
logs/
├── pixcrawler.log      # Main application log (rotated automatically)
├── pixcrawler.log.1    # Rotated log files
├── errors.log          # Error-only log (ERROR and CRITICAL)
└── errors.log.1        # Rotated error logs
```

## API Reference

### Functions

#### `setup_logging(environment=None, config=None, **kwargs)`
Setup Loguru logging for the PixCrawler monorepo.

**Parameters:**
- `environment` (str, optional): Environment type ('development', 'production', 'testing')
- `config` (LoguruConfig, optional): Custom configuration instance
- `**kwargs`: Additional configuration options

#### `get_logger(name=None)`
Get the configured Loguru logger instance.

**Parameters:**
- `name` (str, optional): Logger name for compatibility

**Returns:**
- Configured Loguru logger instance

#### `set_log_level(level)`
Set the global log level.

**Parameters:**
- `level` (str): Log level to set

#### `get_config_info()`
Get current logging configuration information.

**Returns:**
- Dictionary with configuration details

### Classes

#### `LoguruConfig(environment=Environment.DEVELOPMENT)`
Configuration class for Loguru-based logging.

#### `Environment`
Enum for environment types:
- `DEVELOPMENT`
- `PRODUCTION` 
- `TESTING`

#### `LogLevel`
Enum for log levels:
- `CRITICAL`
- `ERROR`
- `WARNING`
- `INFO`
- `DEBUG`
- `TRACE`

## Best Practices

1. **Use context binding**: `logger.bind(key=value)` for structured data
2. **Leverage lazy evaluation**: Use `{}` formatting: `logger.info("User {}", user_id)`
3. **Environment variables**: Configure via env vars for different deployments
4. **Error context**: Use `logger.exception()` for automatic traceback capture

## Examples

### Basic Logging

```python
from utility.logging_config import setup_logging, get_logger

setup_logging('development')
logger = get_logger()

logger.trace("Detailed trace information")
logger.debug("Debug information") 
logger.info("General information")
logger.success("Success message")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical system error")
```

### Exception Handling
```python
try:
    risky_operation()
except Exception as e:
    logger.exception("Operation failed")  # Automatically includes traceback
```

### Structured Logging
```python
logger.bind(
    user_id="user123",
    operation="image_download", 
    batch_size=100
).info("Starting batch processing")
```

## Migration

To migrate from the previous logging system:

1. Install loguru: `pip install loguru>=0.7.0`
2. Update imports: Change import statements to use the new package
3. The API remains compatible with existing code
4. Test functionality with the provided examples
