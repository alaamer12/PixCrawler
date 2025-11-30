# Design Document

## Overview

This design document outlines the architecture for making PixCrawler production-ready with a three-tier configuration system, comprehensive documentation, unified startup scripts, and production-grade components.

### Key Design Principles

1. Separation of Concerns - Global, backend, and frontend configurations are independent
2. Environment-Based Configuration - Support for development, test, and production
3. Fail-Fast Validation - Configuration errors caught at startup
4. Comprehensive Documentation - Every configuration option documented
5. Architecture Compliance - Follows Supabase Auth, retry strategies, logging patterns
6. Production-Grade - Proper error handling, security, monitoring

## Architecture

### Configuration Hierarchy


Root Level: Global project settings, shared credentials
Backend Level: Server, database, Redis, Celery, storage configuration
Frontend Level: Supabase client, API endpoints, Stripe, Resend, app URLs

### Environment File Strategy

Development: .env files in root, backend, and frontend directories
Testing: .env.test files (ignored by git if sensitive)
Production: .env.production files or environment variables in deployment platforms
Examples: .env.example or .env.*.example files with comprehensive documentation

## Components

### 1. Global Configuration System

Location: Root .env file
Purpose: Manage project-wide settings without internal service details


Variables:
- PIXCRAWLER_ENVIRONMENT: development, test, production
- SUPABASE_URL: Shared Supabase project URL
- SUPABASE_SERVICE_ROLE_KEY: Backend service role key
- SUPABASE_ANON_KEY: Frontend anonymous key
- AZURE_STORAGE_CONNECTION_STRING: Azure storage credentials
- LOG_LEVEL: Global logging level

Design Decisions:
- Minimal global configuration to avoid coupling
- Only truly shared credentials at root level
- Each service reads what it needs from global config
- No service-specific details in global config

### 2. Backend Configuration System

Location: backend/.env file
Purpose: Complete backend service configuration


Configuration Sections:

A. Server Application
- ENVIRONMENT: development, staging, production, test
- DEBUG: Boolean flag for debug mode
- HOST: Server bind address (0.0.0.0 for production)
- PORT: Server port (default 8000)
- LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL

B. Database Configuration
- DATABASE_URL: PostgreSQL connection string with asyncpg driver
- DATABASE_POOL_SIZE: Connection pool size (5-10 for Supabase)
- DATABASE_MAX_OVERFLOW: Max overflow connections (10-20)
- DATABASE_POOL_PRE_PING: Health check before using connection
- DATABASE_ECHO: SQL query logging (False in production)

C. Redis Cache Configuration
- CACHE_ENABLED: Enable/disable caching
- CACHE_REDIS_HOST: Redis host
- CACHE_REDIS_PORT: Redis port (default 6379)
- CACHE_REDIS_PASSWORD: Redis password (optional)
- CACHE_REDIS_DB: Database number (0-15)
- CACHE_PREFIX: Key prefix to avoid conflicts
- CACHE_DEFAULT_TTL: Default TTL in seconds


D. Rate Limiter Configuration
- LIMITER_ENABLED: Enable/disable rate limiting
- LIMITER_REDIS_HOST: Redis host for limiter
- LIMITER_REDIS_PORT: Redis port
- LIMITER_REDIS_PASSWORD: Redis password (optional)
- LIMITER_REDIS_DB: Database number (use different from cache)
- LIMITER_PREFIX: Key prefix
- LIMITER_DEFAULT_TIMES: Default request count
- LIMITER_DEFAULT_SECONDS: Default time window

E. Celery Configuration
- CELERY_BROKER_URL: Redis broker URL
- CELERY_RESULT_BACKEND: Redis result backend URL
- CELERY_TASK_TIME_LIMIT: Task timeout
- CELERY_WORKER_CONCURRENCY: Worker concurrency

F. Storage Configuration
- STORAGE_PROVIDER: local, azure
- STORAGE_LOCAL_PATH: Local storage path
- STORAGE_AZURE_CONNECTION_STRING: Azure connection string
- STORAGE_AZURE_CONTAINER_NAME: Container name
- STORAGE_AZURE_MAX_RETRIES: Retry attempts

G. CORS Configuration
- ALLOWED_ORIGINS: Comma-separated list of allowed origins


Design Decisions:
- Modular settings using Pydantic with composition pattern
- Prefix-based environment variables (CACHE_, LIMITER_, etc.)
- Environment-specific defaults (DevSettings, ProdSettings, TestSettings)
- Graceful degradation when Redis unavailable in development
- Fail-fast when Redis unavailable in production
- Cached settings instance for performance

### 3. Frontend Configuration System

Location: frontend/.env file
Purpose: Frontend application configuration with runtime validation

Configuration Sections:

A. Supabase Client
- NEXT_PUBLIC_SUPABASE_URL: Supabase project URL (public)
- NEXT_PUBLIC_SUPABASE_ANON_KEY: Anonymous key (public)
- POSTGRES_URL: Direct database connection (optional)

B. API Configuration
- NEXT_PUBLIC_API_URL: Backend API base URL

C. Stripe Integration (Optional)
- NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: Stripe public key
- STRIPE_SECRET_KEY: Stripe secret key (server-side only)
- STRIPE_WEBHOOK_SECRET: Webhook verification secret
- STRIPE_*_PRICE_ID: Price IDs for different plans


D. Resend Email (Optional)
- RESEND_API_KEY: Resend API key
- CONTACT_EMAIL: Contact form recipient
- FROM_EMAIL: Email sender address

E. Application Settings
- NEXT_PUBLIC_APP_URL: Application public URL
- NODE_ENV: development, production, test

Design Decisions:
- Zod schema validation in lib/env.ts
- Type-safe environment variables with autocomplete
- Fail-fast on missing required variables
- Clear error messages listing missing variables
- NEXT_PUBLIC_ prefix for client-side variables
- Server-side only variables without prefix

### 4. Azure Static Web App Configuration

Location: frontend/staticwebapp.config.json
Purpose: Azure deployment configuration

Configuration Structure:

A. Routes
- API proxy routes to backend
- Static file serving
- Client-side routing fallback

B. Navigation Fallback
- Fallback to index.html for SPA routing
- Exclude API routes from fallback

C. Response Overrides
- Custom 404 page
- Custom error pages

D. Global Headers
- Security headers (CSP, X-Frame-Options, etc.)
- CORS headers
- Cache control headers


### 5. Unified Startup Scripts

Purpose: Start entire application stack with single command

Script Variants:
- start-dev.sh (Unix/Linux/Mac)
- start-dev.ps1 (Windows PowerShell)
- start-dev.cmd (Windows Command Prompt)

Startup Sequence:

1. Dependency Check
   - Check Python 3.11+ installed
   - Check Node.js 18+ installed
   - Check Redis available
   - Check PostgreSQL accessible
   - Display clear error messages if missing

2. Environment Validation
   - Verify .env files exist
   - Validate required environment variables
   - Check Supabase connectivity
   - Check Redis connectivity

3. Backend Startup
   - Navigate to backend directory
   - Install dependencies with UV
   - Start FastAPI with Uvicorn
   - Display backend URL and health check

4. Frontend Startup
   - Navigate to frontend directory
   - Install dependencies with Bun
   - Start Next.js dev server
   - Display frontend URL

5. Service Monitoring
   - Display combined logs from both services
   - Handle Ctrl+C gracefully
   - Shutdown both services cleanly


Design Decisions:
- Platform-specific scripts for better compatibility
- Parallel service startup for faster development
- Graceful shutdown handling
- Clear status messages and URLs
- Dependency checking before startup
- Environment validation before services start

### 6. Database Schema Alignment

Strategy: Frontend Drizzle schema as single source of truth

Alignment Process:

1. Schema Definition
   - Define schema in frontend/lib/db/schema.ts using Drizzle
   - Generate migrations with drizzle-kit
   - Apply migrations to Supabase database

2. Backend Synchronization
   - Create SQLAlchemy models matching Drizzle schema
   - Use same table names, column names, and types
   - Maintain same relationships and constraints

3. Production Schema SQL
   - Keep production_schema.sql in sync with Drizzle schema
   - Include all tables, indexes, RLS policies, triggers
   - Use for fresh database initialization

4. Validation Process
   - Manual review of schema changes
   - Cross-team review (frontend + backend)
   - Test migrations in development before production


Tables to Align:
- profiles (extends auth.users)
- projects
- crawl_jobs (with chunk tracking)
- images
- activity_logs
- api_keys
- credit_accounts
- credit_transactions
- notifications
- notification_preferences
- usage_metrics

Design Decisions:
- Drizzle schema is authoritative
- Backend models are derived from Drizzle
- No automated synchronization (manual review required)
- Production SQL kept in sync for fresh deployments
- RLS policies defined in SQL, not ORM

### 7. API Implementation Completeness

Required Endpoints:

A. Authentication (auth.py)
- POST /auth/login - Supabase Auth login
- POST /auth/signup - Supabase Auth signup
- POST /auth/logout - Logout
- GET /auth/profile - Get user profile
- PATCH /auth/profile - Update profile
- POST /auth/refresh - Refresh token

B. Projects (projects.py)
- GET /projects - List user projects
- POST /projects - Create project
- GET /projects/{id} - Get project details
- PATCH /projects/{id} - Update project
- DELETE /projects/{id} - Delete project


C. Crawl Jobs (crawl_jobs.py)
- GET /jobs - List crawl jobs
- POST /jobs - Create crawl job
- GET /jobs/{id} - Get job details
- PATCH /jobs/{id} - Update job
- DELETE /jobs/{id} - Delete job
- POST /jobs/{id}/start - Start job
- POST /jobs/{id}/stop - Stop job
- POST /jobs/{id}/retry - Retry failed job
- GET /jobs/{id}/progress - Get job progress

D. Images (datasets.py)
- GET /jobs/{id}/images - List job images
- GET /images/{id} - Get image details
- DELETE /images/{id} - Delete image
- GET /images/{id}/download - Download image

E. Notifications (notifications.py)
- GET /notifications - List notifications
- PATCH /notifications/{id}/read - Mark as read
- PATCH /notifications/read-all - Mark all as read
- GET /notifications/preferences - Get preferences
- PATCH /notifications/preferences - Update preferences

F. Credits & Billing
- GET /credits/balance - Get credit balance
- GET /credits/transactions - List transactions
- POST /credits/purchase - Purchase credits
- GET /credits/usage - Get usage metrics


G. API Keys
- GET /api-keys - List API keys
- POST /api-keys - Create API key
- DELETE /api-keys/{id} - Revoke API key
- GET /api-keys/{id}/usage - Get key usage

H. Activity Logs
- GET /activity - List activity logs

I. Health & Metrics (health.py, metrics.py)
- GET /health - Health check
- GET /metrics - System metrics

Design Decisions:
- RESTful API design
- Consistent error responses
- Pagination for list endpoints
- Rate limiting on sensitive endpoints
- Supabase Auth token verification
- OpenAPI documentation

### 8. Architecture Compliance

A. Supabase Authentication

Frontend:
- Use @supabase/ssr with anon key
- Cookie-based sessions
- Row Level Security (RLS) policies
- No custom JWT implementation

Backend:
- Use service role key for admin operations
- Token verification via backend/services/supabase_auth.py
- Bypass RLS with service role
- No custom login/signup endpoints


B. Retry Architecture

Celery Task Level:
- No autoretry by default
- Explicit retry for infrastructure failures only
- bind=True, acks_late=True
- Max 3 retries with 60s countdown

Tenacity Operation Level:
- Retry network/API operations
- Exponential backoff (2-10s)
- Max 3 attempts
- Retry on TimeoutException, NetworkError, HTTPStatusError

Fail-Fast:
- ValidationError - no retry
- 404, 401, 403 - no retry
- Business logic errors - no retry

C. Logging Architecture

Implementation:
- Use utility.logging_config.get_logger()
- Loguru-based centralized logging
- Structured logging with context
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

Logging Strategy:
- Log all retry attempts
- Log all errors with context
- Log API requests/responses in debug mode
- Log configuration validation
- Log service startup/shutdown
