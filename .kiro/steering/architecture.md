---
trigger: model_decision
description: Architecture decisions and patterns for PixCrawler, including shared database approach, authentication strategy, and deployment architecture.
---

ALWAYS USE .venv, ie. `.venv\scripts\python <command>`

# PixCrawler Architecture

## Architecture Decision: Shared Database Approach

Following ADR-001, PixCrawler implements a **Shared Supabase Database** architecture that integrates seamlessly with the Next.js frontend while providing a powerful FastAPI backend.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     PixCrawler Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐              ┌──────────────────┐     │
│  │   Frontend       │              │   Backend        │     │
│  │   Next.js 15     │◄────────────►│   FastAPI        │     │
│  │   React 19       │   REST API   │   Python 3.11+   │     │
│  │   Drizzle ORM    │              │   SQLAlchemy     │     │
│  │   (Anon Key)     │              │   (Service Key)  │     │
│  └────────┬─────────┘              └────────┬─────────┘     │
│           │                                 │                │
│           │         ┌──────────────────────┴────┐           │
│           │         │  Shared Supabase          │           │
│           └────────►│  PostgreSQL Database      │◄──────────┘
│                     │  (10 Tables)              │           │
│                     └───────────────────────────┘           │
│                                                               │
│  ┌──────────────────┐              ┌──────────────────┐     │
│  │   Celery Workers │              │   Redis Broker   │     │
│  │   (Distributed)  │◄────────────►│   (Task Queue)   │     │
│  └──────────────────┘              └──────────────────┘     │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │   Azure Blob Storage (Hot/Warm Tiers)                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Key Architectural Decisions

### 1. Shared Database (Single Source of Truth)

**Decision**: Use a single Supabase PostgreSQL database accessed by both frontend and backend.

**Rationale**:
- Eliminates data synchronization issues
- Leverages Supabase's built-in features (Auth, RLS, Real-time)
- Faster development velocity
- Type-safe schema management with Drizzle ORM

**Implementation**:
- **Frontend**: Drizzle ORM with anon key + RLS policies
- **Backend**: SQLAlchemy with service role key (bypasses RLS)
- **Schema**: Defined in `frontend/lib/db/schema.ts` (10 tables)
- **Migrations**: Generated and applied via Drizzle Kit

### 2. Authentication Strategy (Supabase Auth Only)

**Decision**: Use Supabase Auth exclusively, no custom JWT implementation.

**Rationale**:
- Battle-tested authentication system
- Built-in features: email/password, OAuth, magic links
- Automatic user management and session handling
- Row Level Security (RLS) integration

**Implementation**:
- **Frontend**: `@supabase/ssr` with anon key
- **Backend**: Token verification via `backend/services/supabase_auth.py`
- **No Custom Endpoints**: Login/signup handled by Supabase
- **Backend Endpoints**: Profile management and token verification only

### 3. Distributed Task Processing

**Decision**: Use Celery with Redis for background job processing.

**Rationale**:
- Image crawling is CPU and I/O intensive
- Chunk-based processing for scalability
- Retry logic and failure handling
- Progress tracking and monitoring

**Implementation**:
- **Celery Core**: Shared package (`celery_core/`)
- **Builder Tasks**: Image crawling tasks in `builder/tasks.py`
- **Validator Tasks**: Image validation tasks in `validator/tasks.py`
- **Broker**: Redis (localhost in dev, managed Redis in production)

### 4. Storage Architecture (Hot/Warm Tiers)

**Decision**: Use Azure Blob Storage with hot and warm tiers.

**Rationale**:
- Hot tier: Fast access for recent datasets (ZIP format)
- Warm tier: Cost-optimized archival (7z ultra-compressed)
- Scalable and reliable cloud storage
- Secure time-limited download links

**Implementation**:
- **Hot Storage**: Azure Blob Storage (immediate access)
- **Warm Storage**: Azure Data Lake Gen2 (archival)
- **Local Dev**: Filesystem-based storage
- **Providers**: Abstracted in `backend/storage/`

## Component Interactions

### 1. User Authentication Flow

```
User → Frontend (Supabase Client) → Supabase Auth
                                    ↓
                              JWT Token
                                    ↓
Frontend → Backend API (with Bearer token)
                ↓
    Token Verification (supabase_auth.py)
                ↓
        Access Granted/Denied
```

### 2. Dataset Generation Flow

```
User → Frontend → Backend API (/api/v1/jobs)
                        ↓
                Create CrawlJob (database)
                        ↓
                Dispatch Celery Tasks (chunks)
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
Celery Worker 1                 Celery Worker 2
(Process Chunk 1)               (Process Chunk 2)
        ↓                               ↓
    Builder Package                 Builder Package
    (Image Crawling)                (Image Crawling)
        ↓                               ↓
    Validator Package               Validator Package
    (Integrity Check)               (Integrity Check)
        ↓                               ↓
        └───────────────┬───────────────┘
                        ↓
            Update CrawlJob Progress
                        ↓
            Upload to Azure Storage
                        ↓
            Notify User (email/push)
```

### 3. Real-time Updates Flow

```
Celery Worker → Update Database (CrawlJob progress)
                        ↓
            Supabase Real-time Subscription
                        ↓
            Frontend (useNotifications hook)
                        ↓
            UI Update (progress bar, notifications)
```

## Database Schema Architecture

### Core Entities

1. **profiles** (extends Supabase auth.users)
   - User identity and profile information
   - Created automatically via Auth trigger

2. **projects** → **crawl_jobs** → **images**
   - Hierarchical organization
   - One-to-many relationships

3. **notifications** + **activity_logs**
   - User engagement and audit trail

4. **api_keys**
   - Programmatic access with rate limiting

5. **credit_accounts** + **credit_transactions**
   - Billing and usage tracking

6. **notification_preferences** + **usage_metrics**
   - User settings and analytics

### Access Patterns

- **Frontend (RLS Enabled)**:
  - Users can only access their own data
  - Enforced at database level via RLS policies
  - Uses anon key for all operations

- **Backend (RLS Bypassed)**:
  - Service role key bypasses RLS
  - Used for admin operations and cross-user queries
  - Implements application-level authorization

## Deployment Architecture

### Development Environment

```
Local Machine
├── Backend (localhost:8000)
│   └── uvicorn backend.main:app --reload
├── Frontend (localhost:3000)
│   └── bun dev
├── Redis (localhost:6379)
│   └── redis-server
└── Celery Workers
    └── celery -A celery_core.app worker
```

### Production Environment (Azure + Vercel)

```
┌─────────────────────────────────────────────────────────┐
│                    Azure App Service                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Container (Linux)                                  │ │
│  │  ├── Redis (localhost:6379)                        │ │
│  │  ├── Celery Worker (background)                    │ │
│  │  └── Gunicorn + FastAPI (foreground)               │ │
│  │      └── Backend API (backend.main:app)            │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  Startup: startup-azure.sh                               │
│  Logging: Azure Monitor (Application Insights)           │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│                    Vercel Platform                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Next.js 15 Application                            │ │
│  │  ├── SSR with Supabase Auth                        │ │
│  │  ├── API Routes (/api/*)                           │ │
│  │  └── Static Assets                                 │ │
│  └────────────────────────────────────────────────────┘ │
│                                                           │
│  Build: bun run build                                    │
│  Deploy: Automatic on git push                           │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│              Supabase (Managed Services)                 │
│  ├── PostgreSQL Database (shared)                       │
│  ├── Authentication Service                             │
│  ├── Real-time Subscriptions                            │
│  └── Storage (optional)                                 │
└─────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────┐
│              Azure Storage Services                      │
│  ├── Blob Storage (Hot Tier) - ZIP archives            │
│  └── Data Lake Gen2 (Warm Tier) - 7z archives          │
└─────────────────────────────────────────────────────────┘
```

## Security Architecture

### Authentication & Authorization

1. **Frontend Security**:
   - Supabase Auth with SSR (cookie-based sessions)
   - Row Level Security (RLS) policies
   - HTTPS only in production
   - CSRF protection via Next.js

2. **Backend Security**:
   - JWT token verification on every request
   - Service role key stored in environment variables
   - CORS configuration for allowed origins
   - Rate limiting via FastAPI-Limiter + Redis

3. **API Keys**:
   - Hashed storage (never store plain text)
   - Key prefix for identification
   - Per-key rate limits
   - Usage tracking and expiration

### Data Security

1. **Database**:
   - RLS policies for multi-tenant isolation
   - Encrypted connections (SSL/TLS)
   - Automatic backups via Supabase

2. **Storage**:
   - Time-limited SAS tokens for downloads
   - Private containers (no public access)
   - Encryption at rest (Azure default)

3. **Secrets Management**:
   - Environment variables (never in code)
   - Azure Key Vault (production)
   - `.env.local` for development (gitignored)

## Monitoring & Observability

### Logging Strategy

1. **Centralized Logging** (Loguru):
   - All packages use `utility/logging_config/`
   - Structured logging with context
   - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

2. **Production Logging**:
   - Azure Monitor (Application Insights)
   - Automatic stdout/stderr capture
   - 2-5 minute delay for log ingestion
   - Query via Azure Portal or CLI

3. **Development Logging**:
   - Console output with colors
   - File rotation for debugging
   - Verbose mode available

### Monitoring

1. **Application Metrics**:
   - Request/response times
   - Error rates and status codes
   - Celery task success/failure rates

2. **Infrastructure Metrics**:
   - CPU and memory usage
   - Disk space (ephemeral storage)
   - Network bandwidth

3. **Business Metrics**:
   - Images processed per day
   - Storage usage per user
   - API call counts
   - Credit consumption

## Scalability Considerations

### Horizontal Scaling

1. **Backend API**:
   - Stateless design (no in-memory sessions)
   - Can scale to multiple instances
   - Load balancer distributes traffic

2. **Celery Workers**:
   - Add more workers for increased throughput
   - Chunk-based processing for parallelism
   - Independent scaling from API

3. **Database**:
   - Supabase handles scaling automatically
   - Connection pooling via SQLAlchemy
   - Read replicas (if needed)

### Vertical Scaling

1. **Azure App Service**:
   - Upgrade tier for more CPU/memory
   - Basic → Standard → Premium

2. **Celery Workers**:
   - Increase worker concurrency
   - Larger VM sizes for heavy processing

## Performance Optimization

### Frontend

1. **Next.js Optimizations**:
   - Turbopack for fast dev builds
   - React.memo for component memoization
   - Lazy loading for heavy components
   - Image optimization with next/image

2. **API Client**:
   - Request/response caching
   - Automatic retry with exponential backoff
   - Timeout configuration

### Backend

1. **Database Queries**:
   - Indexed columns for fast lookups
   - Pagination for large result sets
   - Eager loading to avoid N+1 queries

2. **Caching**:
   - Redis for rate limiting
   - Response caching for expensive queries
   - Session storage

3. **Background Jobs**:
   - Chunk-based processing
   - Parallel downloads
   - Progress caching for resume capability

## Future Architecture Enhancements

1. **Microservices** (Phase 3+):
   - Separate services for crawling, validation, export
   - Event-driven architecture with message queues
   - Independent scaling and deployment

2. **CDN Integration**:
   - Azure CDN for static assets
   - Edge caching for API responses
   - Global distribution

3. **Advanced Monitoring**:
   - Distributed tracing (OpenTelemetry)
   - Custom dashboards (Grafana)
   - Alerting and incident management

4. **Multi-Region Deployment**:
   - Geographic distribution for lower latency
   - Data residency compliance
   - Disaster recovery
