# Backend Architecture Refactoring - Deployment Checklist

**Version:** 1.0  
**Date:** January 2025  
**Project:** PixCrawler Backend Architecture Refactoring

## Overview

This checklist ensures a smooth deployment of the backend architecture refactoring changes. Follow each section in order and check off items as completed.

---

## Pre-Deployment Checklist

### 1. Code Quality Verification

- [ ] All tests pass locally
  ```bash
  cd utility && uv run pytest
  cd backend && uv run pytest
  ```

- [ ] Architecture tests pass
  ```bash
  cd backend && uv run pytest tests/test_architecture.py -v
  ```

- [ ] Linting passes with no errors
  ```bash
  uv run ruff check .
  ```

- [ ] Type checking passes
  ```bash
  uv run mypy backend/
  ```

- [ ] Code formatted correctly
  ```bash
  uv run ruff format .
  ```

### 2. Test Coverage Verification

- [ ] Utility package coverage ≥ 85%
  ```bash
  cd utility && uv run pytest --cov=utility --cov-fail-under=85
  ```

- [ ] Backend endpoints coverage ≥ 90% (target)
- [ ] Backend services coverage ≥ 85% (target)
- [ ] Backend repositories coverage ≥ 80% (target)

### 3. Documentation Review

- [ ] README files updated
  - [ ] `utility/README.md`
  - [ ] `backend/README.md`

- [ ] Architecture documentation complete
  - [ ] `backend/ARCHITECTURE.md`
  - [ ] `backend/api/v1/ENDPOINT_STYLE_GUIDE.md`

- [ ] Migration guide reviewed
  - [ ] `docs/MIGRATION_GUIDE.md`

- [ ] API documentation verified
  - [ ] OpenAPI schema generates without errors
  - [ ] Swagger UI accessible at `/docs`
  - [ ] ReDoc accessible at `/redoc`

### 4. Backward Compatibility Verification

- [ ] Old utility configuration methods still work
- [ ] API endpoints maintain same contracts
- [ ] No breaking changes to public APIs
- [ ] Deprecation warnings added where appropriate

---

## Environment Configuration

### 1. Environment Variables to Update

#### Utility Package (New Format)

Add these environment variables with the `PIXCRAWLER_UTILITY_` prefix:

```ini
# Compression Settings
PIXCRAWLER_UTILITY_COMPRESSION__QUALITY=85
PIXCRAWLER_UTILITY_COMPRESSION__FORMAT=webp
PIXCRAWLER_UTILITY_COMPRESSION__LOSSLESS=false
PIXCRAWLER_UTILITY_COMPRESSION__WORKERS=0

# Archive Settings
PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__ENABLE=true
PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__TAR=true
PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__TYPE=zstd
PIXCRAWLER_UTILITY_COMPRESSION__ARCHIVE__LEVEL=10

# Logging Settings
PIXCRAWLER_UTILITY_LOGGING__ENVIRONMENT=production
PIXCRAWLER_UTILITY_LOGGING__LOG_DIR=./logs
PIXCRAWLER_UTILITY_LOGGING__CONSOLE_LEVEL=WARNING
PIXCRAWLER_UTILITY_LOGGING__FILE_LEVEL=INFO
PIXCRAWLER_UTILITY_LOGGING__USE_JSON=true
PIXCRAWLER_UTILITY_LOGGING__USE_COLORS=false
```

**Checklist:**
- [ ] Production environment variables updated
- [ ] Staging environment variables updated
- [ ] Development environment variables updated (optional)
- [ ] Old environment variables can be removed after verification

#### Backend Configuration (No Changes)

Existing backend environment variables remain unchanged:

```ini
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_ANON_KEY=eyJhbGc...

# Database
DATABASE_URL=postgresql+asyncpg://...

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

**Checklist:**
- [ ] All backend environment variables verified
- [ ] No changes needed to existing variables

### 2. Configuration Changes

**No database migrations required** - This refactoring is code-only.

**Checklist:**
- [ ] Confirm no database schema changes
- [ ] Confirm no new database tables
- [ ] Confirm no new database columns

---

## Deployment Steps

### Phase 1: Development Environment

#### 1.1 Deploy to Development

```bash
# Pull latest code
git pull origin main

# Install dependencies
uv sync

# Run tests
uv run pytest

# Start services
# Terminal 1: Backend
cd backend && uv run uvicorn backend.main:app --reload

# Terminal 2: Frontend
cd frontend && bun dev

# Terminal 3: Redis
redis-server

# Terminal 4: Celery
celery -A celery_core.app worker --loglevel=info
```

**Checklist:**
- [ ] Code deployed to development
- [ ] All services started successfully
- [ ] Health check passes: `GET /health`
- [ ] API documentation accessible: `/docs`
- [ ] No errors in logs

#### 1.2 Smoke Tests (Development)

- [ ] Health endpoint responds: `GET /health`
- [ ] Authentication works: `GET /api/v1/auth/me`
- [ ] Create project works: `POST /api/v1/projects/`
- [ ] Create crawl job works: `POST /api/v1/jobs/`
- [ ] List notifications works: `GET /api/v1/notifications/`
- [ ] OpenAPI schema generates: `GET /openapi.json`

#### 1.3 Monitor Development (24 hours)

- [ ] No errors in application logs
- [ ] No errors in Celery worker logs
- [ ] API response times normal
- [ ] No memory leaks
- [ ] No connection pool exhaustion

### Phase 2: Staging Environment

#### 2.1 Deploy to Staging

```bash
# Azure App Service deployment
az webapp deployment source config-zip \
  --resource-group pixcrawler-rg \
  --name pixcrawler-staging \
  --src backend.zip
```

**Checklist:**
- [ ] Code deployed to staging
- [ ] Environment variables updated
- [ ] Services restarted
- [ ] Health check passes
- [ ] Logs show no errors

#### 2.2 Smoke Tests (Staging)

- [ ] Health endpoint responds
- [ ] Authentication works with Supabase
- [ ] CRUD operations work for all resources
- [ ] Background jobs execute successfully
- [ ] Notifications delivered
- [ ] Storage operations work
- [ ] Export functionality works

#### 2.3 Integration Tests (Staging)

- [ ] Frontend integration works
- [ ] Celery workers process jobs
- [ ] Redis caching works
- [ ] Rate limiting works
- [ ] File uploads work
- [ ] File downloads work

#### 2.4 Performance Tests (Staging)

- [ ] API response times < 200ms (p95)
- [ ] Database query times < 100ms
- [ ] No memory leaks after 1 hour
- [ ] Connection pool stable
- [ ] CPU usage normal

#### 2.5 Monitor Staging (48 hours)

- [ ] No errors in application logs
- [ ] No errors in Azure Monitor
- [ ] API response times stable
- [ ] Database performance stable
- [ ] Redis performance stable
- [ ] Celery workers stable

### Phase 3: Production Environment

#### 3.1 Pre-Production Checklist

- [ ] All staging tests passed
- [ ] No critical issues in staging
- [ ] Team notified of deployment
- [ ] Deployment window scheduled
- [ ] Rollback plan prepared
- [ ] Monitoring alerts configured

#### 3.2 Deploy to Production

**Deployment Window:** [Schedule specific time]

```bash
# Azure App Service deployment
az webapp deployment source config-zip \
  --resource-group pixcrawler-rg \
  --name pixcrawler-prod \
  --src backend.zip

# Or use Azure DevOps pipeline
# Trigger production deployment pipeline
```

**Checklist:**
- [ ] Deployment started at scheduled time
- [ ] Code deployed successfully
- [ ] Environment variables verified
- [ ] Services restarted
- [ ] Health check passes immediately

#### 3.3 Post-Deployment Verification (Immediate)

**Within 5 minutes:**

- [ ] Health endpoint responds: `GET /health`
- [ ] API documentation accessible: `/docs`
- [ ] Authentication works
- [ ] No 500 errors in logs
- [ ] No database connection errors
- [ ] Redis connection working

**Within 15 minutes:**

- [ ] Create test project
- [ ] Create test crawl job
- [ ] Verify job starts processing
- [ ] Check notifications delivered
- [ ] Verify frontend integration

**Within 30 minutes:**

- [ ] Monitor error rates (should be < 1%)
- [ ] Monitor response times (should be normal)
- [ ] Check database performance
- [ ] Check Redis performance
- [ ] Check Celery worker status

#### 3.4 Monitor Production (First 24 Hours)

**Metrics to Monitor:**

- [ ] Error rate < 1%
- [ ] API response time p95 < 200ms
- [ ] Database query time < 100ms
- [ ] CPU usage < 70%
- [ ] Memory usage stable
- [ ] Connection pool healthy
- [ ] Celery queue length normal

**Alerts to Watch:**

- [ ] No 500 errors
- [ ] No database connection errors
- [ ] No Redis connection errors
- [ ] No Celery worker failures
- [ ] No memory leaks
- [ ] No connection pool exhaustion

#### 3.5 Extended Monitoring (First Week)

- [ ] Day 1: Hourly checks
- [ ] Day 2-3: Every 4 hours
- [ ] Day 4-7: Daily checks
- [ ] Week 2: Normal monitoring

---

## Rollback Procedures

### When to Rollback

Rollback immediately if:

- ❌ Error rate > 5%
- ❌ API response time p95 > 1 second
- ❌ Critical functionality broken
- ❌ Database connection failures
- ❌ Memory leaks detected
- ❌ Security vulnerabilities discovered

### Rollback Steps

#### 1. Immediate Rollback (Azure App Service)

```bash
# Rollback to previous deployment slot
az webapp deployment slot swap \
  --resource-group pixcrawler-rg \
  --name pixcrawler-prod \
  --slot staging \
  --target-slot production

# Or rollback to specific deployment
az webapp deployment source config-zip \
  --resource-group pixcrawler-rg \
  --name pixcrawler-prod \
  --src backend-previous.zip
```

**Checklist:**
- [ ] Rollback initiated
- [ ] Previous version deployed
- [ ] Services restarted
- [ ] Health check passes
- [ ] Verify functionality restored

#### 2. Verify Rollback

- [ ] Health endpoint responds
- [ ] Authentication works
- [ ] Critical functionality works
- [ ] Error rate normal
- [ ] Response times normal

#### 3. Post-Rollback Actions

- [ ] Notify team of rollback
- [ ] Document rollback reason
- [ ] Investigate root cause
- [ ] Fix issues in staging
- [ ] Plan re-deployment

---

## Monitoring and Alerting

### 1. Application Monitoring

**Azure Monitor / Application Insights:**

- [ ] Error rate alerts configured (> 1%)
- [ ] Response time alerts configured (p95 > 500ms)
- [ ] Availability alerts configured (< 99%)
- [ ] Custom metrics configured

**Metrics to Track:**

- Request rate (requests/minute)
- Error rate (%)
- Response time (p50, p95, p99)
- Database query time
- Redis operation time
- Celery queue length
- Memory usage
- CPU usage

### 2. Database Monitoring

**Supabase Dashboard:**

- [ ] Connection pool usage
- [ ] Query performance
- [ ] Slow query log
- [ ] Database size
- [ ] Active connections

### 3. Redis Monitoring

**Redis Metrics:**

- [ ] Memory usage
- [ ] Connected clients
- [ ] Commands per second
- [ ] Hit rate
- [ ] Evicted keys

### 4. Celery Monitoring

**Celery Metrics:**

- [ ] Active workers
- [ ] Queue length
- [ ] Task success rate
- [ ] Task failure rate
- [ ] Average task duration

### 5. Alert Configuration

**Critical Alerts (Immediate Response):**

- Error rate > 5%
- API down (health check fails)
- Database connection failures
- Redis connection failures
- Memory usage > 90%

**Warning Alerts (Monitor Closely):**

- Error rate > 1%
- Response time p95 > 500ms
- Database query time > 200ms
- Memory usage > 80%
- CPU usage > 80%

---

## Post-Deployment Tasks

### 1. Documentation Updates

- [ ] Update deployment documentation
- [ ] Document any issues encountered
- [ ] Update runbooks if needed
- [ ] Share lessons learned with team

### 2. Team Communication

- [ ] Notify team of successful deployment
- [ ] Share monitoring dashboard links
- [ ] Document any known issues
- [ ] Schedule post-mortem if needed

### 3. Cleanup

- [ ] Remove old environment variables (after verification)
- [ ] Archive old deployment artifacts
- [ ] Update CI/CD pipelines if needed
- [ ] Clean up temporary resources

### 4. Performance Baseline

- [ ] Document new performance baselines
- [ ] Update monitoring thresholds if needed
- [ ] Compare before/after metrics
- [ ] Document any performance improvements

---

## Success Criteria

### Deployment Successful If:

✅ All tests pass  
✅ Zero downtime deployment  
✅ Error rate < 1%  
✅ Response times normal or improved  
✅ No critical bugs reported  
✅ All functionality works as expected  
✅ Monitoring shows healthy metrics  
✅ No rollback required  

### Deployment Failed If:

❌ Error rate > 5%  
❌ Critical functionality broken  
❌ Performance degradation > 20%  
❌ Database connection issues  
❌ Memory leaks detected  
❌ Rollback required  

---

## Contact Information

### Escalation Path

**Level 1:** Development Team  
**Level 2:** Tech Lead  
**Level 3:** CTO / Engineering Manager  

### On-Call Schedule

- **Primary:** [Name] - [Contact]
- **Secondary:** [Name] - [Contact]
- **Escalation:** [Name] - [Contact]

---

## Appendix: Useful Commands

### Health Checks

```bash
# Health endpoint
curl https://api.pixcrawler.com/health

# API documentation
curl https://api.pixcrawler.com/openapi.json

# Test authentication
curl -H "Authorization: Bearer $TOKEN" \
  https://api.pixcrawler.com/api/v1/auth/me
```

### Monitoring

```bash
# View application logs (Azure)
az webapp log tail \
  --resource-group pixcrawler-rg \
  --name pixcrawler-prod

# Check service status
az webapp show \
  --resource-group pixcrawler-rg \
  --name pixcrawler-prod \
  --query state

# View metrics
az monitor metrics list \
  --resource /subscriptions/.../pixcrawler-prod \
  --metric-names Requests,ResponseTime,Errors
```

### Debugging

```bash
# SSH into container (if enabled)
az webapp ssh \
  --resource-group pixcrawler-rg \
  --name pixcrawler-prod

# View environment variables
az webapp config appsettings list \
  --resource-group pixcrawler-rg \
  --name pixcrawler-prod

# Restart application
az webapp restart \
  --resource-group pixcrawler-rg \
  --name pixcrawler-prod
```

---

**Checklist Version:** 1.0  
**Last Updated:** January 2025  
**Next Review:** After first production deployment
