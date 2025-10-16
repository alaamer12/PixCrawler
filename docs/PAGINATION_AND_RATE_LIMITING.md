# Pagination and Rate Limiting Guide

This document explains how to use the pagination and rate limiting features in the PixCrawler backend API.

## 📚 Pagination with fastapi-pagination

### Overview
The backend uses `fastapi-pagination` for automatic pagination support with SQLAlchemy async queries.

### Installation
```bash
uv add fastapi-pagination
```

### Configuration
Pagination is automatically configured in `backend/main.py`:
```python
from fastapi_pagination import add_pagination

app = FastAPI(...)
add_pagination(app)  # Enables pagination
```

### Usage in Endpoints

#### Basic Example
```python
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/datasets/", response_model=Page[DatasetResponse])
async def list_datasets(
    session: AsyncSession = Depends(get_session),
) -> Page[DatasetResponse]:
    """List datasets with automatic pagination."""
    # Pagination happens automatically
    return await paginate(session, select(Dataset))
```

#### Query Parameters
Pagination adds these query parameters automatically:
- `page` (default: 1) - Page number
- `size` (default: 50) - Items per page

Example requests:
```bash
# First page, 50 items
GET /api/v1/datasets/?page=1&size=50

# Second page, 20 items
GET /api/v1/datasets/?page=2&size=20
```

#### Response Format
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 50,
  "pages": 3
}
```

### OpenAPI Documentation
Pagination parameters are automatically added to OpenAPI docs at `/docs`.

---

## 🚦 Rate Limiting with fastapi-limiter

### Overview
The backend uses `fastapi-limiter` with Redis to prevent API abuse and enforce usage quotas.

### Installation
```bash
uv add fastapi-limiter
```

### Configuration

#### 1. Initialize in `backend/main.py`
```python
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to Redis
    redis_connection = await redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    # Initialize rate limiter
    await FastAPILimiter.init(redis_connection)
    
    yield
    
    # Cleanup
    await FastAPILimiter.close()
    await redis_connection.close()

app = FastAPI(lifespan=lifespan)
```

#### 2. Configure Limits in `.env`
```bash
# Rate limiting settings
RATE_LIMIT_ENABLED=true
RATE_LIMIT_CREATE_DATASET=10/60      # 10 requests per 60 seconds
RATE_LIMIT_CREATE_CRAWL_JOB=10/60
RATE_LIMIT_RETRY_JOB=5/60
RATE_LIMIT_BUILD_JOB=5/60
```

### Usage in Endpoints

#### Basic Rate Limiting
```python
from fastapi_limiter.depends import RateLimiter

@router.post(
    "/datasets/",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def create_dataset(...):
    """Create dataset - limited to 10 requests per minute."""
    pass
```

#### Different Limits for Different Endpoints
```python
# Strict limit for expensive operations
@router.post(
    "/datasets/{id}/build",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
)
async def start_build_job(...):
    """Start build - limited to 5 requests per minute."""
    pass

# More lenient for read operations
@router.get(
    "/datasets/",
    dependencies=[Depends(RateLimiter(times=100, seconds=60))]
)
async def list_datasets(...):
    """List datasets - limited to 100 requests per minute."""
    pass
```

### Current Rate Limits

| Endpoint | Limit | Purpose |
|----------|-------|---------|
| `POST /datasets/` | 10/min | Prevent dataset spam |
| `POST /datasets/{id}/build` | 5/min | Expensive build operations |
| `POST /jobs/` | 10/min | Prevent crawl job spam |
| `POST /jobs/{id}/retry` | 5/min | Prevent retry abuse |

### Rate Limit Response

When rate limit is exceeded, the API returns:
```json
{
  "error": {
    "type": "HTTPException",
    "message": "Too Many Requests",
    "status_code": 429
  }
}
```

With headers:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1234567890
```

### Custom Rate Limit Identifier

By default, rate limiting is per IP address. You can customize this:

```python
from fastapi import Request

async def user_identifier(request: Request) -> str:
    """Rate limit by user ID instead of IP."""
    user = request.state.user
    return f"user:{user['user_id']}"

# In main.py
await FastAPILimiter.init(
    redis_connection,
    identifier=user_identifier
)
```

### Disable Rate Limiting (Development)

Set in `.env`:
```bash
RATE_LIMIT_ENABLED=false
```

Or skip the dependency:
```python
# Remove this line to disable rate limiting
dependencies=[Depends(RateLimiter(times=10, seconds=60))]
```

---

## 🧪 Testing

### Test Pagination
```python
import httpx

async def test_pagination():
    async with httpx.AsyncClient() as client:
        # Get first page
        response = await client.get(
            "http://localhost:8000/api/v1/datasets/?page=1&size=10"
        )
        data = response.json()
        
        assert data["page"] == 1
        assert data["size"] == 10
        assert len(data["items"]) <= 10
```

### Test Rate Limiting
```python
async def test_rate_limit():
    async with httpx.AsyncClient() as client:
        # Make 11 requests (limit is 10/min)
        for i in range(11):
            response = await client.post(
                "http://localhost:8000/api/v1/datasets/",
                json={"name": f"test_{i}"}
            )
            
            if i < 10:
                assert response.status_code == 201
            else:
                assert response.status_code == 429  # Rate limited
```

---

## 📊 Monitoring

### Redis Keys
Rate limit data is stored in Redis with keys like:
```
fastapi-limiter:{identifier}:{endpoint}
```

Check current limits:
```bash
redis-cli
> KEYS fastapi-limiter:*
> TTL fastapi-limiter:127.0.0.1:/api/v1/datasets/
```

### Logs
Rate limit events are logged:
```
INFO: Rate limit check: user 127.0.0.1, endpoint /api/v1/datasets/, remaining: 9/10
WARNING: Rate limit exceeded: user 127.0.0.1, endpoint /api/v1/datasets/
```

---

## 🔧 Troubleshooting

### Pagination Not Working
1. Check `add_pagination(app)` is called in `main.py`
2. Verify return type is `Page[Model]`
3. Check SQLAlchemy query is async

### Rate Limiting Not Working
1. Verify Redis is running: `redis-cli ping`
2. Check Redis URL in `.env`: `REDIS_URL=redis://localhost:6379/0`
3. Verify `FastAPILimiter.init()` is called in lifespan
4. Check `RATE_LIMIT_ENABLED=true` in `.env`

### Rate Limits Too Strict
Adjust in `.env`:
```bash
RATE_LIMIT_CREATE_DATASET=20/60  # Increase to 20 per minute
```

Or modify endpoint decorator:
```python
dependencies=[Depends(RateLimiter(times=20, seconds=60))]
```

---

## 📝 Best Practices

### Pagination
1. ✅ Always use `Page[Model]` for list endpoints
2. ✅ Set reasonable default page size (50-100)
3. ✅ Add ordering to queries: `select(Model).order_by(Model.created_at)`
4. ✅ Use `fastapi_pagination.ext.sqlalchemy.paginate` for async queries
5. ❌ Don't load all data into memory before paginating

### Rate Limiting
1. ✅ Apply to all write operations (POST, PUT, DELETE)
2. ✅ Use stricter limits for expensive operations
3. ✅ Use lenient limits for read operations
4. ✅ Rate limit by user ID for authenticated endpoints
5. ✅ Log rate limit violations for monitoring
6. ❌ Don't rate limit health check endpoints
7. ❌ Don't apply same limit to all endpoints

---

## 🚀 Production Deployment

### Environment Variables
```bash
# .env.production
REDIS_URL=redis://production-redis:6379/0
RATE_LIMIT_ENABLED=true
RATE_LIMIT_CREATE_DATASET=10/60
RATE_LIMIT_CREATE_CRAWL_JOB=10/60
```

### Redis Configuration
- Use Redis Cluster for high availability
- Enable persistence (AOF or RDB)
- Set appropriate `maxmemory-policy`
- Monitor Redis memory usage

### Monitoring
- Track rate limit violations
- Monitor Redis connection health
- Alert on high rate limit hit rates
- Dashboard for rate limit metrics

---

## 📚 Additional Resources

- [fastapi-pagination docs](https://uriyyo-fastapi-pagination.netlify.app/)
- [fastapi-limiter GitHub](https://github.com/long2ice/fastapi-limiter)
- [Redis documentation](https://redis.io/docs/)
