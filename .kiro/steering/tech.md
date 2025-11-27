# PixCrawler Technology Stack

## Build System & Package Management
- **Python**: UV package manager with workspace configuration (5 workspace members)
- **Frontend**: **Bun (primary)** / npm (fallback only) for Node.js dependencies
- **Build Backend**: Hatchling for Python package building
- **Important**: Always use Bun commands for frontend development unless explicitly unavailable

## Backend Stack
- **Language**: Python 3.11+ (supports 3.11, 3.12, 3.13)
- **Package Manager**: UV with workspace support
- **Web Framework**: FastAPI 0.104+ with Uvicorn (standard)
- **Database ORM**: SQLAlchemy 2.0+ with Alembic migrations
- **Authentication**: **Supabase Auth ONLY** (no custom JWT implementation)
  - Service role key for backend API
  - Token verification via `backend/services/supabase_auth.py`
  - No custom login/signup endpoints (handled by Supabase)
- **Task Queue**: Celery 5.3+ with Redis 5.0+ broker
- **Caching**: Redis for rate limiting and session management
- **Logging**: Loguru-based centralized logging system (pixcrawler-utility)
- **Image Processing**: Pillow for image validation and manipulation
- **Web Crawling**: icrawler with multiple engine support (Google, Bing, Baidu, DuckDuckGo)
- **Data Validation**: jsonschema for configuration validation, Pydantic 2.0+ for schemas
- **Storage**: Azure Blob Storage, Azure Data Lake Gen2, local filesystem
- **API Features**: FastAPI-Pagination, FastAPI-Limiter with Redis for rate limiting

## Frontend Stack
- **Framework**: Next.js 15.4.0 (canary) with React 19.1.0
- **Runtime**: Node.js >=18.0.0 with TypeScript 5.8.3
- **Package Manager**: **Bun (primary)** with bun.lock / npm (fallback only)
- **Database**: Drizzle ORM 0.43+ with PostgreSQL (postgres 3.4+)
  - **Shared Database**: Single Supabase PostgreSQL instance with frontend + backend
  - Schema defined in `frontend/lib/db/schema.ts` (10 tables)
  - Type-safe queries with Drizzle ORM
- **Authentication**: Supabase Auth (@supabase/ssr, @supabase/supabase-js 2.39+)
  - Anon key + Row Level Security (RLS) for frontend
  - SSR support with cookie-based sessions
  - No custom auth implementation
- **API Client**: Centralized in `lib/api/client.ts`
  - Automatic token injection
  - Request/response interceptors
  - Custom ApiError class for structured error handling
  - Type-safe API methods in `lib/api/index.ts`
- **Environment Validation**: Zod schema validation in `lib/env.ts`
- **Styling**: Tailwind CSS 3.4+ with PostCSS, tw-animate-css
- **UI Components**: 
  - Radix UI (@radix-ui/react-* components)
  - Lucide React 0.545+ icons
  - class-variance-authority for component variants
  - Framer Motion 12.23+ for animations
- **Error Handling**: 
  - ErrorBoundaryProvider for React errors
  - ErrorFallback component with user-friendly UI
- **Data Visualization**: Recharts 3.3+ for charts and graphs
- **Validation**: Zod 3.24+ for schema validation
- **State Management**: React hooks, Tanstack React Table 8.21+
- **Payments**: Stripe (@stripe/stripe-js 8.0+, stripe 19.1+) - planned
- **Email**: Resend 4.0+ for transactional emails (contact forms)
- **Progress**: @bprogress/next for loading indicators
- **Notifications**: Sonner 2.0+ for toast notifications
- **Themes**: next-themes 0.4+ for dark mode support

## Celery & Task Processing
- **Task Queue**: Celery 5.3+ with Redis broker
- **Message Protocol**: Kombu 5.3+
- **Monitoring**: Flower 2.0+ (optional), Prometheus client 0.17+ (optional)
- **Workflow**: Canvas workflows for complex task orchestration
- **Retry Logic**: Built-in retry mechanisms with exponential backoff

## Image Processing & Validation
- **Image Library**: Pillow 10.0+
- **Duplicate Detection**: imagehash 4.3+ (perceptual hashing)
- **Numerical Operations**: numpy 1.24+ for image processing
- **Validation Levels**: Configurable integrity checking (basic, standard, strict)

## Compression & Archiving
- **Compression**: zstandard 0.21+ for high-performance compression
- **Archive Formats**: ZIP, 7z, tar.gz support
- **Progress Tracking**: tqdm 4.65+ for progress bars

## AI & Keyword Generation
- **AI Provider**: g4f (GPT4Free) for keyword generation
- **Search Integration**: ddgs (DuckDuckGo Search) for query expansion

## Development Tools
- **Linting**: Ruff (primary linter and formatter)
- **Type Checking**: MyPy with strict configuration
- **Testing**: Pytest 8.4+ with pytest-asyncio, pytest-cov, pytest-mock
- **Pre-commit**: Configured hooks for code quality
- **Coverage**: Coverage.py with HTML/XML reports
- **API Testing**: Postman collections for all endpoints

## Storage & Cloud Services
- **Azure**: Azure Blob Storage, Azure Data Lake Gen2
- **Supabase**: Authentication, PostgreSQL database, Storage
- **Local**: Filesystem-based storage for development

## Common Commands

### Backend Development
```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn backend.main:app --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=backend --cov-report=html

# Lint and format_
uv run ruff check .
uv run ruff format_ .

# Type checking
uv run mypy .
```

### Frontend Development
```bash
# IMPORTANT: Use Bun as primary package manager (fallback to npm only if unavailable)

# Install dependencies
bun install

# Development server (Turbopack) - PRIMARY
bun dev
# Vercel dev environment (for testing Resend emails)
bun run dev:vercel

# Build for production
bun run build

# Start production server
bun run start

# Database operations
bun run db:generate    # Generate migrations
bun run db:migrate     # Run migrations
bun run db:studio      # Open Drizzle Studio
bun run db:seed        # Seed database (requires real Supabase Auth user UUID)
bun run db:setup       # Setup auth tables and RLS policies

# Generate image manifest
bun run generate:images

# Fallback to npm only if Bun is unavailable
# npm run dev
# npm run build
```

### Celery Workers
```bash
# Start Celery worker
celery -A celery_core.app worker --loglevel=info

# Start Celery beat (scheduler)
celery -A celery_core.app beat --loglevel=info

# Monitor with Flower
celery -A celery_core.app flower
```

### Project Management
```bash
# Install all workspace dependencies
uv sync --all-extras

# Build all packages
uv build

# Run tests across workspace
uv run pytest tests/

# Run specific package tests
uv run pytest backend/tests/
uv run pytest builder/tests/
```

## Code Quality Standards
- **Line Length**: 88 characters (Black/Ruff standard)
- **Python Version**: Minimum 3.11, target 3.11
- **Import Sorting**: isort configuration with first-party packages
- **Type Hints**: Required for all function definitions (MyPy strict mode)
- **Documentation**: Comprehensive docstrings for all public APIs
- **Test Coverage**: Minimum 80% coverage for critical paths
- **Error Handling**: Comprehensive exception handling with custom exceptions

## Environment Configuration

### Backend Environment Variables
```bash
# Application
ENVIRONMENT=production|development
DEBUG=false
LOG_LEVEL=INFO

# Supabase (from Supabase Dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # Backend uses service role key
SUPABASE_ANON_KEY=eyJhbGc...

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres

# Redis (for Celery and rate limiting)
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000

# Storage
AZURE_STORAGE_CONNECTION_STRING=...  # Optional for Azure
```

### Frontend Environment Variables (validated via Zod in `lib/env.ts`)
```bash
# Required
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx  # Frontend uses anon key + RLS
POSTGRES_URL=postgresql://xxx

# Optional (for Stripe)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_SECRET_KEY=sk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Optional (for Resend email)
RESEND_API_KEY=re_xxx
CONTACT_EMAIL=contact@pixcrawler.io
FROM_EMAIL=onboarding@resend.dev  # Use verified domain in production
```

### Important Notes
- **Shared Database**: Single Supabase PostgreSQL for frontend + backend
- **No Custom JWT**: Use Supabase Auth tokens only
- **Environment Validation**: Frontend validates all env vars at runtime with Zod
- **Development**: Use `.env.local` for frontend, `.env` for backend
- **Production**: Set environment variables in Azure Portal and Vercel Dashboard

## API Documentation
- **OpenAPI**: Auto-generated from FastAPI
- **Swagger UI**: Custom branded UI at `/docs`
- **ReDoc**: Alternative documentation at `/redoc`
- **Postman**: Complete collection with environment variables

## Deployment

### Backend (Azure App Service)
- **Platform**: Azure App Service (Linux container)
- **Startup Script**: `startup-azure.sh`
  - Installs UV and dependencies
  - Starts Redis for Celery
  - Starts Celery worker in background
  - Starts FastAPI with Gunicorn
- **Environment**: Set `PIXCRAWLER_ENVIRONMENT=production` in Azure Portal
- **Logging**: Automatic stdout/stderr capture to Azure Monitor
- **API Docs**: Available at `/docs` (Swagger UI) and `/redoc`

### Frontend (Vercel)
- **Platform**: Vercel with Next.js
- **Build Command**: `bun run build`
- **Environment Variables**: Set in Vercel Dashboard
- **Domain**: Custom domain or Vercel subdomain

### Database (Supabase)
- **Type**: Shared PostgreSQL instance
- **Access**: 
  - Frontend: Anon key + RLS policies
  - Backend: Service role key (bypasses RLS)
- **Schema Management**: Drizzle ORM migrations in frontend
- **RLS Policies**: Created via `bun run db:setup`

### Storage (Azure)
- **Hot Tier**: Azure Blob Storage for immediate access (ZIP)
- **Warm Tier**: Azure Data Lake Gen2 for cost-optimized archival (7z)
- **Local Development**: Filesystem-based storage

### Workers (Celery)
- **Development**: Local Celery workers
- **Production**: Azure Container Instances or VMs
- **Monitoring**: Flower dashboard (optional)
- **Broker**: Redis (localhost in Azure App Service, managed Redis in production)
