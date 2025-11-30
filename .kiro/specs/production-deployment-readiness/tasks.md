# Implementation Plan

This implementation plan breaks down the production deployment readiness feature into discrete, manageable coding tasks. Each task builds incrementally on previous tasks and references specific requirements from the requirements document.

## Task List

- [ ] 1. Create comprehensive environment configuration files
- [ ] 1.1 Create root-level .env.example with comprehensive documentation
  - Document global project settings (PIXCRAWLER_ENVIRONMENT, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY)
  - Document Azure storage credentials
  - Add clear section headers and detailed comments for each variable
  - Include examples, valid values, and default values
  - _Requirements: 1.3, 1.4, 1.5, 10.1, 10.2, 10.3_

- [ ] 1.2 Create backend/.env.example with full backend configuration
  - Document server configuration section (ENVIRONMENT, DEBUG, HOST, PORT, LOG_LEVEL)
  - Document database configuration section (DATABASE_URL, DATABASE_POOL_SIZE, DATABASE_MAX_OVERFLOW, DATABASE_POOL_PRE_PING, DATABASE_ECHO)
  - Document Supabase configuration section (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY)
  - Document Redis cache configuration section (CACHE_ENABLED, CACHE_REDIS_HOST, CACHE_REDIS_PORT, CACHE_REDIS_PASSWORD, CACHE_REDIS_DB, CACHE_PREFIX, CACHE_DEFAULT_TTL)
  - Document rate limiter configuration section (LIMITER_ENABLED, LIMITER_REDIS_HOST, LIMITER_REDIS_PORT, LIMITER_REDIS_PASSWORD, LIMITER_REDIS_DB, LIMITER_PREFIX, LIMITER_DEFAULT_TIMES, LIMITER_DEFAULT_SECONDS)
  - Document Celery configuration section (CELERY_BROKER_URL, CELERY_RESULT_BACKEND, CELERY_TASK_TIME_LIMIT, CELERY_WORKER_CONCURRENCY)
  - Document storage configuration section (STORAGE_PROVIDER, STORAGE_LOCAL_PATH, STORAGE_AZURE_CONNECTION_STRING, STORAGE_AZURE_CONTAINER_NAME, STORAGE_AZURE_MAX_RETRIES)
  - Document CORS configuration section (ALLOWED_ORIGINS)
  - Add clear section headers with detailed comments
  - _Requirements: 2.2, 2.3, 10.1, 10.2, 10.3_

- [ ] 1.3 Create frontend/.env.example with full frontend configuration
  - Document Supabase client section (NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, POSTGRES_URL)
  - Document API configuration section (NEXT_PUBLIC_API_URL)
  - Document Stripe integration section (NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_*_PRICE_ID)
  - Document Resend email section (RESEND_API_KEY, CONTACT_EMAIL, FROM_EMAIL)
  - Document application settings section (NEXT_PUBLIC_APP_URL, NODE_ENV)
  - Add clear section headers with detailed comments
  - Mark optional vs required variables
  - _Requirements: 3.3, 10.1, 10.2, 10.3_

- [ ] 1.4 Create frontend/.env.example.production for production-specific configuration
  - Document production-specific values and differences from development
  - Include deployment platform instructions (Vercel, Azure Static Web Apps)
  - _Requirements: 3.1, 10.7_



- [ ] 2. Enhance backend configuration system
- [ ] 2.1 Add cache settings module (backend/core/settings/cache.py)
  - Create CacheSettings class with Pydantic
  - Add fields: enabled, redis_host, redis_port, redis_password, redis_db, prefix, default_ttl
  - Use CACHE_ prefix for environment variables
  - Add validation and default values
  - _Requirements: 2.2, 2.6, 2.7_

- [ ] 2.2 Update RedisSettings to support cache configuration
  - Modify backend/core/settings/redis.py to work with cache settings
  - Ensure backward compatibility


  - _Requirements: 2.2, 2.6_

- [ ] 2.3 Update RateLimitSettings to include all limiter configuration
  - Add redis_host, redis_port, redis_password, redis_db, prefix fields
  - Use LIMITER_ prefix for all environment variables
  - Add validation for rate limit format (times/seconds)
  - _Requirements: 2.2, 2.6, 2.7_

- [ ] 2.4 Update CommonSettings to include cache settings
  - Add cache: CacheSettings field to backend/core/settings/base.py
  - Ensure composition pattern is maintained
  - _Requirements: 2.2_

- [x] 2.5 Update backend main.py to handle Redis gracefully

  - Implement check_redis_available function
  - Add graceful degradation for development (log warnings, continue)
  - Add fail-fast for production (raise error, stop startup)
  - Update lifespan context manager
  - _Requirements: 2.4, 2.5, 8.4_







- [x] 3. Enhance frontend configuration system




- [x] 3.1 Update frontend/lib/env.ts with complete Zod schema


  - Add NEXT_PUBLIC_API_URL validation
  - Add comprehensive Stripe configuration fields
  - Add Resend email configuration fields
  - Add NEXT_PUBLIC_APP_URL validation
  - Improve error messages for missing variables
  - Add type-safe environment variable exports
  - _Requirements: 3.2, 3.5, 3.6, 3.7_

- [x] 3.2 Update frontend API client to use validated environment


  - Modify frontend/lib/api/client.ts to use env.NEXT_PUBLIC_API_URL
  - Ensure type safety with environment variables
  - _Requirements: 3.6, 3.7_

- [x] 3.3 Create .gitignore rules for environment files


  - Ensure .env files are ignored
  - Ensure .env.test with sensitive data is ignored
  - Allow .env.example files to be committed
  - _Requirements: 3.4_



- [x] 4. Create Azure Static Web App configuration




- [x] 4.1 Create frontend/staticwebapp.config.json


  - Define API proxy routes to backend
  - Configure navigation fallback for SPA routing
  - Add response overrides for custom error pages
  - Configure security headers (CSP, X-Frame-Options, X-Content-Type-Options)
  - Add CORS headers configuration
  - Configure cache control headers
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 5. Create unified startup scripts
- [ ] 5.1 Create scripts/start-dev.sh for Unix/Linux/Mac
  - Add shebang and script header
  - Implement dependency checking (Python 3.11+, Node.js 18+, Redis, PostgreSQL)
  - Implement environment validation (.env files exist, required variables set)
  - Implement backend startup (navigate to backend, install with UV, start Uvicorn)
  - Implement frontend startup (navigate to frontend, install with Bun, start Next.js)
  - Implement graceful shutdown handling (trap SIGINT, kill processes)
  - Add clear status messages and service URLs
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 5.2 Create scripts/start-dev.ps1 for Windows PowerShell
  - Implement same functionality as bash script
  - Use PowerShell syntax and commands
  - Handle Windows-specific paths and processes
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] 5.3 Create scripts/start-dev.cmd for Windows Command Prompt
  - Implement same functionality as bash script
  - Use CMD syntax and commands
  - Handle Windows-specific paths and processes
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_



- [ ] 6. Verify and align database schema
- [ ] 6.1 Review frontend Drizzle schema (frontend/lib/db/schema.ts)
  - Verify all 11 tables are defined (profiles, projects, crawl_jobs, images, activity_logs, api_keys, credit_accounts, credit_transactions, notifications, notification_preferences, usage_metrics)
  - Verify relationships and constraints
  - Verify indexes are defined
  - _Requirements: 6.1, 6.5_

- [ ] 6.2 Review backend SQLAlchemy models (backend/database/models.py)
  - Verify models match Drizzle schema exactly
  - Verify table names, column names, and types match
  - Verify relationships match
  - Document any discrepancies
  - _Requirements: 6.2, 6.3_

- [ ] 6.3 Update production_schema.sql if needed
  - Ensure SQL matches Drizzle schema
  - Verify all tables, indexes, RLS policies, and triggers are included
  - Test SQL execution on fresh database
  - _Requirements: 6.3, 6.5_

- [ ] 6.4 Create schema synchronization documentation
  - Document process for keeping schemas in sync
  - Document review process for schema changes
  - Add to project documentation
  - _Requirements: 6.4_



- [ ] 7. Verify API implementation completeness
- [ ] 7.1 Review authentication endpoints (backend/api/v1/endpoints/auth.py)
  - Verify Supabase Auth integration (no custom JWT)
  - Verify profile endpoints exist
  - Verify token refresh endpoint exists
  - Add any missing endpoints
  - _Requirements: 7.2, 8.1, 8.2_

- [ ] 7.2 Review projects endpoints (backend/api/v1/endpoints/projects.py)
  - Verify CRUD operations exist
  - Verify proper error handling
  - Verify Supabase Auth token verification
  - _Requirements: 7.2, 7.3, 7.4_

- [ ] 7.3 Review crawl jobs endpoints (backend/api/v1/endpoints/crawl_jobs.py)
  - Verify CRUD operations exist
  - Verify start, stop, retry endpoints exist
  - Verify progress endpoint exists
  - Verify chunk tracking is implemented
  - _Requirements: 7.2, 7.3, 7.4_

- [ ] 7.4 Review images endpoints (backend/api/v1/endpoints/datasets.py)
  - Verify list, get, delete, download endpoints exist
  - Verify proper error handling
  - _Requirements: 7.2, 7.3, 7.4_

- [ ] 7.5 Review notifications endpoints (backend/api/v1/endpoints/notifications.py)
  - Verify list, mark as read, preferences endpoints exist
  - Verify proper error handling
  - _Requirements: 7.2, 7.3, 7.4_

- [ ] 7.6 Create credits and billing endpoints
  - Create backend/api/v1/endpoints/credits.py
  - Implement GET /credits/balance endpoint
  - Implement GET /credits/transactions endpoint
  - Implement POST /credits/purchase endpoint
  - Implement GET /credits/usage endpoint
  - Add to API router
  - _Requirements: 7.2, 7.3, 7.4, 7.5_

- [ ] 7.7 Create API keys endpoints
  - Create backend/api/v1/endpoints/api_keys.py
  - Implement GET /api-keys endpoint (list)
  - Implement POST /api-keys endpoint (create with hashing)
  - Implement DELETE /api-keys/{id} endpoint (revoke)
  - Implement GET /api-keys/{id}/usage endpoint
  - Add to API router
  - _Requirements: 7.2, 7.3, 7.4, 7.5_

- [ ] 7.8 Create activity logs endpoints
  - Create backend/api/v1/endpoints/activity.py
  - Implement GET /activity endpoint (list with pagination)
  - Add to API router
  - _Requirements: 7.2, 7.3, 7.4, 7.5_



- [ ] 8. Verify architecture compliance
- [ ] 8.1 Review Supabase Auth implementation
  - Verify backend uses service role key from backend/services/supabase_auth.py
  - Verify frontend uses anon key with RLS
  - Verify no custom JWT implementation exists
  - Document any non-compliance
  - _Requirements: 8.1, 8.2_

- [ ] 8.2 Review retry logic implementation
  - Verify Celery tasks do NOT use autoretry
  - Verify Celery tasks explicitly handle infrastructure failures
  - Verify network operations use Tenacity
  - Verify permanent errors fail fast
  - Document any non-compliance
  - _Requirements: 8.3, 8.4, 8.5, 8.6_

- [ ] 8.3 Review logging implementation
  - Verify all modules use utility.logging_config.get_logger()
  - Verify structured logging with context
  - Verify appropriate log levels
  - Verify retry attempts are logged
  - Document any non-compliance
  - _Requirements: 8.7_

- [ ] 8.4 Review database access patterns
  - Verify frontend uses Drizzle ORM
  - Verify backend uses SQLAlchemy
  - Verify both connect to same Supabase PostgreSQL
  - Verify RLS policies are respected
  - Document any non-compliance
  - _Requirements: 8.8_



- [ ] 9. Implement production-grade components
- [ ] 9.1 Enhance error handling in backend
  - Review and update custom exception classes
  - Verify global exception handlers are comprehensive
  - Verify structured error responses
  - Verify error logging with context
  - Add any missing error handling
  - _Requirements: 9.1_

- [ ] 9.2 Enhance error handling in frontend
  - Verify ErrorBoundaryProvider is implemented
  - Verify ErrorFallback component exists
  - Verify ApiError class is used consistently
  - Verify toast notifications for user feedback
  - Add any missing error handling
  - _Requirements: 9.1_

- [ ] 9.3 Verify security implementations
  - Verify API key hashing in backend
  - Verify service role key is only in environment
  - Verify CORS configuration
  - Verify rate limiting is implemented
  - Verify input validation with Pydantic
  - Verify frontend environment variable validation
  - Verify secure cookie settings
  - _Requirements: 9.4, 9.5, 9.6_

- [ ] 9.4 Implement health check endpoints
  - Verify /health endpoint exists in backend
  - Add database connection health check
  - Add Redis connection health check
  - Add Celery worker health check
  - _Requirements: 9.2_

- [ ] 9.5 Verify database connection management
  - Verify connection pooling is configured
  - Verify pool size is appropriate for Supabase (5-10)
  - Verify max overflow is configured (10-20)
  - Verify pre-ping health checks are enabled
  - Verify connection timeout handling
  - Verify graceful connection cleanup
  - _Requirements: 9.8_

- [ ] 9.6 Verify Redis configuration
  - Verify separate databases for cache (0) and limiter (1)
  - Verify connection timeout is set (2s)
  - Verify socket timeout is set (2s)
  - Verify graceful degradation in development
  - Verify fail-fast in production
  - _Requirements: 9.9_



- [ ] 10. Create comprehensive documentation
- [ ] 10.1 Update root README.md
  - Add Environment Setup section
  - Add Configuration Guide section
  - Add Development Workflow section
  - Add Production Deployment section
  - Add Troubleshooting section
  - Link to detailed documentation
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

- [ ] 10.2 Create CONFIGURATION.md documentation
  - Document all environment variables
  - Document configuration hierarchy
  - Document environment-specific settings
  - Document validation rules
  - Provide examples for each configuration
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 10.3 Create DEPLOYMENT.md documentation
  - Document development deployment
  - Document production deployment to Azure
  - Document production deployment to Vercel
  - Document environment variable setup
  - Document troubleshooting common issues
  - _Requirements: 10.7, 10.8_

- [ ] 10.4 Update API documentation
  - Verify OpenAPI/Swagger documentation is complete
  - Add examples for all endpoints
  - Document authentication requirements
  - Document rate limiting
  - Document error responses
  - _Requirements: 7.5_



- [ ] 11. Testing and validation
- [ ]* 11.1 Create configuration tests for backend
  - Test environment variable loading
  - Test default values
  - Test validation rules
  - Test environment-specific settings
  - Test Redis availability handling
  - Test database connection handling
  - _Requirements: 2.4, 2.5, 9.8, 9.9_

- [ ]* 11.2 Create configuration tests for frontend
  - Test Zod schema validation
  - Test missing required variables
  - Test invalid variable formats
  - Test environment-specific behavior
  - _Requirements: 3.5, 3.6_

- [ ]* 11.3 Create integration tests
  - Test backend-frontend communication
  - Test Supabase authentication flow
  - Test API endpoint responses
  - Test error handling
  - Test rate limiting
  - _Requirements: 7.3, 7.4, 8.1, 9.6_

- [ ]* 11.4 Test startup scripts
  - Test dependency checking
  - Test environment validation
  - Test service startup
  - Test graceful shutdown
  - Test on Windows, Mac, and Linux
  - _Requirements: 5.2, 5.3, 5.4, 5.5_

- [ ] 11.5 Validate production readiness
  - Test all .env.example files are complete
  - Test configuration loading in all environments
  - Test startup scripts work correctly
  - Test health check endpoints
  - Test error handling
  - Test security configurations
  - Verify all documentation is complete
  - _Requirements: All requirements_

