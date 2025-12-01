# PixCrawler Configuration Guide

This guide provides comprehensive documentation for all configuration options in PixCrawler. The application uses a three-tier configuration system to separate concerns between global, backend, and frontend settings.

## Table of Contents

- [Configuration Hierarchy](#configuration-hierarchy)
- [Environment-Specific Settings](#environment-specific-settings)
- [Root Level Configuration](#root-level-configuration)
- [Backend Configuration](#backend-configuration)
- [Frontend Configuration](#frontend-configuration)
- [Validation Rules](#validation-rules)
- [Configuration Examples](#configuration-examples)

---

## Configuration Hierarchy

PixCrawler uses a three-tier configuration system:

```
Root Level (.env)
├── Global project settings
├── Shared Supabase credentials
└── Azure storage settings

Backend Level (backend/.env)
├── Server application settings
├── Database configuration
├── Redis cache and rate limiter
├── Celery task queue
├── Storage providers
└── CORS settings

Frontend Level (frontend/.env)
├── Supabase client settings
├── API endpoints
├── Lemon Squeezy integration (optional)
├── Resend email (optional)
└── Application URLs
```

### Configuration Loading Order

1. **Root `.env`** - Loaded first, provides global defaults
2. **Service-specific `.env`** - Overrides root settings for backend/frontend
3. **Environment variables** - Highest priority, overrides file-based config

---

## Environment-Specific Settings

### Development Environment

- **Location**: `.env`, `backend/.env`, `frontend/.env`
- **Characteristics**:
  - Debug mode enabled
  - Verbose logging
  - Local storage providers
  - Relaxed security settings
  - Redis failures logged as warnings (graceful degradation)

### Test Environment

- **Location**: `.env.test`, `backend/.env.test`, `frontend/.env.test`
- **Characteristics**:
  - Isolated test database
  - Mock external services
  - Fast execution settings
  - Minimal logging

### Production Environment

- **Location**: Environment variables in deployment platform
- **Characteristics**:
  - Debug mode disabled
  - Error-level logging only
  - Cloud storage providers
  - Strict security settings
  - Redis failures cause startup failure (fail-fast)

---

## Root Level Configuration

**File**: `.env`

### Global Settings

```bash
# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

# Application environment
# - Purpose: Controls environment-specific behavior across the application
# - Valid values: development, test, production
# - Default: development
# - Required: Yes
# - Example: production
PIXCRAWLER_ENVIRONMENT=development
```

### Supabase Configuration

```bash
# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================

# Supabase project URL
# - Purpose: Base URL for Supabase services (Auth, Database, Storage)
# - Valid values: https://<project-id>.supabase.co
# - Default: None
# - Required: Yes
# - Example: https://abcdefghijklmnop.supabase.co
SUPABASE_URL=https://your-project.supabase.co

# Supabase service role key (Backend only)
# - Purpose: Administrative access for backend operations (bypasses RLS)
# - Valid values: JWT token starting with "eyJ"
# - Default: None
# - Required: Yes (backend)
# - Security: NEVER expose in frontend or commit to git
# - Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Supabase anonymous key (Frontend)
# - Purpose: Public key for frontend client (respects RLS policies)
# - Valid values: JWT token starting with "eyJ"
# - Default: None
# - Required: Yes (frontend)
# - Security: Safe to expose in frontend
# - Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_ANON_KEY=your-anon-key
```

### Azure Storage Configuration

```bash
# =============================================================================
# AZURE STORAGE CONFIGURATION
# =============================================================================

# Azure Storage connection string
# - Purpose: Credentials for Azure Blob Storage and Data Lake
# - Valid values: Connection string from Azure Portal
# - Default: None
# - Required: No (optional, for Azure storage)
# - Security: Keep confidential
# - Example: DefaultEndpointsProtocol=https;AccountName=...
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
```

### Logging Configuration

```bash
# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Global log level
# - Purpose: Controls verbosity of logging across all services
# - Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
# - Default: INFO
# - Required: No
# - Example: INFO (production), DEBUG (development)
LOG_LEVEL=INFO
```

---

## Backend Configuration

**File**: `backend/.env`

### Server Application Settings

```bash
# =============================================================================
# SERVER APPLICATION CONFIGURATION
# =============================================================================

# Application environment
# - Purpose: Controls backend-specific environment behavior
# - Valid values: development, staging, production, test
# - Default: development
# - Required: Yes
ENVIRONMENT=development

# Debug mode
# - Purpose: Enables detailed error messages and auto-reload
# - Valid values: true, false
# - Default: false
# - Required: No
# - Warning: MUST be false in production
DEBUG=false

# Server host
# - Purpose: Network interface to bind the server
# - Valid values: 0.0.0.0 (all interfaces), 127.0.0.1 (localhost)
# - Default: 127.0.0.1
# - Required: No
# - Production: Use 0.0.0.0
HOST=127.0.0.1

# Server port
# - Purpose: Port number for the API server
# - Valid values: 1024-65535
# - Default: 8000
# - Required: No
PORT=8000

# Log level
# - Purpose: Backend logging verbosity
# - Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
# - Default: INFO
# - Required: No
LOG_LEVEL=INFO
```

### Database Configuration

```bash
# =============================================================================
# DATABASE CONFIGURATION (Supabase PostgreSQL)
# =============================================================================

# Database connection URL
# - Purpose: PostgreSQL connection string for SQLAlchemy
# - Valid values: postgresql+asyncpg://user:pass@host:port/db
# - Default: None
# - Required: Yes
# - Format: postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
# - Example: postgresql+asyncpg://postgres:password@db.abcdef.supabase.co:5432/postgres
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres

# Connection pool size
# - Purpose: Number of persistent database connections
# - Valid values: 1-20
# - Default: 5
# - Required: No
# - Supabase recommendation: 5-10 connections
DATABASE_POOL_SIZE=5

# Maximum overflow connections
# - Purpose: Additional connections beyond pool size
# - Valid values: 0-50
# - Default: 10
# - Required: No
# - Supabase recommendation: 10-20 overflow
DATABASE_MAX_OVERFLOW=10

# Connection pre-ping
# - Purpose: Health check before using pooled connection
# - Valid values: true, false
# - Default: true
# - Required: No
# - Recommendation: Always true for reliability
DATABASE_POOL_PRE_PING=true

# SQL query echo
# - Purpose: Log all SQL queries to console
# - Valid values: true, false
# - Default: false
# - Required: No
# - Warning: Set to false in production (performance impact)
DATABASE_ECHO=false
```

### Redis Cache Configuration

```bash
# =============================================================================
# REDIS CACHE CONFIGURATION
# =============================================================================

# Enable caching
# - Purpose: Toggle Redis caching on/off
# - Valid values: true, false
# - Default: true
# - Required: No
CACHE_ENABLED=true

# Redis host
# - Purpose: Redis server hostname or IP
# - Valid values: hostname or IP address
# - Default: localhost
# - Required: Yes (if cache enabled)
CACHE_REDIS_HOST=localhost

# Redis port
# - Purpose: Redis server port
# - Valid values: 1-65535
# - Default: 6379
# - Required: No
CACHE_REDIS_PORT=6379

# Redis password
# - Purpose: Authentication for Redis server
# - Valid values: Any string
# - Default: None (no auth)
# - Required: No (depends on Redis config)
CACHE_REDIS_PASSWORD=

# Redis database number
# - Purpose: Logical database within Redis instance
# - Valid values: 0-15
# - Default: 0
# - Required: No
# - Recommendation: Use 0 for cache, 1 for rate limiter
CACHE_REDIS_DB=0

# Cache key prefix
# - Purpose: Namespace for cache keys to avoid conflicts
# - Valid values: Any string
# - Default: pixcrawler:cache:
# - Required: No
CACHE_PREFIX=pixcrawler:cache:

# Default TTL (Time To Live)
# - Purpose: Default expiration time for cached items
# - Valid values: Positive integer (seconds)
# - Default: 3600 (1 hour)
# - Required: No
CACHE_DEFAULT_TTL=3600
```

### Rate Limiter Configuration

```bash
# =============================================================================
# RATE LIMITER CONFIGURATION
# =============================================================================

# Enable rate limiting
# - Purpose: Toggle rate limiting on/off
# - Valid values: true, false
# - Default: true
# - Required: No
# - Production: Should be true
LIMITER_ENABLED=true

# Redis host
# - Purpose: Redis server for rate limit tracking
# - Valid values: hostname or IP address
# - Default: localhost
# - Required: Yes (if limiter enabled)
LIMITER_REDIS_HOST=localhost

# Redis port
# - Purpose: Redis server port
# - Valid values: 1-65535
# - Default: 6379
# - Required: No
LIMITER_REDIS_PORT=6379

# Redis password
# - Purpose: Authentication for Redis server
# - Valid values: Any string
# - Default: None (no auth)
# - Required: No
LIMITER_REDIS_PASSWORD=

# Redis database number
# - Purpose: Logical database for rate limiter
# - Valid values: 0-15
# - Default: 1
# - Required: No
# - Recommendation: Use different DB than cache (e.g., 1)
LIMITER_REDIS_DB=1

# Rate limit key prefix
# - Purpose: Namespace for rate limit keys
# - Valid values: Any string
# - Default: pixcrawler:limiter:
# - Required: No
LIMITER_PREFIX=pixcrawler:limiter:

# Default request limit
# - Purpose: Default number of requests allowed
# - Valid values: Positive integer
# - Default: 100
# - Required: No
LIMITER_DEFAULT_TIMES=100

# Default time window
# - Purpose: Time window for rate limit (seconds)
# - Valid values: Positive integer
# - Default: 60 (1 minute)
# - Required: No
LIMITER_DEFAULT_SECONDS=60
```

### Celery Configuration

```bash
# =============================================================================
# CELERY TASK QUEUE CONFIGURATION
# =============================================================================

# Celery broker URL
# - Purpose: Message broker for task distribution
# - Valid values: redis://host:port/db
# - Default: redis://localhost:6379/0
# - Required: Yes
# - Example: redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Celery result backend
# - Purpose: Storage for task results
# - Valid values: redis://host:port/db
# - Default: redis://localhost:6379/0
# - Required: Yes
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Task time limit
# - Purpose: Maximum execution time for tasks (seconds)
# - Valid values: Positive integer
# - Default: 1800 (30 minutes)
# - Required: No
CELERY_TASK_TIME_LIMIT=1800

# Worker concurrency
# - Purpose: Number of concurrent worker processes
# - Valid values: Positive integer
# - Default: 4
# - Required: No
# - Recommendation: Number of CPU cores
CELERY_WORKER_CONCURRENCY=4
```

### Storage Configuration

```bash
# =============================================================================
# STORAGE CONFIGURATION
# =============================================================================

# Storage provider
# - Purpose: Select storage backend
# - Valid values: local, azure
# - Default: local
# - Required: Yes
# - Production: Use azure
STORAGE_PROVIDER=local

# Local storage path
# - Purpose: Directory for local file storage
# - Valid values: Valid filesystem path
# - Default: ./storage
# - Required: Yes (if provider=local)
STORAGE_LOCAL_PATH=./storage

# Azure connection string
# - Purpose: Azure Storage credentials
# - Valid values: Azure connection string
# - Default: None
# - Required: Yes (if provider=azure)
STORAGE_AZURE_CONNECTION_STRING=

# Azure container name
# - Purpose: Blob container for file storage
# - Valid values: Valid container name (lowercase, alphanumeric, hyphens)
# - Default: pixcrawler-datasets
# - Required: Yes (if provider=azure)
STORAGE_AZURE_CONTAINER_NAME=pixcrawler-datasets

# Azure max retries
# - Purpose: Retry attempts for Azure operations
# - Valid values: 0-10
# - Default: 3
# - Required: No
STORAGE_AZURE_MAX_RETRIES=3
```

### CORS Configuration

```bash
# =============================================================================
# CORS CONFIGURATION
# =============================================================================

# Allowed origins
# - Purpose: Whitelist of origins for CORS
# - Valid values: Comma-separated list of URLs
# - Default: http://localhost:3000
# - Required: Yes
# - Production: Add production frontend URL
# - Example: https://pixcrawler.com,https://app.pixcrawler.com
ALLOWED_ORIGINS=http://localhost:3000
```

---

## Frontend Configuration

**File**: `frontend/.env` (development) or `frontend/.env.production` (production)

### Supabase Client Configuration

```bash
# =============================================================================
# SUPABASE CLIENT CONFIGURATION
# =============================================================================

# Supabase project URL (Public)
# - Purpose: Base URL for Supabase client
# - Valid values: https://<project-id>.supabase.co
# - Default: None
# - Required: Yes
# - Security: Safe to expose (public)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co

# Supabase anonymous key (Public)
# - Purpose: Public key for client-side operations
# - Valid values: JWT token starting with "eyJ"
# - Default: None
# - Required: Yes
# - Security: Safe to expose (respects RLS)
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Direct database connection (Optional)
# - Purpose: Direct PostgreSQL connection for server-side operations
# - Valid values: postgresql://user:pass@host:port/db
# - Default: None
# - Required: No
# - Use case: Server-side rendering, API routes
POSTGRES_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
```

### API Configuration

```bash
# =============================================================================
# API CONFIGURATION
# =============================================================================

# Backend API URL (Public)
# - Purpose: Base URL for backend API calls
# - Valid values: http://localhost:8000 (dev), https://api.pixcrawler.com (prod)
# - Default: http://localhost:8000
# - Required: Yes
# - Development: http://localhost:8000
# - Production: https://your-backend.azurewebsites.net
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Lemon Squeezy Integration (Optional)

```bash
# =============================================================================
# LEMON SQUEEZY PAYMENT INTEGRATION (Optional)
# =============================================================================

# Lemon Squeezy API key (Server-side only)
# - Purpose: Server-side Lemon Squeezy API calls
# - Valid values: API key from Lemon Squeezy dashboard
# - Default: None
# - Required: No (only if using payments)
# - Security: NEVER expose in client-side code
LEMONSQUEEZY_API_KEY=your_api_key

# Lemon Squeezy Store ID
# - Purpose: Identify your store
# - Valid values: Store ID from Lemon Squeezy dashboard
# - Default: None
# - Required: No (only if using payments)
LEMONSQUEEZY_STORE_ID=your_store_id

# Lemon Squeezy webhook secret
# - Purpose: Verify webhook signatures
# - Valid values: Webhook secret from Lemon Squeezy dashboard
# - Default: None
# - Required: No (only if using webhooks)
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret

# Lemon Squeezy variant IDs
# - Purpose: Product variant configuration
# - Valid values: Variant IDs from Lemon Squeezy Dashboard
# - Default: None
# - Required: No (only if using payments)
LEMONSQUEEZY_HOBBY_VARIANT_ID=variant_id
LEMONSQUEEZY_PRO_VARIANT_ID=variant_id
LEMONSQUEEZY_PAYG_VARIANT_ID=variant_id
LEMONSQUEEZY_CREDITS_1000_VARIANT_ID=variant_id
LEMONSQUEEZY_CREDITS_5000_VARIANT_ID=variant_id
LEMONSQUEEZY_CREDITS_10000_VARIANT_ID=variant_id
```

### Resend Email Configuration (Optional)

```bash
# =============================================================================
# RESEND EMAIL SERVICE (Optional)
# =============================================================================

# Resend API key
# - Purpose: Send transactional emails
# - Valid values: re_* API key from Resend
# - Default: None
# - Required: No (only if using email)
# - Security: Keep confidential
RESEND_API_KEY=re_...

# Contact form recipient
# - Purpose: Email address for contact form submissions
# - Valid values: Valid email address
# - Default: None
# - Required: No (only if using contact form)
CONTACT_EMAIL=contact@pixcrawler.com

# From email address
# - Purpose: Sender address for outgoing emails
# - Valid values: Valid email address (must be verified in Resend)
# - Default: onboarding@resend.dev
# - Required: No
# - Production: Use verified domain
FROM_EMAIL=onboarding@resend.dev
```

### Application Settings

```bash
# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

# Application public URL (Public)
# - Purpose: Base URL for the application
# - Valid values: http://localhost:3000 (dev), https://pixcrawler.com (prod)
# - Default: http://localhost:3000
# - Required: Yes
# - Used for: Redirects, email links, sitemap
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Node environment
# - Purpose: Controls Next.js build and runtime behavior
# - Valid values: development, production, test
# - Default: development
# - Required: Yes
# - Note: Automatically set by Next.js in most cases
NODE_ENV=development
```

---

## Validation Rules

### Backend Validation

The backend uses Pydantic for configuration validation:

- **Required fields**: Must be present or have default values
- **Type checking**: Automatic type conversion and validation
- **Format validation**: URLs, connection strings, etc.
- **Range validation**: Numeric values within acceptable ranges
- **Environment-specific**: Different validation rules per environment

### Frontend Validation

The frontend uses Zod for runtime validation (`frontend/lib/env.ts`):

- **Fail-fast**: Application won't start with invalid config
- **Type-safe**: TypeScript types generated from schema
- **Clear errors**: Detailed error messages for missing/invalid variables
- **Public vs private**: Validates NEXT_PUBLIC_ prefix for client-side vars

### Common Validation Errors

1. **Missing required variable**
   ```
   Error: Missing required environment variable: SUPABASE_URL
   ```
   **Fix**: Add the variable to your `.env` file

2. **Invalid URL format**
   ```
   Error: SUPABASE_URL must be a valid URL
   ```
   **Fix**: Ensure URL starts with http:// or https://

3. **Invalid connection string**
   ```
   Error: DATABASE_URL must use postgresql+asyncpg:// driver
   ```
   **Fix**: Use correct driver format for SQLAlchemy

4. **Port out of range**
   ```
   Error: PORT must be between 1024 and 65535
   ```
   **Fix**: Use a valid port number

---

## Configuration Examples

### Development Environment

**Root `.env`**:
```bash
PIXCRAWLER_ENVIRONMENT=development
SUPABASE_URL=https://abcdefgh.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_ANON_KEY=eyJhbGc...
LOG_LEVEL=DEBUG
```

**Backend `backend/.env`**:
```bash
ENVIRONMENT=development
DEBUG=true
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=DEBUG

DATABASE_URL=postgresql+asyncpg://postgres:password@db.abcdefgh.supabase.co:5432/postgres
DATABASE_POOL_SIZE=5
DATABASE_ECHO=true

CACHE_ENABLED=true
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_DB=0

LIMITER_ENABLED=true
LIMITER_REDIS_HOST=localhost
LIMITER_REDIS_PORT=6379
LIMITER_REDIS_DB=1

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

STORAGE_PROVIDER=local
STORAGE_LOCAL_PATH=./storage

ALLOWED_ORIGINS=http://localhost:3000
```

**Frontend `frontend/.env`**:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://abcdefgh.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
NODE_ENV=development
```

### Production Environment

**Backend (Azure App Service Environment Variables)**:
```bash
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

DATABASE_URL=postgresql+asyncpg://postgres:prod_password@db.abcdefgh.supabase.co:5432/postgres
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_PRE_PING=true
DATABASE_ECHO=false

CACHE_ENABLED=true
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_DB=0

LIMITER_ENABLED=true
LIMITER_REDIS_HOST=localhost
LIMITER_REDIS_PORT=6379
LIMITER_REDIS_DB=1

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_TIME_LIMIT=1800
CELERY_WORKER_CONCURRENCY=8

STORAGE_PROVIDER=azure
STORAGE_AZURE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
STORAGE_AZURE_CONTAINER_NAME=pixcrawler-datasets

ALLOWED_ORIGINS=https://pixcrawler.com,https://app.pixcrawler.com

SUPABASE_URL=https://abcdefgh.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
```

**Frontend (Vercel Environment Variables)**:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://abcdefgh.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...
NEXT_PUBLIC_API_URL=https://api.pixcrawler.com
NEXT_PUBLIC_APP_URL=https://pixcrawler.com
NODE_ENV=production

# Optional: Lemon Squeezy
LEMONSQUEEZY_API_KEY=your_api_key
LEMONSQUEEZY_STORE_ID=your_store_id
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret

# Optional: Resend
RESEND_API_KEY=re_...
CONTACT_EMAIL=contact@pixcrawler.com
FROM_EMAIL=noreply@pixcrawler.com
```

---

## Best Practices

1. **Never commit `.env` files** - Use `.env.example` as templates
2. **Use strong secrets** - Generate secure random strings for keys
3. **Separate environments** - Different credentials for dev/staging/prod
4. **Validate early** - Check configuration at application startup
5. **Document changes** - Update `.env.example` when adding new variables
6. **Rotate secrets** - Regularly update API keys and passwords
7. **Use environment variables** - Prefer platform env vars over files in production
8. **Monitor usage** - Track connection pool usage, rate limits, etc.

---

## Troubleshooting

### Configuration Not Loading

1. Check file location (must be in correct directory)
2. Verify file name (`.env`, not `env` or `.env.txt`)
3. Restart application after changes
4. Check for syntax errors (no spaces around `=`)

### Validation Errors

1. Review error message for specific variable
2. Check `.env.example` for correct format
3. Verify required vs optional variables
4. Ensure proper quoting for special characters

### Connection Issues

1. Verify credentials are correct
2. Check network connectivity
3. Confirm service is running (Redis, PostgreSQL)
4. Review firewall and security group rules

---

For deployment-specific configuration, see [DEPLOYMENT.md](./DEPLOYMENT.md).
