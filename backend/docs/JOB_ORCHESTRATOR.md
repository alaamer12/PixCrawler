# Job Orchestrator Service

## Overview

The `JobOrchestrator` service manages complex multi-step workflows for dataset builds. It provides:

- **Workflow Definition**: Define multi-step workflows with dependencies
- **State Persistence**: Save workflow state for recovery and monitoring
- **Task Execution**: Execute tasks with retry logic and timeout support
- **Progress Tracking**: Real-time progress updates and monitoring
- **Error Recovery**: Automatic recovery from failures with configurable retry attempts
- **Dependency Management**: Handle task dependencies and execution ordering

## Architecture

### Components

1. **WorkflowDefinition**: Defines a complete workflow with steps
2. **WorkflowStep**: Represents a single step in a workflow
3. **JobOrchestrator**: Main orchestration service
4. **WorkflowState**: Persists workflow execution state
5. **WorkflowTask**: Tracks individual task execution

### Database Models

```
WorkflowState
├── id: Primary key
├── job_id: Reference to CrawlJob
├── status: pending, running, paused, completed, failed, cancelled, recovering
├── current_step: Current step index
├── total_steps: Total number of steps
├── progress: Progress percentage (0-100)
├── metadata: Workflow-specific metadata
├── recovery_attempts: Number of recovery attempts
└── tasks: List of WorkflowTask objects

WorkflowTask
├── id: Primary key
├── workflow_id: Reference to WorkflowState
├── task_name: Name of the task
├── task_type: Type of task (download, validate, etc.)
├── status: pending, queued, running, completed, failed, retrying, skipped, cancelled
├── step_index: Step index in workflow
├── celery_task_id: Celery task ID for monitoring
├── retry_count: Number of retry attempts
├── dependencies: List of task IDs this task depends on
├── result: Task result data
└── error_message: Error message if failed
```

## Usage

### 1. Define a Workflow

```python
from backend.services import JobOrchestrator, WorkflowStep, WorkflowDefinition

# Define workflow steps
async def download_images():
    """Download images from sources."""
    # Implementation
    return {"downloaded": 1000}

async def validate_images():
    """Validate downloaded images."""
    # Implementation
    return {"valid": 950}

async def deduplicate_images():
    """Remove duplicate images."""
    # Implementation
    return {"deduplicated": 50}

# Create workflow steps
steps = [
    WorkflowStep(
        name="Download Images",
        task_type="download",
        handler=download_images,
        max_retries=3,
        estimated_duration=300,
    ),
    WorkflowStep(
        name="Validate Images",
        task_type="validate",
        handler=validate_images,
        max_retries=2,
        dependencies=[0],  # Depends on step 0
        estimated_duration=200,
    ),
    WorkflowStep(
        name="Deduplicate Images",
        task_type="deduplicate",
        handler=deduplicate_images,
        max_retries=2,
        dependencies=[1],  # Depends on step 1
        estimated_duration=150,
    ),
]

# Create workflow definition
workflow_def = WorkflowDefinition(
    name="Dataset Build Workflow",
    steps=steps,
    max_recovery_attempts=3,
)
```

### 2. Create and Execute Workflow

```python
from backend.repositories import (
    WorkflowStateRepository,
    WorkflowTaskRepository,
    CrawlJobRepository,
)

# Initialize repositories
workflow_repo = WorkflowStateRepository(session)
task_repo = WorkflowTaskRepository(session)
job_repo = CrawlJobRepository(session)

# Create orchestrator
orchestrator = JobOrchestrator(workflow_repo, task_repo, job_repo)

# Create workflow
workflow = await orchestrator.create_workflow(
    job_id=1,
    workflow_def=workflow_def,
    metadata={"dataset_name": "animals"}
)

# Execute workflow
completed_workflow = await orchestrator.execute_workflow(
    workflow_id=workflow.id,
    workflow_def=workflow_def
)
```

### 3. Monitor Workflow Progress

```python
# Get workflow progress
progress = await orchestrator.get_workflow_progress(workflow_id=1)

print(f"Status: {progress['status']}")
print(f"Progress: {progress['progress']}%")
print(f"Current Step: {progress['current_step']}/{progress['total_steps']}")
print(f"Completed Tasks: {progress['completed_tasks']}")
print(f"Failed Tasks: {progress['failed_tasks']}")

# Get all active workflows
active_workflows = await orchestrator.get_active_workflows()

# Get failed workflows
failed_workflows = await orchestrator.get_failed_workflows()

# Get recoverable workflows
recoverable = await orchestrator.get_recoverable_workflows()
```

### 4. Handle Workflow Lifecycle

```python
# Pause workflow
await orchestrator.pause_workflow(workflow_id=1)

# Resume workflow (by recovering from current step)
await orchestrator.recover_workflow(
    workflow_id=1,
    from_step=2
)

# Cancel workflow
await orchestrator.cancel_workflow(workflow_id=1)
```

## Features

### Retry Logic

Tasks automatically retry on failure with exponential backoff:

```python
WorkflowStep(
    name="Download Images",
    task_type="download",
    handler=download_images,
    max_retries=3,  # Retry up to 3 times
    timeout=300,    # 5 minute timeout
)
```

Retry delays: 1s, 2s, 4s, 8s, etc. (2^attempt seconds)

### Dependency Management

Tasks can depend on previous tasks:

```python
WorkflowStep(
    name="Validate Images",
    task_type="validate",
    handler=validate_images,
    dependencies=[0],  # Must complete step 0 first
)
```

### State Persistence

Workflow state is persisted to database for recovery:

- Workflow status and progress
- Task status and results
- Error messages and recovery attempts
- Timestamps for monitoring

### Error Recovery

Workflows can be recovered from failures:

```python
# Recover from step 2
await orchestrator.recover_workflow(
    workflow_id=1,
    from_step=2
)
```

Recovery resets tasks from the specified step and increments recovery attempts.

### Real-time Progress Tracking

Get detailed progress information:

```python
progress = await orchestrator.get_workflow_progress(workflow_id=1)

# Returns:
{
    "workflow_id": 1,
    "job_id": 1,
    "status": "running",
    "progress": 50,
    "current_step": 1,
    "total_steps": 3,
    "completed_tasks": 1,
    "failed_tasks": 0,
    "running_tasks": 1,
    "recovery_attempts": 0,
    "tasks": [
        {
            "id": 1,
            "name": "Download Images",
            "type": "download",
            "status": "completed",
            "retry_count": 0,
            "error_message": None,
        },
        ...
    ]
}
```

## Workflow States

```
pending ──→ running ──→ completed
             ├──→ paused ──→ running
             ├──→ failed ──→ recovering ──→ running
             └──→ cancelled
```

## Task States

```
pending ──→ queued ──→ running ──→ completed
            ├──→ failed ──→ retrying ──→ queued
            └──→ skipped
```

## Error Handling

### Task Failures

Tasks fail after max retries:

```python
try:
    result = await orchestrator.execute_workflow(workflow_id=1, workflow_def=workflow_def)
except Exception as e:
    # Workflow failed
    # Get failed workflow for recovery
    failed_workflow = await orchestrator.get_workflow(workflow_id=1)
    
    # Recover from specific step
    await orchestrator.recover_workflow(workflow_id=1, from_step=2)
```

### Timeout Handling

Tasks with timeout support:

```python
WorkflowStep(
    name="Download Images",
    task_type="download",
    handler=download_images,
    timeout=300,  # 5 minute timeout
)
```

## Integration with Celery

Tasks can be dispatched to Celery workers:

```python
# In workflow step handler
from celery_core.app import get_celery_app

app = get_celery_app()

async def download_images():
    # Dispatch to Celery
    task = app.send_task('backend.tasks.download_images', args=[job_id])
    
    # Wait for completion
    result = task.get(timeout=300)
    return result
```

## Best Practices

1. **Keep Steps Focused**: Each step should do one thing well
2. **Set Realistic Timeouts**: Account for network delays and processing time
3. **Use Dependencies**: Properly define task dependencies
4. **Monitor Progress**: Regularly check workflow progress
5. **Handle Errors**: Implement proper error handling in step handlers
6. **Test Workflows**: Test workflow definitions before production use
7. **Set Recovery Limits**: Don't allow infinite recovery attempts

## Example: Complete Dataset Build Workflow

```python
from backend.services import JobOrchestrator, WorkflowStep, WorkflowDefinition

# Define workflow steps
async def download_step():
    # Download images
    return {"downloaded": 1000}

async def validate_step():
    # Validate images
    return {"valid": 950}

async def deduplicate_step():
    # Remove duplicates
    return {"deduplicated": 50}

async def label_step():
    # Generate labels
    return {"labeled": 900}

async def store_step():
    # Move to storage
    return {"stored": 900}

# Create workflow
steps = [
    WorkflowStep(
        name="Download Images",
        task_type="download",
        handler=download_step,
        max_retries=3,
        estimated_duration=300,
    ),
    WorkflowStep(
        name="Validate Images",
        task_type="validate",
        handler=validate_step,
        max_retries=2,
        dependencies=[0],
        estimated_duration=200,
    ),
    WorkflowStep(
        name="Deduplicate Images",
        task_type="deduplicate",
        handler=deduplicate_step,
        max_retries=2,
        dependencies=[1],
        estimated_duration=150,
    ),
    WorkflowStep(
        name="Generate Labels",
        task_type="label",
        handler=label_step,
        max_retries=1,
        dependencies=[2],
        estimated_duration=100,
    ),
    WorkflowStep(
        name="Store Dataset",
        task_type="storage",
        handler=store_step,
        max_retries=2,
        dependencies=[3],
        estimated_duration=200,
    ),
]

workflow_def = WorkflowDefinition(
    name="Complete Dataset Build",
    steps=steps,
    max_recovery_attempts=3,
)

# Execute workflow
orchestrator = JobOrchestrator(workflow_repo, task_repo, job_repo)
workflow = await orchestrator.create_workflow(job_id=1, workflow_def=workflow_def)
result = await orchestrator.execute_workflow(workflow.id, workflow_def)
```

## API Reference

### JobOrchestrator Methods

- `create_workflow(job_id, workflow_def, metadata)` - Create new workflow
- `get_workflow(workflow_id)` - Get workflow by ID
- `get_workflow_by_job(job_id)` - Get workflow by job ID
- `start_workflow(workflow_id)` - Start workflow execution
- `execute_workflow(workflow_id, workflow_def)` - Execute complete workflow
- `pause_workflow(workflow_id)` - Pause workflow
- `cancel_workflow(workflow_id)` - Cancel workflow
- `recover_workflow(workflow_id, from_step)` - Recover from failure
- `get_workflow_progress(workflow_id)` - Get progress details
- `get_active_workflows()` - Get all active workflows
- `get_failed_workflows()` - Get all failed workflows
- `get_recoverable_workflows()` - Get all recoverable workflows
