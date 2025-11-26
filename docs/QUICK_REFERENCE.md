# Database Schema Quick Reference

## Foreign Key Relationships

```
Profile (1) ──FK── (many) Project
Project (1) ──FK── (many) CrawlJob
CrawlJob (1) ──FK── (many) Image
CrawlJob (1) ──FK── (many) JobChunk
Profile (1) ──FK── (many) ActivityLog
Profile (1) ──FK── (1) CreditAccount
CreditAccount (1) ──FK── (many) CreditTransaction
Profile (1) ──FK── (many) APIKey
Profile (1) ──FK── (many) Notification
Profile (1) ──FK── (1) NotificationPreference
Profile (1) ──FK── (many) UsageMetric
```

## Common Queries

### Get user's projects
```python
user = session.query(Profile).get(user_id)
projects = user.projects  # Eager loaded via selectin
```

### Get project's jobs
```python
project = session.query(Project).get(project_id)
jobs = project.crawl_jobs  # Eager loaded via selectin
```

### Get job's images
```python
job = session.query(CrawlJob).get(job_id)
images = job.images  # Eager loaded via selectin
```

### Get user's credit account
```python
user = session.query(Profile).get(user_id)
account = user.credit_account  # Eager loaded via selectin
transactions = account.transactions  # Eager loaded via selectin
```

## Cascade Delete Behavior

| Delete | Cascades To |
|--------|------------|
| Profile | Projects, ActivityLogs, CreditAccount, APIKeys, Notifications, UsageMetrics |
| Project | CrawlJobs |
| CrawlJob | Images, JobChunks |
| CreditAccount | CreditTransactions |

## Indexes for Performance

### User Queries
- `profiles.user_tier` - Filter by subscription tier
- `projects.user_id` - Find user's projects
- `activity_logs.user_id` - Find user's activities
- `credit_accounts.user_id` - Find user's credit account
- `api_keys.user_id` - Find user's API keys
- `notifications.user_id` - Find user's notifications
- `usage_metrics.user_id` - Find user's usage

### Job Queries
- `crawl_jobs.project_id` - Find project's jobs
- `crawl_jobs.status` - Filter jobs by status
- `crawl_jobs.(project_id, status)` - Find jobs by project and status
- `images.crawl_job_id` - Find job's images
- `job_chunks.job_id` - Find job's chunks
- `job_chunks.status` - Filter chunks by status

### Activity Queries
- `activity_logs.(user_id, timestamp)` - User activity timeline
- `activity_logs.(resource_type, resource_id)` - Find activities by resource

## Constraints

### Status Values
- **CrawlJob**: pending, running, completed, failed, cancelled
- **JobChunk**: pending, processing, completed, failed
- **Notification**: success, info, warning, error
- **APIKey**: active, revoked, expired
- **CreditTransaction**: completed, pending, failed, cancelled

### Ranges
- **JobChunk.priority**: 0-10 (higher = more urgent)
- **CreditAccount.current_balance**: >= 0
- **CreditAccount.monthly_usage**: >= 0
- **UsageMetric.images_processed**: >= 0

## Unique Constraints
- `profiles.email` - One email per user
- `credit_accounts.user_id` - One account per user
- `notification_preferences.user_id` - One preference set per user
- `usage_metrics.(user_id, metric_date)` - One record per user per day

## Deployment Checklist

- [ ] Review migration file: `alembic/versions/003_add_foreign_keys_and_relationships.py`
- [ ] Test migration on staging database
- [ ] Verify no orphaned records exist in production data
- [ ] Back up production database
- [ ] Apply migration: `alembic upgrade head`
- [ ] Verify migration applied: `alembic current`
- [ ] Run integration tests
- [ ] Monitor query performance
- [ ] Update API documentation if needed

## Migration Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade 003

# Rollback one migration
alembic downgrade -1

# Check current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic upgrade head --sql
```

## Model Imports

```python
from backend.models import (
    Profile,
    Project,
    CrawlJob,
    Image,
    ActivityLog,
    JobChunk,
    CreditAccount,
    CreditTransaction,
    APIKey,
    Notification,
    NotificationPreference,
    UsageMetric,
)
```

## Relationship Loading Strategies

All relationships use `lazy="selectin"` for eager loading:
- Avoids N+1 query problems
- Loads related data in separate query
- Optimal for most use cases

Override if needed:
```python
# Lazy load (default SQLAlchemy behavior)
user.projects  # Triggers query

# Joined load
session.query(Profile).options(joinedload(Profile.projects))

# Selectin load (current default)
session.query(Profile).options(selectinload(Profile.projects))
```

## Performance Tips

1. **Use relationships instead of manual joins**
   ```python
   # Good - uses relationship
   user.projects
   
   # Avoid - manual join
   session.query(Project).filter(Project.user_id == user_id)
   ```

2. **Batch operations**
   ```python
   # Good - single commit
   session.add_all([job1, job2, job3])
   session.commit()
   
   # Avoid - multiple commits
   session.add(job1)
   session.commit()
   ```

3. **Use indexes for filtering**
   ```python
   # Good - uses index
   session.query(CrawlJob).filter(CrawlJob.status == 'running')
   
   # Avoid - full table scan
   session.query(CrawlJob).filter(CrawlJob.name.like('%pattern%'))
   ```

4. **Limit result sets**
   ```python
   # Good - limited results
   session.query(ActivityLog).filter(...).limit(50)
   
   # Avoid - loading all records
   session.query(ActivityLog).filter(...)
   ```

## Testing Relationships

```python
# Test FK constraint
def test_fk_constraint():
    job = CrawlJob(project_id=999)  # Invalid project
    with pytest.raises(IntegrityError):
        session.add(job)
        session.commit()

# Test relationship loading
def test_relationship_loading():
    user = create_profile()
    project = create_project(user=user)
    
    # Verify relationship
    assert project in user.projects
    assert project.user == user

# Test cascade delete
def test_cascade_delete():
    user = create_profile()
    project = create_project(user=user)
    
    session.delete(user)
    session.commit()
    
    # Project should be deleted
    assert not session.query(Project).filter_by(id=project.id).first()
```

## Troubleshooting

### Foreign Key Constraint Violation
```
IntegrityError: (psycopg2.errors.ForeignKeyViolation) 
insert or update on table "projects" violates foreign key constraint
```
**Solution**: Ensure `user_id` references valid `profiles.id`

### Cascade Delete Issues
```
IntegrityError: update or delete on table "profiles" violates 
foreign key constraint on table "projects"
```
**Solution**: Check if cascade delete is properly configured (should be automatic)

### N+1 Query Problem
```python
# Bad - triggers query for each user's projects
for user in users:
    print(user.projects)  # Query per user

# Good - eager loads all projects
users = session.query(Profile).options(selectinload(Profile.projects))
for user in users:
    print(user.projects)  # No additional queries
```

## Documentation Links

- **Full Schema**: `docs/DATABASE_SCHEMA.md`
- **Migration Guide**: `docs/MIGRATION_GUIDE.md`
- **Schema Decision**: `docs/SCHEMA_DECISION.md`
- **Implementation Summary**: `docs/SCHEMA_ALIGNMENT_SUMMARY.md`
