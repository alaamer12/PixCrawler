# Requirements Document

## Introduction

This specification defines the requirements for making PixCrawler production-ready with a comprehensive deployment configuration system. The goal is to establish a robust, well-documented, and production-grade configuration architecture that separates concerns between global, backend, and frontend configurations while ensuring alignment with the project's architecture principles (Supabase shared database, retry strategies, logging, etc.).

The system must support both development and production environments with clear documentation, proper environment variable management, startup scripts, and production-grade components across the entire stack.

## Requirements

### Requirement 1: Global Environment Configuration Management

**User Story:** As a DevOps engineer, I want a global environment configuration system that manages project-wide settings without knowing about internal backend or frontend configurations, so that I can deploy the application consistently across environments.

#### Acceptance Criteria

1. WHEN the project is deployed THEN there SHALL be a root-level `.env` file that contains only global project configuration
2. WHEN the root `.env` is read THEN it SHALL NOT contain backend-specific or frontend-specific configuration details
3. WHEN the root `.env.example` is provided THEN it SHALL be comprehensively documented with comments explaining each variable, its purpose, valid values, and examples
4. IF a developer needs to configure the project THEN the `.env.example` SHALL provide clear guidance on required vs optional variables
5. WHEN environment variables are set THEN they SHALL follow a consistent naming convention with appropriate prefixes (e.g., `PIXCRAWLER_`, `SUPABASE_`, `AZURE_`)

### Requirement 2: Backend Configuration System

**User Story:** As a backend developer, I want a complete backend configuration system that manages all backend-specific settings independently, so that the backend can be configured and deployed without affecting frontend configuration.

#### Acceptance Criteria

1. WHEN the backend is configured THEN there SHALL be a `backend/.env` file that contains all backend-specific configuration
2. WHEN backend configuration is defined THEN it SHALL include settings for:
   - Server application (host, port, environment, debug mode, log level)
   - Supabase (URL, service role key, anon key)
   - Database (connection URL, pool size, max overflow, echo mode)
   - Redis cache (enabled flag, host, port, password, database, prefix, TTL)
   - Rate limiter (enabled flag, host, port, password, database, prefix, default limits)
   - Celery (broker URL, result backend, worker settings)
   - Storage providers (local, Azure Blob, Azure Data Lake)
   - CORS (allowed origins)
3. WHEN the backend `.env.example` is provided THEN it SHALL be comprehensively documented with detailed comments for each configuration section
4. WHEN Redis is unavailable in development THEN the backend SHALL log warnings but continue to operate
5. WHEN Redis is unavailable in production THEN the backend SHALL fail with a clear error message
6. WHEN rate limiting is configured THEN it SHALL support enabling/disabling without code changes
7. WHEN caching is configured THEN it SHALL support enabling/disabling without code changes

### Requirement 3: Frontend Configuration System

**User Story:** As a frontend developer, I want a complete frontend configuration system with environment validation, so that the frontend can be configured independently and catch configuration errors at build time.

#### Acceptance Criteria

1. WHEN the frontend is configured THEN there SHALL be a `frontend/.env` file for development, `frontend/.env.production` for production, and `frontend/.env.test` for testing
2. WHEN frontend configuration is defined THEN it SHALL include settings for:
   - Supabase (URL, anon key)
   - Database (PostgreSQL connection URL)
   - Stripe (publishable key, secret key, webhook secret, price IDs)
   - Resend (API key, contact email, from email)
   - Application (public URL, environment)
3. WHEN the frontend `.env.example` or `.env.example.production` files are provided THEN they SHALL be comprehensively documented with detailed comments
4. WHEN sensitive information is in `.env.test` THEN it SHALL be ignored by git, otherwise it MAY be committed
5. WHEN the frontend starts THEN it SHALL validate all environment variables using Zod schema
6. IF required environment variables are missing THEN the frontend SHALL fail with a clear error message listing the missing variables
7. WHEN environment validation is implemented THEN it SHALL be type-safe and provide autocomplete for environment variables

### Requirement 4: Azure Static Web App Configuration

**User Story:** As a DevOps engineer, I want proper Azure Static Web App configuration for the frontend, so that the frontend can be deployed to Azure with proper routing and build settings.

#### Acceptance Criteria

1. WHEN the frontend is deployed to Azure Static Web Apps THEN there SHALL be a `staticwebapp.config.json` file in the frontend directory
2. WHEN the configuration is defined THEN it SHALL include:
   - Route definitions for API proxying to backend
   - Fallback routes for client-side routing
   - Response overrides for custom error pages
   - Security headers
   - MIME type mappings
3. WHEN API routes are configured THEN they SHALL proxy requests to the backend API
4. WHEN client-side routing is used THEN all routes SHALL fallback to index.html

### Requirement 5: Unified Startup Scripts

**User Story:** As a developer, I want unified startup scripts that can launch both backend and frontend together, so that I can start the entire application with a single command.

#### Acceptance Criteria

1. WHEN a startup script is executed THEN it SHALL start both backend and frontend services
2. WHEN the script runs THEN it SHALL check for required dependencies (Python, Node.js, Redis, PostgreSQL)
3. IF dependencies are missing THEN the script SHALL provide clear error messages with installation instructions
4. WHEN services start THEN the script SHALL display startup logs and service URLs
5. WHEN the script is interrupted THEN it SHALL gracefully shut down all services
6. WHEN the script is provided THEN there SHALL be versions for both Windows (PowerShell) and Unix (Bash)

### Requirement 6: Database Schema Alignment

**User Story:** As a full-stack developer, I want the database schema to be aligned between frontend (Drizzle) and backend (SQLAlchemy), so that both systems work with the same data structure without conflicts.

#### Acceptance Criteria

1. WHEN the database schema is defined THEN the frontend Drizzle schema SHALL be the single source of truth
2. WHEN backend models are created THEN they SHALL be synchronized with the frontend Drizzle schema
3. WHEN the production schema SQL is provided THEN it SHALL match the Drizzle schema exactly
4. WHEN schema changes are made THEN there SHALL be a documented process for keeping frontend and backend in sync
5. WHEN the database is initialized THEN the production schema SQL SHALL create all tables, indexes, RLS policies, and triggers

### Requirement 7: Complete API Implementation

**User Story:** As a frontend developer, I want all necessary backend API endpoints to be implemented, so that the frontend can connect to the backend without missing functionality.

#### Acceptance Criteria

1. WHEN the backend API is reviewed THEN all endpoints required by the frontend SHALL be implemented
2. WHEN API endpoints are defined THEN they SHALL include:
   - Authentication (login, signup, logout, profile, token refresh)
   - Projects (CRUD operations)
   - Crawl jobs (CRUD operations, start, stop, status, progress)
   - Images (list, get, delete, download)
   - Notifications (list, mark as read, preferences)
   - Credits (balance, transactions, usage metrics)
   - API keys (CRUD operations)
   - Activity logs (list)
3. WHEN endpoints are implemented THEN they SHALL follow RESTful conventions
4. WHEN endpoints are implemented THEN they SHALL include proper error handling and validation
5. WHEN endpoints are implemented THEN they SHALL be documented in OpenAPI/Swagger

### Requirement 8: Architecture Compliance

**User Story:** As a system architect, I want the application to comply with all documented architecture decisions, so that the system is built according to established patterns and principles.

#### Acceptance Criteria

1. WHEN Supabase authentication is used THEN the backend SHALL use the service role key and the frontend SHALL use the anon key with RLS
2. WHEN custom JWT implementation is considered THEN it SHALL be rejected in favor of Supabase Auth tokens
3. WHEN retry logic is implemented THEN it SHALL follow the retry architecture (single retry layer per failure type)
4. WHEN Celery tasks are defined THEN they SHALL NOT use autoretry and SHALL explicitly handle infrastructure failures
5. WHEN network operations are performed THEN they SHALL use Tenacity for operation-level retries
6. WHEN permanent errors occur THEN they SHALL fail fast without retries
7. WHEN logging is implemented THEN it SHALL use the centralized Loguru-based logging system from the utility package
8. WHEN the database is accessed THEN the frontend SHALL use Drizzle ORM and the backend SHALL use SQLAlchemy, both connecting to the same Supabase PostgreSQL instance

### Requirement 9: Production-Grade Components

**User Story:** As a quality assurance engineer, I want all components to be production-grade with proper error handling, logging, monitoring, and security, so that the application is reliable and maintainable in production.

#### Acceptance Criteria

1. WHEN errors occur THEN they SHALL be logged with appropriate context and severity levels
2. WHEN the application runs THEN it SHALL provide health check endpoints for monitoring
3. WHEN sensitive data is handled THEN it SHALL be properly secured (encrypted, not logged)
4. WHEN API keys are stored THEN they SHALL be hashed with only prefixes stored in plain text
5. WHEN rate limiting is enabled THEN it SHALL protect against abuse
6. WHEN CORS is configured THEN it SHALL only allow specified origins
7. WHEN the application starts THEN it SHALL validate all configuration before accepting requests
8. WHEN database connections are made THEN they SHALL use connection pooling with appropriate limits
9. WHEN Redis is used THEN it SHALL have proper timeout and retry configuration
10. WHEN file uploads are handled THEN they SHALL have size limits and type validation

### Requirement 10: Comprehensive Documentation

**User Story:** As a new developer joining the project, I want comprehensive documentation for all configuration options, so that I can understand and configure the application without extensive guidance.

#### Acceptance Criteria

1. WHEN `.env.example` or `.env.*.example` or `.env.example.*` files are provided THEN they SHALL include detailed comments for every variable
2. WHEN configuration sections are defined THEN they SHALL be clearly separated with headers
3. WHEN variables have specific formats THEN examples SHALL be provided
4. WHEN variables are optional THEN this SHALL be clearly indicated
5. WHEN variables have dependencies THEN these SHALL be documented
6. WHEN variables have default values THEN these SHALL be documented
7. WHEN configuration is environment-specific THEN differences between development and production SHALL be documented
8. WHEN startup scripts are provided THEN they SHALL include usage instructions and examples
