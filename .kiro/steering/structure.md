# PixCrawler Project Structure

## Repository Organization
This is a monorepo using UV workspace configuration with 5 Python packages and a Next.js frontend application.

## Root Level Structure
```
pixcrawler/
├── .kiro/                    # Kiro AI assistant configuration
├── backend/                  # FastAPI backend service (pixcrawler-backend)
├── builder/                  # Core image crawling engine (pixcrawler-builder)
├── celery_core/              # Distributed task processing (pixcrawler-celery-core)
├── frontend/                 # Next.js web application
├── utility/                  # Shared utilities & logging (pixcrawler-utility)
├── validator/                # Image validation system (pixcrawler-validator)
├── src/                      # Root package source (report generation)
├── tests/                    # Cross-package integration tests
├── docs/                     # Comprehensive documentation
├── scripts/                  # Utility scripts (worker management)
├── postman/                  # API testing collections
├── pyproject.toml           # Root workspace configuration
└── uv.lock                  # UV lockfile for reproducible builds
```

## Package Structure

### Backend Package (`backend/`)
- **Purpose**: FastAPI REST API server with Supabase authentication
- **Type**: Python package using Hatchling
- **Key Components**:
  - `api/v1/endpoints/`: REST endpoints (auth, crawl_jobs, datasets, exports, health, storage, users, validation)
  - `core/`: Configuration, middleware, exceptions, security
    - `settings/supabase.py`: Supabase configuration (URL, service role key, anon key)
  - `database/`: Database connection and models
    - `models.py`: SQLAlchemy models synchronized with frontend Drizzle schema
  - `models/`: SQLAlchemy/Pydantic models
  - `repositories/`: Data access layer
  - `schemas/`: Request/response schemas
  - `services/`: Business logic layer
    - `supabase_auth.py`: Token verification and user management (NO custom JWT)
  - `storage/`: Storage provider implementations (Azure Blob, Azure Data Lake, local)
  - `utils/`: Helper utilities
  - `main.py`: Application entry point with lifespan management
  - `static/`: Custom Swagger UI and ReDoc HTML files
- **Dependencies**: FastAPI, Uvicorn, SQLAlchemy, Alembic, Redis, Celery, Supabase
- **Authentication**: Supabase Auth ONLY - no custom login/signup endpoints

### Builder Package (`builder/`)
- **Purpose**: Core image crawling and dataset generation engine
- **Key Modules**:
  - `_generator.py`: Main dataset generation orchestration
  - `_config.py`: Configuration management and validation
  - `_downloader.py`: Multi-engine image downloading
  - `_engine.py`: Search engine implementations
  - `_builder.py`: Dataset building logic
  - `_keywords.py`: AI-powered keyword generation
  - `_helpers.py`: Helper functions and utilities
  - `_constants.py`: Application constants
  - `_exceptions.py`: Custom exception classes
  - `tasks.py`: Celery task definitions
  - `progress.py`: Progress tracking
- **Dependencies**: icrawler, requests, Pillow, ddgs, g4f, jsonschema

### Celery Core Package (`celery_core/`)
- **Purpose**: Shared Celery configuration and task management
- **Key Modules**:
  - `app.py`: Celery application instance
  - `config.py`: Celery configuration
  - `base.py`: Base task classes
  - `manager.py`: Task management utilities
  - `tasks.py`: Common task definitions
  - `workflows.py`: Workflow orchestration
- **Dependencies**: Celery, Redis, Pydantic

### Frontend Package (`frontend/`)
- **Purpose**: Next.js 15 web application with Supabase integration
- **Structure**:
  - `app/`: Next.js app router (pages, layouts, API routes)
    - `layout.tsx`: Root layout with ErrorBoundaryProvider
    - `api/`: API routes (notifications, contact form)
  - `components/`: React components (UI, landing page, providers)
    - `providers/error-boundary-provider.tsx`: Global error boundary
    - `error-fallback.tsx`: User-friendly error UI
    - `ui/`: Reusable UI components (Radix UI based)
    - `LandingPage/`: Landing page components
  - `lib/`: Shared utilities, database schema (Drizzle ORM), Supabase client
    - `db/schema.ts`: **Single source of truth** for database schema (10 tables)
    - `db/setup.ts`: Creates profiles table and RLS policies
    - `db/seed.ts`: Seed data (requires real Supabase Auth user UUID)
    - `api/client.ts`: Centralized API client with interceptors
    - `api/index.ts`: Type-safe API methods
    - `env.ts`: Zod-based environment variable validation
  - `hooks/`: Custom React hooks
    - `useNotifications.ts`: Real-time notifications hook
  - `public/`: Static assets
  - `scripts/`: Build scripts (image manifest generation)
  - `middleware.ts`: Next.js middleware for auth
  - `drizzle.config.ts`: Drizzle ORM configuration
  - `bun.lock`: **Primary lockfile** (use Bun, not npm)
- **Tech Stack**: Next.js 15, React 19, TypeScript, Drizzle ORM, Supabase, Tailwind CSS, Radix UI
- **Database**: **Shared Supabase PostgreSQL** with backend
  - 10 tables: profiles, projects, crawl_jobs, images, notifications, activity_logs, api_keys, credit_accounts, credit_transactions, notification_preferences, usage_metrics
  - Schema managed by Drizzle ORM in frontend
  - Backend SQLAlchemy models synchronized with frontend schema

### Utility Package (`utility/`)
- **Purpose**: Centralized utilities, logging, compression, and archiving
- **Key Components**:
  - `logging_config/`: Loguru-based logging system
  - `compress/`: Compression utilities (archiving, formats, pipeline)
- **Dependencies**: Loguru, Pydantic, zstandard, Pillow, tqdm
- **Scope**: Shared across all workspace packages

### Validator Package (`validator/`)
- **Purpose**: Image validation, integrity checking, and duplicate detection
- **Key Modules**:
  - `validation.py`: Image validation logic
  - `integrity.py`: Integrity checking
  - `level.py`: Validation levels
  - `tasks.py`: Celery validation tasks
- **Dependencies**: Pillow, imagehash, numpy, jsonschema

## Naming Conventions

### Python Packages
- **Module Names**: Snake_case with underscore prefix for internal modules (`_generator.py`, `_config.py`)
- **Public Modules**: No prefix for public APIs (`tasks.py`, `progress.py`)
- **Package Names**: Lowercase with hyphens (`pixcrawler-backend`, `pixcrawler-utility`)

### File Organization
- **Configuration Files**: Root level for workspace-wide settings
- **Package-Specific**: Each package maintains its own `pyproject.toml`
- **Tests**: Both centralized (`/tests`) and package-level (`backend/tests`, `builder/tests`)

## Workspace Dependencies
The root `pyproject.toml` defines 5 workspace members:
- `backend` → depends on: utility, celery_core
- `builder` → depends on: utility, celery_core
- `celery_core` → depends on: utility
- `validator` → depends on: utility, celery_core
- `utility` → standalone (no workspace dependencies)

## API Endpoints Structure
Backend provides RESTful API v1 with the following endpoints:
- `/api/v1/health` - Health checks and system status
- `/api/v1/auth` - Authentication and user profile
- `/api/v1/users` - User management (admin)
- `/api/v1/datasets` - Dataset CRUD operations
- `/api/v1/jobs` - Crawl job management
- `/api/v1/storage` - Storage operations
- `/api/v1/exports` - Dataset export functionality
- `/api/v1/validation` - Image validation services

## Database Schema (Shared Supabase PostgreSQL)

**Single Source of Truth**: `frontend/lib/db/schema.ts`

PostgreSQL database managed by Drizzle ORM (frontend) and SQLAlchemy (backend):

### Core Tables
- **profiles**: User profiles (extends Supabase auth.users)
  - UUID primary key references auth.users.id
  - email, full_name, avatar_url, role, onboarding status
  - Created automatically via Supabase Auth trigger
- **projects**: Project organization
  - Groups crawl jobs together
  - Belongs to user (userId references profiles.id)
- **crawl_jobs**: Image crawling tasks with chunk tracking
  - Belongs to project (projectId references projects.id)
  - keywords (JSONB), max_images, status, progress
  - Chunk tracking: total_chunks, active_chunks, completed_chunks, failed_chunks
  - task_ids (JSONB) for Celery task tracking
- **images**: Crawled image metadata
  - Belongs to crawl_job (crawlJobId references crawl_jobs.id)
  - original_url, filename, storage_url, dimensions, file_size, format
  - hash (for duplicate detection), is_valid, is_duplicate
  - labels (JSONB), metadata (JSONB)

### User Management Tables
- **activity_logs**: User activity tracking
  - action, resource_type, resource_id, metadata (JSONB)
- **api_keys**: Programmatic access keys
  - name, key_hash, key_prefix, status, permissions (JSONB)
  - rate_limit, usage_count, last_used_at, expires_at
- **notifications**: User notifications
  - type, category, title, message, icon, color
  - action_url, action_label, metadata (JSONB)
  - is_read, read_at

### Billing Tables
- **credit_accounts**: User billing and credits
  - current_balance, monthly_usage, average_daily_usage
  - auto_refill_enabled, refill_threshold, refill_amount, monthly_limit
- **credit_transactions**: Transaction history
  - type (purchase, usage, refund, bonus)
  - amount, balance_after, status, metadata (JSONB)
- **notification_preferences**: User notification settings
  - email_enabled, push_enabled, sms_enabled
  - crawl_jobs_enabled, datasets_enabled, billing_enabled, security_enabled
  - digest_frequency, quiet_hours_start, quiet_hours_end
- **usage_metrics**: Daily usage tracking
  - metric_date, images_processed, storage_used_gb, api_calls, bandwidth_used_gb
  - Corresponding limits for each metric

### Database Access Patterns
- **Frontend**: Anon key + Row Level Security (RLS) policies
- **Backend**: Service role key (bypasses RLS for admin operations)
- **Migrations**: Generated and applied via Drizzle Kit (`bun run db:generate`, `bun run db:migrate`)
- **Setup**: RLS policies created via `bun run db:setup`

## Development Workflow

### 1. Root Level - Workspace Management
```bash
uv sync                    # Install all workspace dependencies
uv sync --all-extras       # Install with optional dependencies
uv run pytest tests/       # Run cross-package integration tests
uv build                   # Build all packages
```

### 2. Backend - FastAPI Development
```bash
cd backend
uv run uvicorn backend.main:app --reload  # Development server
uv run pytest backend/tests/               # Run backend tests
uv run pytest --cov=backend --cov-report=html  # With coverage
```
- API documentation: http://localhost:8000/docs (Swagger UI)
- Alternative docs: http://localhost:8000/redoc
- Postman collections in `postman/` directory

### 3. Builder - Dataset Generation Engine
```bash
# Used as library by backend and celery workers
# Standalone usage example in builder/example/
```

### 4. Frontend - Next.js Development (Use Bun!)
```bash
cd frontend
bun install                # Install dependencies
bun dev                    # Development server with Turbopack
bun run dev:vercel         # Vercel dev (for testing Resend emails)
bun run db:generate        # Generate Drizzle migrations
bun run db:migrate         # Apply migrations
bun run db:studio          # Open Drizzle Studio
bun run db:setup           # Setup RLS policies (first time only)
```
- Frontend: http://localhost:3000
- **Important**: Use Bun, not npm (fallback only if Bun unavailable)

### 5. Celery - Distributed Task Processing
```bash
# Start Redis (required for Celery)
redis-server

# Start Celery worker
celery -A celery_core.app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A celery_core.app beat --loglevel=info

# Monitor with Flower (optional)
celery -A celery_core.app flower
```

### 6. Full Stack Development
```bash
# Terminal 1: Backend
cd backend && uv run uvicorn backend.main:app --reload

# Terminal 2: Frontend
cd frontend && bun dev

# Terminal 3: Redis
redis-server

# Terminal 4: Celery Worker
celery -A celery_core.app worker --loglevel=info
```

## Import Patterns
- **Internal Imports**: Relative imports within packages
- **Cross-Package**: Import via workspace dependency names (`from utility.logging_config import get_logger`)
- **First-Party Packages**: `["backend", "builder", "logging_config", "celery_core", "validator"]`

## Configuration Management
- **Root**: Workspace-wide linting (Ruff), formatting, type checking (MyPy), testing (Pytest)
- **Package**: Individual package metadata, dependencies, and build configuration
- **Frontend**: Separate Node.js ecosystem with TypeScript, ESLint, Tailwind configuration
