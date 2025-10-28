# PixCrawler Backend

Professional backend API service for the PixCrawler image dataset platform. Built with FastAPI, following clean
architecture principles and industry best practices.

## Architecture Overview

The backend follows a layered architecture pattern with clear separation of concerns:

```
backend/
├── api/v1/                 # API Layer - FastAPI routers and endpoints
│   ├── endpoints/          # Individual endpoint modules
│   └── router.py          # Main API router
├── core/                  # Core utilities and configuration
│   ├── config.py          # Application settings
│   ├── exceptions.py      # Custom exceptions
│   └── middleware.py      # Custom middleware
├── models/                # Pydantic models for request/response
│   ├── base.py           # Base schemas and common models
│   ├── user.py           # User-related schemas
│   └── dataset.py        # Dataset-related schemas
├── services/              # Service Layer - Business logic
│   ├── auth.py           # Authentication service
│   ├── user.py           # User management service
│   └── dataset.py        # Dataset processing service
├── repositories/          # Repository Layer - Data access
│   └── base.py           # Base repository with CRUD operations
├── database/              # Database configuration and models
│   ├── connection.py     # Database connection setup
│   └── models.py         # SQLAlchemy models
└── main.py               # Application entry point
```

## Features

- **RESTful API**: Clean, versioned REST endpoints with OpenAPI documentation
- **Supabase Integration**: Seamless integration with Supabase Auth and PostgreSQL
- **Shared Database**: Direct connection to Supabase PostgreSQL with SQLAlchemy ORM
- **Real-time Updates**: Leverages Supabase real-time for job status updates
- **Background Jobs**: Async crawl job execution with progress tracking
- **Builder Integration**: Uses PixCrawler builder package for image crawling
- **Logging**: Centralized logging with structured output
- **Validation**: Comprehensive request/response validation with Pydantic
- **Error Handling**: Structured error responses with proper HTTP status codes
- **Security**: Supabase Auth integration with service role key management

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

### Crawl Jobs (Image Dataset Generation)

- `POST /api/v1/jobs/` - Create and start crawl job
- `GET /api/v1/jobs/{id}` - Get crawl job status and progress
- `POST /api/v1/jobs/{id}/cancel` - Cancel running crawl job

### Legacy Datasets (Deprecated)

- `POST /api/v1/datasets/` - Create dataset generation job
- `GET /api/v1/datasets/` - List datasets (paginated)
- `GET /api/v1/datasets/stats` - Get dataset statistics

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

- **Linting**: Ruff for fast Python linting and formatting
- **Type Checking**: MyPy with strict configuration
- **Testing**: Pytest with async support and mocking
- **Pre-commit**: Automated code quality checks

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run ruff format .
uv run ruff check .
```

### Type Checking

```bash
uv run mypy .
```

## Deployment

The backend is designed for containerized deployment with:

- **Docker**: Multi-stage builds for production optimization
- **Health Checks**: Built-in health endpoints for load balancers
- **Logging**: Structured JSON logging for centralized collection
- **Monitoring**: Request tracing and performance metrics

## Contributing

1. Follow the established architecture patterns
2. Add comprehensive type hints to all functions
3. Include docstrings for all public APIs
4. Write tests for new functionality
5. Update documentation as needed

## License

MIT License - see LICENSE file for details.
