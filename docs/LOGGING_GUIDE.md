# PixCrawler Logging Guide

Complete guide to logging architecture, configuration, and best practices for PixCrawler.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Development vs Production](#development-vs-production)
5. [Structured Logging](#structured-logging)
6. [Task-Level Logging](#task-level-logging)
7. [Azure Monitor Integration](#azure-monitor-integration)
8. [Querying Logs](#querying-logs)
9. [Best Practices](#best-practices)
10. [Cost Management](#cost-management)
11. [Troubleshooting](#troubleshooting)

---

## Overview

PixCrawler uses **Loguru** for application logging with environment-aware configuration:

- **Development**: Colored console + local files with rotation
- **Production**: JSON to stdout → Azure Monitor (automatic)
- **Testing**: Minimal console output only

### Key Features

✅ **Structured logging** - JSON format with key-value pairs  
✅ **Environment-aware** - Different configs per environment  
✅ **Azure Monitor ready** - Automatic integration  
✅ **Task context** - Track logs by task_id, user_id, job_id  
✅ **Zero setup** - Works out of the box in Azure  

---

## Architecture

### Logging Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Development                          │
├─────────────────────────────────────────────────────────┤
│  Your App                                               │
│    ↓                                                    │
│  logger.info("message", key=value)                      │
│    ↓                                                    │
│  Loguru                                                 │
│    ├─→ Console (stderr): Colored, DEBUG                │
│    ├─→ logs/pixcrawler.log: Rotated files              │
│    └─→ logs/errors.log: Errors only                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    Production                           │
├─────────────────────────────────────────────────────────┤
│  Your App (Azure App Service)                           │
│    ↓                                                    │
│  logger.info("message", key=value)                      │
│    ↓                                                    │
│  Loguru                                                 │
│    ├─→ Console (stderr): WARNING level                 │
│    └─→ stdout: JSON format                             │
│         ↓                                               │
│  Azure App Service (automatic capture)                  │
│         ↓                                               │
│  Azure Monitor / Application Insights                   │
│    • Stores in Log Analytics Workspace                  │
│    • Indexes all fields                                 │
│    • Retention: 30-730 days (configurable)             │
│    • Query via KQL                                      │
│    • Dashboards & Alerts                                │
└─────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Set environment
export PIXCRAWLER_ENVIRONMENT=production  # or development, testing

# Optional overrides
export PIXCRAWLER_LOG_DIR=logs
export PIXCRAWLER_LOG_JSON=true
export PIXCRAWLER_LOG_COLORS=false
```

### Code Setup

```python
from logging_config import setup_logging, get_logger

# Setup once at application start
setup_logging(environment='production')

# Get logger anywhere in your code
logger = get_logger()
```

### Configuration by Environment

| Setting | Development | Production | Testing |
|---------|------------|------------|---------|
| **Console Level** | DEBUG | WARNING | ERROR |
| **File Level** | DEBUG | INFO | - |
| **Format** | Colored text | JSON | Text |
| **Output** | stderr + files | stderr + stdout | stderr only |
| **Colors** | ✅ Yes | ❌ No | ❌ No |
| **File Rotation** | ✅ 10 MB | ❌ N/A | ❌ N/A |
| **Retention** | 5 files | Azure manages | - |

---

## Development vs Production

### Development (Local)

**Purpose**: Debugging, testing, local development

**Configuration**:
```python
setup_logging(environment='development')
```

**Outputs**:
```
Console (stderr):
22:35:15 | INFO     | celery_core.tasks:process_chunk:42 - Chunk processing started

Files:
logs/
├── pixcrawler.log       # All logs, rotated at 10 MB
├── pixcrawler.log.1     # Backup 1
├── pixcrawler.log.2     # Backup 2
├── errors.log           # Errors only
└── errors.log.1         # Error backup
```

**Features**:
- ✅ Colored output for readability
- ✅ DEBUG level (verbose)
- ✅ Local file storage
- ✅ Automatic rotation
- ✅ 5 backup files kept

---

### Production (Azure)

**Purpose**: Monitoring, alerting, analytics

**Configuration**:
```python
setup_logging(environment='production')
```

**Outputs**:
```
Console (stderr):
2025-10-30 22:35:15 | WARNING | High memory usage detected

stdout (JSON):
{
  "text": "Chunk processing started",
  "record": {
    "elapsed": {"seconds": 0.006},
    "level": {"name": "INFO", "no": 20},
    "message": "Chunk processing started",
    "extra": {
      "task_id": "abc-123",
      "chunk_id": "chunk_001",
      "user_id": "user_789"
    },
    "time": {"timestamp": 1730319315.123}
  }
}
```

**Features**:
- ✅ JSON format (machine-readable)
- ✅ Stdout → Azure Monitor (automatic)
- ✅ No file management needed
- ✅ Azure handles storage/retention
- ✅ Queryable via KQL
- ✅ Dashboards & alerts

---

## Structured Logging

### What is Structured Logging?

Instead of string concatenation, pass data as keyword arguments:

**❌ Old Way (String-based)**:
```python
logger.info(f"Chunk {chunk_id} processed: {valid} valid, {failed} failed")
```

**✅ New Way (Structured)**:
```python
logger.info(
    "Chunk processing completed",
    chunk_id=chunk_id,
    images_valid=valid,
    images_failed=failed,
    duration_sec=42.5
)
```

### Why Structured Logging?

**Benefits**:
- ✅ Easy to query specific fields
- ✅ Aggregate metrics programmatically
- ✅ Filter by any field
- ✅ Machine-readable

**Example Query**:
```kusto
// Find all chunks with low success rate
logs
| where images_valid < 400
| project chunk_id, images_valid, images_failed
```

### JSON Output

```json
{
  "message": "Chunk processing completed",
  "extra": {
    "chunk_id": "chunk_001",
    "images_valid": 450,
    "images_failed": 50,
    "duration_sec": 42.5
  }
}
```

---

## Task-Level Logging

### Binding Context

**Always bind task context** to track logs across distributed tasks:

```python
from logging_config import get_logger
from celery import Task

@celery_app.task(bind=True)
def process_chunk(self: Task, chunk_id: str, job_id: str, user_id: str):
    # Bind context once
    logger = get_logger().bind(
        task_id=self.request.id,
        task_name=self.name,
        chunk_id=chunk_id,
        job_id=job_id,
        user_id=user_id,
        worker=self.request.hostname,
        retry_count=self.request.retries
    )
    
    # All subsequent logs include this context
    logger.info("Chunk processing started")
    logger.info("Download phase", phase="download")
    logger.info("Validation phase", phase="validation")
    logger.info("Chunk completed", images_processed=450)
```

### Context Fields

**Required fields** for all task logs:
- `task_id` - Celery task ID
- `task_name` - Task function name
- `chunk_id` - Chunk identifier
- `job_id` - Parent job identifier
- `user_id` - User who initiated the job

**Optional fields**:
- `worker` - Worker hostname
- `retry_count` - Number of retries
- `phase` - Processing phase (download, validate, upload)

### Log Phases

```python
logger.info("Download started", phase="download")
images = download_images(chunk_id)
logger.info("Download completed", phase="download", count=len(images))

logger.info("Validation started", phase="validation")
valid = validate_images(images)
logger.info("Validation completed", phase="validation", valid=len(valid))

logger.info("Upload started", phase="upload")
upload_to_storage(valid)
logger.info("Upload completed", phase="upload")

logger.info(
    "Chunk completed",
    images_downloaded=len(images),
    images_valid=len(valid),
    images_failed=len(images) - len(valid),
    success_rate=len(valid) / len(images),
    duration_sec=time.time() - start_time
)
```

---

## Azure Monitor Integration

### Automatic Setup

**No code changes needed!** Azure App Service automatically:

1. Creates Application Insights resource
2. Creates Log Analytics Workspace
3. Captures stdout/stderr
4. Sends to Azure Monitor
5. Indexes all JSON fields

### Accessing Logs

**Azure Portal**:
1. Go to `portal.azure.com`
2. Navigate to **Azure Monitor** → **Logs**
3. Select your Log Analytics Workspace
4. Query using KQL

### Configuration

**Retention Settings**:
```
Azure Monitor → Log Analytics Workspace → Settings

Data Retention: 30-730 days
Daily Cap: Optional limit (GB/day)
Archive: Move to cheaper storage after X days
```

**Pricing Tiers**:
- **Interactive (Hot)**: 30-90 days, fast queries
- **Archive (Cold)**: 90+ days, slower queries, cheaper

---

## Querying Logs

### KQL (Kusto Query Language)

**Basic Queries**:

```kusto
// All logs from last hour
logs
| where timestamp > ago(1h)

// All errors
logs
| where level == "ERROR"

// Logs for specific user
logs
| where user_id == "user_123"

// Logs for specific task
logs
| where task_id == "abc-123"
| order by timestamp asc

// Logs for specific job (all chunks)
logs
| where job_id == "job_456"
| project timestamp, chunk_id, message, level
```

**Aggregation Queries**:

```kusto
// Average processing time
logs
| where message == "Chunk completed"
| summarize avg(duration_sec)

// Error count by type
logs
| where level == "ERROR"
| summarize count() by error
| order by count_ desc

// Success rate by hour
logs
| where message == "Chunk completed"
| summarize avg(success_rate) by bin(timestamp, 1h)
| render timechart

// Slowest chunks today
logs
| where timestamp > startofday(now())
| where message == "Chunk completed"
| where duration_sec > 60
| project chunk_id, user_id, duration_sec, images_valid
| order by duration_sec desc
```

**Advanced Queries**:

```kusto
// Find failed jobs and their errors
logs
| where job_id == "job_456"
| where level == "ERROR"
| project timestamp, chunk_id, error, traceback
| order by timestamp desc

// User with most errors
logs
| where level == "ERROR"
| summarize error_count = count() by user_id
| order by error_count desc
| take 10

// Processing time percentiles
logs
| where message == "Chunk completed"
| summarize 
    p50 = percentile(duration_sec, 50),
    p95 = percentile(duration_sec, 95),
    p99 = percentile(duration_sec, 99)
```

### Web UI Filters

**Point-and-click filtering** (no KQL needed):
- Filter by level (ERROR, WARNING, INFO)
- Filter by time range
- Filter by any field
- Create charts and visualizations

---

## Best Practices

### 1. Always Use Structured Logging

**✅ Good**:
```python
logger.info(
    "Chunk completed",
    chunk_id=chunk_id,
    images_valid=450,
    duration_sec=42.5
)
```

**❌ Bad**:
```python
logger.info(f"Chunk {chunk_id} completed with 450 valid images in 42.5s")
```

### 2. Bind Context Early

**✅ Good**:
```python
logger = get_logger().bind(task_id=task_id, user_id=user_id)
logger.info("Started")
logger.info("Processing")
logger.info("Completed")
```

**❌ Bad**:
```python
logger.info("Started", task_id=task_id, user_id=user_id)
logger.info("Processing", task_id=task_id, user_id=user_id)
logger.info("Completed", task_id=task_id, user_id=user_id)
```

### 3. Log Phase Transitions

```python
logger.info("Download started", phase="download")
# ... download logic ...
logger.info("Download completed", phase="download", count=500)

logger.info("Validation started", phase="validation")
# ... validation logic ...
logger.info("Validation completed", phase="validation", valid=450)
```

### 4. Use Exception Logging

**✅ Good**:
```python
try:
    process_chunk()
except Exception as e:
    logger.exception("Chunk processing failed", chunk_id=chunk_id)
    raise
```

**❌ Bad**:
```python
try:
    process_chunk()
except Exception as e:
    logger.error(f"Error: {str(e)}")  # No traceback!
    raise
```

### 5. Log Metrics

```python
logger.info(
    "Chunk metrics",
    images_downloaded=500,
    images_valid=450,
    images_failed=50,
    success_rate=0.90,
    duration_sec=42.5,
    storage_used_mb=250,
    avg_image_size_kb=512
)
```

### 6. Appropriate Log Levels

| Level | Use For | Example |
|-------|---------|---------|
| **TRACE** | Very detailed debugging | Variable values, loop iterations |
| **DEBUG** | Debugging information | Function entry/exit, state changes |
| **INFO** | General information | Task started/completed, phase transitions |
| **WARNING** | Warning conditions | Retries, degraded performance |
| **ERROR** | Error conditions | Failed operations, exceptions |
| **CRITICAL** | Critical failures | System failures, data corruption |

---

## Cost Management

### Pricing

**Azure Monitor**:
- **Ingestion**: $2.76/GB
- **Retention**: 
  - First 31 days: Free
  - 31-90 days: $0.12/GB/month
  - 90+ days (archive): $0.02/GB/month

### Estimated Costs

**100 users, 1GB logs/day**:
```
Ingestion: 1GB × 30 days × $2.76 = $82.80/month
Retention (30 days): Free
Total: ~$83/month
```

**1,000 users, 5GB logs/day**:
```
Ingestion: 5GB × 30 days × $2.76 = $414/month
Retention (30 days): Free
Total: ~$414/month
```

### Cost Optimization

**1. Set Appropriate Log Levels**:
```python
# Production: INFO level (not DEBUG)
if environment == Environment.PRODUCTION:
    self.console_level = LogLevel.INFO  # Not DEBUG
```

**2. Filter Noisy Packages**:
```python
# Already configured in _package_filter()
noisy_packages = [
    'urllib3.connectionpool',
    'requests.packages.urllib3',
    'PIL.PngImagePlugin'
]
```

**3. Use Daily Cap**:
```
Azure Monitor → Settings → Daily Cap
Set limit: 5 GB/day (prevents runaway costs)
```

**4. Archive Old Logs**:
```
Retention: 30 days (hot)
Archive: 90+ days (cold, cheaper)
```

**5. Sample High-Volume Logs**:
```python
# Sample 10% of debug logs
if random.random() < 0.1:
    logger.debug("Detailed info")
```

---

## Troubleshooting

### Logs Not Appearing in Azure Monitor

**Check**:
1. Environment variable set: `PIXCRAWLER_ENVIRONMENT=production`
2. Application Insights created (automatic with App Service)
3. Logs written to stdout (check with `print()` test)
4. Wait 2-5 minutes (ingestion delay)

**Test**:
```python
import sys
print(json.dumps({"test": "message"}), file=sys.stdout, flush=True)
```

### Cannot Query Logs

**Check**:
1. Log Analytics Workspace exists
2. Application Insights connected to workspace
3. Using correct table name (`traces`, `customEvents`, etc.)
4. Time range includes your logs

**Query**:
```kusto
// Check if any logs exist
traces
| where timestamp > ago(1d)
| take 10
```

### High Costs

**Solutions**:
1. Reduce log level (INFO instead of DEBUG)
2. Set daily cap
3. Filter noisy packages
4. Sample high-volume logs
5. Reduce retention period

### Missing Context Fields

**Check**:
```python
# Ensure bind() is called
logger = get_logger().bind(
    task_id=task_id,
    user_id=user_id
)

# Not just:
logger = get_logger()
```

### Local Development Issues

**Check**:
1. `logs/` directory permissions
2. Disk space available
3. Environment set to `development`

**Reset**:
```python
from logging_config import setup_logging
setup_logging(environment='development')
```

---

## Quick Reference

### Setup

```python
from logging_config import setup_logging, get_logger

# Application start
setup_logging(environment='production')

# Get logger
logger = get_logger()
```

### Basic Logging

```python
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Structured Logging

```python
logger.info(
    "Event occurred",
    key1="value1",
    key2=123,
    key3=True
)
```

### Context Binding

```python
logger = get_logger().bind(
    task_id="abc-123",
    user_id="user_789"
)
```

### Exception Logging

```python
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")
```

### KQL Query

```kusto
logs
| where user_id == "user_123"
| where level == "ERROR"
| order by timestamp desc
```

---

## Additional Resources

- [Loguru Documentation](https://loguru.readthedocs.io/)
- [Azure Monitor Documentation](https://docs.microsoft.com/azure/azure-monitor/)
- [KQL Reference](https://docs.microsoft.com/azure/data-explorer/kusto/query/)
- [Application Insights](https://docs.microsoft.com/azure/azure-monitor/app/app-insights-overview)

---

**Last Updated**: 2025-10-30  
**Version**: 1.0  
**Maintainer**: PixCrawler Team
