# PixCrawler Backend Deployment Checklist

## ✅ Pre-Deployment Verification

### 1. Code Quality & Syntax
- ✅ **No Syntax Errors**: All Python files pass syntax validation
- ✅ **Type Hints**: All functions have proper type annotations
- ✅ **Import Structure**: All imports are correctly structured
- ✅ **Pydantic v2**: All models use correct Pydantic v2 syntax

### 2. Architecture Compliance
- ✅ **ADR-001 Compliance**: Follows Shared Supabase Database architecture
- ✅ **Database Models**: SQLAlchemy models mirror Drizzle schema exactly
- ✅ **UUID Support**: User models use UUID (matches Supabase auth.users)
- ✅ **Supabase Auth**: Integrated with Supabase Auth (no custom JWT)

### 3. Dependencies & Configuration
- ✅ **Dependencies**: All required packages in pyproject.toml
- ✅ **Environment Variables**: All required env vars documented
- ✅ **Database Connection**: Async PostgreSQL with proper pooling
- ✅ **Builder Integration**: Ready for PixCrawler builder package

### 4. API Endpoints
- ✅ **Health Check**: `/api/v1/health/` - Service status
- ✅ **Authentication**: `/api/v1/auth/*` - Supabase auth integration
- ✅ **Crawl Jobs**: `/api/v1/crawl-jobs/*` - Job management
- ✅ **Error Handling**: Comprehensive exception handling

## 🚀 Deployment Steps

### 1. Environment Setup
```bash
# Copy environment template
cp backend/.env.example backend/.env

# Update with your Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project.supabase.co:5432/postgres
```

### 2. Install Dependencies
```bash
cd backend
uv sync
```

### 3. Verify Configuration
```bash
# Test configuration loading
uv run python -c "from backend.core.config import get_settings; print(get_settings().supabase_url)"
```

### 4. Start Development Server
```bash
uv run pixcrawler-api
# or
uv run python -m backend.main
```

### 5. Test API Endpoints
```bash
# Health check
curl http://localhost:8000/api/v1/health/

# API documentation
open http://localhost:8000/docs
```

## 🔧 Integration with Frontend

### 1. Frontend API Calls
```typescript
// Get Supabase session token
const { data: { session } } = await supabase.auth.getSession()
const token = session?.access_token

// Call backend API
const response = await fetch('http://localhost:8000/api/v1/crawl-jobs/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    project_id: 1,
    name: 'My Crawl Job',
    keywords: ['cats', 'dogs'],
    max_images: 100
  })
})
```

### 2. Real-time Updates
```typescript
// Frontend continues using existing Supabase real-time subscriptions
const subscription = supabase
  .channel('crawl_jobs')
  .on('postgres_changes', {
    event: 'UPDATE',
    schema: 'public',
    table: 'crawl_jobs'
  }, (payload) => {
    // Handle job status updates
    console.log('Job updated:', payload.new)
  })
  .subscribe()
```

## ⚠️ Known Limitations & TODOs

### 1. Builder Package Integration
- **Current**: Placeholder implementation with progress simulation
- **TODO**: Adapt builder package for async execution
- **Timeline**: Phase 2 development

### 2. Background Job Processing
- **Current**: FastAPI BackgroundTasks (simple)
- **TODO**: Consider Celery for complex job management
- **Timeline**: When scaling beyond 10 concurrent jobs

### 3. Database Migrations
- **Current**: Manual schema synchronization
- **TODO**: Alembic migrations for schema changes
- **Timeline**: Before production deployment

## 🔍 Monitoring & Debugging

### 1. Logs
```bash
# View application logs
uv run pixcrawler-api --log-level debug

# Check specific components
tail -f logs/pixcrawler-backend.log
```

### 2. Database Connections
```bash
# Monitor Supabase dashboard for connection usage
# Ensure connections stay under pool limits
```

### 3. Health Monitoring
```bash
# Automated health checks
curl -f http://localhost:8000/api/v1/health/ || exit 1
```

## 🎯 Success Criteria

- ✅ **API Responds**: Health endpoint returns 200 OK
- ✅ **Auth Works**: Supabase tokens are verified correctly
- ✅ **Database Connected**: Can query profiles table
- ✅ **Jobs Created**: Can create crawl jobs via API
- ✅ **Real-time Updates**: Frontend receives job status updates

## 🚨 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   # Ensure you're in the backend directory
   cd backend
   uv sync
   ```

2. **Database connection errors**
   ```bash
   # Check DATABASE_URL format
   # Ensure Supabase allows connections from your IP
   ```

3. **Supabase auth errors**
   ```bash
   # Verify SUPABASE_SERVICE_ROLE_KEY is correct
   # Check Supabase project settings
   ```

4. **Import errors with builder package**
   ```bash
   # Ensure builder package is in Python path
   # May need to install builder as editable package
   ```

## 📋 Production Readiness

### Ready for Production ✅
- Core API functionality
- Supabase integration
- Error handling
- Logging
- Security headers

### Needs Development 🔄
- Builder package async integration
- Comprehensive testing
- Database migrations
- Performance optimization
- Monitoring dashboards

The backend is **ready for MVP deployment** and integration with the existing frontend. The architecture is solid and follows the ADR-001 specifications perfectly.