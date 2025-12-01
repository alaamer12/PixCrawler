# 🐳 PixCrawler Docker Guide

This guide explains how to run PixCrawler using Docker and Docker Compose.
   
## 📋 Prerequisites

- **Docker** 20.10+ 
- **Docker Compose** v2.0+
- **Windows/Linux/macOS** with Docker Desktop or Docker Engine

## 🚀 Quick Start
 
### Option 1: Standalone Mode (No Redis)
    
For development without Celery/Redis dependencies:

```bash
# Build and start
docker compose build
docker compose up

# Access the API
# http://localhost:8000/docs
```

This runs only the backend service without Redis, Celery workers, or Flower monitoring.

### Option 2: Full Stack with Redis

For full functionality with async task processing:

```bash
# Build and start all services
docker compose --profile with-redis up --build

# Services running:
# - Redis (port 6379)
# - Backend API (port 8000)
# - Celery Worker
```

### Option 3: Full Stack with Monitoring

For production-like environment with Flower monitoring:

```bash
# Build and start all services including monitoring
docker compose --profile with-redis --profile monitoring up --build

# Services running:
# - Redis (port 6379)
# - Backend API (port 8000)
# - Celery Worker
# - Flower Monitoring (port 5555)

# Access Flower monitoring dashboard
# http://localhost:5555
```

## 🏗️ Architecture

### Service Overview

| Service | Port | Profile | Description |
|---------|------|---------|-------------|
| **backend-standalone** | 8000 | default | FastAPI backend without Redis |
| **backend** | 8000 | with-redis | FastAPI backend with Redis |
| **redis** | 6379 | with-redis | Redis cache & message broker |
| **worker** | - | with-redis | Celery worker for async tasks |
| **flower** | 5555 | monitoring | Celery monitoring dashboard |

### Network & Volumes

```yaml
Network: pixcrawler-network (bridge)

Volumes:
├── redis_data         # Redis persistence
├── backend_storage    # Backend file storage
├── backend_logs       # Backend application logs
├── worker_storage     # Worker file storage
└── worker_logs        # Worker application logs
```

## 📝 Common Commands

### Build

```bash
# Build all services
docker compose build

# Build specific service
docker compose build backend-standalone

# Build without cache (clean build)
docker compose build --no-cache
```

### Start/Stop

```bash
# Start in foreground
docker compose up

# Start in background (detached)
docker compose up -d

# Start with specific profile
docker compose --profile with-redis up -d

# Stop all services
docker compose down

# Stop and remove volumes (⚠️ deletes data)
docker compose down -v
```

### Logs

```bash
# View all logs
docker compose logs

# Follow logs in real-time
docker compose logs -f

# View specific service logs
docker compose logs backend-standalone
docker compose logs redis
docker compose logs worker

# View last 100 lines
docker compose logs --tail=100 backend-standalone
```

### Service Management

```bash
# Restart a specific service
docker compose restart backend-standalone

# Stop a specific service
docker compose stop worker

# Start a specific service
docker compose start worker

# View running services
docker compose ps

# View service status
docker compose ps -a
```

### Exec into Containers

```bash
# Open shell in backend container
docker compose exec backend-standalone bash

# Run Python REPL
docker compose exec backend-standalone python

# Run CLI commands
docker compose exec backend-standalone uvicorn --help
```

### Health Checks

```bash
# Check backend health
curl http://localhost:8000/health

# Check Flower (if monitoring enabled)
curl http://localhost:5555/

# View Docker health status
docker compose ps
```

### Scaling Workers (Production)

```bash
# Run 4 worker instances
docker compose --profile with-redis up --scale worker=4 -d
```

## 🔧 Configuration

### Environment Variables

Key environment variables can be configured in `docker-compose.yml` or via `.env` file:

```bash
# Application
ENVIRONMENT=development
DEBUG=true
PYTHONPATH=/app

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Database
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Storage
STORAGE_PROVIDER=local
STORAGE_LOCAL_STORAGE_PATH=/app/storage

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Custom Configuration

Create a `.env` file in the project root:

```bash
# .env
ENVIRONMENT=production
DEBUG=false
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/pixcrawler
```

Then run:

```bash
docker compose --profile with-redis up
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Error: Bind for 0.0.0.0:8000 failed: port is already allocated

# Solution: Change port mapping in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 on host instead
```

### Redis Connection Issues

```bash
# Check Redis is running
docker compose ps redis

# View Redis logs
docker compose logs redis

# Test Redis connection
docker compose exec redis redis-cli ping
# Should return: PONG
```

### Worker Not Starting

```bash
# View worker logs
docker compose logs worker

# Restart worker
docker compose restart worker

# Check Redis connection from worker
docker compose exec worker celery -A celery_core.app inspect ping
```

### Build Failures

```bash
# Clean build (remove cache)
docker compose build --no-cache

# Remove old images
docker image prune -a

# Check disk space
docker system df
```

### Volume Permission Issues

```bash
# Reset volumes (⚠️ deletes data)
docker compose down -v
docker compose up --build
```

## 📊 Monitoring

### Container Stats

```bash
# Real-time resource usage
docker stats

# Specific container
docker stats pixcrawler-backend-standalone
```

### Flower Dashboard

When running with `--profile monitoring`:

1. Open browser: `http://localhost:5555`
2. View active tasks, workers, and task history
3. Monitor task success/failure rates
4. Inspect task details and arguments

### Health Endpoints

```bash
# Backend health
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"PixCrawler API"}

# API documentation
curl http://localhost:8000/docs
# Opens Swagger UI

# OpenAPI schema
curl http://localhost:8000/openapi.json
```

## 🏭 Production Deployment

### Production Best Practices

```bash
# Use production-ready settings
docker compose --profile with-redis up -d \
  --scale worker=4 \
  --build

# Enable resource limits (add to docker-compose.yml)
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '1'
      memory: 1G
```

### Security Recommendations

1. **Do not use** `-v .:/app` in production (remove code mounts)
2. **Use secrets** for sensitive environment variables
3. **Enable TLS/SSL** for Redis and database connections
4. **Use PostgreSQL** instead of SQLite
5. **Implement proper logging** and monitoring

### PostgreSQL Example

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: pixcrawler
      POSTGRES_USER: pixcrawler
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - pixcrawler-network

  backend:
    # ... other config ...
    environment:
      DATABASE_URL: postgresql+asyncpg://pixcrawler:${DB_PASSWORD}@postgres:5432/pixcrawler
    depends_on:
      - postgres
```

## 🧪 Development Workflow

### Hot Reload Development

The default compose setup supports hot-reload:

```bash
# Start with hot-reload enabled
docker compose up

# Edit files in ./backend, ./builder, etc.
# Changes are automatically detected and server reloads
```

### Running Tests

```bash
# Run tests inside container
docker compose exec backend-standalone pytest

# Run with coverage
docker compose exec backend-standalone pytest --cov=backend

# Run specific test file
docker compose exec backend-standalone pytest tests/test_api.py
```

### Database Migrations

```bash
# Generate migration
docker compose exec backend-standalone alembic revision --autogenerate -m "Add new table"

# Apply migrations
docker compose exec backend-standalone alembic upgrade head

# Rollback migration
docker compose exec backend-standalone alembic downgrade -1
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Profiles](https://docs.docker.com/compose/profiles/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Flower Documentation](https://flower.readthedocs.io/)

## 💡 Tips & Tricks

### View Docker Compose Configuration

```bash
# See final configuration (with profiles)
docker compose --profile with-redis config
```

### Clean Up Everything

```bash
# Stop and remove containers, networks, volumes
docker compose down -v

# Remove all unused Docker resources
docker system prune -a --volumes
```

### Export/Import Volumes

```bash
# Backup volume
docker run --rm -v pixcrawler-backend-storage:/data -v $(pwd):/backup \
  alpine tar czf /backup/backend-storage-backup.tar.gz -C /data .

# Restore volume
docker run --rm -v pixcrawler-backend-storage:/data -v $(pwd):/backup \
  alpine tar xzf /backup/backend-storage-backup.tar.gz -C /data
```

## ❓ FAQ

**Q: Can I run without Docker?**
A: Yes! See the main README for local development setup using `uv`.

**Q: How do I update to the latest image?**
A: Run `docker compose build --pull --no-cache`

**Q: Where are logs stored?**
A: Logs are in named volumes `backend_logs` and `worker_logs`. Access via `docker compose exec backend-standalone ls -la /app/logs`

**Q: Can I use this for production?**
A: The Dockerfile is production-ready, but review security settings, use PostgreSQL, enable TLS, and configure proper secrets management.

---

**Need help?** Open an issue on GitHub or check the main project documentation.
