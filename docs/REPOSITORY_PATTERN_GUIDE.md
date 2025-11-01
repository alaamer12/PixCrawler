# Repository Pattern Implementation Guide

## Overview

PixCrawler implements the **Repository Pattern** for clean separation between business logic and data access. This is a critical architectural pattern for production-ready FastAPI applications.

---

## Architecture Layers

```
┌─────────────────────────────────────────┐
│ API ENDPOINTS (Controllers)             │
│ - Route handlers                        │
│ - Request/Response validation           │
│ - Dependency injection                  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ SERVICE LAYER (Business Logic)          │
│ - Orchestration                         │
│ - Business rules & validation           │
│ - Transaction management                │
│ - Uses repositories (NOT DB directly)   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ REPOSITORY LAYER (Data Access)          │
│ - CRUD operations                       │
│ - Complex queries                       │
│ - Database-specific logic               │
│ - Direct SQLAlchemy access              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ DATABASE (PostgreSQL/Supabase)          │
└─────────────────────────────────────────┘
```

---

## Directory Structure

```
backend/
├── repositories/              # Data Access Layer
│   ├── __init__.py           # Exports all repositories
│   ├── base.py               # BaseRepository with CRUD
│   ├── crawl_job_repository.py
│   ├── project_repository.py
│   ├── image_repository.py
│   ├── user_repository.py
│   └── activity_log_repository.py
│
├── services/                  # Business Logic Layer
│   ├── base.py               # BaseService
│   ├── crawl_job.py          # Uses repositories
│   ├── dataset.py
│   └── validation.py
│
└── api/                       # API Layer
    ├── dependencies.py        # DI for services
    └── v1/endpoints/
        └── crawl_jobs.py      # Uses services via DI
```

---

## Implementation Examples

### 1. Repository Layer

```python
# backend/repositories/crawl_job_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import CrawlJob
from .base import BaseRepository

class CrawlJobRepository(BaseRepository[CrawlJob]):
    """Repository for CrawlJob data access."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, CrawlJob)
    
    async def get_by_project(self, project_id: int) -> List[CrawlJob]:
        """Get all jobs for a project."""
        result = await self.session.execute(
            select(CrawlJob).where(CrawlJob.project_id == project_id)
        )
        return list(result.scalars().all())
    
    async def get_active_jobs(self) -> List[CrawlJob]:
        """Get all active jobs."""
        result = await self.session.execute(
            select(CrawlJob).where(CrawlJob.status == "running")
        )
        return list(result.scalars().all())
```

### 2. Service Layer

```python
# backend/services/crawl_job.py
from backend.repositories import (
    CrawlJobRepository,
    ProjectRepository,
    ImageRepository
)

class CrawlJobService(BaseService):
    """Service for crawl job business logic."""
    
    def __init__(
        self,
        crawl_job_repo: CrawlJobRepository,
        project_repo: ProjectRepository,
        image_repo: ImageRepository
    ):
        super().__init__()
        self.crawl_job_repo = crawl_job_repo
        self.project_repo = project_repo
        self.image_repo = image_repo
    
    async def create_job(
        self,
        project_id: int,
        name: str,
        keywords: List[str]
    ) -> CrawlJob:
        """Create a new crawl job (business logic)."""
        
        # ✅ Use repository instead of direct DB access
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")
        
        # ✅ Business logic: validate keywords
        if not keywords:
            raise ValidationError("Keywords cannot be empty")
        
        # ✅ Use repository to create
        job = await self.crawl_job_repo.create(
            project_id=project_id,
            name=name,
            keywords={"keywords": keywords},
            status="pending"
        )
        
        return job
```

### 3. API Layer with Dependency Injection

```python
# backend/api/dependencies.py
from backend.repositories import CrawlJobRepository, ProjectRepository
from backend.services.crawl_job import CrawlJobService

async def get_crawl_job_service(
    session: AsyncSession = Depends(get_session)
) -> CrawlJobService:
    """Dependency injection for CrawlJobService."""
    crawl_job_repo = CrawlJobRepository(session)
    project_repo = ProjectRepository(session)
    image_repo = ImageRepository(session)
    
    return CrawlJobService(
        crawl_job_repo=crawl_job_repo,
        project_repo=project_repo,
        image_repo=image_repo
    )
```

```python
# backend/api/v1/endpoints/crawl_jobs.py
from fastapi import APIRouter, Depends
from backend.services.crawl_job import CrawlJobService
from backend.api.dependencies import get_crawl_job_service

router = APIRouter()

@router.post("/")
async def create_crawl_job(
    request: CreateJobRequest,
    service: CrawlJobService = Depends(get_crawl_job_service)
):
    """Create a new crawl job."""
    return await service.create_job(
        project_id=request.project_id,
        name=request.name,
        keywords=request.keywords
    )

@router.get("/{job_id}")
async def get_crawl_job(
    job_id: int,
    service: CrawlJobService = Depends(get_crawl_job_service)
):
    """Get crawl job by ID."""
    job = await service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
```

---

## Benefits

| Aspect | Without Repositories | With Repositories |
|--------|---------------------|-------------------|
| **Testability** | Hard to mock DB | Easy to mock repos |
| **Separation** | Mixed concerns | Clear layers |
| **Reusability** | Duplicate queries | Reusable queries |
| **Maintainability** | DB logic scattered | Centralized data access |
| **Flexibility** | Tight coupling | Easy to swap DB |

---

## Testing

### Mock Repositories for Unit Tests

```python
# tests/test_crawl_job_service.py
import pytest
from unittest.mock import AsyncMock
from backend.services.crawl_job import CrawlJobService

@pytest.mark.asyncio
async def test_create_job():
    # Mock repositories
    crawl_job_repo = AsyncMock()
    project_repo = AsyncMock()
    image_repo = AsyncMock()
    
    # Setup mocks
    project_repo.get_by_id.return_value = {"id": 1, "name": "Test"}
    crawl_job_repo.create.return_value = {"id": 1, "status": "pending"}
    
    # Create service with mocked repos
    service = CrawlJobService(
        crawl_job_repo=crawl_job_repo,
        project_repo=project_repo,
        image_repo=image_repo
    )
    
    # Test
    job = await service.create_job(
        project_id=1,
        name="Test Job",
        keywords=["cat"]
    )
    
    assert job["status"] == "pending"
    project_repo.get_by_id.assert_called_once_with(1)
    crawl_job_repo.create.assert_called_once()
```

---

## Migration Checklist

When refactoring existing services to use repositories:

- [ ] Create repository for each model
- [ ] Add custom query methods to repository
- [ ] Update service constructor to accept repositories
- [ ] Replace direct DB queries with repository calls
- [ ] Remove `session` attribute from service
- [ ] Create dependency injection function
- [ ] Update API endpoints to use DI
- [ ] Update tests to mock repositories
- [ ] Remove SQLAlchemy imports from services

---

## Common Patterns

### 1. Custom Queries in Repository

```python
class CrawlJobRepository(BaseRepository[CrawlJob]):
    async def get_jobs_with_high_progress(self, min_progress: int = 80):
        """Get jobs with progress above threshold."""
        result = await self.session.execute(
            select(CrawlJob)
            .where(CrawlJob.progress >= min_progress)
            .order_by(CrawlJob.progress.desc())
        )
        return list(result.scalars().all())
```

### 2. Transaction Management in Service

```python
class CrawlJobService:
    async def create_job_with_images(self, job_data, images_data):
        """Create job and images in single transaction."""
        # Both repos share same session = same transaction
        job = await self.crawl_job_repo.create(**job_data)
        
        for image_data in images_data:
            image_data['crawl_job_id'] = job.id
        
        await self.image_repo.bulk_create(images_data)
        # Transaction commits when session commits
        return job
```

### 3. Bulk Operations

```python
class ImageRepository(BaseRepository[Image]):
    async def bulk_create(self, images_data: List[dict]) -> List[Image]:
        """Create multiple images efficiently."""
        images = [Image(**data) for data in images_data]
        self.session.add_all(images)
        await self.session.commit()
        
        for image in images:
            await self.session.refresh(image)
        
        return images
```

---

## Best Practices

1. **One Repository Per Model** - Each model gets its own repository
2. **Keep Repositories Thin** - Only data access, no business logic
3. **Services Orchestrate** - Services use multiple repositories
4. **Dependency Injection** - Always inject repositories into services
5. **Test with Mocks** - Mock repositories for fast unit tests
6. **Shared Session** - All repositories in a service share the same session
7. **Custom Queries** - Add domain-specific queries to repositories
8. **No Direct DB in Services** - Services never import SQLAlchemy

---

## Related Documentation

- [Clean Architecture Guide](./ARCHITECTURE_SUMMARY.md)
- [Chunk Orchestration Guide](./CHUNK_ORCHESTRATION_GUIDE.md)
- [API Design Patterns](./API_DESIGN.md)
