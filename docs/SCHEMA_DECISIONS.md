# Database Schema Design Decisions

## Decision: Keep Project/CrawlJob Model, Deprecate Dataset

**Date**: 2024-11-14  
**Status**: APPROVED  
**Impact**: Database schema, API contracts, Pydantic schemas

---

## Executive Summary

After analyzing the codebase, we decided to **consolidate on the Project/CrawlJob model** and **deprecate the Dataset schema**. This reduces schema duplication, improves maintainability, and aligns the backend with the existing data model.

---

## Analysis

### Current State

The codebase has **two parallel data models** for the same concept:

#### Model 1: Project/CrawlJob (Primary)
- **Location**: `backend/models/__init__.py`
- **Status**: Active, used in repositories and services
- **Features**: Chunk tracking, progress monitoring, timestamps
- **Scope**: Fully featured production model

#### Model 2: Dataset (Legacy/Alternative)
- **Location**: `backend/schemas/dataset.py`
- **Status**: Defined but underutilized
- **Features**: Basic dataset lifecycle management
- **Scope**: Appears to be alternative interface

### Comparison

| Feature | Project/CrawlJob | Dataset |
|---------|------------------|---------|
| Chunk tracking | Yes | No |
| Progress monitoring | Yes | Yes |
| Search engines | No | Yes |
| Validation rules | No | No |
| Export options | No | No |
| Timestamps | Yes | Yes |
| Repository support | Yes | No |
| Service support | Yes | No |
| API endpoints | Yes | No |

---

## Decision Rationale

### 1. Reduce Duplication

**Problem**: Maintaining two models for the same concept increases:
- Code complexity
- Testing burden
- Documentation overhead
- Migration complexity

**Solution**: Consolidate on Project/CrawlJob, which is:
- Already fully implemented
- Already integrated with services and repositories
- Already exposed via API
- Already used in production code

### 2. Leverage Existing Infrastructure

**Project/CrawlJob has**:
- Repository pattern implementation
- Service layer integration
- API endpoints
- Chunk tracking for distributed processing
- Comprehensive progress tracking

**Dataset has**:
- No repository implementation
- No service layer integration
- No API endpoints
- No chunk tracking
- Limited progress tracking

### 3. Align with Architecture

The project uses:
- **Repository Pattern**: Project/CrawlJob repositories exist
- **Service Layer**: Project/CrawlJob services exist
- **API Routes**: Project/CrawlJob routes exist
- **Chunk Processing**: CrawlJob supports Celery chunks

Dataset doesn't fit this architecture.

### 4. Future Extensibility

Project/CrawlJob can be extended with:
- Search engine selection (add to CrawlJob)
- Validation rules (add ValidationJob table)
- Export options (add ExportJob table)
- Custom processing pipelines

Dataset would require parallel implementation.

---

## Implementation Plan

### Phase 1: Consolidate Models - DONE

- Add foreign key constraints to Project/CrawlJob
- Add SQLAlchemy relationships
- Add database indexes
- Create ValidationJob table
- Create ExportJob table
- Initialize Alembic migrations

### Phase 2: Update Pydantic Schemas (TODO)

- Update `CrawlJobResponse` to include relationships
- Update `ProjectResponse` to include crawl_jobs
- Update `ProfileResponse` to include projects
- Add `ValidationJobResponse` schema
- Add `ExportJobResponse` schema
- Keep `DatasetResponse` for backward compatibility (deprecated)

### Phase 3: Deprecate Dataset (TODO)

- Mark `DatasetResponse` as deprecated in docstrings
- Add deprecation warning in API docs
- Plan removal in v1.0.0
- Provide migration guide for API consumers

### Phase 4: Update API Endpoints (TODO)

- Ensure Project/CrawlJob endpoints are complete
- Add ValidationJob endpoints
- Add ExportJob endpoints
- Document migration from Dataset to CrawlJob

### Phase 5: Update Documentation (TODO)

- Update API documentation
- Update database schema docs
- Update developer guides
- Add migration guide for consumers

---

## Migration Path for API Consumers

### Old Way (Dataset)
```python
# Create dataset
POST /api/datasets
{
  "name": "My Dataset",
  "keywords": ["cat", "dog"],
  "max_images": 1000,
  "search_engines": ["google", "bing"]
}

# Get dataset
GET /api/datasets/{id}
```

### New Way (Project + CrawlJob)
```python
# Create project
POST /api/projects
{
  "name": "My Project",
  "description": "Image collection project"
}

# Create crawl job in project
POST /api/projects/{project_id}/crawl-jobs
{
  "name": "Google Images Crawl",
  "keywords": ["cat", "dog"],
  "max_images": 1000,
  "sources": ["google", "bing"]
}

# Get crawl job
GET /api/projects/{project_id}/crawl-jobs/{job_id}
```

### Benefits of New Way
- Organize multiple jobs per project
- Better progress tracking with chunks
- Validation and export as separate jobs
- More flexible and extensible
- Aligns with actual application architecture

---

## Backward Compatibility

### Short Term (v0.x)

- Keep `DatasetResponse` schema
- Keep Dataset endpoints if they exist
- Add deprecation warnings in responses
- Document migration path

### Long Term (v1.0+)

- Remove Dataset schema
- Remove Dataset endpoints
- Require migration to Project/CrawlJob
- Provide migration script if needed

---

## Risk Assessment

### Low Risk
- Project/CrawlJob already in production
- No existing Dataset API consumers (internal only)
- Clear migration path
- Backward compatibility maintained

### Mitigation
- Document decision clearly
- Provide migration guide
- Add deprecation warnings
- Plan removal timeline

---

## Related Changes

### Models Updated
- Profile: Added projects and activity_logs relationships
- Project: Added user and crawl_jobs relationships, FK constraints
- CrawlJob: Added project and images relationships, FK constraints
- Image: Added crawl_job relationship, FK constraint
- ActivityLog: Added user relationship, FK constraint
- ValidationJob: New table with relationships
- ExportJob: New table with relationships

### Indexes Added
- profiles.email
- projects.user_id
- crawl_jobs.status
- crawl_jobs(project_id, status) - composite
- images.crawl_job_id
- activity_logs.user_id
- activity_logs.timestamp
- validation_jobs.status
- export_jobs.status
- export_jobs.user_id

### Migrations Created
- 001_initial_schema.py - Creates all tables with FKs and indexes

---

## Future Enhancements

### Planned Features
1. **Search Engine Selection**: Add sources field to CrawlJob
2. **Validation Pipeline**: Use ValidationJob for image validation
3. **Export Formats**: Use ExportJob for dataset export
4. **Batch Processing**: Leverage chunk tracking for parallel processing
5. **Job Scheduling**: Schedule crawl jobs for recurring tasks
6. **Job Templates**: Save job configurations as templates

### Extensibility Points
- CrawlJob.keywords → Can add source selection
- ValidationJob.validation_rules → Can add custom validators
- ExportJob.export_options → Can add format-specific options
- ActivityLog.metadata_ → Can track detailed changes

---

## References

### Related Files
- `backend/models/__init__.py` - SQLAlchemy models
- `backend/models/jobs.py` - ValidationJob and ExportJob
- `backend/schemas/crawl_jobs.py` - CrawlJob schemas
- `backend/schemas/dataset.py` - Dataset schemas (deprecated)
- `alembic/versions/001_initial_schema.py` - Database migration
- `docs/DATABASE_SCHEMA.md` - Schema documentation

### Documentation
- [SQLAlchemy Relationships](https://docs.sqlalchemy.org/en/20/orm/relationships.html)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Database Design](https://en.wikipedia.org/wiki/Database_normalization)

---

## Approval

- **Decided By**: Architecture Review
- **Date**: 2024-11-14
- **Status**: APPROVED
- **Next Review**: v1.0.0 release (for Dataset removal)
