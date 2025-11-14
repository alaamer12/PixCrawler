# PixCrawler Database Schema Documentation

## Overview

This document describes the complete database schema for PixCrawler, including all tables, relationships, constraints, and indexes.

**Database Type**: PostgreSQL 13+  
**ORM**: SQLAlchemy 2.0+  
**Migrations**: Alembic  
**Authentication**: Supabase Auth

## Core Principles

1. **Foreign Key Constraints**: All relationships enforced at database level
2. **Cascade Deletes**: Parent deletion cascades to children (except ActivityLog)
3. **Timestamps**: All tables include `created_at` and `updated_at` (except Image, ActivityLog)
4. **Indexes**: Strategic indexes on frequently queried columns
5. **UUID for Users**: Profile IDs reference Supabase auth.users.id
6. **JSONB for Flexibility**: Complex data stored as JSONB for querying

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         PROFILES (Users)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ id (UUID, PK)                                            │   │
│  │ email (String, UNIQUE, INDEX)                            │   │
│  │ full_name (String, nullable)                             │   │
│  │ avatar_url (Text, nullable)                              │   │
│  │ role (String, default='user')                            │   │
│  │ created_at (DateTime, server_default=now())              │   │
│  │ updated_at (DateTime, server_default=now())              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
    (1:N)      (1:N)       (1:N)
        │           │           │
┌───────────────┐  │  ┌──────────────────┐
│   PROJECTS    │  │  │  ACTIVITY_LOGS   │
│ ┌───────────┐ │  │  │ ┌──────────────┐ │
│ │ id (PK)   │ │  │  │ │ id (PK)      │ │
│ │ name      │ │  │  │ │ user_id (FK) │ │
│ │ description
│ │ user_id   │◄─┘  │ │ action       │ │
│ │ (FK)      │     │ │ resource_type│ │
│ │ status    │     │ │ resource_id  │ │
│ │ created_at│     │ │ metadata_    │ │
│ │ updated_at│     │ │ timestamp    │ │
│ └───────────┘     │ └──────────────┘ │
└───────────────┘   └──────────────────┘
        │
        │ (1:N)
        ▼
┌──────────────────────────────────────────┐
│          CRAWL_JOBS                      │
│ ┌──────────────────────────────────────┐ │
│ │ id (PK)                              │ │
│ │ project_id (FK, INDEX)               │ │
│ │ name                                 │ │
│ │ keywords (JSONB)                     │ │
│ │ max_images                           │ │
│ │ status (INDEX)                       │ │
│ │ progress                             │ │
│ │ total_images, downloaded_images      │ │
│ │ valid_images                         │ │
│ │ started_at, completed_at             │ │
│ │ total_chunks, active_chunks          │ │
│ │ completed_chunks, failed_chunks      │ │
│ │ task_ids (JSONB)                     │ │
│ │ created_at, updated_at               │ │
│ │ COMPOSITE INDEX (project_id, status) │ │
│ └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
        │
    ┌───┼───┬───────────────────┐
    │   │   │                   │
    ▼   ▼   ▼                   ▼
(1:N) (1:N) (1:N)          (1:N)
    │   │   │                   │
┌─────────────────┐  ┌──────────────────────┐
│     IMAGES      │  │  VALIDATION_JOBS     │
│ ┌─────────────┐ │  │ ┌──────────────────┐ │
│ │ id (PK)     │ │  │ │ id (PK)          │ │
│ │ crawl_job_id│◄┤  │ │ crawl_job_id (FK)│ │
│ │ (FK, INDEX) │ │  │ │ name             │ │
│ │ original_url│ │  │ │ status (INDEX)   │ │
│ │ filename    │ │  │ │ progress         │ │
│ │ storage_url │ │  │ │ total_images     │ │
│ │ width       │ │  │ │ validated_images │ │
│ │ height      │ │  │ │ invalid_images   │ │
│ │ file_size   │ │  │ │ validation_rules │ │
│ │ format      │ │  │ │ started_at       │ │
│ └─────────────┘ │  │ │ completed_at     │ │
└─────────────────┘  │ │ error_message    │ │
                     │ │ created_at       │ │
                     │ │ updated_at       │ │
                     │ └──────────────────┘ │
                     └──────────────────────┘
                                │
                                │ (1:N)
                                ▼
                     ┌──────────────────────┐
                     │   EXPORT_JOBS        │
                     │ ┌──────────────────┐ │
                     │ │ id (PK)          │ │
                     │ │ crawl_job_id (FK)│ │
                     │ │ user_id (FK)     │ │
                     │ │ name             │ │
                     │ │ status (INDEX)   │ │
                     │ │ progress         │ │
                     │ │ format           │ │
                     │ │ total_images     │ │
                     │ │ exported_images  │ │
                     │ │ file_size        │ │
                     │ │ download_url     │ │
                     │ │ export_options   │ │
                     │ │ started_at       │ │
                     │ │ completed_at     │ │
                     │ │ expires_at       │ │
                     │ │ error_message    │ │
                     │ │ created_at       │ │
                     │ │ updated_at       │ │
                     │ └──────────────────┘ │
                     └──────────────────────┘
```

## Table Specifications

### 1. profiles

**Purpose**: User profile information (extends Supabase auth.users)

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | UUID | PK | References auth.users.id from Supabase |
| email | String(255) | UNIQUE, NOT NULL, INDEX | User email address |
| full_name | String(100) | NULL | User's display name |
| avatar_url | Text | NULL | URL to profile picture |
| role | String(20) | NOT NULL, DEFAULT='user' | User role (user, admin, moderator) |
| created_at | DateTime | NOT NULL, DEFAULT=now() | Account creation timestamp |
| updated_at | DateTime | NOT NULL, DEFAULT=now() | Last profile update |

**Indexes**:
- `ix_profiles_email` on `email` (UNIQUE)

**Relationships**:
- One-to-Many: projects
- One-to-Many: activity_logs

---

### 2. projects

**Purpose**: Organize crawl jobs for users

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | Integer | PK, AUTO_INCREMENT | Project identifier |
| name | String(100) | NOT NULL | Project name |
| description | Text | NULL | Project description |
| user_id | UUID | FK→profiles.id, NOT NULL, INDEX | Project owner |
| status | String(20) | NOT NULL, DEFAULT='active' | active, archived, deleted |
| created_at | DateTime | NOT NULL, DEFAULT=now() | Creation timestamp |
| updated_at | DateTime | NOT NULL, DEFAULT=now() | Last update timestamp |

**Indexes**:
- `ix_project_user_id` on `user_id` (for user's projects)

**Foreign Keys**:
- `user_id` → `profiles.id` (CASCADE DELETE)

**Relationships**:
- Many-to-One: user (Profile)
- One-to-Many: crawl_jobs

---

### 3. crawl_jobs

**Purpose**: Track image crawling tasks with chunk-based processing

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | Integer | PK, AUTO_INCREMENT | Job identifier |
| project_id | Integer | FK→projects.id, NOT NULL, INDEX | Parent project |
| name | String(100) | NOT NULL | Job name |
| keywords | JSONB | NOT NULL | Array of search keywords |
| max_images | Integer | NOT NULL, DEFAULT=1000 | Target image count |
| status | String(20) | NOT NULL, DEFAULT='pending', INDEX | pending, running, completed, failed, cancelled |
| progress | Integer | NOT NULL, DEFAULT=0 | Progress percentage (0-100) |
| total_images | Integer | NOT NULL, DEFAULT=0 | Images found |
| downloaded_images | Integer | NOT NULL, DEFAULT=0 | Images downloaded |
| valid_images | Integer | NOT NULL, DEFAULT=0 | Valid images |
| started_at | DateTime | NULL | Job start time |
| completed_at | DateTime | NULL | Job completion time |
| total_chunks | Integer | NOT NULL, DEFAULT=0 | Total processing chunks |
| active_chunks | Integer | NOT NULL, DEFAULT=0 | Currently processing |
| completed_chunks | Integer | NOT NULL, DEFAULT=0 | Successfully completed |
| failed_chunks | Integer | NOT NULL, DEFAULT=0 | Failed chunks |
| task_ids | JSONB | NOT NULL, DEFAULT='[]' | Celery task IDs |
| created_at | DateTime | NOT NULL, DEFAULT=now() | Creation timestamp |
| updated_at | DateTime | NOT NULL, DEFAULT=now() | Last update timestamp |

**Indexes**:
- `ix_crawl_job_status` on `status`
- `ix_crawl_job_project_status` on `(project_id, status)` (composite)

**Foreign Keys**:
- `project_id` → `projects.id` (CASCADE DELETE)

**Relationships**:
- Many-to-One: project (Project)
- One-to-Many: images
- One-to-Many: validation_jobs
- One-to-Many: export_jobs

---

### 4. images

**Purpose**: Metadata for crawled images

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | Integer | PK, AUTO_INCREMENT | Image identifier |
| crawl_job_id | Integer | FK→crawl_jobs.id, NOT NULL, INDEX | Parent job |
| original_url | Text | NOT NULL | Source URL |
| filename | String(255) | NOT NULL | Stored filename |
| storage_url | Text | NULL | Supabase Storage URL |
| width | Integer | NULL | Image width in pixels |
| height | Integer | NULL | Image height in pixels |
| file_size | Integer | NULL | File size in bytes |
| format | String(10) | NULL | Image format (jpg, png, etc.) |

**Indexes**:
- `ix_image_crawl_job_id` on `crawl_job_id`

**Foreign Keys**:
- `crawl_job_id` → `crawl_jobs.id` (CASCADE DELETE)

**Relationships**:
- Many-to-One: crawl_job (CrawlJob)

---

### 5. activity_logs

**Purpose**: Track user actions and system events

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | Integer | PK, AUTO_INCREMENT | Log entry ID |
| user_id | UUID | FK→profiles.id, NULL, INDEX | User who performed action |
| action | Text | NOT NULL | Action description |
| resource_type | String(50) | NULL | Type of resource (project, job, etc.) |
| resource_id | String(50) | NULL | ID of affected resource |
| metadata_ | JSONB | NULL | Additional event data |
| timestamp | DateTime | NOT NULL, DEFAULT=now(), INDEX | Event timestamp |

**Indexes**:
- `ix_activity_log_user_id` on `user_id`
- `ix_activity_log_timestamp` on `timestamp`

**Foreign Keys**:
- `user_id` → `profiles.id` (SET NULL on delete)

**Relationships**:
- Many-to-One: user (Profile, optional)

---

### 6. validation_jobs

**Purpose**: Track image validation tasks

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | Integer | PK, AUTO_INCREMENT | Job identifier |
| crawl_job_id | Integer | FK→crawl_jobs.id, NOT NULL, INDEX | Parent crawl job |
| name | String(100) | NOT NULL | Validation job name |
| status | String(20) | NOT NULL, DEFAULT='pending', INDEX | pending, running, completed, failed |
| progress | Integer | NOT NULL, DEFAULT=0 | Progress percentage (0-100) |
| total_images | Integer | NOT NULL, DEFAULT=0 | Images to validate |
| validated_images | Integer | NOT NULL, DEFAULT=0 | Successfully validated |
| invalid_images | Integer | NOT NULL, DEFAULT=0 | Invalid images |
| validation_rules | JSONB | NOT NULL, DEFAULT='{}' | Validation rules config |
| started_at | DateTime | NULL | Job start time |
| completed_at | DateTime | NULL | Job completion time |
| error_message | Text | NULL | Error description if failed |
| created_at | DateTime | NOT NULL, DEFAULT=now() | Creation timestamp |
| updated_at | DateTime | NOT NULL, DEFAULT=now() | Last update timestamp |

**Indexes**:
- `ix_validation_job_status` on `status`
- `ix_validation_job_crawl_job_id` on `crawl_job_id`

**Foreign Keys**:
- `crawl_job_id` → `crawl_jobs.id` (CASCADE DELETE)

**Relationships**:
- Many-to-One: crawl_job (CrawlJob)

---

### 7. export_jobs

**Purpose**: Track dataset export tasks

| Column | Type | Constraints | Notes |
|--------|------|-----------|-------|
| id | Integer | PK, AUTO_INCREMENT | Job identifier |
| crawl_job_id | Integer | FK→crawl_jobs.id, NOT NULL, INDEX | Source crawl job |
| user_id | UUID | FK→profiles.id, NOT NULL, INDEX | Export requester |
| name | String(100) | NOT NULL | Export job name |
| status | String(20) | NOT NULL, DEFAULT='pending', INDEX | pending, running, completed, failed |
| progress | Integer | NOT NULL, DEFAULT=0 | Progress percentage (0-100) |
| format | String(20) | NOT NULL, DEFAULT='zip' | Export format (zip, tar, csv) |
| total_images | Integer | NOT NULL, DEFAULT=0 | Images to export |
| exported_images | Integer | NOT NULL, DEFAULT=0 | Successfully exported |
| file_size | Integer | NULL | Exported file size in bytes |
| download_url | Text | NULL | URL to download file |
| export_options | JSONB | NOT NULL, DEFAULT='{}' | Export configuration |
| started_at | DateTime | NULL | Job start time |
| completed_at | DateTime | NULL | Job completion time |
| expires_at | DateTime | NULL | Download link expiration |
| error_message | Text | NULL | Error description if failed |
| created_at | DateTime | NOT NULL, DEFAULT=now() | Creation timestamp |
| updated_at | DateTime | NOT NULL, DEFAULT=now() | Last update timestamp |

**Indexes**:
- `ix_export_job_status` on `status`
- `ix_export_job_user_id` on `user_id`
- `ix_export_job_crawl_job_id` on `crawl_job_id`

**Foreign Keys**:
- `crawl_job_id` → `crawl_jobs.id` (CASCADE DELETE)
- `user_id` → `profiles.id` (CASCADE DELETE)

**Relationships**:
- Many-to-One: crawl_job (CrawlJob)
- Many-to-One: user (Profile)

---

## Data Integrity Rules

### Cascade Deletes

When a parent record is deleted:

| Parent | Child | Behavior |
|--------|-------|----------|
| Profile | Project | DELETE (cascade) |
| Profile | ActivityLog | SET NULL |
| Project | CrawlJob | DELETE (cascade) |
| CrawlJob | Image | DELETE (cascade) |
| CrawlJob | ValidationJob | DELETE (cascade) |
| CrawlJob | ExportJob | DELETE (cascade) |

### Constraints

1. **Unique Constraints**:
   - `profiles.email` - One email per user

2. **Not Null Constraints**:
   - All foreign keys are NOT NULL except `activity_logs.user_id`
   - All primary keys are NOT NULL
   - All status fields have defaults

3. **Check Constraints** (application-level):
   - Progress: 0-100
   - Image counts: >= 0
   - Chunk counts: >= 0

---

## Performance Optimization

### Index Strategy

**Lookup Indexes** (single column):
- `profiles.email` - User authentication
- `crawl_jobs.status` - Filter by status
- `activity_logs.user_id` - User's activity
- `activity_logs.timestamp` - Recent activity
- `validation_jobs.status` - Filter by status
- `export_jobs.status` - Filter by status

**Foreign Key Indexes** (automatic):
- `projects.user_id` - User's projects
- `crawl_jobs.project_id` - Project's jobs
- `images.crawl_job_id` - Job's images
- `validation_jobs.crawl_job_id` - Job's validations
- `export_jobs.user_id` - User's exports
- `export_jobs.crawl_job_id` - Job's exports

**Composite Indexes** (multi-column):
- `crawl_jobs(project_id, status)` - Common filter pattern

### Query Optimization Tips

1. **User's Projects**: Use index on `projects.user_id`
   ```sql
   SELECT * FROM projects WHERE user_id = $1 ORDER BY created_at DESC;
   ```

2. **Active Jobs**: Use composite index on `crawl_jobs(project_id, status)`
   ```sql
   SELECT * FROM crawl_jobs WHERE project_id = $1 AND status = 'running';
   ```

3. **Recent Activity**: Use index on `activity_logs.timestamp`
   ```sql
   SELECT * FROM activity_logs WHERE timestamp > now() - interval '7 days';
   ```

4. **Job Images**: Use index on `images.crawl_job_id`
   ```sql
   SELECT * FROM images WHERE crawl_job_id = $1 LIMIT 100;
   ```

---

## Migration Strategy

### Initial Setup

1. Run Alembic migration to create schema:
   ```bash
   alembic upgrade head
   ```

2. Verify schema:
   ```bash
   \d profiles
   \d projects
   # ... etc
   ```

### Future Changes

1. Modify SQLAlchemy models
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Description"
   ```
3. Review and test migration
4. Apply to database:
   ```bash
   alembic upgrade head
   ```

---

## Backup & Recovery

### Regular Backups

```bash
# Full database backup
pg_dump pixcrawler > backup_$(date +%Y%m%d).sql

# Restore from backup
psql pixcrawler < backup_20240101.sql
```

### Point-in-Time Recovery

PostgreSQL WAL archiving enables recovery to any point in time.

---

## Monitoring & Maintenance

### Key Metrics

- Table sizes: `SELECT pg_size_pretty(pg_total_relation_size('table_name'));`
- Index usage: `SELECT * FROM pg_stat_user_indexes;`
- Query performance: Enable `log_min_duration_statement`

### Maintenance Tasks

1. **VACUUM**: Reclaim space from deleted rows
2. **ANALYZE**: Update table statistics
3. **REINDEX**: Rebuild indexes if corrupted

---

## References

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Database Design Best Practices](https://en.wikipedia.org/wiki/Database_normalization)
