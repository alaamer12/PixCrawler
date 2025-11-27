# PixCrawler Backend

Professional backend API service for the PixCrawler image dataset platform. Built with FastAPI, following clean
architecture principles and industry best practices.

## Architecture Overview

The backend follows a **three-layer architecture pattern** with clear separation of concerns:

```
backend/
├── api/v1/                 # API Layer - HTTP request/response handling
│   ├── endpoints/          # Individual endpoint modules
│   ├── dependencies.py     # Dependency injection factories
│   ├── types.py           # Type aliases for dependencies
│   └── router.py          # Main API router
├── services/              # Service Layer - Business logic orchestration
│   ├── auth.py           # Authentication service
│   ├── user.py           # User management service
│   ├── crawl_job.py      # Crawl job orchestration
│   └── dataset.py        # Dataset processing service
├── repositories/          # Repository Layer - Data access operations
│   ├── base.py           # Base repository with CRUD operations
│   ├── user_repository.py
│   ├── crawl_job_repository.py
│   └── ...               # Other repositories
├── schemas/               # Pydantic models for request/response
│   ├── user.py           # User-related schemas
│   ├── crawl_job.py      # Crawl job schemas
│   └── ...               # Other schemas
├── database/              # Database configuration and models
│   ├── connection.py     # Database connection setup
│   └── models.py         # SQLAlchemy models
├── core/                  # Core utilities and configuration
│   ├── config.py          # Application settings
│   ├── exceptions.py      # Custom exceptions
│   └── middleware.py      # Custom middleware
└── main.py               # Application entry point
```

### Layer Responsibilities

**API Layer (Endpoints)**
- HTTP request/response handling
- Input validation using Pydantic schemas
- Authentication and authorization
- OpenAPI documentation
- Response serialization

**Service Layer (Business Logic)**
- Business rules and validation
- Workflow orchestration
- Cross-repository coordination
- Error handling and custom exceptions
- Data transformation and aggregation

**Repository Layer (Data Access)**
- CRUD operations
- Query construction and execution
- Database transaction management
- No business logic

For detailed architecture documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md).

## Features

- **RESTful API**: Clean, versioned REST endpoints with comprehensive OpenAPI documentation
- **Clean Architecture**: Three-layer architecture (API, Service, Repository) with proper separation of concerns
- **Repository Pattern**: Consistent data access layer with BaseRepository
- **Dependency Injection**: FastAPI dependency system for loose coupling
- **Supabase Integration**: Seamless integration with Supabase Auth and PostgreSQL
- **Shared Database**: Direct connection to Supabase PostgreSQL with SQLAlchemy ORM
- **Real-time Updates**: Leverages Supabase real-time for job status updates
- **Background Jobs**: Async crawl job execution with Celery and progress tracking
- **Builder Integration**: Uses PixCrawler builder package for image crawling
- **Logging**: Centralized logging with structured output via Loguru
- **Validation**: Comprehensive request/response validation with Pydantic V2
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Security**: Supabase Auth integration with service role key management
- **Type Safety**: Full type hints with MyPy strict mode
- **Code Quality**: Ruff linting and formatting with 88 character line length

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- UV package manager

### Installation

1. Install dependencies:

```bash
uv sync
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:

```bash
# TODO: Add Alembic migration commands
```

4. Start the development server:

```bash
uv run pixcrawler-api
# or
uv run python -m backend.main
```

The API will be available at `http://localhost:8000` with interactive documentation at `/docs`.

## API Endpoints

All endpoints follow standardized patterns defined in the [Endpoint Style Guide](./api/v1/ENDPOINT_STYLE_GUIDE.md).

### Health Check

- `GET /api/v1/health/` - Service health status

### Authentication (Supabase Integration)

- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/verify-token` - Verify Supabase JWT token
- `POST /api/v1/auth/sync-profile` - Sync user profile from Supabase Auth

### Users

- `POST /api/v1/users/` - Create user account
- `GET /api/v1/users/` - List users (paginated)
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Projects

- `POST /api/v1/projects/` - Create project
- `GET /api/v1/projects/` - List user projects
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Crawl Jobs (Image Dataset Generation)

- `POST /api/v1/jobs/` - Create and start crawl job
- `GET /api/v1/jobs/` - List crawl jobs (paginated)
- `GET /api/v1/jobs/{id}` - Get crawl job status and progress
- `POST /api/v1/jobs/{id}/cancel` - Cancel running crawl job
- `POST /api/v1/jobs/{id}/retry` - Retry failed crawl job
- `GET /api/v1/jobs/{id}/logs` - Get crawl job logs
- `GET /api/v1/jobs/{id}/progress` - Get real-time progress

### Notifications

- `GET /api/v1/notifications/` - List user notifications
- `POST /api/v1/notifications/{id}/read` - Mark notification as read
- `POST /api/v1/notifications/read-all` - Mark all notifications as read

### Storage

- `GET /api/v1/storage/usage` - Get storage usage statistics
- `GET /api/v1/storage/presigned-url` - Generate presigned download URL

### Exports

- `POST /api/v1/exports/json` - Export dataset as JSON
- `POST /api/v1/exports/csv` - Export dataset as CSV
- `POST /api/v1/exports/zip` - Export dataset as ZIP archive

### Validation

- `POST /api/v1/validation/batch` - Create batch validation job
- `GET /api/v1/validation/{id}` - Get validation job status

### Legacy Datasets (Deprecated)

- `POST /api/v1/datasets/` - Create dataset generation job
- `GET /api/v1/datasets/` - List datasets (paginated)
- `GET /api/v1/datasets/stats` - Get dataset statistics

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Configuration

The application uses environment-based configuration with Pydantic Settings. Key configuration areas:

- **Application**: Environment, debug mode, host/port
- **Security**: JWT secrets, token expiration, CORS origins
- **Database**: PostgreSQL connection and pool settings
- **Redis**: Cache and session configuration
- **Celery**: Background job processing
- **External APIs**: Google, Bing API keys

See `.env.example` for all available configuration options.

## Development

### Code Quality

The project enforces high code quality standards:

- **Linting**: Ruff for fast Python linting and formatting (88 character line length)
- **Type Checking**: MyPy with strict configuration
- **Testing**: Pytest with async support, mocking, and architecture tests
- **Pre-commit**: Automated code quality checks
- **Architecture Tests**: Automated verification of layer separation

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend --cov-report=html

# Run specific test file
uv run pytest backend/tests/test_architecture.py

# Run architecture tests only
uv run pytest backend/tests/test_architecture.py -v
```

### Code Formatting

```bash
# Format code
uv run ruff format .

# Check for linting issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .
```

### Type Checking

```bash
# Run type checking
uv run mypy backend/

# Run with verbose output
uv run mypy backend/ --verbose
```

### Architecture Compliance

The backend enforces architectural patterns through automated tests:

```bash
# Verify services don't import AsyncSession directly
# Verify repositories extend BaseRepository
# Verify endpoints don't have database queries
# Verify dependency injection patterns
uv run pytest backend/tests/test_architecture.py
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation.

## Deployment

The backend is designed for containerized deployment with:

- **Docker**: Multi-stage builds for production optimization
- **Health Checks**: Built-in health endpoints for load balancers
- **Logging**: Structured JSON logging for centralized collection
- **Monitoring**: Request tracing and performance metrics

## Contributing

1. Follow the established architecture patterns (see [ARCHITECTURE.md](./ARCHITECTURE.md))
2. Follow the endpoint style guide (see [api/v1/ENDPOINT_STYLE_GUIDE.md](./api/v1/ENDPOINT_STYLE_GUIDE.md))
3. Add comprehensive type hints to all functions
4. Include docstrings for all public APIs (Google style)
5. Write tests for new functionality (unit, integration, architecture)
6. Update documentation as needed
7. Run linting, type checking, and tests before committing
8. Ensure test coverage meets minimum thresholds:
   - Endpoints: ≥ 90%
   - Services: ≥ 85%
   - Repositories: ≥ 80%

### Architecture Guidelines

**Services:**
- Depend on repositories only (no direct AsyncSession)
- Contain business logic and orchestration
- No database queries or HTTP concerns

**Repositories:**
- Extend BaseRepository
- Focus on data access only
- No business logic

**Endpoints:**
- Handle HTTP concerns only
- Use service layer via dependency injection
- No business logic or database queries
- Follow standardized patterns

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed guidelines and examples.

## Additional Documentation

- [Architecture Documentation](./ARCHITECTURE.md) - Detailed architecture patterns and guidelines
- [Endpoint Style Guide](./api/v1/ENDPOINT_STYLE_GUIDE.md) - API endpoint standards
- [Migration Guide](../docs/MIGRATION_GUIDE.md) - Guide for migrating to refactored architecture
- [Repository Pattern Audit](../docs/REPOSITORY_PATTERN_AUDIT.md) - Audit findings and remediation

## License

MIT License - see LICENSE file for details.
