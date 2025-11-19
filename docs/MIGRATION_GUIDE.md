# Database Migration Guide

## Overview

This guide covers the Alembic migrations for PixCrawler database schema updates, including the new `job_chunks` table and `user_tier` column.

## Migrations

### Migration 001: Create job_chunks Table

**File**: `alembic/versions/001_create_job_chunks_table.py`

**Purpose**: Creates the `job_chunks` table for tracking individual processing chunks within crawl jobs.

**SQL Operations**:

```sql
-- Create table
CREATE TABLE job_chunks (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 5,
    image_range JSONB NOT NULL,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    task_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX ix_job_chunks_job_id ON job_chunks(job_id);
CREATE INDEX ix_job_chunks_status ON job_chunks(status);
CREATE INDEX ix_job_chunks_job_status ON job_chunks(job_id, status);
CREATE INDEX ix_job_chunks_priority_created ON job_chunks(priority, created_at);
CREATE INDEX ix_job_chunks_task_id ON job_chunks(task_id);

-- Create constraints
ALTER TABLE job_chunks ADD CONSTRAINT ck_job_chunks_status_valid 
    CHECK (status IN ('pending', 'processing', 'completed', 'failed'));
ALTER TABLE job_chunks ADD CONSTRAINT ck_job_chunks_priority_range 
    CHECK (priority >= 0 AND priority <= 10);
ALTER TABLE job_chunks ADD CONSTRAINT ck_job_chunks_retry_count_positive 
    CHECK (retry_count >= 0);
```

**Columns**:
- `id`: Serial primary key
- `job_id`: Foreign key to `crawl_jobs.id` with CASCADE delete
- `chunk_index`: Sequential chunk number within the job
- `status`: Chunk status (pending, processing, completed, failed)
- `priority`: Processing priority (0-10, higher = more urgent)
- `image_range`: JSONB object with `{start: int, end: int}` for image indices
- `error_message`: Optional error message if chunk failed
- `retry_count`: Number of retry attempts (non-negative)
- `task_id`: Celery task ID for this chunk
- `created_at`: Timestamp when chunk was created
- `updated_at`: Timestamp when chunk was last updated

**Indexes**:
- `ix_job_chunks_job_id`: Fast lookup by job
- `ix_job_chunks_status`: Fast filtering by status
- `ix_job_chunks_job_status`: Composite index for job + status queries
- `ix_job_chunks_priority_created`: For priority queue operations
- `ix_job_chunks_task_id`: Fast lookup by Celery task ID

**Constraints**:
- Status must be one of: pending, processing, completed, failed
- Priority must be between 0 and 10
- Retry count must be non-negative

---

### Migration 002: Add user_tier to profiles Table

**File**: `alembic/versions/002_add_user_tier_to_profiles.py`

**Purpose**: Adds subscription tier tracking to the profiles table for feature access and billing.

**SQL Operations**:

```sql
-- Add column
ALTER TABLE profiles ADD COLUMN user_tier VARCHAR(20) NOT NULL DEFAULT 'FREE';

-- Create index
CREATE INDEX ix_profiles_user_tier ON profiles(user_tier);

-- Add constraint
ALTER TABLE profiles ADD CONSTRAINT ck_profiles_user_tier_valid 
    CHECK (user_tier IN ('FREE', 'PRO', 'ENTERPRISE'));
```

**Column Details**:
- `user_tier`: Subscription tier (FREE, PRO, ENTERPRISE)
- Default: FREE
- Indexed for fast filtering by tier

**Tiers**:
- `FREE`: Basic tier with limited features
- `PRO`: Professional tier with enhanced features
- `ENTERPRISE`: Enterprise tier with full features

---

### Migration 003: Add Foreign Keys and Relationships

**File**: `alembic/versions/003_add_foreign_keys_and_relationships.py`

**Purpose**: Establishes referential integrity by adding all missing foreign key constraints and performance indexes across the schema.

**Foreign Keys Added**:

```sql
-- Project relationships
ALTER TABLE projects ADD CONSTRAINT fk_projects_user_id 
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

-- CrawlJob relationships
ALTER TABLE crawl_jobs ADD CONSTRAINT fk_crawl_jobs_project_id 
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- Image relationships
ALTER TABLE images ADD CONSTRAINT fk_images_crawl_job_id 
    FOREIGN KEY (crawl_job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE;

-- ActivityLog relationships
ALTER TABLE activity_logs ADD CONSTRAINT fk_activity_logs_user_id 
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

-- Credit relationships
ALTER TABLE credit_accounts ADD CONSTRAINT fk_credit_accounts_user_id 
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE credit_transactions ADD CONSTRAINT fk_credit_transactions_account_id 
    FOREIGN KEY (account_id) REFERENCES credit_accounts(id) ON DELETE CASCADE;

ALTER TABLE credit_transactions ADD CONSTRAINT fk_credit_transactions_user_id 
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

-- API Key relationships
ALTER TABLE api_keys ADD CONSTRAINT fk_api_keys_user_id 
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

-- Notification relationships
ALTER TABLE notifications ADD CONSTRAINT fk_notifications_user_id 
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

ALTER TABLE notification_preferences ADD CONSTRAINT fk_notification_preferences_user_id 
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

-- Usage metrics relationships
ALTER TABLE usage_metrics ADD CONSTRAINT fk_usage_metrics_user_id 
    FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
```

**Indexes Added**:

```sql
-- Project indexes
CREATE INDEX ix_projects_user_id ON projects(user_id);
CREATE INDEX ix_projects_status ON projects(status);

-- CrawlJob indexes
CREATE INDEX ix_crawl_jobs_project_id ON crawl_jobs(project_id);
CREATE INDEX ix_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX ix_crawl_jobs_project_status ON crawl_jobs(project_id, status);
CREATE INDEX ix_crawl_jobs_created_at ON crawl_jobs(created_at);

-- Image indexes
CREATE INDEX ix_images_crawl_job_id ON images(crawl_job_id);
CREATE INDEX ix_images_created_at ON images(created_at);

-- ActivityLog indexes
CREATE INDEX ix_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX ix_activity_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX ix_activity_logs_user_timestamp ON activity_logs(user_id, timestamp);
CREATE INDEX ix_activity_logs_resource ON activity_logs(resource_type, resource_id);
```

**Benefits**:

- **Data Integrity**: Foreign keys prevent orphaned records and enforce referential consistency
- **Cascade Deletes**: Automatic cleanup when parent records are deleted
- **Performance**: Indexes accelerate common query patterns (user lookups, status filtering, sorting)
- **Query Optimization**: Composite indexes support multi-column WHERE and JOIN conditions

**Impact**:

- Existing data must satisfy FK constraints (no orphaned records)
- Cascade deletes will remove related records when parent is deleted
- Indexes consume additional storage but improve query performance
- No downtime required for this migration

---

## Running Migrations

### Prerequisites

```bash
# Install dependencies
pip install alembic sqlalchemy psycopg2-binary

# Set up database URL in environment
export DATABASE_URL="postgresql://user:password@localhost:5432/pixcrawler"
```

### Upgrade to Latest

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade 002
```

### Downgrade

```bash
# Downgrade to previous migration
alembic downgrade -1

# Downgrade to specific migration
alembic downgrade 001

# Downgrade all
alembic downgrade base
```

### Check Migration Status

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic upgrade head --sql
```

---

## Creating New Migrations

### Auto-generate from Model Changes

```bash
# Generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Review generated migration in alembic/versions/
# Edit if needed, then apply
alembic upgrade head
```

### Manual Migration

```bash
# Create empty migration
alembic revision -m "Description of changes"

# Edit the generated file in alembic/versions/
# Add upgrade() and downgrade() functions
# Then apply
alembic upgrade head
```

---

## Migration Structure

Each migration file has this structure:

```python
"""Migration description

Revision ID: 003
Revises: 002
Create Date: 2025-01-16 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the migration."""
    # SQL operations here
    pass


def downgrade() -> None:
    """Revert the migration."""
    # Reverse SQL operations here
    pass
```

---

## Best Practices

1. **Always write downgrade functions** - Ensures you can rollback if needed
2. **Test migrations locally** - Run on test database first
3. **Use descriptive names** - Migration files should describe what they do
4. **Keep migrations small** - One logical change per migration
5. **Add comments** - Explain complex operations
6. **Use server defaults** - For performance and consistency
7. **Create indexes** - For frequently queried columns
8. **Add constraints** - For data integrity

---

## Troubleshooting

### Migration fails to apply

```bash
# Check migration status
alembic current

# View migration details
alembic history -v

# Check database logs
psql -U user -d pixcrawler -c "SELECT * FROM alembic_version;"
```

### Rollback stuck migration

```bash
# Mark migration as applied without running
alembic stamp 001

# Then downgrade
alembic downgrade base
```

### Recreate migration history

```bash
# WARNING: Only for development!
# Delete alembic_version table
psql -U user -d pixcrawler -c "DROP TABLE alembic_version;"

# Reset to base
alembic stamp base

# Apply all migrations
alembic upgrade head
```

---

## Related Files

- **Models**: `backend/models/`
  - `__init__.py` - Core models (Profile, Project, CrawlJob, Image, ActivityLog)
  - `chunks.py` - JobChunk model
  - `credits.py` - Credit models
  - `notifications.py` - Notification models
  - `api_keys.py` - API key model
  - `usage.py` - Usage metrics model

- **Configuration**: `alembic/`
  - `alembic.ini` - Alembic configuration
  - `env.py` - Migration environment setup
  - `versions/` - Migration files

- **Schema Documentation**: `docs/DATABASE_SCHEMA.sql` - Full SQL schema

---

## Schema Diagram

```
                                    ┌─────────────────────────────────────────────────┐
                                    │          PROFILES (Users)                       │
                                    │  ────────────────────────────────────────────   │
                                    │  id (UUID) | email | full_name | user_tier     │
                                    └─────────────────────────────────────────────────┘
                                                    │
                    ┌───────────────────────────────┼───────────────────────────────┐
                    │                               │                               │
                    ▼                               ▼                               ▼
        ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
        │ PROJECTS             │      │ ACTIVITY_LOGS        │      │ CREDIT_ACCOUNTS      │
        │ ────────────────────│      │ ────────────────────│      │ ────────────────────│
        │ id | name | user_id │      │ id | user_id | ... │      │ id | user_id | ... │
        └──────────────────────┘      └──────────────────────┘      └──────────────────────┘
                    │                                                         │
                    ▼                                                         ▼
        ┌──────────────────────┐                              ┌──────────────────────┐
        │ CRAWL_JOBS           │                              │ CREDIT_TRANSACTIONS  │
        │ ────────────────────│                              │ ────────────────────│
        │ id | project_id | ..│                              │ id | account_id | ..│
        └──────────────────────┘                              └──────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
    ┌──────────────┐    ┌──────────────┐
    │ JOB_CHUNKS   │    │ IMAGES       │
    │ ────────────│    │ ────────────│
    │ id | job_id │    │ id | job_id │
    └──────────────┘    └──────────────┘

Additional Relationships (all from PROFILES):
    ├─ NOTIFICATIONS (1:many)
    ├─ NOTIFICATION_PREFERENCES (1:1)
    ├─ API_KEYS (1:many)
    └─ USAGE_METRICS (1:many)
```

**Key Relationships**:
- All tables with `user_id` reference `profiles.id` with CASCADE delete
- `projects.user_id` → `profiles.id`
- `crawl_jobs.project_id` → `projects.id`
- `images.crawl_job_id` → `crawl_jobs.id`
- `job_chunks.job_id` → `crawl_jobs.id`
- `activity_logs.user_id` → `profiles.id`
- `credit_accounts.user_id` → `profiles.id`
- `credit_transactions.account_id` → `credit_accounts.id`
- `credit_transactions.user_id` → `profiles.id`
- `api_keys.user_id` → `profiles.id`
- `notifications.user_id` → `profiles.id`
- `notification_preferences.user_id` → `profiles.id`
- `usage_metrics.user_id` → `profiles.id`

---

## Key Features

### Job Chunks Table

Enables:
- **Fine-grained progress tracking** - Track individual chunk status
- **Distributed processing** - Process chunks in parallel with Celery
- **Retry logic** - Retry failed chunks independently
- **Priority queuing** - Process high-priority chunks first
- **Error tracking** - Store error messages per chunk

### User Tier Column

Enables:
- **Subscription management** - Track user subscription level
- **Feature access control** - Limit features by tier
- **Billing integration** - Different pricing per tier
- **Usage analytics** - Track usage by tier
- **Tier-based quotas** - Different limits per tier

---

## Performance Considerations

### Indexes

The `job_chunks` table has 5 indexes optimized for:
- **Lookup by job**: `ix_job_chunks_job_id`
- **Status filtering**: `ix_job_chunks_status`
- **Job + status queries**: `ix_job_chunks_job_status`
- **Priority queue**: `ix_job_chunks_priority_created`
- **Task tracking**: `ix_job_chunks_task_id`

### Query Examples

```sql
-- Get all pending chunks for a job
SELECT * FROM job_chunks 
WHERE job_id = 123 AND status = 'pending'
ORDER BY priority DESC, created_at ASC;

-- Get high-priority chunks
SELECT * FROM job_chunks 
WHERE status = 'processing' 
ORDER BY priority DESC, created_at ASC
LIMIT 10;

-- Get failed chunks for retry
SELECT * FROM job_chunks 
WHERE status = 'failed' AND retry_count < 3
ORDER BY created_at ASC;

-- Get users by tier
SELECT COUNT(*), user_tier FROM profiles 
GROUP BY user_tier;
```

---

## Maintenance

### Regular Tasks

```bash
# Analyze query performance
ANALYZE job_chunks;

# Vacuum to reclaim space
VACUUM ANALYZE job_chunks;

# Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE tablename = 'job_chunks';
```

### Monitoring

Monitor these metrics:
- Chunk processing time
- Failed chunk percentage
- Retry count distribution
- User tier distribution
- Query performance on indexes
