# Alembic Migrations for PixCrawler

This directory contains Alembic database migrations for PixCrawler.

## Overview

Alembic is a lightweight database migration tool for SQLAlchemy. It allows us to:
- Version control database schema changes
- Automatically generate migration scripts
- Apply and rollback migrations safely
- Track schema evolution over time

## Directory Structure

```
alembic/
├── versions/          # Migration scripts
├── env.py            # Alembic environment configuration
├── script.py.mako    # Migration template
└── README.md         # This file
```

## Common Commands

### Create a new migration

```bash
# Auto-generate migration based on model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration for manual editing
alembic revision -m "Description of changes"
```

### Apply migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Apply to specific revision
alembic upgrade 001
```

### Rollback migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 001

# Rollback all migrations
alembic downgrade base
```

### View migration history

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show detailed history
alembic history --verbose
```

## Initial Migration

The initial migration (`001_initial_schema.py`) creates:

- **profiles**: User profiles (references Supabase auth)
- **projects**: User projects for organizing crawl jobs
- **crawl_jobs**: Image crawl jobs with chunk tracking
- **images**: Metadata for crawled images
- **activity_logs**: User activity tracking
- **validation_jobs**: Image validation tasks
- **export_jobs**: Dataset export tasks

### Foreign Key Relationships

```
Profile (1) ──────── (N) Project
  │                      │
  │                      └──── (1) ──── (N) CrawlJob
  │                                         │
  │                                         ├──── (1) ──── (N) Image
  │                                         ├──── (1) ──── (N) ValidationJob
  │                                         └──── (1) ──── (N) ExportJob
  │
  └──── (1) ──── (N) ActivityLog
```

### Indexes for Performance

- `profiles.email` - User lookup by email
- `projects.user_id` - User's projects
- `crawl_jobs.status` - Filter by status
- `crawl_jobs(project_id, status)` - Composite for common queries
- `images.crawl_job_id` - Job's images
- `activity_logs.user_id` - User's activity
- `activity_logs.timestamp` - Sort by time
- `validation_jobs.status` - Filter by status
- `export_jobs.status` - Filter by status
- `export_jobs.user_id` - User's exports

## Migration Best Practices

1. **Always test migrations** before deploying to production
2. **Keep migrations small** - one logical change per migration
3. **Write both upgrade and downgrade** - ensure reversibility
4. **Use descriptive names** - clearly describe what changes
5. **Document complex migrations** - add comments explaining why
6. **Review auto-generated migrations** - verify they're correct
7. **Test rollbacks** - ensure downgrade works correctly

## Environment Configuration

The `env.py` file handles:
- Loading database URL from settings
- Converting async URLs to sync for migrations
- Configuring SQLAlchemy engine
- Running migrations in online/offline mode

## Troubleshooting

### Migration conflicts

If you have conflicting migrations:
```bash
# Merge conflicting branches
alembic merge -m "Merge branches"
```

### Reset database

```bash
# Drop all tables and start fresh
alembic downgrade base

# Then apply all migrations
alembic upgrade head
```

### Check migration status

```bash
# Show which migrations are pending
alembic current
alembic history
```

## Integration with CI/CD

For automated deployments:

```bash
# In your deployment script
alembic upgrade head
```

This ensures database schema is up-to-date before starting the application.

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
