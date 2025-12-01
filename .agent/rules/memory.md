---
trigger: always_on
---

PixCrawler

🎯 PROJECT OVERVIEW
PixCrawler is an automated image dataset builder SaaS platform designed for ML/AI researchers, enterprises, and developers. It transforms search keywords into organized, validated, ready-to-use image datasets.
Core Value Proposition:
Multi-source image scraping in addition to search engine crawling (Google, Bing, Baidu, DDG)
AI-powered keyword generation and expansion
Automated validation, deduplication, and quality checks
ML-ready output with multiple label formats
Hot/warm storage tiers for optimized delivery

🏗️ ARCHITECTURE
Architecture Pattern: Shared Supabase Database
Frontend: Next.js 15 + Drizzle ORM + Supabase Client (anon key + RLS)
Backend: FastAPI + SQLAlchemy + Supabase Client (service role key)
Database: Single Supabase PostgreSQL instance (source of truth)
Real-time: Supabase real-time subscriptions (no custom WebSockets)
Monorepo Structure (UV Workspace)
pixcrawler/
├── backend/          # FastAPI API server
├── builder/          # Core image crawling engine
├── frontend/         # Next.js web application
├── celery_core/      # Celery task queue (future scaling)
├── logging_config/   # Centralized Loguru logging
├── validator/        # Image validation package
| ...etc              # More packages in Future
└── pyproject.toml    # Root workspace config



🔧 TECHNOLOGY STACK
Backend (Python 3.10+)
Framework: FastAPI with Uvicorn
ORM: SQLAlchemy 2.0 (async)
Database: PostgreSQL via Supabase
Auth: Supabase Auth + PyJWT
Task Queue: Celery + Redis (configured, not fully implemented)
Validation: Pydantic 2.0+ with Settings
Logging: Loguru (centralized)
Package Manager: UV with workspace support
Build System: Hatchling

🎨 DESIGN PATTERNS & CONVENTIONS
Backend Patterns
Clean Architecture
Separation: API → Services → Database
Dependency injection via FastAPI Depends()
Base service class for common functionality
Exception Handling
Custom exception hierarchy (PixCrawlerException base)
Specific exceptions: ValidationError, NotFoundError, AuthenticationError, etc.
Centralized exception handlers with structured JSON responses
Comprehensive logging with request context
Configuration Management
Pydantic Settings with environment variable support
Validation at configuration load time
Cached settings with @lru_cache()
Environment-specific defaults (development/staging/production)
Middleware Stack
Request logging with UUID tracking
Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
CORS configuration
Process time tracking
API Design
RESTful endpoints with versioning (/api/v1/)
Pydantic models for request/response validation
Pagination support with PaginatedResponse
Background task execution via FastAPI BackgroundTasks

📝 CODING STANDARDS
Python Standards
Type Hints
Full type annotations required (MyPy strict mode)
Modern typing (PEP 484, 585, 604)
Use Optional, List, Dict, Any, etc.
Documentation
Google-style docstrings for public functions
Module-level docstrings with __all__
Comprehensive inline comments for complex logic
Imports
Absolute imports preferred
Grouped: standard library → third-party → local
Sorted with isort (Ruff integration)
Error Handling
Catch specific exceptions
Avoid bare except
Log meaningful context with Loguru
Use custom exception classes
Functions
Keep functions < 20 lines
Single responsibility principle
Early returns for guard clauses
Use type hints for all parameters and returns

🚀 DEPLOYMENT & OPERATIONS
Development Workflow
Backend:
uv sync                    # Install dependencies
uv run pytest              # Run tests
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run mypy .              # Type check

🎯 IMPLEMENTATION HIGHLIGHTS
Configuration Flexibility
JSON schema validation
Environment variable overrides
CLI argument support
Sensible defaults
Type Safety
Full type coverage in Python (MyPy strict)
TypeScript throughout frontend
Pydantic models for runtime validation

-------

# PixCrawler Frontend Architecture - Complete Review

## Technology Stack & Configuration

### Core Technologies
- **Framework**: Next.js 15 (canary v15.4.0-canary.47) with App Router
- **React**: v19.1.0
- **TypeScript**: v5.8.3 with strict mode
- **Package Manager**: Bun (>=1.0.0)
- **Build Tool**: Turbopack for development

### Next.js Configuration (next.config.ts)
- Experimental Features: PPR (Partial Prerendering), clientSegmentCache, nodeMiddleware
- Image Optimization: WebP/AVIF formats, responsive device sizes (640-3840px)
- Remote Patterns: Allows all HTTPS domains

### TypeScript Configuration
- Target: ESNext with strict type checking
- Path aliases: @/* maps to root directory
- Module resolution: bundler mode

## Architecture Pattern: Shared Supabase Database

### Database Stack
- **ORM**: Drizzle ORM v0.43.1 (type-safe)
- **Connection**: Direct PostgreSQL via postgres package
- **Schema**: lib/db/schema.ts with 5 main tables (profiles, projects, crawl_jobs, images, activity_logs)
- **Migrations**: Managed via drizzle-kit

### Data Flow
Frontend (anon key + RLS) ↔ Supabase PostgreSQL ↔ Backend (service role)

## Project Structure

### App Directory (Next.js 15 App Router)
```
app/
├── (auth)/              # Auth route group
├── (dashboard)/         # Dashboard route group
├── api/                 # API routes (payments, webhooks, contact)
├── dashboard/           # Protected dashboard
│   ├── billing/
│   ├── datasets/
│   ├── profile/
│   ├── projects/new/    # Project creation
│   └── settings/
├── login/, signup/
├── welcome/             # Onboarding
├── layout.tsx           # Root layout with theme provider
└── page.tsx             # Landing page
```

### Component Organization
```
components/
├── ui/                  # Shadcn UI (25+ components)
│   ├── button.tsx       # Enhanced with CVA variants
│   ├── sidebar.tsx
│   └── ...
├── LandingPage/         # Hero, Navigation, Features, etc.
├── auth/                # auth-guard.tsx
├── Image/, dataset/, pricing/, payments/
```

### Library Structure
```
lib/
├── auth/
│   ├── index.ts         # AuthService class
│   ├── hooks.ts         # useAuth, useRequireAuth
│   └── server.ts        # Server-side auth
├── db/
│   ├── schema.ts        # Drizzle schema
│   ├── index.ts         # DB client
│   └── setup.ts, seed.ts
├── supabase/
│   ├── client.ts        # Client-side
│   └── server.ts        # Server-side
└── utils.ts             # cn() utility
```

## Authentication Architecture (Multi-Layer)

### 1. Middleware Layer (middleware.ts)
- Runs on every request before page load
- Supabase server client with cookie management
- Protected routes: /dashboard, /welcome
- Auth routes: /login, /signup
- Onboarding flow check (onboarding_completed)
- Dev bypass: ?dev_bypass=true

### 2. Client-Side Auth (lib/auth/)
- **AuthService Class**: Sign up/in, OAuth (GitHub, Google), password reset, profile fetching
- **useAuth Hook**: Provides user state, loading, signOut
- **useRequireAuth Hook**: Redirects if not authenticated
- Dev bypass support with mock user

### 3. Component-Level Guards
- **AuthGuard Component**: Wraps protected pages, shows loading, redirects if unauthenticated
- Used in dashboard layout

### 4. Server-Side Auth
- Server Components use createClient() from lib/supabase/server.ts
- Cookie-based session management
- SSR-compatible

## Styling Architecture

### Design System (globals.css)
- HSL color system with CSS variables
- 12 semantic colors (primary, secondary, muted, destructive, etc.)
- Light/Dark mode via .dark class
- Custom scrollbar with gradient colors
- Custom animations: float, gradient, shimmer, slideInUp
- Background patterns: grid, radial gradient, noise
- Utility classes: line-clamp, progress indicators

### Tailwind Configuration
- Dark mode: class-based
- Custom container with 2rem padding
- Extended theme with HSL variables
- CVA (class-variance-authority) for component variants
- Radix UI integration

### Component Styling Pattern
```typescript
const buttonVariants = cva(baseStyles, {
  variants: { variant, size, loading }
})
className={cn(buttonVariants({ variant, size }), className)}
```

## State Management & Data Flow

### No Global State Library
- Local State: useState for component state
- Server State: Supabase real-time subscriptions
- Auth State: useAuth hook
- URL State: useSearchParams

### Data Fetching
- **Server Components**: Async RSC with direct Supabase queries
- **Client Components**: useAuth hook, direct Supabase queries or API routes
- **Real-time**: Supabase subscriptions via onAuthStateChange

## Routing Architecture

### App Router Features
- Route Groups: (auth), (dashboard)
- Nested Layouts: Root, Dashboard, per-section
- Loading States: loading.tsx, error.tsx, global-error.tsx, not-found.tsx
- API Routes: app/api/ for server-side endpoints

## Key Patterns & Best Practices

### Component Patterns
- Memoization: React.memo with displayName
- Composition: asChild pattern with Radix Slot
- Variants: CVA for type-safe variants

### Type Safety
- Drizzle type inference: $inferSelect, $inferInsert
- Enum definitions for status types
- Full TypeScript strict mode

### Performance Optimizations
- Next.js Image with WebP/AVIF
- Automatic code splitting
- React.memo for expensive components
- Turbopack for fast dev builds

### Developer Experience
- Scripts: dev, build, db:generate, db:migrate, db:studio
- Pre-build hooks: generateImageManifest.js
- Drizzle Studio GUI for database

## Integration Points

### Supabase
- Auth: Email/password, OAuth (GitHub, Google)
- Database: Direct PostgreSQL via Drizzle
- Storage: Configured for images
- Real-time: Subscriptions for live updates

### Lemon Squeezy
- Payment routes in app/api/payments/
- Checkout session, order details, webhooks

### Third-Party Libraries
- UI: Radix UI primitives (14+ components)
- Icons: Lucide React
- Animations: Framer Motion
- Forms: React Hook Form
- Validation: Zod
- Charts: Recharts

## Implementation Status

### ✅ Fully Implemented
- Authentication flow (email, OAuth)
- Middleware protection
- Database schema & ORM
- UI component library
- Landing page
- Dashboard shell
- Project creation UI
- Theme system (light/dark)
- Responsive design

### 🚧 Partially Implemented
- Real-time subscriptions (configured)
- Lemon Squeezy payments (routes exist)
- Image crawling integration (UI ready)
- Activity logging (schema exists)

### 📋 Planned
- Backend API integration
- Crawl job creation
- Real-time job progress
- Image gallery/preview
- Dataset export

## Architecture Strengths
1. Type Safety: Full TypeScript with strict mode
2. Modern Stack: Latest Next.js, React 19
3. Scalability: Clean separation of concerns
4. Performance: Turbopack, image optimization, PPR
5. Developer Experience: Excellent tooling
6. Design System: Consistent, themeable, accessible
7. Security: RLS, middleware protection, proper auth
-----
