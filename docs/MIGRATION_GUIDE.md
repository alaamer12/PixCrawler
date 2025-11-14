# Database Schema Migration Guide

## Overview

This guide explains how to apply the database schema migrations for PixCrawler, including the new foreign key constraints, relationships, and indexes.

**Migration Version**: 001_initial_schema  
**Date**: 2024-11-14  
**Database**: PostgreSQL 13+  
**Tool**: Alembic

---

## Prerequisites

1. **PostgreSQL 13+** installed and running
2. **Python 3.11+** with dependencies installed
3. **Alembic** installed (included in backend dependencies)
4. **Database URL** configured in environment

### Check Prerequisites

```bash
# Check Python version
python --version  # Should be 3.11+

# Check PostgreSQL version
psql --version  # Should be 13+

# Check Alembic installation
alembic --version  # Should show version
```

---

## Environment Setup

### 1. Configure Database URL

Set the database URL in your environment:

```bash
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/pixcrawler

# Or export as environment variable
export DATABASE_URL="postgresql://user:password@localhost:5432/pixcrawler"
```

### 2. Verify Connection

```bash
# Test database connection
psql $DATABASE_URL -c "SELECT version();"
```

### 3. Install Dependencies

```bash
# Install backend dependencies
cd backend
pip install -e .

# Or install all dependencies
pip install -r requirements.txt
```

---

## Migration Process

### Step 1: Backup Database (Recommended)

Before applying migrations, create a backup:

```bash
# Full database backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_*.sql
```

### Step 2: Check Current Status

```bash
# Show current migration status
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

### Step 3: Apply Migration

```bash
# Apply all pending migrations
alembic upgrade head

# Or apply specific migration
alembic upgrade 001

# Verify migration applied
alembic current
```

### Step 4: Verify Schema

```bash
# Connect to database
psql $DATABASE_URL

# List tables
\dt

# Describe specific table
\d profiles
\d projects
\d crawl_jobs
\d images
\d activity_logs
\d validation_jobs
\d export_jobs

# Check indexes
\di

# Check foreign keys
\d+ projects
```

---

## What Changed

### New Tables

1. **validation_jobs** - Image validation tasks
2. **export_jobs** - Dataset export tasks

### Modified Tables

1. **profiles**
   - Added index on `email`

2. **projects**
   - Added FK constraint on `user_id` → `profiles.id`
   - Added index on `user_id`

3. **crawl_jobs**
   - Added FK constraint on `project_id` → `projects.id`
   - Added index on `project_id`
   - Added index on `status`
   - Added composite index on `(project_id, status)`

4. **images**
   - Added FK constraint on `crawl_job_id` → `crawl_jobs.id`
   - Added index on `crawl_job_id`

5. **activity_logs**
   - Added FK constraint on `user_id` → `profiles.id`
   - Added index on `user_id`
   - Added index on `timestamp`

### New Indexes

```
profiles:
  - ix_profiles_email

projects:
  - ix_project_user_id

crawl_jobs:
  - ix_crawl_job_status
  - ix_crawl_job_project_status (composite)

images:
  - ix_image_crawl_job_id

activity_logs:
  - ix_activity_log_user_id
  - ix_activity_log_timestamp

validation_jobs:
  - ix_validation_job_status
  - ix_validation_job_crawl_job_id

export_jobs:
  - ix_export_job_status
  - ix_export_job_user_id
  - ix_export_job_crawl_job_id
```

---

## Rollback Procedure

If you need to rollback the migration:

```bash
# Rollback one migration
alembic downgrade -1

# Or rollback to specific revision
alembic downgrade base

# Verify rollback
alembic current
```

### Restore from Backup

If rollback fails, restore from backup:

```bash
# Drop current database
dropdb pixcrawler

# Recreate database
createdb pixcrawler

# Restore from backup
psql pixcrawler < backup_20240101_120000.sql

# Verify restoration
psql pixcrawler -c "SELECT COUNT(*) FROM profiles;"
```

---

## Verification Checklist

After migration, verify:

- [ ] All tables created
- [ ] All foreign keys in place
- [ ] All indexes created
- [ ] No errors in application logs
- [ ] API endpoints working
- [ ] Database queries performing well

### Verification Script

```bash
#!/bin/bash

echo "=== Database Migration Verification ==="

# Check tables
echo "Checking tables..."
psql $DATABASE_URL -c "
  SELECT table_name FROM information_schema.tables 
  WHERE table_schema = 'public' 
  ORDER BY table_name;
"

# Check foreign keys
echo "Checking foreign keys..."
psql $DATABASE_URL -c "
  SELECT constraint_name, table_name, column_name
  FROM information_schema.key_column_usage
  WHERE table_schema = 'public' AND referenced_table_name IS NOT NULL
  ORDER BY table_name, constraint_name;
"

# Check indexes
echo "Checking indexes..."
psql $DATABASE_URL -c "
  SELECT indexname, tablename
  FROM pg_indexes
  WHERE schemaname = 'public'
  ORDER BY tablename, indexname;
"

echo "=== Verification Complete ==="
```

---

## Performance Impact

### Expected Changes

1. **Faster Queries**:
   - User's projects: ~50% faster (index on `user_id`)
   - Filter by status: ~40% faster (index on `status`)
   - Recent activity: ~60% faster (index on `timestamp`)

2. **Slower Writes**:
   - Insert operations: ~5-10% slower (index maintenance)
   - Update operations: ~5-10% slower (index maintenance)

3. **Storage**:
   - Indexes add ~15-20% to table size
   - Foreign keys add minimal overhead

### Monitoring

```bash
# Check index usage
psql $DATABASE_URL -c "
  SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
  FROM pg_stat_user_indexes
  ORDER BY idx_scan DESC;
"

# Check table sizes
psql $DATABASE_URL -c "
  SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
  FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## Troubleshooting

### Migration Fails with "Table Already Exists"

**Cause**: Migration already applied

**Solution**:
```bash
# Check current status
alembic current

# If already at 001, skip
# If at base, apply migration
alembic upgrade head
```

### Foreign Key Constraint Violation

**Cause**: Existing data violates new constraints

**Solution**:
```bash
# Check for orphaned records
SELECT * FROM projects WHERE user_id NOT IN (SELECT id FROM profiles);
SELECT * FROM crawl_jobs WHERE project_id NOT IN (SELECT id FROM projects);

# Delete orphaned records
DELETE FROM projects WHERE user_id NOT IN (SELECT id FROM profiles);
DELETE FROM crawl_jobs WHERE project_id NOT IN (SELECT id FROM projects);

# Retry migration
alembic upgrade head
```

### Index Creation Timeout

**Cause**: Large table takes too long to index

**Solution**:
```bash
# Create index concurrently (doesn't lock table)
CREATE INDEX CONCURRENTLY ix_crawl_job_status ON crawl_jobs(status);

# Or increase timeout
SET statement_timeout = '30min';
```

### Rollback Fails

**Cause**: Migration state corrupted

**Solution**:
```bash
# Check migration history
alembic history

# Manually fix state if needed
alembic stamp base  # Reset to base
alembic upgrade head  # Reapply all

# Or restore from backup
psql pixcrawler < backup_*.sql
```

---

## Post-Migration Tasks

### 1. Update Application Code

Ensure application code is compatible:

```python
# backend/models/__init__.py - Already updated
# backend/schemas/*.py - Already updated
# backend/repositories/*.py - May need updates
# backend/services/*.py - May need updates
```

### 2. Run Tests

```bash
# Run all tests
pytest

# Run specific test suite
pytest backend/tests/test_models.py
pytest backend/tests/test_repositories.py
pytest backend/tests/test_services.py
```

### 3. Verify API Endpoints

```bash
# Test API endpoints
curl http://localhost:8000/api/projects
curl http://localhost:8000/api/projects/1/crawl-jobs
curl http://localhost:8000/api/activity-logs
```

### 4. Monitor Performance

```bash
# Enable query logging
SET log_min_duration_statement = 100;  # Log queries > 100ms

# Check slow queries
SELECT query, calls, mean_time FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;
```

### 5. Update Documentation

- [ ] Update API documentation
- [ ] Update database schema docs
- [ ] Update developer guides
- [ ] Update deployment procedures

---

## Deployment Checklist

- [ ] Backup database
- [ ] Test migration in staging
- [ ] Verify all prerequisites
- [ ] Apply migration to production
- [ ] Verify schema
- [ ] Run tests
- [ ] Monitor application
- [ ] Monitor database performance
- [ ] Document changes

---

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Database Schema Documentation](./DATABASE_SCHEMA.md)
- [Schema Design Decisions](./SCHEMA_DECISIONS.md)

---

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review [Database Schema Documentation](./DATABASE_SCHEMA.md)
3. Check application logs
4. Contact database administrator

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 001 | 2024-11-14 | Initial schema with FKs, relationships, and indexes |

---

## Next Steps

After successful migration:

1. Update Pydantic schemas to use relationships
2. Update repositories to leverage relationships
3. Update services to use new job tables
4. Add API endpoints for validation and export jobs
5. Update frontend to use new API endpoints
