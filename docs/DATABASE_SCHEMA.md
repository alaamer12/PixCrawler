# PixCrawler Database Schema Documentation

## Overview

This document provides comprehensive documentation of the PixCrawler database schema, including all tables, relationships, constraints, and indexes.

**Database**: PostgreSQL 12+  
**ORM**: SQLAlchemy 2.0  
**Migrations**: Alembic  
**Last Updated**: 2024-11-18

---

## Table of Contents

1. [Core Tables](#core-tables)
2. [Credit System](#credit-system)
3. [Notification System](#notification-system)
4. [API & Usage](#api--usage)
5. [Relationships](#relationships)
6. [Indexes](#indexes)
7. [Constraints](#constraints)
8. [Performance Considerations](#performance-considerations)

---

## Core Tables

### profiles

User profile information extending Supabase Auth.

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY,                    -- Supabase auth.users.id
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    avatar_url TEXT,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    user_tier VARCHAR(20) NOT NULL DEFAULT 'FREE',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: UUID from Supabase Auth
- `email`: User email (unique)
- `full_name`: User's display name
- `avatar_url`: Profile picture URL
- `role`: User role (user, admin, moderator)
- `user_tier`: Subscription tier (FREE, PRO, ENTERPRISE)
- `created_at`: Account creation timestamp
- `updated_at`: Last profile update

**Indexes**:
- `user_tier` - Filter users by subscription tier

---

### projects

Container for organizing crawl jobs.

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: Serial primary key
- `name`: Project name (required)
- `description`: Optional project description
- `user_id`: FK to profiles (CASCADE delete)
- `status`: Project status (active, archived, deleted)
- `created_at`: Creation timestamp
- `updated_at`: Last modification timestamp

**Indexes**:
- `user_id` - Find projects by user
- `status` - Filter by project status

**Relationships**:
- One Profile → Many Projects (1:many)
- One Project → Many CrawlJobs (1:many)

---

### crawl_jobs

Individual crawling tasks within a project.

```sql
CREATE TABLE crawl_jobs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    keywords JSONB NOT NULL,
    max_images INTEGER NOT NULL DEFAULT 1000,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    total_images INTEGER NOT NULL DEFAULT 0,
    downloaded_images INTEGER NOT NULL DEFAULT 0,
    valid_images INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_chunks INTEGER NOT NULL DEFAULT 0,
    active_chunks INTEGER NOT NULL DEFAULT 0,
    completed_chunks INTEGER NOT NULL DEFAULT 0,
    failed_chunks INTEGER NOT NULL DEFAULT 0,
    task_ids JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: Serial primary key
- `project_id`: FK to projects (CASCADE delete)
- `name`: Job name
- `keywords`: JSON array of search keywords
- `max_images`: Maximum images to collect
- `status`: Job status (pending, running, completed, failed, cancelled)
- `progress`: Progress percentage (0-100)
- `total_images`: Total images found
- `downloaded_images`: Successfully downloaded count
- `valid_images`: Valid/usable images count
- `started_at`: Job start timestamp
- `completed_at`: Job completion timestamp
- `total_chunks`: Total processing chunks
- `active_chunks`: Currently processing chunks
- `completed_chunks`: Successfully completed chunks
- `failed_chunks`: Failed chunks
- `task_ids`: Celery task IDs for tracking

**Indexes**:
- `project_id` - Find jobs by project
- `status` - Filter by job status
- `(project_id, status)` - Composite for common queries
- `created_at` - Sort by creation date

**Relationships**:
- One Project → Many CrawlJobs (1:many)
- One CrawlJob → Many Images (1:many)
- One CrawlJob → Many JobChunks (1:many)

---

### job_chunks

Individual processing chunks within a crawl job.

```sql
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
```

**Fields**:
- `id`: Serial primary key
- `job_id`: FK to crawl_jobs (CASCADE delete)
- `chunk_index`: Sequential chunk number
- `status`: Chunk status (pending, processing, completed, failed)
- `priority`: Processing priority (0-10, higher = urgent)
- `image_range`: JSON with {start, end} image indices
- `error_message`: Error details if failed
- `retry_count`: Number of retry attempts
- `task_id`: Celery task ID

**Indexes**:
- `job_id` - Find chunks by job
- `status` - Filter by status
- `(job_id, status)` - Composite for job status queries
- `(priority, created_at)` - Priority queue ordering
- `task_id` - Track by Celery task

**Constraints**:
- Status must be: pending, processing, completed, failed
- Priority must be 0-10
- Retry count must be non-negative

---

### images

Metadata for crawled images.

```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    crawl_job_id INTEGER NOT NULL REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    original_url TEXT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    storage_url TEXT,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    format VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: Serial primary key
- `crawl_job_id`: FK to crawl_jobs (CASCADE delete)
- `original_url`: Source image URL
- `filename`: Stored filename
- `storage_url`: Supabase Storage URL
- `width`: Image width in pixels
- `height`: Image height in pixels
- `file_size`: File size in bytes
- `format`: Image format (jpg, png, webp, etc.)

**Indexes**:
- `crawl_job_id` - Find images by job
- `created_at` - Sort by upload date

---

### activity_logs

Audit trail of user actions and system events.

```sql
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(50),
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: Serial primary key
- `user_id`: FK to profiles (CASCADE delete, nullable)
- `action`: Action description
- `resource_type`: Type of affected resource
- `resource_id`: ID of affected resource
- `metadata`: Additional event data (JSON)
- `timestamp`: Event timestamp

**Indexes**:
- `user_id` - Find activities by user
- `timestamp` - Sort by time
- `(user_id, timestamp)` - User activity timeline
- `(resource_type, resource_id)` - Find activities by resource

---

## Credit System

### credit_accounts

User billing and credit accounts.

```sql
CREATE TABLE credit_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    current_balance INTEGER NOT NULL DEFAULT 0,
    monthly_usage INTEGER NOT NULL DEFAULT 0,
    average_daily_usage NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    auto_refill_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    refill_threshold INTEGER NOT NULL DEFAULT 100,
    refill_amount INTEGER NOT NULL DEFAULT 500,
    monthly_limit INTEGER NOT NULL DEFAULT 2000,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: UUID primary key
- `user_id`: FK to profiles (unique, CASCADE delete)
- `current_balance`: Current credit balance
- `monthly_usage`: Credits used this month
- `average_daily_usage`: Average daily usage for forecasting
- `auto_refill_enabled`: Auto-refill enabled flag
- `refill_threshold`: Balance threshold to trigger refill
- `refill_amount`: Amount to add on refill
- `monthly_limit`: Maximum credits per month

**Constraints**:
- `current_balance >= 0`
- `monthly_usage >= 0`
- `refill_threshold > 0`
- `refill_amount > 0`
- `monthly_limit > 0`

---

### credit_transactions

Transaction history for billing.

```sql
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES credit_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: UUID primary key
- `account_id`: FK to credit_accounts (CASCADE delete)
- `user_id`: FK to profiles (CASCADE delete, denormalized)
- `type`: Transaction type (purchase, usage, refund, bonus)
- `description`: Human-readable description
- `amount`: Credit amount (positive/negative)
- `balance_after`: Account balance after transaction
- `status`: Transaction status (completed, pending, failed, cancelled)
- `metadata`: Additional transaction data (JSON)
- `created_at`: Transaction timestamp

**Indexes**:
- `account_id` - Find transactions by account
- `user_id` - Find transactions by user
- `type` - Filter by transaction type
- `status` - Filter by status
- `created_at` - Sort by date
- `(user_id, created_at)` - User transaction history

---

## Notification System

### notifications

User notifications and alerts.

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    icon VARCHAR(50),
    color VARCHAR(20),
    action_url TEXT,
    action_label VARCHAR(100),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: Serial primary key
- `user_id`: FK to profiles (CASCADE delete)
- `title`: Notification title
- `message`: Notification message
- `type`: Type (success, info, warning, error)
- `category`: Category (crawl_job, payment, system, security, etc.)
- `icon`: Lucide icon name
- `color`: Display color
- `action_url`: Optional action link
- `action_label`: Button label
- `is_read`: Read status
- `read_at`: When marked as read
- `metadata`: Additional data (JSON)

**Indexes**:
- `user_id` - Find notifications by user
- `is_read` - Filter read/unread
- `type` - Filter by type
- `category` - Filter by category
- `created_at` - Sort by date (DESC)
- `(user_id, is_read)` - Unread notifications for user
- `(user_id, created_at)` - User notification timeline

---

### notification_preferences

User notification settings.

```sql
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    push_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    sms_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    crawl_jobs_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    datasets_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    billing_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    security_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    marketing_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    product_updates_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    digest_frequency VARCHAR(20) NOT NULL DEFAULT 'daily',
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- Channel preferences: email, push, SMS
- Category preferences: crawl_jobs, datasets, billing, security, marketing, product_updates
- `digest_frequency`: Notification frequency (realtime, daily, weekly, never)
- `quiet_hours_start/end`: Do not disturb time window

---

## API & Usage

### api_keys

API keys for programmatic access.

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    permissions JSONB NOT NULL DEFAULT '[]',
    rate_limit INTEGER NOT NULL DEFAULT 1000,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    last_used_ip VARCHAR(45),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: UUID primary key
- `user_id`: FK to profiles (CASCADE delete)
- `name`: User-friendly key name
- `key_hash`: Hashed API key
- `key_prefix`: Key prefix for identification
- `status`: Status (active, revoked, expired)
- `permissions`: JSON array of permissions
- `rate_limit`: Requests per hour
- `usage_count`: Total uses
- `last_used_at`: Last usage timestamp
- `last_used_ip`: Last IP address
- `expires_at`: Optional expiration

---

### usage_metrics

Daily usage tracking.

```sql
CREATE TABLE usage_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    images_processed INTEGER NOT NULL DEFAULT 0,
    images_limit INTEGER NOT NULL DEFAULT 10000,
    storage_used_gb NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    storage_limit_gb NUMERIC(10, 2) NOT NULL DEFAULT 100.00,
    api_calls INTEGER NOT NULL DEFAULT 0,
    api_calls_limit INTEGER NOT NULL DEFAULT 50000,
    bandwidth_used_gb NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    bandwidth_limit_gb NUMERIC(10, 2) NOT NULL DEFAULT 500.00,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

**Fields**:
- `id`: UUID primary key
- `user_id`: FK to profiles (CASCADE delete)
- `metric_date`: Date for metrics
- Images: processed count and limit
- Storage: used (GB) and limit (GB)
- API calls: count and limit
- Bandwidth: used (GB) and limit (GB)

**Unique Constraint**:
- `(user_id, metric_date)` - One record per user per day

---

## Relationships

### Relationship Hierarchy

```
Profile (1)
├── (1:many) Projects
│   └── (1:many) CrawlJobs
│       ├── (1:many) Images
│       └── (1:many) JobChunks
├── (1:many) ActivityLogs
├── (1:1) CreditAccount
│   └── (1:many) CreditTransactions
├── (1:many) Notifications
├── (1:1) NotificationPreferences
├── (1:many) APIKeys
└── (1:many) UsageMetrics
```

### Cascade Delete Behavior

When a parent record is deleted:
- Delete all child records with CASCADE
- Example: Deleting a Profile cascades to Projects → CrawlJobs → Images/JobChunks

---

## Indexes

### Primary Indexes (High Priority)

```sql
-- User lookups
CREATE INDEX ix_projects_user_id ON projects(user_id);
CREATE INDEX ix_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX ix_credit_accounts_user_id ON credit_accounts(user_id);
CREATE INDEX ix_api_keys_user_id ON api_keys(user_id);
CREATE INDEX ix_notifications_user_id ON notifications(user_id);
CREATE INDEX ix_usage_metrics_user_id ON usage_metrics(user_id);

-- Job lookups
CREATE INDEX ix_crawl_jobs_project_id ON crawl_jobs(project_id);
CREATE INDEX ix_images_crawl_job_id ON images(crawl_job_id);
CREATE INDEX ix_job_chunks_job_id ON job_chunks(job_id);

-- Status filtering
CREATE INDEX ix_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX ix_job_chunks_status ON job_chunks(status);
```

### Composite Indexes (Medium Priority)

```sql
-- Multi-column queries
CREATE INDEX ix_crawl_jobs_project_status ON crawl_jobs(project_id, status);
CREATE INDEX ix_job_chunks_job_status ON job_chunks(job_id, status);
CREATE INDEX ix_activity_logs_user_timestamp ON activity_logs(user_id, timestamp);
CREATE INDEX ix_credit_transactions_user_created ON credit_transactions(user_id, created_at);
CREATE INDEX ix_usage_metrics_user_date ON usage_metrics(user_id, metric_date);
```

### Sorting Indexes (Medium Priority)

```sql
-- Date-based sorting
CREATE INDEX ix_crawl_jobs_created_at ON crawl_jobs(created_at);
CREATE INDEX ix_images_created_at ON images(created_at);
CREATE INDEX ix_notifications_created_at ON notifications(created_at DESC);
```

---

## Constraints

### Check Constraints

```sql
-- CrawlJob status
ALTER TABLE crawl_jobs ADD CONSTRAINT ck_crawl_jobs_status_valid
    CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'));

-- JobChunk status
ALTER TABLE job_chunks ADD CONSTRAINT ck_job_chunks_status_valid
    CHECK (status IN ('pending', 'processing', 'completed', 'failed'));

-- JobChunk priority
ALTER TABLE job_chunks ADD CONSTRAINT ck_job_chunks_priority_range
    CHECK (priority >= 0 AND priority <= 10);

-- Credit constraints
ALTER TABLE credit_accounts ADD CONSTRAINT ck_credit_accounts_balance_positive
    CHECK (current_balance >= 0);

-- Notification type
ALTER TABLE notifications ADD CONSTRAINT ck_notifications_type_valid
    CHECK (type IN ('success', 'info', 'warning', 'error'));
```

### Unique Constraints

```sql
-- One profile per email
ALTER TABLE profiles ADD CONSTRAINT uq_profiles_email UNIQUE (email);

-- One credit account per user
ALTER TABLE credit_accounts ADD CONSTRAINT uq_credit_accounts_user_id UNIQUE (user_id);

-- One metric record per user per day
ALTER TABLE usage_metrics ADD CONSTRAINT uq_usage_metrics_user_date UNIQUE (user_id, metric_date);

-- One preference set per user
ALTER TABLE notification_preferences ADD CONSTRAINT uq_notification_preferences_user_id UNIQUE (user_id);
```

---

## Performance Considerations

### Query Patterns

**Find user's projects**:
```sql
SELECT * FROM projects WHERE user_id = $1 ORDER BY created_at DESC;
-- Uses: ix_projects_user_id
```

**Find project's jobs by status**:
```sql
SELECT * FROM crawl_jobs 
WHERE project_id = $1 AND status = $2
ORDER BY created_at DESC;
-- Uses: ix_crawl_jobs_project_status
```

**Find pending chunks for processing**:
```sql
SELECT * FROM job_chunks 
WHERE job_id = $1 AND status = 'pending'
ORDER BY priority DESC, created_at ASC
LIMIT 10;
-- Uses: ix_job_chunks_job_status, ix_job_chunks_priority_created
```

**Get user activity timeline**:
```sql
SELECT * FROM activity_logs 
WHERE user_id = $1
ORDER BY timestamp DESC
LIMIT 50;
-- Uses: ix_activity_logs_user_timestamp
```

### Index Statistics

Regular maintenance:
```sql
-- Analyze table statistics
ANALYZE crawl_jobs;

-- Vacuum to reclaim space
VACUUM ANALYZE crawl_jobs;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan 
FROM pg_stat_user_indexes 
WHERE tablename = 'crawl_jobs'
ORDER BY idx_scan DESC;
```

### Storage Estimates

- **profiles**: ~1 KB per record
- **projects**: ~500 B per record
- **crawl_jobs**: ~2 KB per record
- **images**: ~1 KB per record
- **job_chunks**: ~500 B per record
- **activity_logs**: ~1 KB per record

For 1 million users:
- ~1 GB for profiles
- ~5 GB for projects (5 per user)
- ~50 GB for crawl_jobs (50 per project)
- ~500 GB for images (10,000 per job)
- ~50 GB for job_chunks (1,000 per job)

---

## Migration History

| Revision | Description | Date |
|----------|-------------|------|
| 001 | Create job_chunks table | 2024-11-16 |
| 002 | Add user_tier to profiles | 2024-11-17 |
| 003 | Add foreign keys and relationships | 2024-11-18 |

---

## Related Documentation

- [Migration Guide](./MIGRATION_GUIDE.md) - How to run and create migrations
- [Schema Decision](./SCHEMA_DECISION.md) - Design decisions and rationale
- [Backend Rules](../.windsurf/rules/backend.md) - Python development guidelines
