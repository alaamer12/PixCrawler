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


---
trigger: model_decision
description:  rules and best practices for Python development within the PixCrawler project, ensuring code consistency and quality.
---

# Python Development Guidelines

This document outlines the best practices and conventions for Python development in the PixCrawler project.

## 1. Code Style

- **PEP 8**: All Python code must adhere to the [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/).
- **Typing**: All functions and methods must have type hints as per [PEP 484](https://www.python.org/dev/peps/pep-0484/). Use modern type hinting syntax (e.g., `list[int]` instead of `typing.List[int]`).
- **Docstrings**: Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#3.8-comments-and-docstrings) for all public modules, classes, functions, and methods.
- **Imports**: Imports should be grouped in the following order: standard library, third-party libraries, and local application imports. Use absolute imports.
- **Linting**: Use `Ruff` for linting and formatting. The configuration is in [pyproject.toml](cci:7://file:///f:/Projects/Languages/Python/WorkingOnIt/PixCrawler/pyproject.toml:0:0-0:0).

## 2. Dependency Management

- **Poetry**: Use [Poetry](https://python-poetry.org/) for dependency management.
- **Adding Dependencies**: Add new dependencies using `poetry add <package>`.
- **Updating Dependencies**: Keep dependencies up to date by running `poetry update` periodically.
- **Lock File**: Always commit the `poetry.lock` file to ensure reproducible builds.

## 3. Testing

- **Framework**: Use `pytest` for writing and running tests.
- **Test Location**: Tests for the `builder` package should be in the `tests/` directory.
- **Coverage**: Aim for a high test coverage. All new features should have corresponding tests.
- **Mocks**: Use `pytest-mock` for mocking objects and dependencies.

## 4. General Practices

- **Configuration**: Store configuration in [pyproject.toml](cci:7://file:///f:/Projects/Languages/Python/WorkingOnIt/PixCrawler/pyproject.toml:0:0-0:0) or dedicated configuration files, not in code.
- **Logging**: Use the `logging` module for logging. Configure it via `logging_config/`.
- **Error Handling**: Catch specific exceptions. Avoid bare `except:` clauses.

---
trigger: model_decision
description: Guidelines for TypeScript and Next.js development in the frontend application, focusing on code style, component structure, and state management.
---

# TypeScript and Next.js Development Guidelines

This document outlines the best practices for TypeScript and Next.js development in the PixCrawler frontend.

## 1. Code Style and Formatting

- **Style Guide**: Follow the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript).
- **Formatting**: Use `Prettier` for automatic code formatting. The configuration is in your project files.
- **Typing**: Strive for full type coverage. Avoid using `any` unless absolutely necessary. Use utility types like `Partial`, `Pick`, and `Omit` where appropriate.
- **JSDoc**: Add JSDoc comments to all public functions, components, and hooks, explaining their purpose, parameters, and return values.

## 2. Naming Conventions

- **Components**: Use `PascalCase` for React component files and components (e.g., `UserProfile.tsx`).
- **Files**: Use `kebab-case` for non-component files (e.g., `user-api.ts`).
- **Variables & Functions**: Use `camelCase` for variables and functions.
- **Environment Variables**: Prefix all environment variables with `NEXT_PUBLIC_` if they need to be exposed to the browser.

## 3. Component & Directory Structure

- **App Router**: Utilize the Next.js App Router for routing and layouts.
- **Component Organization**:
    - `app/`: Contains the main application routes and pages.
    - `components/ui/`: For reusable, generic UI components (e.g., Button, Input), often from a library like Shadcn UI.
    - `components/shared/`: For components shared across multiple routes.
    - `lib/`: For utility functions, API calls, and other non-component logic.
- **Styling**: Use `Tailwind CSS` for styling. Avoid inline styles and CSS files where possible.

## 4. State Management

- **Client State**: For simple client-side state, use React Hooks (`useState`, `useReducer`, `useContext`).
- **Server State**: Use `TanStack Query` (React Query) for managing server state, including caching, refetching, and mutations.
- **Forms**: Use `React Hook Form` for form state management and `Zod` for validation.

## 5. Dependency Management

- **Package Manager**: Use `bun` for package management.
- **Adding Dependencies**: Add new dependencies using `bun add <package>`.
- **Lock File**: Always commit the `bun.lockb` file to ensure reproducible builds.

---
trigger: always_on
---

# AI Interaction and Collaboration Guidelines

This document defines the rules for how AI assistants should interact with users in this workspace, ensuring transparency, user control, and effective collaboration.

## Core Principle: User-in-the-Loop

The user is the final authority on all changes. The AI's role is to assist, not to operate with full autonomy on significant tasks. The AI must prioritize keeping the user informed and empowered at all times.

## 1. Proposing Significant Changes

Before undertaking any significant changes, the AI **must** present a clear proposal to the user and wait for explicit approval before proceeding.

### What is a "Significant Change"?

A change is considered significant if it involves one or more of the following:

- **Large-Scale Code Edits**: Modifying more than 50 lines of code across one or more files.
- **Core Refactoring**: Restructuring or rewriting critical application logic (e.g., authentication, data processing, state management).
- **File System Operations**: Creating, deleting, or renaming multiple files or directories.
- **Dependency Management**: Adding, removing, or updating project dependencies.
- **Configuration Changes**: Modifying critical configuration files (e.g., [pyproject.toml](cci:7://file:///f:/Projects/Languages/Python/WorkingOnIt/PixCrawler/pyproject.toml:0:0-0:0), [package.json](cci:7://file:///f:/Projects/Languages/Python/WorkingOnIt/PixCrawler/frontend/package.json:0:0-0:0), [next.config.ts](cci:7://file:///f:/Projects/Languages/Python/WorkingOnIt/PixCrawler/frontend/next.config.ts:0:0-0:0), CI/CD pipelines).

### The Proposal Format

When a significant change is required, the AI must pause and provide the following information in a clear, structured format:

1.  **Summary of Change**: A high-level overview of what is being changed and why it is necessary.
    - *Example: "I am proposing to refactor the data fetching logic in the `builder` to improve performance and reduce duplicate code."*

2.  **Proposed Plan & Justification**: A step-by-step plan detailing the actions the AI will take. For each major step, provide a brief justification explaining why this approach is optimal compared to potential alternatives.
    - *Example:*
        - *1. Create a new file `lib/api_client.ts` to centralize all API calls. This avoids code duplication.*
        - *2. Refactor the `dashboard/page.tsx` component to use the new `api_client`. This simplifies the component's logic.*
        - *3. Update the tests in `__tests__/dashboard.test.tsx` to mock the new client.*

3.  **Request for Approval**: The AI must conclude its proposal by explicitly asking for the user's permission to proceed.
    - *Example: "Does this plan look good to you? Please let me know if you'd like any adjustments before I proceed."*

## 2. Acknowledging User Input

The AI must acknowledge and adapt to user feedback. If the user suggests an alternative approach or asks for modifications to the plan, the AI must adjust its plan accordingly and, if necessary, present a revised proposal.

By following these rules, the AI will act as a true pair-programming assistant, ensuring you always have full context and control over your project.

---
trigger: model_decision
description: This file defines the project-wide conventions for version control, commit messages, and the monorepo structure, ensuring a smooth and consistent development workflow for all contributors.
---

# Project-Wide Guidelines

This document outlines the conventions and best practices for the PixCrawler monorepo.

## 1. Version Control

- **Branching Strategy**:
    - `main`: The main branch, which should always be stable and deployable.
    - `develop`: The development branch, where new features are integrated.
    - `feature/<feature-name>`: Branches for developing new features.
    - `fix/<issue-name>`: Branches for bug fixes.
- **Pull Requests**: All changes must be submitted through a pull request (PR). PRs must be reviewed and approved by at least one other team member before merging.
- **Code Reviews**: Code reviews should be constructive and focus on code quality, correctness, and adherence to project guidelines.

## 2. Commit Messages

- **Semantic Commits**: Use [semantic commit messages](https://www.conventionalcommits.org/en/v1.0.0/) to ensure a clear and descriptive commit history.
- **Format**: `<type>(<scope>): <subject>`
    - **type**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
    - **scope**: The part of the project affected (e.g., `backend`, `frontend`, `builder`).
    - **subject**: A concise description of the change.

## 3. Monorepo Structure

- **`backend/`**: The Python backend application.
- **`frontend/`**: The Next.js frontend application.
- **`builder/`**: The Python web crawler and data processing engine.
- **`logging_config/`**: Shared logging configuration.
- **`tests/`**: Tests for the Python packages.
- **`.windsurf/`**: Contains workspace rules and other development-related configurations.

## 4. Working in the Monorepo

- **Dependencies**: Each package (`backend`, `frontend`, `builder`) manages its own dependencies.
- **Shared Code**: There is currently no shared code between the `frontend` and `backend`. If this changes, a `packages/shared` directory should be created.
- **Environment Variables**: Do not commit [.env](cci:7://file:///f:/Projects/Languages/Python/WorkingOnIt/PixCrawler/frontend/.env:0:0-0:0) files. Instead, use `.env.example` files to provide a template for required environment variables.