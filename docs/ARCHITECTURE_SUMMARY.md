# PixCrawler Backend Architecture Summary

## Overview

The PixCrawler backend has been designed as a **Shared Supabase Database** architecture that integrates seamlessly with the existing Next.js frontend. This approach maximizes development velocity while leveraging the existing Supabase infrastructure.

## Architecture Decision

Following ADR-001, we implemented a shared database approach where:

- **Frontend**: Next.js + Drizzle ORM + Supabase Client (anon key + RLS)
- **Backend**: FastAPI + SQLAlchemy + Supabase Client (service role key)
- **Database**: Single Supabase PostgreSQL instance
- **Auth**: Supabase Auth (no custom JWT implementation)

## Key Components

### 1. Database Models (`backend/database/models.py`)
- **Synchronized with Drizzle Schema**: SQLAlchemy models mirror the frontend Drizzle schema
- **UUID Support**: Uses Supabase auth.users UUID references
- **JSON Fields**: PostgreSQL JSONB for complex data structures
- **Models**: Profile, Project, CrawlJob, Image, ActivityLog

### 2. Supabase Auth Integration
- **Service**: `backend/services/supabase_auth.py` - Token verification and user management
- **Dependencies**: `backend/api/dependencies.py` - Auth injection for endpoints
- **Endpoints**: Profile management and token verification (not login/signup)

### 3. Crawl Job Management
- **Service**: `backend/services/crawl_job.py` - Job creation and execution
- **Endpoints**: `backend/api/v1/endpoints/crawl_jobs.py` - API for job management
- **Integration**: Uses PixCrawler builder package for actual crawling

### 4. Real-time Updates
- **Frontend**: Continues using Supabase real-time subscriptions
- **Backend**: Updates database directly, triggering real-time notifications
- **No Custom WebSockets**: Leverages existing Supabase infrastructure

## API Endpoints

### Authentication (Supabase Integration)
```
GET  /api/v1/auth/me              - Get current user profile
POST /api/v1/auth/verify-token    - Verify Supabase JWT token  
POST /api/v1/auth/sync-profile    - Sync user profile
```

### Crawl Jobs (Primary Feature)
```
POST /api/v1/crawl-jobs/          - Create and start crawl job
GET  /api/v1/crawl-jobs/{id}      - Get job status and progress
POST /api/v1/crawl-jobs/{id}/cancel - Cancel running job
```

### Health & Monitoring
```
GET  /api/v1/health/              - Service health check
```

## Data Flow

### 1. Job Creation Flow
```
Frontend → POST /api/v1/crawl-jobs/ → Backend → Database → Background Task
                                                     ↓
Frontend ← Real-time Updates ← Database ← Progress Updates ← Crawl Execution
```

### 2. Authentication Flow
```
Frontend → Supabase Auth → JWT Token → Backend API → Token Verification → User Context
```

### 3. Real-time Updates Flow
```
Backend → Database Update → Supabase Real-time → Frontend Subscription → UI Update
```

## Configuration

### Environment Variables
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Database (same Supabase instance)
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres

# Application
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# Redis & Celery (optional for future scaling)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
```

## Benefits Achieved

### ✅ **Fast Development (1-2 weeks)**
- No frontend changes required
- Leverages existing Supabase investment
- Direct database access for high performance

### ✅ **Single Source of Truth**
- No data synchronization complexity
- Consistent data across frontend/backend
- Real-time updates work seamlessly

### ✅ **Minimal Operational Overhead**
- One database to manage
- Existing Supabase monitoring and backups
- No custom auth infrastructure

### ✅ **Builder Package Integration**
- Seamless integration with existing crawling logic
- Background job execution with progress tracking
- Error handling and status updates

## Trade-offs Accepted

### ⚠️ **Vendor Lock-in to Supabase**
- **Mitigation**: Standard PostgreSQL underneath, migration possible
- **Acceptable**: Productivity gains outweigh long-term flexibility concerns

### ⚠️ **Manual Schema Synchronization**
- **Mitigation**: Drizzle schema as source of truth, code review process
- **Acceptable**: Simpler than automated sync for current team size

### ⚠️ **Service Role Key Security**
- **Mitigation**: Secure key storage, explicit authorization checks in code
- **Acceptable**: Standard practice for backend services

## Success Metrics

- ✅ **Functional Integration**: Crawl jobs created in frontend execute in backend
- ✅ **Real-time Updates**: Job status updates appear in frontend immediately
- ✅ **Performance**: Database queries under 100ms for 95% of requests
- ✅ **Developer Experience**: Clear separation of concerns, easy to extend

## Future Considerations

### Scaling Options
1. **Connection Pooling**: Monitor Supabase connection limits
2. **Read Replicas**: Use Supabase read replicas for heavy queries
3. **Caching Layer**: Add Redis for frequently accessed data
4. **Queue System**: Add Celery for more complex background processing

### Migration Path
If vendor lock-in becomes a concern:
1. **Database Migration**: Standard PostgreSQL migration tools
2. **Auth Migration**: Implement custom auth service
3. **Real-time Migration**: Custom WebSocket implementation
4. **API-First Refactor**: Gradually move frontend to API calls

## Development Workflow

### 1. Schema Changes
1. Update Drizzle schema in frontend
2. Run Drizzle migrations
3. Update corresponding SQLAlchemy models in backend
4. Test both frontend and backend

### 2. New Features
1. Define API endpoints in backend
2. Implement business logic with builder integration
3. Add real-time subscriptions in frontend if needed
4. Test end-to-end functionality

### 3. Deployment
1. Deploy backend with environment variables
2. Verify Supabase connectivity
3. Test authentication flow
4. Monitor connection usage

This architecture provides a solid foundation for rapid development while maintaining the flexibility to evolve as the product grows.