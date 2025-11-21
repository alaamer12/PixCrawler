# Temporary Storage Cleanup System

## Overview

The Temporary Storage Cleanup System is a comprehensive solution for managing temporary storage files in the PixCrawler backend. It automatically cleans up temporary files across various scenarios to prevent storage overflow and maintain system performance.

## Features

### ✅ Cleanup Scenarios Supported

1. **Normal Cleanup** - Delete temp files after chunk completion
2. **Crash Recovery** - Clean temp files for failed chunks/jobs  
3. **Emergency Cleanup** - Trigger cleanup at 95% storage threshold
4. **Orphaned Files** - Detect and delete orphaned files
5. **Scheduled Cleanup** - Periodic cleanup via Celery Beat
6. **Manual Triggers** - API endpoints for manual cleanup operations

### ✅ Key Components

- **TempStorageCleanupService** - Core cleanup service with all scenarios
- **OrphanedFileDetector** - Intelligent orphaned file detection
- **Celery Tasks** - Background cleanup execution
- **API Endpoints** - Manual cleanup triggers and monitoring
- **Configuration** - Comprehensive settings with validation
- **Comprehensive Tests** - Full test coverage for all scenarios

## Architecture

```
backend/
├── services/
│   └── temp_storage_cleanup.py          # Core cleanup service
├── tasks/
│   └── temp_storage_cleanup.py          # Celery background tasks
├── api/v1/endpoints/
│   └── temp_storage_cleanup.py          # REST API endpoints
├── core/settings/
│   └── temp_storage_cleanup.py          # Configuration settings
└── tests/
    └── test_temp_storage_cleanup.py     # Comprehensive test suite
```

## Configuration

### Environment Variables

All settings use the `TEMP_STORAGE_CLEANUP_` prefix:

```bash
# Storage thresholds
TEMP_STORAGE_CLEANUP_EMERGENCY_CLEANUP_THRESHOLD=95.0
TEMP_STORAGE_CLEANUP_WARNING_THRESHOLD=85.0

# Cleanup behavior
TEMP_STORAGE_CLEANUP_MAX_ORPHAN_AGE_HOURS=24
TEMP_STORAGE_CLEANUP_CLEANUP_BATCH_SIZE=1000

# Scheduling
TEMP_STORAGE_CLEANUP_SCHEDULED_CLEANUP_INTERVAL_MINUTES=60
TEMP_STORAGE_CLEANUP_EMERGENCY_CHECK_INTERVAL_MINUTES=5

# Safety settings
TEMP_STORAGE_CLEANUP_MIN_FREE_SPACE_GB=1.0
TEMP_STORAGE_CLEANUP_MAX_FILES_PER_CLEANUP=10000
```

### Default Configuration

```python
TempStorageCleanupSettings(
    temp_storage_path=Path("./temp_storage"),
    emergency_cleanup_threshold=95.0,      # Trigger emergency at 95%
    warning_threshold=85.0,                # Log warnings at 85%
    cleanup_batch_size=1000,               # Process 1000 files per batch
    max_orphan_age_hours=24,               # Files older than 24h are orphaned
    scheduled_cleanup_interval_minutes=60,  # Run cleanup every hour
    cleanup_failed_jobs_after_hours=1,     # Clean failed jobs after 1 hour
    enable_storage_monitoring=True,         # Enable continuous monitoring
    log_cleanup_stats=True                 # Log detailed statistics
)
```

## Usage

### 1. Automatic Cleanup (Recommended)

The system runs automatically via Celery Beat with these schedules:

- **Scheduled Cleanup**: Every hour at minute 0
- **Emergency Check**: Every 5 minutes (triggers emergency if needed)
- **Orphaned Cleanup**: Every 6 hours at minute 30

### 2. Manual Cleanup via API

#### Get Storage Statistics
```bash
GET /api/v1/cleanup/stats
```

#### Trigger Emergency Cleanup
```bash
POST /api/v1/cleanup/emergency
```

#### Clean Orphaned Files
```bash
POST /api/v1/cleanup/orphaned
Content-Type: application/json

{
  "max_age_hours": 12
}
```

#### Crash Recovery Cleanup
```bash
# Clean specific job
POST /api/v1/cleanup/crash/123

# Clean all failed jobs
POST /api/v1/cleanup/crash/0
```

#### Scheduled Cleanup
```bash
POST /api/v1/cleanup/scheduled
```

#### Check Task Status
```bash
GET /api/v1/cleanup/task/{task_id}/status
```

#### Health Check
```bash
GET /api/v1/cleanup/health
```

### 3. Programmatic Usage

```python
from backend.services.temp_storage_cleanup import TempStorageCleanupService
from backend.storage.factory import get_storage_provider

# Initialize service
storage_provider = get_storage_provider()
cleanup_service = TempStorageCleanupService(
    storage_provider=storage_provider,
    session=session
)

# Get storage statistics
stats = await cleanup_service.get_storage_stats()

# Trigger emergency cleanup
emergency_stats = await cleanup_service.emergency_cleanup()

# Clean up after chunk completion
chunk_stats = await cleanup_service.cleanup_after_chunk_completion(
    job_id=123,
    chunk_id="abc",
    completed_files=["image1.jpg", "image2.jpg"]
)

# Clean up after crash
crash_stats = await cleanup_service.cleanup_after_crash(job_id=456)

# Clean orphaned files
orphan_stats = await cleanup_service.cleanup_orphaned_files(max_age_hours=24)
```

### 4. Celery Tasks

```python
from backend.tasks.temp_storage_cleanup import (
    task_scheduled_cleanup,
    task_emergency_cleanup,
    task_cleanup_orphaned_files,
    task_cleanup_after_crash,
    task_cleanup_after_chunk
)

# Trigger tasks
task_result = task_emergency_cleanup.delay()
result = task_result.get()  # Wait for completion

# Check task status
task_id = task_result.id
status = task_result.status
```

## Cleanup Logic

### Normal Cleanup (Chunk Completion)
- Triggered after successful chunk processing
- Deletes temp files matching: `job_{job_id}_chunk_{chunk_id}_*`
- Only deletes files that were successfully processed
- Immediate execution for optimal storage usage

### Crash Recovery Cleanup
- Triggered for failed/cancelled/error jobs
- Deletes all temp files for failed jobs: `job_{job_id}_*`
- Can target specific job or all failed jobs
- Waits 1 hour after job failure (configurable)

### Emergency Cleanup
- Triggered when storage exceeds 95% threshold
- Priority cleanup order:
  1. Orphaned files (most aggressive, 1-hour age limit)
  2. Failed job temp files
  3. Oldest temp files (with 10% buffer)
- Continues until storage drops below threshold

### Orphaned File Detection
Files are considered orphaned if:
1. No corresponding active crawl job exists
2. Belong to failed/cancelled jobs older than threshold
3. Have no database references
4. Match pattern but job doesn't exist
5. No job ID pattern and older than threshold

### Scheduled Cleanup
- Comprehensive cleanup combining all scenarios
- Checks for emergency conditions first
- Runs orphaned file cleanup
- Cleans failed job files
- Provides detailed statistics

## Monitoring

### Storage Statistics
```json
{
  "storage_usage_percent": 75.0,
  "emergency_threshold": 95.0,
  "temp_files_count": 1250,
  "temp_files_size_bytes": 104857600,
  "active_jobs_count": 5,
  "failed_jobs_count": 2,
  "orphaned_files_count": 8,
  "orphaned_files_size_bytes": 2097152,
  "cleanup_needed": false
}
```

### Cleanup Statistics
```json
{
  "trigger": "emergency_threshold",
  "start_time": "2024-01-15T10:30:00Z",
  "end_time": "2024-01-15T10:32:15Z",
  "duration_seconds": 135.0,
  "files_scanned": 1500,
  "files_deleted": 800,
  "bytes_freed": 83886080,
  "storage_before_percent": 96.5,
  "storage_after_percent": 78.2,
  "errors": []
}
```

### Health Status
- **Healthy**: Storage < 85%
- **Warning**: Storage 85-95%
- **Critical**: Storage ≥ 95%

## Safety Features

### Batch Processing
- Processes files in configurable batches (default: 1000)
- Prevents memory overflow on large cleanup operations
- Allows for interruption and resumption

### Error Handling
- Comprehensive exception handling
- Continues cleanup even if individual files fail
- Logs all errors for investigation
- Graceful degradation on service failures

### Validation
- Validates file patterns before deletion
- Confirms job status before cleanup
- Respects minimum free space requirements
- Enforces maximum files per cleanup operation

### Dry Run Mode
```python
# Enable dry run mode (logs what would be deleted)
settings.cleanup_dry_run = True
```

### Debugging Mode
```python
# Keep temp files for debugging
settings.keep_temp_files_for_debugging = True
```

## Integration with PixCrawler

### Celery Integration
- Tasks routed to `maintenance` queue with priority 2
- Automatic retry on failures (max 3 retries)
- Rate limiting to prevent system overload
- Integration with Celery Beat for scheduling

### Storage Provider Integration
- Works with all storage providers (local, Azure Blob)
- Uses provider-specific usage statistics when available
- Fallbacks to filesystem stats for local storage
- Supports archive tier considerations

### Database Integration
- Queries crawl job status for cleanup decisions
- Tracks cleanup statistics (optional)
- Integrates with activity logging
- Respects database connection pooling

## Testing

### Comprehensive Test Suite
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **API Tests**: REST endpoint testing
- **Configuration Tests**: Settings validation testing

### Test Coverage
- ✅ All cleanup scenarios
- ✅ Orphaned file detection
- ✅ API endpoints
- ✅ Configuration validation
- ✅ Error handling
- ✅ Integration workflows

### Running Tests
```bash
# Run all cleanup tests
pytest backend/tests/test_temp_storage_cleanup.py -v

# Run specific test class
pytest backend/tests/test_temp_storage_cleanup.py::TestTempStorageCleanupService -v

# Run with coverage
pytest backend/tests/test_temp_storage_cleanup.py --cov=backend.services.temp_storage_cleanup
```

## Performance Considerations

### Scalability
- Handles thousands of temp files efficiently
- Batch processing prevents memory issues
- Parallel cleanup workers (configurable)
- Optimized file system operations

### Resource Usage
- Minimal CPU impact during normal operations
- I/O optimized for large file operations
- Memory usage controlled via batch sizes
- Network impact minimal (local file operations)

### Monitoring Impact
- Storage checks every 30 seconds (configurable)
- Lightweight database queries
- Cached statistics where possible
- Minimal overhead on active operations

## Troubleshooting

### Common Issues

#### High Storage Usage Not Triggering Cleanup
- Check emergency threshold configuration
- Verify Celery workers are running
- Check task routing configuration
- Review cleanup service logs

#### Orphaned Files Not Being Detected
- Verify file naming patterns match expected format
- Check database connectivity
- Review orphan age threshold settings
- Examine file timestamps

#### API Endpoints Not Working
- Verify router is included in main API
- Check authentication requirements
- Review endpoint permissions
- Examine request/response formats

#### Cleanup Tasks Failing
- Check Celery worker logs
- Verify database connections
- Review storage provider configuration
- Examine file system permissions

### Debugging Commands

```bash
# Check storage statistics
curl -X GET http://localhost:8000/api/v1/cleanup/stats

# Check service health
curl -X GET http://localhost:8000/api/v1/cleanup/health

# Trigger manual cleanup (for testing)
curl -X POST http://localhost:8000/api/v1/cleanup/scheduled

# Check Celery task status
celery -A celery_core.app inspect active
celery -A celery_core.app inspect scheduled
```

### Log Analysis

```bash
# Filter cleanup-related logs
grep "temp_storage_cleanup" /var/log/pixcrawler/backend.log

# Monitor cleanup operations
tail -f /var/log/pixcrawler/backend.log | grep -E "(cleanup|storage)"

# Check for errors
grep -E "(ERROR|CRITICAL)" /var/log/pixcrawler/backend.log | grep cleanup
```

## Future Enhancements

### Planned Features
- [ ] Cleanup statistics dashboard
- [ ] Predictive cleanup scheduling
- [ ] Storage usage alerts
- [ ] Cleanup policy templates
- [ ] Integration with monitoring systems

### Potential Optimizations
- [ ] Parallel file processing
- [ ] Incremental cleanup strategies
- [ ] Smart scheduling based on usage patterns
- [ ] Integration with storage lifecycle policies
- [ ] Machine learning for orphan detection

## Contributing

When contributing to the cleanup system:

1. **Follow Patterns**: Use established service/task/API patterns
2. **Add Tests**: Include comprehensive test coverage
3. **Update Documentation**: Keep this README current
4. **Consider Safety**: Prioritize data safety over performance
5. **Monitor Impact**: Consider system resource impact

## License

This cleanup system is part of the PixCrawler project and follows the same MIT license terms.
