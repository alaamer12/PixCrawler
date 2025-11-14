# Database Schema - Quick Reference

## Schema Overview

```
Profile (User)
  ├── 1:N → Project
  │         ├── 1:N → CrawlJob
  │         │         ├── 1:N → Image
  │         │         ├── 1:N → ValidationJob
  │         │         └── 1:N → ExportJob
  │         └── (user_id FK)
  │
  ├── 1:N → ActivityLog
  │         └── (user_id FK, nullable)
  │
  └── 1:N → ExportJob
            └── (user_id FK)
```

---

## Tables at a Glance

| Table | Purpose | Key Fields | Indexes |
|-------|---------|-----------|---------|
| **profiles** | Users | id (UUID), email, role | email |
| **projects** | Project containers | id, name, user_id (FK) | user_id |
| **crawl_jobs** | Image crawl tasks | id, project_id (FK), status | status, (project_id, status) |
| **images** | Crawled images | id, crawl_job_id (FK), url | crawl_job_id |
| **activity_logs** | User activity | id, user_id (FK), action | user_id, timestamp |
| **validation_jobs** | Image validation | id, crawl_job_id (FK), status | status, crawl_job_id |
| **export_jobs** | Dataset export | id, crawl_job_id (FK), user_id (FK) | status, user_id, crawl_job_id |

---

## Foreign Keys

```sql
-- projects.user_id → profiles.id (CASCADE)
ALTER TABLE projects ADD CONSTRAINT fk_projects_user_id
  FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;

-- crawl_jobs.project_id → projects.id (CASCADE)
ALTER TABLE crawl_jobs ADD CONSTRAINT fk_crawl_jobs_project_id
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- images.crawl_job_id → crawl_jobs.id (CASCADE)
ALTER TABLE images ADD CONSTRAINT fk_images_crawl_job_id
  FOREIGN KEY (crawl_job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE;

-- activity_logs.user_id → profiles.id (SET NULL)
ALTER TABLE activity_logs ADD CONSTRAINT fk_activity_logs_user_id
  FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE SET NULL;

-- validation_jobs.crawl_job_id → crawl_jobs.id (CASCADE)
ALTER TABLE validation_jobs ADD CONSTRAINT fk_validation_jobs_crawl_job_id
  FOREIGN KEY (crawl_job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE;

-- export_jobs.crawl_job_id → crawl_jobs.id (CASCADE)
ALTER TABLE export_jobs ADD CONSTRAINT fk_export_jobs_crawl_job_id
  FOREIGN KEY (crawl_job_id) REFERENCES crawl_jobs(id) ON DELETE CASCADE;

-- export_jobs.user_id → profiles.id (CASCADE)
ALTER TABLE export_jobs ADD CONSTRAINT fk_export_jobs_user_id
  FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
```

---

## Indexes

```sql
-- Lookup indexes
CREATE INDEX ix_profiles_email ON profiles(email);
CREATE INDEX ix_project_user_id ON projects(user_id);
CREATE INDEX ix_crawl_job_status ON crawl_jobs(status);
CREATE INDEX ix_crawl_jobs_project_id ON crawl_jobs(project_id);
CREATE INDEX ix_image_crawl_job_id ON images(crawl_job_id);
CREATE INDEX ix_activity_log_user_id ON activity_logs(user_id);
CREATE INDEX ix_activity_log_timestamp ON activity_logs(timestamp);
CREATE INDEX ix_validation_job_status ON validation_jobs(status);
CREATE INDEX ix_validation_job_crawl_job_id ON validation_jobs(crawl_job_id);
CREATE INDEX ix_export_job_status ON export_jobs(status);
CREATE INDEX ix_export_job_user_id ON export_jobs(user_id);
CREATE INDEX ix_export_job_crawl_job_id ON export_jobs(crawl_job_id);

-- Composite index
CREATE INDEX ix_crawl_job_project_status ON crawl_jobs(project_id, status);
```

---

## Common Queries

### Get User's Projects
```sql
SELECT * FROM projects 
WHERE user_id = $1 
ORDER BY created_at DESC;
-- Uses: ix_project_user_id
```

### Get Active Jobs
```sql
SELECT * FROM crawl_jobs 
WHERE project_id = $1 AND status = 'running'
ORDER BY created_at DESC;
-- Uses: ix_crawl_job_project_status
```

### Get Job's Images
```sql
SELECT * FROM images 
WHERE crawl_job_id = $1 
LIMIT 100;
-- Uses: ix_image_crawl_job_id
```

### Get Recent Activity
```sql
SELECT * FROM activity_logs 
WHERE user_id = $1 
ORDER BY timestamp DESC 
LIMIT 50;
-- Uses: ix_activity_log_timestamp
```

### Get Export Jobs
```sql
SELECT * FROM export_jobs 
WHERE user_id = $1 AND status = 'completed'
ORDER BY created_at DESC;
-- Uses: ix_export_job_user_id
```

---

## SQLAlchemy Usage

### Load Relationships
```python
from backend.models import Profile, Project, CrawlJob

# Get profile with projects
profile = session.query(Profile).filter_by(id=user_id).first()
projects = profile.projects  # Lazy loaded

# Get project with jobs
project = session.query(Project).filter_by(id=project_id).first()
jobs = project.crawl_jobs  # Lazy loaded

# Get job with images
job = session.query(CrawlJob).filter_by(id=job_id).first()
images = job.images  # Lazy loaded
```

### Eager Loading
```python
from sqlalchemy.orm import joinedload

# Load profile with projects eagerly
profile = session.query(Profile)\
    .options(joinedload(Profile.projects))\
    .filter_by(id=user_id)\
    .first()

# Load project with jobs and images
project = session.query(Project)\
    .options(joinedload(Project.crawl_jobs).joinedload(CrawlJob.images))\
    .filter_by(id=project_id)\
    .first()
```

### Create with Relationships
```python
# Create profile
profile = Profile(id=uuid, email="user@example.com", role="user")

# Create project
project = Project(name="My Project", user=profile)

# Create job
job = CrawlJob(name="Crawl Job", project=project, keywords=["cat", "dog"])

# Create image
image = Image(original_url="https://...", crawl_job=job)

session.add(profile)
session.commit()
```

### Delete with Cascade
```python
# Delete profile - cascades to projects, jobs, images
session.delete(profile)
session.commit()

# Delete project - cascades to jobs, images
session.delete(project)
session.commit()

# Delete job - cascades to images, validation_jobs, export_jobs
session.delete(job)
session.commit()
```

---

## Pydantic Schemas

### Profile Response
```python
from backend.schemas.profile import ProfileResponse

response = ProfileResponse(
    id=uuid,
    email="user@example.com",
    full_name="John Doe",
    role="user",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)
```

### Project Response
```python
from backend.schemas.projects import ProjectResponse, ProjectDetailResponse

# Basic response
response = ProjectResponse(
    id=1,
    name="My Project",
    user_id=uuid,
    status="active",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)

# Detailed response with jobs
detail = ProjectDetailResponse(
    id=1,
    name="My Project",
    user_id=uuid,
    status="active",
    crawl_jobs=[...],  # List of CrawlJobResponse
    created_at=datetime.now(),
    updated_at=datetime.now(),
)
```

### CrawlJob Response
```python
from backend.schemas.crawl_jobs import CrawlJobResponse

response = CrawlJobResponse(
    id=1,
    project_id=1,
    name="Google Images Crawl",
    keywords={"keywords": ["cat", "dog"]},
    status="running",
    progress=45,
    total_images=1000,
    downloaded_images=450,
    valid_images=400,
    total_chunks=10,
    active_chunks=2,
    completed_chunks=7,
    failed_chunks=1,
    created_at=datetime.now(),
    updated_at=datetime.now(),
)
```

### Validation Job Response
```python
from backend.schemas.jobs import ValidationJobResponse

response = ValidationJobResponse(
    id=1,
    crawl_job_id=1,
    name="Image Validation",
    status="running",
    progress=60,
    total_images=400,
    validated_images=240,
    invalid_images=10,
    validation_rules={"min_width": 100, "min_height": 100},
    created_at=datetime.now(),
    updated_at=datetime.now(),
)
```

### Export Job Response
```python
from backend.schemas.jobs import ExportJobResponse

response = ExportJobResponse(
    id=1,
    crawl_job_id=1,
    user_id=uuid,
    name="Export Dataset",
    status="completed",
    progress=100,
    format="zip",
    total_images=400,
    exported_images=400,
    file_size=52428800,  # 50MB
    download_url="https://storage.example.com/exports/1.zip",
    export_options={"include_metadata": True},
    created_at=datetime.now(),
    updated_at=datetime.now(),
)
```

---

## Migration Commands

```bash
# Check status
alembic current
alembic history

# Apply migrations
alembic upgrade head
alembic upgrade +1

# Rollback
alembic downgrade -1
alembic downgrade base

# Create migration
alembic revision --autogenerate -m "Description"

# Show SQL
alembic upgrade head --sql
```

---

## Performance Tips

1. **Use indexes for WHERE clauses**
   - Filter by `user_id`, `status`, `timestamp`
   - Use composite index for `(project_id, status)`

2. **Eager load relationships when needed**
   - Avoid N+1 queries
   - Use `joinedload()` for related data

3. **Limit result sets**
   - Use `LIMIT` and `OFFSET` for pagination
   - Avoid loading entire tables

4. **Monitor slow queries**
   - Enable `log_min_duration_statement`
   - Check `pg_stat_statements`

5. **Analyze query plans**
   - Use `EXPLAIN ANALYZE`
   - Verify index usage

---

## Troubleshooting

### FK Constraint Violation
```sql
-- Check for orphaned records
SELECT * FROM projects WHERE user_id NOT IN (SELECT id FROM profiles);
SELECT * FROM crawl_jobs WHERE project_id NOT IN (SELECT id FROM projects);

-- Delete orphaned records
DELETE FROM projects WHERE user_id NOT IN (SELECT id FROM profiles);
```

### Slow Queries
```sql
-- Check index usage
SELECT * FROM pg_stat_user_indexes ORDER BY idx_scan DESC;

-- Analyze query plan
EXPLAIN ANALYZE SELECT * FROM projects WHERE user_id = $1;

-- Rebuild index if needed
REINDEX INDEX ix_project_user_id;
```

### Migration Issues
```bash
# Check migration status
alembic current

# Reset to base
alembic stamp base

# Reapply all migrations
alembic upgrade head
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `backend/models/__init__.py` | SQLAlchemy models |
| `backend/models/jobs.py` | ValidationJob, ExportJob models |
| `backend/schemas/projects.py` | Project schemas |
| `backend/schemas/crawl_jobs.py` | CrawlJob schemas |
| `backend/schemas/jobs.py` | ValidationJob, ExportJob schemas |
| `alembic/env.py` | Alembic environment |
| `alembic/versions/001_initial_schema.py` | Initial migration |
| `docs/DATABASE_SCHEMA.md` | Complete schema documentation |
| `docs/SCHEMA_DECISIONS.md` | Design decisions |
| `docs/MIGRATION_GUIDE.md` | Migration instructions |

---

## Key Dates

- **Implementation**: 2024-11-14
- **Migration Version**: 001
- **Status**: Ready for testing

---

## Support

For detailed information:
- Schema details: See `DATABASE_SCHEMA.md`
- Design decisions: See `SCHEMA_DECISIONS.md`
- Migration steps: See `MIGRATION_GUIDE.md`
- Alembic help: See `alembic/README.md`
