# JobOrchestrator Quick Reference

## Quick Start

### 1. Define Workflow Steps

```python
from backend.services import WorkflowStep

async def my_task():
    # Do work
    return {"result": "data"}

step = WorkflowStep(
    name="My Task",
    task_type="process",
    handler=my_task,
    max_retries=3,
    timeout=300,
    estimated_duration=60,
)
```

### 2. Create Workflow Definition

```python
from backend.services import WorkflowDefinition

workflow = WorkflowDefinition(
    name="My Workflow",
    steps=[step1, step2, step3],
    max_recovery_attempts=3,
)
```

### 3. Execute Workflow

```python
from backend.services import JobOrchestrator

orchestrator = JobOrchestrator(workflow_repo, task_repo, job_repo)

# Create workflow
workflow = await orchestrator.create_workflow(
    job_id=1,
    workflow_def=workflow_def,
)

# Execute workflow
result = await orchestrator.execute_workflow(
    workflow_id=workflow.id,
    workflow_def=workflow_def,
)
```

## Common Patterns

### Pattern 1: Sequential Tasks

```python
steps = [
    WorkflowStep(name="Step 1", task_type="task", handler=handler1),
    WorkflowStep(name="Step 2", task_type="task", handler=handler2, dependencies=[0]),
    WorkflowStep(name="Step 3", task_type="task", handler=handler3, dependencies=[1]),
]
```

### Pattern 2: Parallel Tasks

```python
steps = [
    WorkflowStep(name="Download", task_type="download", handler=download),
    WorkflowStep(name="Validate", task_type="validate", handler=validate, dependencies=[0]),
    WorkflowStep(name="Process A", task_type="process", handler=process_a, dependencies=[1]),
    WorkflowStep(name="Process B", task_type="process", handler=process_b, dependencies=[1]),
    WorkflowStep(name="Merge", task_type="merge", handler=merge, dependencies=[2, 3]),
]
```

### Pattern 3: With Error Recovery

```python
# Monitor workflow
progress = await orchestrator.get_workflow_progress(workflow_id)

# If failed, recover
if progress['status'] == 'failed':
    await orchestrator.recover_workflow(
        workflow_id=workflow_id,
        from_step=progress['current_step'],
    )
```

## API Reference

### Create Workflow
```python
workflow = await orchestrator.create_workflow(
    job_id: int,
    workflow_def: WorkflowDefinition,
    metadata: Optional[Dict] = None,
) -> WorkflowState
```

### Get Workflow
```python
workflow = await orchestrator.get_workflow(workflow_id: int) -> Optional[WorkflowState]
workflow = await orchestrator.get_workflow_by_job(job_id: int) -> Optional[WorkflowState]
```

### Execute Workflow
```python
result = await orchestrator.execute_workflow(
    workflow_id: int,
    workflow_def: WorkflowDefinition,
) -> WorkflowState
```

### Control Workflow
```python
await orchestrator.start_workflow(workflow_id: int) -> WorkflowState
await orchestrator.pause_workflow(workflow_id: int) -> WorkflowState
await orchestrator.cancel_workflow(workflow_id: int) -> WorkflowState
await orchestrator.recover_workflow(workflow_id: int, from_step: int) -> WorkflowState
```

### Monitor Workflow
```python
progress = await orchestrator.get_workflow_progress(workflow_id: int) -> Dict
active = await orchestrator.get_active_workflows() -> List[WorkflowState]
failed = await orchestrator.get_failed_workflows() -> List[WorkflowState]
recoverable = await orchestrator.get_recoverable_workflows() -> List[WorkflowState]
```

## Workflow States

| State | Description |
|-------|-------------|
| `pending` | Workflow created, not started |
| `running` | Workflow executing |
| `paused` | Workflow paused |
| `completed` | Workflow completed successfully |
| `failed` | Workflow failed |
| `cancelled` | Workflow cancelled |
| `recovering` | Workflow recovering from failure |

## Task States

| State | Description |
|-------|-------------|
| `pending` | Task waiting to start |
| `queued` | Task queued for execution |
| `running` | Task executing |
| `completed` | Task completed successfully |
| `failed` | Task failed |
| `retrying` | Task retrying after failure |
| `skipped` | Task skipped |
| `cancelled` | Task cancelled |

## Progress Information

```python
progress = await orchestrator.get_workflow_progress(workflow_id)

# Returns:
{
    "workflow_id": 1,
    "job_id": 1,
    "status": "running",
    "progress": 50,              # 0-100%
    "current_step": 1,           # Current step index
    "total_steps": 3,            # Total steps
    "completed_tasks": 1,        # Completed tasks
    "failed_tasks": 0,           # Failed tasks
    "running_tasks": 1,          # Running tasks
    "total_tasks": 3,            # Total tasks
    "recovery_attempts": 0,      # Recovery attempts
    "max_recovery_attempts": 3,  # Max recovery attempts
    "started_at": "2024-01-01T00:00:00Z",
    "completed_at": None,
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

## Error Handling

### Retry Logic
- Automatic retry on task failure
- Exponential backoff: 1s, 2s, 4s, 8s, ...
- Configurable max retries per task

### Recovery
- Recover from specific step
- Resets tasks from recovery point
- Increments recovery attempt counter

### Timeout
- Tasks can have timeout
- Raises `asyncio.TimeoutError` on timeout
- Counts as failure, triggers retry

## Example: Dataset Build Workflow

```python
from backend.services import JobOrchestrator, WorkflowStep, WorkflowDefinition

# Define steps
async def download():
    # Download images
    return {"count": 1000}

async def validate():
    # Validate images
    return {"valid": 950}

async def deduplicate():
    # Remove duplicates
    return {"unique": 900}

async def label():
    # Generate labels
    return {"labeled": 900}

async def store():
    # Store dataset
    return {"stored": 900}

# Create workflow
steps = [
    WorkflowStep("Download", "download", download, max_retries=3, estimated_duration=300),
    WorkflowStep("Validate", "validate", validate, max_retries=2, dependencies=[0], estimated_duration=200),
    WorkflowStep("Deduplicate", "deduplicate", deduplicate, max_retries=2, dependencies=[1], estimated_duration=150),
    WorkflowStep("Label", "label", label, max_retries=1, dependencies=[2], estimated_duration=100),
    WorkflowStep("Store", "storage", store, max_retries=2, dependencies=[3], estimated_duration=200),
]

workflow_def = WorkflowDefinition("Dataset Build", steps, max_recovery_attempts=3)

# Execute
orchestrator = JobOrchestrator(workflow_repo, task_repo, job_repo)
workflow = await orchestrator.create_workflow(job_id=1, workflow_def=workflow_def)
result = await orchestrator.execute_workflow(workflow.id, workflow_def)

# Monitor
progress = await orchestrator.get_workflow_progress(workflow.id)
print(f"Status: {progress['status']}, Progress: {progress['progress']}%")
```

## Best Practices

1. **Keep steps focused** - Each step should do one thing
2. **Set realistic timeouts** - Account for network/processing delays
3. **Use dependencies** - Properly define task dependencies
4. **Monitor progress** - Check workflow progress regularly
5. **Handle errors** - Implement proper error handling in handlers
6. **Test workflows** - Test before production use
7. **Set recovery limits** - Don't allow infinite recovery attempts
8. **Log operations** - Add logging to step handlers
9. **Use metadata** - Store workflow context in metadata
10. **Clean up resources** - Clean up resources in error handlers

## Troubleshooting

### Workflow stuck in "running" state
- Check task logs for errors
- Verify task dependencies
- Check timeout settings
- Try recovery from current step

### Tasks failing repeatedly
- Increase max_retries
- Increase timeout
- Check handler implementation
- Verify dependencies

### Recovery not working
- Check recovery_attempts < max_recovery_attempts
- Verify from_step is valid
- Check task status after recovery

### Progress not updating
- Verify orchestrator.get_workflow_progress() call
- Check database connection
- Verify workflow_id is correct

## Performance Tips

1. **Batch operations** - Process data in batches
2. **Use timeouts** - Prevent hanging tasks
3. **Monitor resources** - Track CPU, memory, disk
4. **Optimize handlers** - Keep handlers efficient
5. **Use Celery** - Offload heavy work to workers
6. **Cache results** - Avoid redundant processing
7. **Index database** - Ensure proper indexes on workflow tables
8. **Clean up old workflows** - Archive completed workflows

## Integration with Celery

```python
from celery_core.app import get_celery_app

app = get_celery_app()

async def my_task():
    # Dispatch to Celery
    task = app.send_task('backend.tasks.my_task', args=[arg1, arg2])
    
    # Wait for completion
    result = task.get(timeout=300)
    return result
```

## Database Queries

### Get active workflows
```python
active = await orchestrator.get_active_workflows()
```

### Get failed workflows
```python
failed = await orchestrator.get_failed_workflows()
```

### Get recoverable workflows
```python
recoverable = await orchestrator.get_recoverable_workflows()
```

### Get workflow by job
```python
workflow = await orchestrator.get_workflow_by_job(job_id=1)
```

## Metrics and Monitoring

Track workflow metrics:
- Total workflows created
- Workflows completed successfully
- Workflows failed
- Average completion time
- Task retry rate
- Recovery success rate

## Support

For issues or questions:
1. Check documentation: `backend/docs/JOB_ORCHESTRATOR.md`
2. Review examples: `backend/tests/services/test_job_orchestrator.py`
3. Check logs for error messages
4. Verify database schema
5. Test with simple workflow first
