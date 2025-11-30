# Dataset Processing Pipeline

## Overview

The `DatasetProcessingPipeline` orchestrates the complete dataset creation workflow, integrating storage, validation, job orchestration, and quality reporting. It manages an 8-step workflow that transforms raw crawled images into a high-quality, organized dataset.

## Architecture

### Components

```
DatasetProcessingPipeline
├── JobOrchestrator (workflow management)
├── CrawlJobService (image crawling)
├── StorageService (storage operations)
├── MetricsService (metrics tracking)
├── CheckManager (validation)
├── LabelGenerator (label generation)
└── StorageProvider (hot/cold storage)
```

### Workflow Steps

1. **Setup Workspace** - Create temporary directory structure
2. **Crawl Images** - Download images with real-time validation
3. **Validate Images** - Progressive validation and filtering
4. **Deduplicate Images** - Detect and remove duplicates
5. **Generate Labels** - Create labels for images
6. **Storage Tiering** - Move to hot/cold storage
7. **Quality Report** - Generate quality metrics
8. **Cleanup** - Remove temporary workspace

## Configuration

### PipelineConfig

```python
from backend.services import PipelineConfig

config = PipelineConfig(
    enable_validation=True,           # Enable image validation
    enable_deduplication=True,        # Enable duplicate detection
    enable_labeling=False,            # Enable label generation
    enable_storage_tiering=True,      # Enable hot/cold storage
    enable_quality_report=True,       # Enable quality reporting
    hot_storage_threshold=1000,       # Images to keep in hot storage
    temp_workspace_cleanup=True,      # Clean up temp workspace
    validation_mode="strict",         # Validation mode
    max_concurrent_validations=5,     # Concurrent validation tasks
)
```

## Usage

### 1. Initialize Pipeline

```python
from backend.services import (
    DatasetProcessingPipeline,
    PipelineConfig,
    JobOrchestrator,
)
from backend.services.crawl_job import CrawlJobService
from backend.services.storage import StorageService
from backend.services.metrics import MetricsService

# Create configuration
config = PipelineConfig(
    enable_validation=True,
    enable_deduplication=True,
    enable_labeling=False,
    enable_storage_tiering=True,
)

# Initialize services
orchestrator = JobOrchestrator(workflow_repo, task_repo, job_repo)
crawl_job_service = CrawlJobService(...)
storage_service = StorageService(...)
metrics_service = MetricsService(...)

# Create pipeline
pipeline = DatasetProcessingPipeline(
    orchestrator=orchestrator,
    crawl_job_service=crawl_job_service,
    storage_service=storage_service,
    metrics_service=metrics_service,
    config=config,
)
```

### 2. Create Pipeline Workflow

```python
# Create workflow for a job
workflow = await pipeline.create_pipeline_workflow(
    job_id=1,
    dataset_name="Animals Dataset",
)

print(f"Workflow created: {workflow.id}")
```

### 3. Execute Pipeline

```python
# Execute the complete pipeline
completed_workflow, metrics = await pipeline.execute_pipeline(
    workflow_id=workflow.id,
)

print(f"Pipeline completed in {metrics.total_duration}s")
print(f"Quality score: {metrics.quality_score}%")
```

### 4. Monitor Progress

```python
# Get detailed progress
progress = await pipeline.get_pipeline_progress(workflow_id=workflow.id)

print(f"Status: {progress['status']}")
print(f"Progress: {progress['progress']}%")
print(f"Current step: {progress['current_step']}/{progress['total_steps']}")

# Get metrics
metrics = await pipeline.get_pipeline_metrics()
print(f"Images crawled: {metrics.images_crawled}")
print(f"Valid images: {metrics.valid_images}")
print(f"Unique images: {metrics.unique_images}")
```

## Workflow Steps

### Step 1: Setup Workspace

Creates temporary directory structure for processing:

```
temp_workspace/
├── crawled/        # Raw crawled images
├── validated/      # Validated images
├── deduplicated/   # Deduplicated images
└── labeled/        # Labeled images
```

**Configuration:**
- Retries: 2
- Duration: ~30 seconds
- Dependencies: None

### Step 2: Crawl Images

Downloads images from configured sources with real-time validation:

**Features:**
- Multi-source crawling
- Real-time validation filtering
- Progress tracking
- Error recovery

**Configuration:**
- Retries: 3
- Timeout: 30 minutes
- Duration: ~10 minutes
- Dependencies: Setup Workspace

### Step 3: Validate Images

Progressive validation of crawled images:

**Validation Checks:**
- Image format validation
- Minimum size requirements
- Corruption detection
- Format compatibility

**Configuration:**
- Retries: 2
- Duration: ~5 minutes
- Dependencies: Crawl Images
- Optional: Can be disabled

### Step 4: Deduplicate Images

Detects and removes duplicate images:

**Features:**
- Hash-based duplicate detection
- Perceptual hashing for similar images
- Batch processing
- Detailed duplicate reporting

**Configuration:**
- Retries: 2
- Duration: ~3 minutes
- Dependencies: Validate Images
- Optional: Can be disabled

### Step 5: Generate Labels

Creates labels for images:

**Formats:**
- Text files (.txt)
- JSON format
- Custom formats

**Configuration:**
- Retries: 1
- Duration: ~2 minutes
- Dependencies: Deduplicate Images
- Optional: Can be disabled

### Step 6: Storage Tiering

Moves images to hot/cold storage:

**Hot Storage:**
- Fast access tier
- Default: First 1000 images
- Use case: Recent/important images

**Cold Storage:**
- Archive tier
- Cost-effective
- Use case: Historical/backup images

**Configuration:**
- Retries: 2
- Duration: ~5 minutes
- Dependencies: Generate Labels
- Optional: Can be disabled

### Step 7: Quality Report

Generates comprehensive quality metrics:

**Metrics:**
- Quality score (%)
- Total images processed
- Valid/invalid count
- Duplicate statistics
- Processing duration
- Storage distribution

**Configuration:**
- Retries: 1
- Duration: ~1 minute
- Dependencies: Storage Tiering
- Optional: Can be disabled

### Step 8: Cleanup

Removes temporary workspace:

**Operations:**
- Delete temp directories
- Release resources
- Log cleanup status

**Configuration:**
- Retries: 1
- Duration: ~30 seconds
- Dependencies: Quality Report
- Always runs

## Metrics

### PipelineMetrics

Comprehensive metrics collected during execution:

```python
metrics = PipelineMetrics()

# Timing
metrics.start_time          # Pipeline start time
metrics.end_time            # Pipeline end time
metrics.total_duration      # Total execution time

# Crawling
metrics.images_crawled      # Total images downloaded
metrics.crawl_duration      # Crawling duration

# Validation
metrics.images_validated    # Total images validated
metrics.valid_images        # Valid image count
metrics.invalid_images      # Invalid image count
metrics.validation_duration # Validation duration

# Deduplication
metrics.duplicates_found    # Duplicates detected
metrics.duplicates_removed  # Duplicates removed
metrics.unique_images       # Unique image count
metrics.dedup_duration      # Deduplication duration

# Labeling
metrics.images_labeled      # Images with labels
metrics.labeling_duration   # Labeling duration

# Storage
metrics.hot_storage_count   # Images in hot storage
metrics.cold_storage_count  # Images in cold storage
metrics.storage_duration    # Storage tiering duration

# Quality
metrics.quality_score       # Quality percentage (0-100)
metrics.report_generated    # Report generation status
```

### Accessing Metrics

```python
# Get metrics during execution
metrics = await pipeline.get_pipeline_metrics()

# Get metrics as dictionary
metrics_dict = metrics.to_dict()

# Get metrics from progress
progress = await pipeline.get_pipeline_progress(workflow_id=1)
metrics = progress["metrics"]
```

## Real-time Validation

The pipeline implements real-time validation during crawling:

### Features

1. **Progressive Filtering** - Invalid images filtered during crawling
2. **Batch Validation** - Concurrent validation of image batches
3. **Real-time Updates** - Progress updates via Supabase
4. **Error Recovery** - Automatic retry on validation failures

### Configuration

```python
config = PipelineConfig(
    enable_validation=True,
    validation_mode="strict",  # strict, lenient, report-only
    max_concurrent_validations=5,
)
```

### Validation Modes

- **strict**: Fail on any validation error
- **lenient**: Log errors but continue
- **report-only**: Only report, don't filter

## Error Handling

### Retry Logic

Each step has configurable retry logic:

```python
WorkflowStep(
    name="Step Name",
    handler=handler_func,
    max_retries=3,          # Retry up to 3 times
    timeout=300,            # 5 minute timeout
)
```

### Recovery

Pipeline can be recovered from failures:

```python
# Recover from specific step
await orchestrator.recover_workflow(
    workflow_id=workflow.id,
    from_step=3,  # Restart from step 3
)
```

## Integration Examples

### Example 1: Basic Pipeline

```python
# Minimal configuration
config = PipelineConfig(
    enable_validation=True,
    enable_deduplication=True,
    enable_labeling=False,
    enable_storage_tiering=True,
)

pipeline = DatasetProcessingPipeline(
    orchestrator=orchestrator,
    crawl_job_service=crawl_job_service,
    storage_service=storage_service,
    metrics_service=metrics_service,
    config=config,
)

# Execute
workflow = await pipeline.create_pipeline_workflow(job_id=1, dataset_name="Dataset")
result, metrics = await pipeline.execute_pipeline(workflow.id)
```

### Example 2: Full-Featured Pipeline

```python
# Complete configuration
config = PipelineConfig(
    enable_validation=True,
    enable_deduplication=True,
    enable_labeling=True,
    enable_storage_tiering=True,
    enable_quality_report=True,
    hot_storage_threshold=500,
    validation_mode="strict",
)

pipeline = DatasetProcessingPipeline(
    orchestrator=orchestrator,
    crawl_job_service=crawl_job_service,
    storage_service=storage_service,
    metrics_service=metrics_service,
    config=config,
)

# Execute with monitoring
workflow = await pipeline.create_pipeline_workflow(job_id=1, dataset_name="Full Dataset")
result, metrics = await pipeline.execute_pipeline(workflow.id)

# Check results
print(f"Quality Score: {metrics.quality_score}%")
print(f"Unique Images: {metrics.unique_images}")
print(f"Hot Storage: {metrics.hot_storage_count}")
print(f"Cold Storage: {metrics.cold_storage_count}")
```

### Example 3: Custom Configuration

```python
# Custom configuration
config = PipelineConfig(
    enable_validation=True,
    enable_deduplication=True,
    enable_labeling=False,
    enable_storage_tiering=True,
    enable_quality_report=True,
    hot_storage_threshold=2000,  # Keep 2000 in hot storage
    temp_workspace_cleanup=True,
    validation_mode="lenient",
    max_concurrent_validations=10,
)

pipeline = DatasetProcessingPipeline(
    orchestrator=orchestrator,
    crawl_job_service=crawl_job_service,
    storage_service=storage_service,
    metrics_service=metrics_service,
    config=config,
)
```

## Performance Considerations

### Optimization Tips

1. **Batch Processing** - Process images in batches
2. **Concurrent Validation** - Increase `max_concurrent_validations`
3. **Storage Tiering** - Adjust `hot_storage_threshold` based on access patterns
4. **Timeout Settings** - Set realistic timeouts for each step
5. **Resource Monitoring** - Monitor CPU, memory, disk usage

### Scalability

- **Horizontal**: Distribute crawling across multiple workers
- **Vertical**: Increase concurrent validation tasks
- **Storage**: Use cloud storage for scalability

## Troubleshooting

### Pipeline Stuck in Running State

1. Check task logs for errors
2. Verify storage connectivity
3. Check timeout settings
4. Try recovery from current step

### Validation Failures

1. Check image format compatibility
2. Verify minimum size requirements
3. Check disk space
4. Review validation mode settings

### Storage Tiering Issues

1. Verify storage provider configuration
2. Check storage credentials
3. Verify container/bucket exists
4. Check network connectivity

### Quality Score Low

1. Review validation settings
2. Check image sources
3. Verify deduplication is working
4. Check for corrupted images

## API Reference

### DatasetProcessingPipeline

#### Methods

- `create_pipeline_workflow(job_id, dataset_name)` - Create workflow
- `execute_pipeline(workflow_id)` - Execute pipeline
- `get_pipeline_progress(workflow_id)` - Get progress
- `get_pipeline_metrics()` - Get metrics

#### Properties

- `config` - Pipeline configuration
- `metrics` - Current metrics
- `temp_workspace` - Temporary workspace path

### PipelineConfig

#### Parameters

- `enable_validation` - Enable validation step
- `enable_deduplication` - Enable deduplication step
- `enable_labeling` - Enable labeling step
- `enable_storage_tiering` - Enable storage tiering
- `enable_quality_report` - Enable quality reporting
- `hot_storage_threshold` - Images in hot storage
- `temp_workspace_cleanup` - Clean up temp workspace
- `validation_mode` - Validation mode
- `max_concurrent_validations` - Concurrent validation tasks

### PipelineMetrics

#### Properties

All metrics are read-only and updated during execution.

## Best Practices

1. **Monitor Progress** - Regularly check pipeline progress
2. **Handle Errors** - Implement proper error handling
3. **Test Workflows** - Test with small datasets first
4. **Set Realistic Timeouts** - Account for network delays
5. **Use Appropriate Validation Mode** - Choose based on requirements
6. **Monitor Resources** - Track CPU, memory, disk usage
7. **Archive Old Datasets** - Move completed datasets to cold storage
8. **Backup Metrics** - Store metrics for analysis

## Conclusion

The DatasetProcessingPipeline provides a robust, production-ready solution for managing complex dataset creation workflows. It combines state persistence, error recovery, real-time monitoring, and flexible configuration to ensure reliable and efficient dataset creation.
