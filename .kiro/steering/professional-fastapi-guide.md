## Project Structure

### Core Directory Organization

**Events Pattern**: Store events in `core/events/` directory. These events represent database events but can be reused as FastAPI events in endpoints or lifespan handlers.

**SQL Management**:

- Use PyPika for dynamic SQL code execution
- For static queries, store simple SQL files in `database/queries/` or `database/sql/`

**Settings**: Create a dedicated `core/settings/` folder with Pydantic Settings classes for different configuration domains.

## Error Handling

### Exception Types

Maintain two distinct exception categories:

- HTTP errors (for API responses)
- Normal exceptions (for internal logic)

### Resource Messages

Create a `resources.py` file for centralized error messages:

```python
USER_DOES_NOT_EXIST_ERROR = "user does not exist"
ARTICLE_DOES_NOT_EXIST_ERROR = "article does not exist"
ARTICLE_ALREADY_EXISTS = "article already exists"
USER_IS_NOT_AUTHOR_OF_ARTICLE = "you are not an author of this article"

```

### Exception Hierarchy

Implement layered exceptions for different concerns:

```python
__all__ = [
    "AppException",
    "DatabaseException",
    "AuthenticationException",
    "UnauthorizedException",
    "AuthorizationException",
    "ValidationException",
    "NotFoundException",
    "ConflictException",
    "RateLimitException",
    "InvalidConfigurationException",
    "InvalidFormulaException",
    "InvalidHierarchyException",
    "FeatureDisabledException",
    "setup_exception_handlers",
]

```

## Type Safety

### Custom Types

Use a dedicated `types.py` file for consistency. When migrating existing code, ensure all instances are updated together.

**Best Practices**:

- Use Pydantic types like `PositiveInt` instead of plain `int`
- Use `Annotated` for enhanced documentation
- Use `SecretStr` for sensitive data like passwords
- Ensure comprehensive typing throughout the codebase

## Utility Functions

### Feature Flag Management

```python
def check_feature_flag(flag_name: str) -> None:
    """Check if a feature flag is enabled, raise exception if not.

    This function validates that a specific experimental feature is enabled
    in the application settings. If the feature is disabled, it raises a
    FeatureDisabledException.

    Args:
        flag_name: Name of the feature flag to check (e.g., 'experimental_customers_page')

    Raises:
        FeatureDisabledException: If feature is disabled

    Example:
        >>> check_feature_flag('experimental_customers_page')
        # Raises FeatureDisabledException if customers page is disabled

    Note:
        This function is typically called at the beginning of admin endpoints
        to ensure the feature is available before processing the request.
    """

```

**Feature Flag Conventions**:

- Use `EXPERIMENTAL_` prefix for naming
- Implement helper functions for consistent handling
- Essential for gradual feature rollouts

### Redirect Response Builder

```python
def build_redirect_response(
    url: str,
    message: str | None = None,
    message_type: str = "success",
    status_code: int = status.HTTP_303_SEE_OTHER,
) -> RedirectResponse:
    """Build redirect response with optional message.

    Creates a redirect response with an optional message that can be displayed
    to the user. The message is added as a query parameter with the specified
    message type (success, error, warning, info).

    Args:
        url: Target URL for the redirect
        message: Optional message to display to the user
        message_type: Type of message (success, error, warning, info). Defaults to 'success'
        status_code: HTTP status code for redirect. Defaults to 303 (See Other)

    Returns:
        RedirectResponse: FastAPI redirect response with message in query params

    Example:
        >>> build_redirect_response(
        ...     url="/admin/customers",
        ...     message="Customer created successfully",
        ...     message_type="success"
        ... )
        RedirectResponse(url="/admin/customers?success=Customer created successfully")

    Note:
        - Uses 303 See Other by default (POST-Redirect-GET pattern)
        - Message types should match template expectations
        - URL encoding is handled automatically by RedirectResponse
    """

```

### Validation Error Formatter

```python
def format_validation_errors(validation_error: ValidationError) -> list[str]:
    """Convert Pydantic validation errors to user-friendly messages.

    Takes a Pydantic ValidationError and converts it into a list of
    human-readable error messages suitable for display in templates.

    Args:
        validation_error: Pydantic ValidationError from schema validation

    Returns:
        list[str]: List of formatted error messages

    Example:
        >>> from pydantic import BaseModel, ValidationError
        >>> class User(BaseModel):
        ...     email: str
        ...     age: int
        >>> try:
        ...     User(email="invalid", age="not a number")
        ... except ValidationError as e:
        ...     errors = format_validation_errors(e)
    """

```

### Common API Responses

```python
def get_common_responses(*status_codes: int) -> dict[int, dict[str, Any]]:
    """Get common response schemas for specified status codes.

    This function is lightweight and doesn't need @lru_cache because:
    1. It only does dictionary lookups (O(1) operations)
    2. The response_map is a module-level constant
    3. The result is a small dict that's immediately used in decorator
    4. Caching would add overhead without meaningful performance gain

    Args:
        *status_codes: HTTP status codes to include

    Returns:
        dict[int, dict[str, Any]]: Dictionary mapping status codes to response schemas

    Example:
        ```python
        responses = get_common_responses(401, 404, 500)
        ```
    """
    return {code: _RESPONSE_MAP[code] for code in status_codes if code in _RESPONSE_MAP}

```

**Usage Example**:

```python
@router.get(
    "/",
    response_model=Page[QuoteSchema],
    summary="List Quotes",
    description="List user's quotes with pagination. Superusers can see all quotes.",
    response_description="Paginated list of quotes",
    operation_id="listQuotes",
    responses={
        200: {
            "description": "Successfully retrieved quotes",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "configuration_id": 123,
                                "customer_id": 42,
                                "quote_number": "Q-2024-001",
                                "subtotal": "525.00",
                                "tax_rate": "8.50",
                                "tax_amount": "44.63",
                                "discount_amount": "0.00",
                                "total_amount": "569.63",
                                "valid_until": "2024-02-15",
                                "status": "sent",
                                "created_at": "2024-01-01T00:00:00Z",
                                "updated_at": "2024-01-01T00:00:00Z",
                            }
                        ],
                        "total": 5,
                        "page": 1,
                        "size": 50,
                        "pages": 1,
                    }
                }
            },
        },
        **get_common_responses(401, 500),
    },
)

```

## Dependencies

### User Authentication

In `dependencies.py`, implement distinct functions:

- `get_user`: Basic user retrieval
- `get_current_user` or `get_active_user`: Active user retrieval

Group related dependencies together for better organization.

### Authorization Levels

Always consider these user types:

- **Required**: user, superuser
- **Optional**: admin, superadmin

## API Endpoints

### Essential Authentication Endpoints

```
/auth/me
/auth/login
/auth/logout
/auth/create

```

### Documentation Standards

- Document superuser requirements in code and OpenAPI documentation
- Use descriptive tags for enhanced readability
- Avoid using `...` (Ellipsis) in route functions as they're not JSON serializable

### Data Export Endpoints

Implement export functionality for data retrieval and reporting purposes.

## Configuration Files

### Dedicated Configuration

Create separate configuration files for:

- Caching
- Pagination
- Rate limiting (even when using third-party packages)

### core directory files

Maintain dedicated files:

- `middlewares.py`: Application middleware
- `security.py`: Security utilities
- `logging.py`: logging utilities
- `cache.py`: cache utilities
- `settings.py`: Security utilities
- …etc.

## Database Management

### Connection Handling

Implement two distinct functions:

- `get_db`: Database connection
- `get_session`: Session management for context handling

### Database-Specific Features

Ensure consistency across SQL engines. Example for PostgreSQL LTREE:

```python
# Custom SQL expressions for LTREE functions
class ltree_subpath(expression.FunctionElement):
    """Extract subpath from LTREE path.

    Example:
        ```python
        # Get subpath from position 1 to 3
        subpath = select(ltree_subpath(Node.ltree_path, 1, 3))
        ```
    """

    type = LTREE()
    name = "subpath"

```

### Helper Functions

Essential database utilities in the database directory:

```python
__all__ = [
    "execute_raw_query",
    "check_connection",
    "get_table_names",
]

```

### Database Environments

**Best Practice**: Separate databases for development, testing, and production.

**Budget-Friendly Alternative**: Use separate schemas for testing and development (not recommended for production).

## Caching

Keep cache implementation simple yet efficient:

```python
__all__ = ["init_cache", "close_cache", "cache_key_builder", "get_redis_client"]

```

Prefer simple functions over complex classes with multiple methods.

## Design Patterns

### Repository Pattern

Always follow the repository pattern correctly and consistently.

### Template Styling

- Ensure uniform template styling across the application
- Use tools like **Infima** for consistent design
- Create reusable base templates and components
- Use text markers like `[OK]` instead of icons

## Testing

### Directory Structure

```
tests/
├── e2e/              # End-to-end tests (if admin/dashboard exists)
├── factories/        # Test factories (essential for robust testing)
├── integration/      # Integration tests
└── unit/            # Unit tests
    ├── database/
    ├── models/
    ├── repos/
    └── ...

```

### Test Configuration

**Config File**: Create `tests/config.py` with all test configurations used by `conftest.py`.

```python
__all__ = ["TestSettings", "get_test_settings"]

```

Where `TestSettings` is a Pydantic Settings class reading from `.env.test`.

**Note**: If `.env.test` contains no secrets, you can commit it to git.

### Testing Best Practices

1. **Use Fixtures**: Avoid hardcoded values; use fixtures for consistency
2. **Smart Assertions**: Test if content X is in C, not if X equals C (unless necessary)
3. **Essential Tests**: Always include `test_connection` or `test_supabase` to verify connectivity
4. **Separate Databases**: Use different databases for development, testing, and production

## Environment Files

```
.env                      # Development
.env.test                 # Testing
.env.test.example         # CI/CD template
.env.production           # Production (or .env.prod)
.env.production.example   # CI/CD template

```

## Management CLI

Create `manage.py` at project root for common administrative tasks:

```
Commands:
    createsuperuser              Create a new superuser account
    promote <username>           Promote an existing user to superuser
    create_tables                Create all database tables with LTREE extension
    drop_tables                  Drop all database tables (requires confirmation)
    reset_db                     Drop and recreate all tables (requires confirmation)
    reset_password <username>    Reset password for a user
    check_env                    Validate environment configuration
    seed_data                    Create sample data for development
    clean_db                     Clean orphaned types and recreate database
    verify_setup                 Verify complete setup is working
    stamp_alembic                Stamp Alembic to current version
    check_db                     Check database connection and schema
    tables                       Display table information with pandas

```

## CI/CD Configuration

### Manual Trigger

Enable manual workflow dispatch:

```yaml
workflow_dispatch:  # Allow manual trigger

```

### FastAPI Server in CI/CD

Essential for Playwright or E2E tests:

```yaml
- name: Start FastAPI server in background
  run: |
    uv run uvicorn main:app --host 0.0.0.0 --port 8000 &
    echo $! > server.pid
    echo "Server started with PID $(cat server.pid)"
    # Wait for server to be ready
    for i in {1..30}; do
      if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Server is ready!"
        break
      fi
      echo "Waiting for server... ($i/30)"
      sleep 1
    done
  env:
    # environment variables

```

### Database Services

When using services like Supabase that don't work in CI/CD, use native clients:

```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: windx_test
    ports:
      - 5432:5432
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5

steps:
  - name: Install PostgreSQL client
    run: |
      sudo apt-get update
      sudo apt-get install -y postgresql-client

```

## FastAPI Application Setup

### Application Configuration

Use comprehensive FastAPI initialization:

```python
app = FastAPI(
    title="Your API Title",
    summary="Brief API summary",
    description="Detailed API description",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,  # Disable default docs if needed
    redoc_url="/redoc",
    contact={
        "name": "Your Name",
        "email": "your.email@example.com",
    },
    license_info={
        "name": "License Name",
        "url": "https://license-url.com",
    },
    openapi_tags=[
        # Define your tags here
    ],
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayOperationId": False,
        "displayRequestDuration": True,
        "filter": True,
        "tryItOutEnabled": True,
        "syntaxHighlight.theme": "monokai",
    },
)

```

### Health Endpoints

Implement two types of health checks:

1. **Simple Health Check**: Basic "hello world" endpoint
2. **Detailed Health Check**: Comprehensive check covering all services (Redis, database, cache, etc.)

### Application Lifespan

```python
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    Initializes database, cache, and rate limiter on startup.

    Args:
        application (FastAPI): FastAPI application instance

    Yields:
        None: Control back to FastAPI
    """
    # Startup
    print("[*] Starting application...")

    # Validate environment configuration
    try:
        validate_env_config()
    except Exception as e:
        print(f"[-] Configuration error: {e}")
        raise

    await init_services()  # db, cache, limiter

    # Check if database is set up
    try:
        check_db_setup()
    except Exception as e:
        print(f"[!] Could not check database status: {e}")

    print("[+] Application started successfully")

    yield

    # Shutdown
    print("[*] Shutting down application...")
    await close_services()  # db, cache, limiter
    print("[+] Application shutdown complete")

```

### Middleware Configuration

Create a single source of truth for all middleware setup:

```python
def setup_middleware(app: FastAPI, settings: Settings | None = None) -> None:
    """Configure all middleware for the application.

    Middleware is applied in reverse order (last added = first executed).
    Order matters for security and functionality.

    Args:
        app (FastAPI): FastAPI application instance
        settings (Settings | None): Application settings

    Note:
        Execution order (first to last):
        1. RequestSizeLimitMiddleware - Check request size first
        2. TimeoutMiddleware - Prevent hanging requests
        3. TrustedHostMiddleware - Validate host headers (prod)
        4. HTTPSRedirectMiddleware - Redirect to HTTPS (prod)
        5. CORSMiddleware - Handle CORS preflight
        6. SecurityHeadersMiddleware - Add security headers
        7. GZipMiddleware - Compress responses
        8. RequestIDMiddleware - Add request tracking
        9. LoggingMiddleware - Log everything
    """

```

## Security Best Practices

### Token Handling

**Avoid this mistake** - unclear return values:

```python
def decode_access_token(token: str) -> str | None:
    """Decode and verify JWT access token.

    Args:
        token (str): JWT token to decode

    Returns:
        str | None: Token subject if valid, None otherwise
    """
    settings = get_settings()

    # Handle SecretStr for secret_key
    secret_key = (
        settings.security.secret_key.get_secret_value()
        if hasattr(settings.security.secret_key, "get_secret_value")
        else settings.security.secret_key
    )

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[settings.security.algorithm],
        )
        return payload.get("sub")
    except JWTError:
        return None

```

**Issue**: Either return the entire payload or clearly document that you're returning only the `sub` field.

### BCrypt Version Compatibility

Be aware of breaking changes between BCrypt v4 and v5. Test thoroughly when upgrading.

## Advanced Testing

### Test Configuration Files

**Good conftest.py structure**:

```python
__all__ = [
    # Utility Functions
    "check_redis_available",
    "get_test_database_url",
    # Fixtures - Session Scope
    "event_loop",
    "test_settings",
    "setup_test_settings",
    # Fixtures - Function Scope
    "redis_test_settings",
    "test_engine",
    "test_session_maker",
    "db_session",
    "client",
    # Test Data Fixtures
    "test_user_data",
    "test_admin_data",
    "test_superuser_data",
    "test_passwords",
    # User Fixtures
    "test_user",
    "test_superuser",
    # Auth Fixtures
    "auth_headers",
    "superuser_auth_headers",
]

```

**E2E conftest.py structure**:

```python
__all__ = [
    # Configuration Fixtures
    "base_url",
    # Browser Fixtures
    "browser",
    "context",
    "page",
    # User Fixtures
    "admin_user",
    # Authenticated Fixtures
    "authenticated_page",
    "hierarchy_pages",
    # Cleanup Fixtures
    "cleanup_e2e_data",
]

```

### Testing External Services

For services like Redis in CI/CD, use one of these approaches:

1. **Dedicated environment file**: Use `.env.redis` for Redis-specific configuration
2. **Fixtures**: Enable services conditionally in test fixtures

### Playwright with Pytest

**Known Issue**: Pytest session scope and Playwright both try to bootstrap simultaneously, causing infinite waiting.

**Solution 1 - Function Scope**:

```python
@pytest_asyncio.fixture(scope="function")
async def browser() -> AsyncGenerator[Browser, None]:
    """Create Playwright browser instance.

    Yields:
        Browser: Chromium browser instance
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # Set to False for debugging
            args=["--disable-dev-shm-usage"],  # Prevent crashes in CI
        )
        yield browser
        await browser.close()

```

**Solution 2 - Session Scope** (Recommended):

```python
# Prevents "The test is hanging during collection" issue
@pytest_asyncio.fixture(scope="session")
async def browser() -> AsyncGenerator[Browser, None]:
    """Create session-scoped Playwright browser.

    Manually starts Playwright after pytest collection phase.
    """
    # 1. Start playwright (engine)
    p = await async_playwright().start()

    # 2. Launch browser after engine is ready
    browser = await p.chromium.launch(
        headless=True,
        args=["--disable-dev-shm-usage"],
    )

    # 3. Give the browser to tests
    yield browser

    # 4. Cleanup when all tests finish
    await browser.close()
    await p.stop()

```

## Admin Pages

### Template Context

If you have admin pages, implement a common context builder:

```python
def get_admin_context() -> dict:
    """Build common template context for admin pages.

    Returns:
        dict: Common context data for admin templates
    """
    # Implementation here

```

## Content Delivery Network (CDN)

### CDN Selection for CSP

- ✅ **Use**: `https://cdn.jsdelivr.net`
- ❌ **Avoid**: `https://cdnjs.cloudflare.com`

Use jsDelivr for Content Security Policy (CSP) compliance.

## Core Principles

1. **Simplicity**: Be simple in creating things yet efficient and professional
2. **Consistency**: Maintain consistency across the codebase
3. **Documentation**: Document code thoroughly and maintain clear API documentation
4. **Testing**: Ensure robust testing with factories and proper test structure
5. **Separation of Concerns**: Keep configuration, business logic, and presentation separate
6. **Security**: Follow security best practices for tokens, middleware, and external service

---

### **1. Use prefixes for configuration contexts**

It’s a good practice to group environment variables by prefix (e.g., `CACHE_`, `LIMITER_`) and keep all related configurations in the `.env` file.

Example:

```tsx
# Cache (Redis) – Disabled for local development
CACHE_ENABLED=False
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_PASSWORD=
CACHE_REDIS_DB=0
CACHE_PREFIX=devapi:cache
CACHE_DEFAULT_TTL=300

# Rate Limiter (Redis) – Disabled for local development
LIMITER_ENABLED=False
LIMITER_REDIS_HOST=localhost
LIMITER_REDIS_PORT=6379
LIMITER_REDIS_PASSWORD=
LIMITER_REDIS_DB=1
LIMITER_PREFIX=devapi:limiter
LIMITER_DEFAULT_TIMES=100
LIMITER_DEFAULT_SECONDS=60

```

---

### **2. Test CORS behavior against your defined configuration**

Make sure to test all CORS scenarios based on your planned configuration:

- Preflight requests (`OPTIONS`)
- Actual requests (`GET`, `POST`, etc.)
- Cookie handling (credentials)
- Allowed origins
- Allowed methods
- Allowed headers
- Exposed headers
    
    This ensures your backend behaves exactly as intended in real browser environments.
    

---

### **3. For full-stack apps, define a shared JSON schema for consistency**

If your project is fullstack, it’s a good practice to create a shared JSON schema file (it doesn’t have to follow OpenAPI or any standard).

This schema documents the **expected contract** between frontend and backend:

- Simple to update
- Simple to parse
- Easy for both teams to follow
- Helps align request/response structures across the entire codebase

---

Add API Versioning Strategy ⭐ (Medium Impact, Medium Effort)

**Why**: Professional APIs need clear versioning for backward compatibility
**Enhancement**: Add version deprecation headers

```python
class APISettings(BaseSettings):
    """API configuration."""
    
    v1_prefix: str = "/api/v1"
    current_version: str = "1.0.0"
    min_supported_version: str = "1.0.0"
    deprecated_versions: list[str] = []
    
    # API metadata
    title: str = "WindX Product Configurator API"
    description: str = "Automated product configuration and pricing"
    contact: dict = {
        "name": "WindX Support",
        "email": "support@windx.example.com",
    }
    license_info: dict = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
    
# app/middleware/versioning.py

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class APIVersionMiddleware(BaseHTTPMiddleware):
    """Add API version headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add version headers
        response.headers["X-API-Version"] = "1.0.0"
        response.headers["X-API-Min-Version"] = "1.0.0"
        
        # Warn about deprecated endpoints
        if request.url.path.startswith("/api/v0/"):
            response.headers["X-API-Deprecated"] = "true"
            response.headers["X-API-Sunset"] = "2025-12-31"
        
        return response
```

### 5. Add Request ID Tracking ⭐ (Medium Impact, Medium Effort)
**Why**: Essential for debugging, log correlation, and support

```python
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response

# app/core/logging.py

import logging
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

class RequestIDFilter(logging.Filter):
    """Add request ID to log records."""
    
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] [%(request_id)s] %(message)s",
    level=logging.INFO,
)
```

---

---

---

Optionally, to simplify things you can make two functions:

```python
from typing import Optional
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def success_response(
    message: str, status_code: int = status.HTTP_200_OK, data: Optional[dict] = None
):
    """
    :param message: description of the response
    :param status_code: HTTP status code
    :param data: optional dictionary data

    :description: Renders a JSON response for uniformity across all API endpoints.
    """
    content = {"message": message, "data": data}
    return JSONResponse(content=jsonable_encoder(content), status_code=status_code)

def failing_response(
    message: str, status_code: int = status.HTTP_200_OK, data: Optional[dict] = None
):
    """
    :param message: description of the response
    :param status_code: HTTP status code
    :param data: optional dictionary data

    :description: Renders a JSON response for uniformity across all API endpoints.
    """
    content = {"message": message, "data": data}
    return JSONResponse(content=jsonable_encoder(content), status_code=status_code)
```

By using `JsonResponse` and `jsonable_encoder`, you can simplify responses.

---

Other best practices and utilities:

- A good idea is to use the `Unidecode` library or a URL slugifying library like `python-slugify`, because URL inputs can be tricky.
- It's a good practice to have one or more helper functions to parse or handle URLs better.
- Sometimes you may want to customize logging from `uvicorn` or `gunicorn`, for which you can use an `InterceptHandler()` class.
- You may need RBAC/ABAC tools like `casl` to operate permissions.
- You may also need functions for peer-type:

```python
def require_peer_type(authenticator: JWTAuthenticator, claims: JWTClaims, required_type: PeerType):
    ...

```

- Remember to handle encryption correctly if working with multiple encryption and verification steps:

```python
from enum import Enum

class EncryptionKeyFormat(str, Enum):
    """
    Represents the supported formats for storing encryption keys.

    - PEM (https://en.wikipedia.org/wiki/Privacy-Enhanced_Mail)
    - SSH (RFC4716) or short format (RFC4253, section-6.6)
      explained here: https://coolaj86.com/articles/the-ssh-public-key-format/
    - DER (https://en.wikipedia.org/wiki/X.690#DER_encoding)
    """
    pem = 'pem'
    ssh = 'ssh'
    der = 'der'
    # etc.

```

- Good practice is to use `yarl` over the `urllib` library to handle URL parsing and other URL-related operations.

---

- Ensure your code is written in good way allow to test different parts inside it without leading to bugs during testing phase, for example you may have rate-limting wrapped apis, you should write your code in a way to:
    - able to test rate limiting alone
    - able to test rate limiting on api endpoint
    - able to test api endpoint with rate limiting hits [infinite limits]