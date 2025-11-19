# Database Schema Decision Document

## Overview
This document outlines the strategic decisions made for the PixCrawler database schema alignment, specifically regarding the Project vs Dataset model strategy.

## Decision: Project Model as Primary Organizational Unit

### Choice
**Keep the `Project` model as the primary organizational unit for crawl jobs. Deprecate the standalone `Dataset` concept in favor of Project + CrawlJob composition.**

### Rationale

1. **Existing Implementation**: The database schema already has a `Project` model that serves as the organizational container for crawl jobs. Introducing a separate `Dataset` table would create redundancy.

2. **Semantic Alignment**: 
   - `Project` = User's organizational container (e.g., "Animal Classification Project")
   - `CrawlJob` = Individual crawling task within a project (e.g., "Collect cat images")
   - This hierarchy is more intuitive than having both Project and Dataset

3. **Relationship Clarity**:
   - One User → Many Projects (one-to-many)
   - One Project → Many CrawlJobs (one-to-many)
   - One CrawlJob → Many Images (one-to-many)

4. **API Schema Mapping**:
   - `DatasetResponse` Pydantic schema will map to `Project` model
   - `DatasetStats` will aggregate data from `Project` and `CrawlJob` tables
   - This avoids database-level duplication while maintaining API compatibility

### Implementation Impact

#### Models to Keep
- ✅ `Profile` - User profiles (references Supabase auth)
- ✅ `Project` - Project container (will add FK to Profile)
- ✅ `CrawlJob` - Individual crawl tasks (will add FK to Project)
- ✅ `Image` - Crawled images (will add FK to CrawlJob)
- ✅ `JobChunk` - Processing chunks (already has FK to CrawlJob)
- ✅ `ActivityLog` - Audit trail (will add FK to Profile)
- ✅ `CreditAccount` - User billing (will add FK to Profile)
- ✅ `CreditTransaction` - Transaction history (will add FKs)
- ✅ `APIKey` - API authentication
- ✅ `UsageMetric` - Usage tracking
- ✅ `Notification` - User notifications
- ✅ `NotificationPreference` - Notification settings

#### Pydantic Schemas to Update
- `DatasetResponse` → Maps to `Project` with aggregated `CrawlJob` statistics
- `DatasetCreate` → Maps to `ProjectCreate` (rename or create alias)
- `DatasetUpdate` → Maps to `ProjectUpdate`
- `DatasetStats` → Aggregates from `Project` and `CrawlJob` tables

#### Future Considerations
- If export/validation features are needed, create dedicated `ExportJob` and `ValidationJob` tables
- These would reference `CrawlJob` and track their own lifecycle independently

## Foreign Key Constraints

All models will enforce referential integrity at the database level:

```
Profile (id)
├── Project (user_id) → Profile.id
│   └── CrawlJob (project_id) → Project.id
│       ├── Image (crawl_job_id) → CrawlJob.id
│       └── JobChunk (job_id) → CrawlJob.id
├── ActivityLog (user_id) → Profile.id
├── CreditAccount (user_id) → Profile.id
│   └── CreditTransaction (account_id) → CreditAccount.id
│       └── CreditTransaction (user_id) → Profile.id
└── APIKey (user_id) → Profile.id
```

## Indexes for Performance

### Primary Indexes (High Priority)
- `Project.user_id` - Filter projects by user
- `CrawlJob.project_id` - Filter jobs by project
- `CrawlJob.status` - Filter jobs by status
- `Image.crawl_job_id` - Retrieve images for a job
- `ActivityLog.user_id` - Retrieve user activities

### Composite Indexes (Medium Priority)
- `(CrawlJob.project_id, CrawlJob.status)` - Common filter combination
- `(ActivityLog.user_id, ActivityLog.created_at)` - User activity timeline
- `(CreditTransaction.user_id, CreditTransaction.created_at)` - User transaction history

### Sorting Indexes (Medium Priority)
- `CrawlJob.created_at` - Sort jobs by creation date
- `Image.created_at` - Sort images by creation date
- `ActivityLog.timestamp` - Sort activities by time

## Migration Strategy

1. **Phase 1**: Add all foreign key constraints
2. **Phase 2**: Add all indexes
3. **Phase 3**: Add SQLAlchemy relationships
4. **Phase 4**: Test and validate data integrity

All changes will be applied in a single Alembic migration for atomicity.

## Validation Checklist

- ✅ All foreign keys defined in models
- ✅ All relationships defined with proper cascade behaviors
- ✅ All indexes created for performance
- ✅ Alembic migration created and tested
- ✅ Schema documentation updated
- ✅ Pydantic schemas aligned with models
