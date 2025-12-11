# PixCrawler

> ***Automated Image Dataset Builder for ML & Research***
> 

## 📋 Overview

PixCrawler is a powerful, scalable SaaS platform that automates the creation of high-quality image datasets for machine learning, research, and data science projects. Transform keywords into organized, validated, and ready-to-use image collections with just a few clicks.

### ✨ Key Features

- 🤖 **Intelligent Crawling** - Multiple discovery methods for comprehensive image collection
- 🔍 **Smart Validation** - Automated quality checks and integrity verification
- 🗂️ **Auto Organization** - Structured folder hierarchies and metadata generation
- 🚀 **Parallel Processing** - High-speed concurrent downloads and processing
- 🔄 **Duplicate Detection** - Advanced deduplication using perceptual and content hashing
- 📦 **Multi-Format Output** - Support for various label formats (JSON, CSV, YAML, TXT)
- ⚡ **Hot & Warm Storage** - Optimized storage tiers for different access patterns
- 🎯 **AI-Powered Keywords** - Intelligent search term expansion and generation

---

## 🎯 Use Cases

### 🔬 **Research & Academia**

- Build custom datasets for computer vision research
- Create balanced training sets for academic projects
- Generate benchmark datasets for model evaluation

### 🏢 **Enterprise & Startups**

- Rapid prototyping of ML models with custom data
- Product image datasets for e-commerce applications
- Visual content analysis for business intelligence

### 👨‍💻 **Individual Developers**

- Personal ML projects and experimentation
- Learning and educational purposes
- Portfolio and demonstration projects

---

## 🚀 Quick Start - Simple Flow System

```bash
# 1. Install
uv sync --all-extras
uv add --group dev poethepoet

# 2. Start Redis server (required)
redis-server

# 3. Start backend + worker
poe dev

# 4. Test
poe test-flow
```

Images saved to `datasets/` directory. API at http://127.0.0.1:8000/docs

### Prerequisites

- **Python**: 3.11 or higher
- **Redis**: For task queue
- **Bun**: Latest version (primary package manager for frontend)
- **Redis**: 5.0 or higher
- **PostgreSQL**: 14 or higher (via Supabase)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pixcrawler.git
   cd pixcrawler
   ```

2. **Set up environment variables**
   
   Copy the example environment files and configure them:
   ```bash
   # Root level (global settings)
   cp .env.example .env
   
   # Backend configuration
   cp backend/.env.example backend/.env
   
   # Frontend configuration
   cp frontend/.env.example frontend/.env
   ```
   
   See [CONFIGURATION.md](./CONFIGURATION.md) for detailed configuration guide.

3. **Install dependencies**
   
   ```bash
   # Backend (Python with UV)
   uv sync
   
   # Frontend (Bun)
   cd frontend
   bun install
   ```

4. **Set up the database**
   
   ```bash
   cd frontend
   bun run db:setup    # Create RLS policies
   bun run db:migrate  # Run migrations
   ```

5. **Start the development environment**
   
   Use the unified startup script for your platform:
   
   ```bash
   # Unix/Linux/Mac
   ./scripts/start-dev.sh
   
   # Windows PowerShell
   .\scripts\start-dev.ps1
   
   # Windows Command Prompt
   .\scripts\start-dev.cmd
   ```
   
   Or start services individually:
   
   ```bash
   # Terminal 1: Backend
   cd backend
   uv run uvicorn backend.main:app --reload
   
   # Terminal 2: Frontend
   cd frontend
   bun dev
   
   # Terminal 3: Redis
   redis-server
   
   # Terminal 4: Celery Worker
   celery -A celery_core.app worker --loglevel=info
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### 1️⃣ **Configuration**

Create your dataset configuration using our intuitive web interface or JSON schema:

```json
{
  "name": "my_dataset",
  "categories": ["cats", "dogs", "birds"],
  "max_images_per_category": 1000,
  "engines": ["primary", "secondary", "tertiary"],
  "quality_filters": {
    "min_resolution": [224, 224],
    "formats": ["jpg", "png", "webp"]
  }
}

```

### 2️⃣ **Processing**

Submit your job through our dashboard

### 3️⃣ **Download**

Get your processed dataset in optimized formats:

- **Hot Version**: Quick access ZIP (available in minutes)
- **Warm Version**: Ultra-compressed 7z (available within hours)

---

## 🏗️ Architecture

### 📊 **Processing Pipeline**

```mermaid
graph LR
    A[🔍 Discovery] --> B[📥 Download]
    B --> C[✅ Validation]
    C --> D[🔍 Deduplication]
    D --> E[📁 Organization]
    E --> F[📦 Compression]
    F --> G[☁️ Storage]

```

### 🔄 **Workflow Overview**

1. **Discovery Phase** 📡
    - Multi-source image discovery
    - Intelligent keyword expansion
    - URL validation and filtering
2. **Processing Phase** ⚙️
    - Concurrent image downloads
    - Real-time integrity checks
    - Advanced deduplication algorithms
3. **Organization Phase** 📚
    - Structured directory creation
    - Metadata generation
    - Label file creation
4. **Delivery Phase** 🚚
    - Hot storage (immediate access)
    - Warm storage (cost-optimized)
    - Secure download links

---

## 📚 Documentation

### 🔗 **Quick Links**

- 📖 [Configuration Guide](./CONFIGURATION.md) - Complete environment variable reference
- 🚀 [Deployment Guide](./DEPLOYMENT.md) - Production deployment instructions
- 🔧 [API Documentation](http://localhost:8000/docs) - Interactive API reference
- 🏗️ [Architecture Guide](./backend/ARCHITECTURE.md) - System architecture overview
- 📊 [Compliance Reports](./docs/compilance/) - Architecture compliance documentation

### 🛠️ **Developer Resources**

- 📊 Jupyter Examples
- 🔄 [Retry Architecture](./docs/RETRY_ARCHITECTURE.md) - Retry strategy guide
- 📝 [Logging Guide](./docs/LOGGING_GUIDE.md) - Centralized logging system
- 🔀 [Workflows Guide](./docs/WORKFLOWS_GUIDE.md) - Celery workflow patterns
- 📦 [Chunk Orchestration](./docs/CHUNK_ORCHESTRATION_GUIDE.md) - Distributed processing guide

---

## ⚙️ Configuration Guide

PixCrawler uses a three-tier configuration system:

1. **Root Level** (`.env`) - Global project settings
   - Supabase credentials (URL, service role key, anon key)
   - Azure storage connection strings
   - Global environment settings

2. **Backend Level** (`backend/.env`) - Backend-specific configuration
   - Server settings (host, port, debug mode)
   - Database connection (PostgreSQL via Supabase)
   - Redis cache and rate limiter settings
   - Celery task queue configuration
   - Storage provider settings
   - CORS configuration

3. **Frontend Level** (`frontend/.env`) - Frontend-specific configuration
   - Supabase client settings (URL, anon key)
   - API endpoint URLs
   - Lemon Squeezy integration (optional)
   - Resend email service (optional)
   - Application URLs

For detailed configuration options, see [CONFIGURATION.md](./CONFIGURATION.md).

---

## 🔧 Development Workflow

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest
uv run pytest --cov=backend --cov-report=html

# Frontend tests (when available)
cd frontend
bun test
```

### Code Quality

```bash
# Backend linting and formatting
cd backend
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy .

# Frontend linting
cd frontend
bun run lint
```

### Database Migrations

```bash
cd frontend

# Generate new migration
bun run db:generate

# Apply migrations
bun run db:migrate

# Open Drizzle Studio
bun run db:studio
```

### API Development

- API documentation is auto-generated at `/docs` (Swagger UI)
- Alternative documentation at `/redoc`
- Postman collections available in `postman/` directory

---

## 🚀 Production Deployment

### Backend Deployment (Azure App Service)

1. **Set environment variables** in Azure Portal
   - Copy all variables from `backend/.env.example`
   - Set `PIXCRAWLER_ENVIRONMENT=production`
   - Configure Supabase credentials
   - Set up Azure storage connection strings

2. **Deploy using Azure CLI**
   ```bash
   az webapp up --name pixcrawler-backend --resource-group pixcrawler-rg
   ```

3. **Verify deployment**
   - Check health endpoint: `https://your-app.azurewebsites.net/health`
   - Review logs in Azure Monitor

### Frontend Deployment (Vercel)

1. **Connect repository** to Vercel
2. **Configure environment variables** in Vercel Dashboard
   - Use values from `frontend/.env.example.production`
   - Set Supabase URL and anon key
   - Configure API URL to point to backend
   - Add Lemon Squeezy keys (if using payments)
   - Add Resend API key (if using email)

3. **Deploy**
   ```bash
   cd frontend
   bun run build
   vercel --prod
   ```

### Alternative: Azure Static Web Apps

1. **Create Static Web App** in Azure Portal
2. **Configure build settings**
   - Build command: `bun run build`
   - Output directory: `.next`
   - App location: `frontend`

3. **Set environment variables** in Azure Portal
4. **Deploy via GitHub Actions** (auto-configured)

For detailed deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md).

---

## 🔍 Troubleshooting

### Common Issues

#### Redis Connection Failed

**Problem**: Backend fails to start with "Redis connection refused"

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis if not running
redis-server

# For development, Redis failures are logged as warnings
# For production, ensure Redis is properly configured
```

#### Database Connection Issues

**Problem**: "Could not connect to database"

**Solution**:
1. Verify Supabase credentials in `.env` files
2. Check database URL format: `postgresql+asyncpg://user:pass@host:5432/db`
3. Ensure connection pool settings are appropriate for Supabase (5-10 connections)
4. Check Supabase dashboard for connection limits

#### Frontend Environment Variables Missing

**Problem**: "Missing required environment variable"

**Solution**:
1. Ensure all required variables from `frontend/.env.example` are set
2. Restart the Next.js dev server after changing `.env` files
3. Check `frontend/lib/env.ts` for validation errors

#### Celery Worker Not Processing Tasks

**Problem**: Tasks stuck in pending state

**Solution**:
```bash
# Check if Celery worker is running
celery -A celery_core.app inspect active

# Restart worker
celery -A celery_core.app worker --loglevel=info

# Check Redis connection
redis-cli ping
```

#### Port Already in Use

**Problem**: "Address already in use" error

**Solution**:
```bash
# Find process using port 8000 (backend)
lsof -i :8000  # Unix/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or use a different port
uvicorn backend.main:app --reload --port 8001
```

### Getting Help

- Check [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment-specific issues
- Review [CONFIGURATION.md](./CONFIGURATION.md) for configuration problems
- Open an issue on GitHub for bugs
- Contact support for production issues

---

## 🌟 Key Benefits

### ⚡ **Speed & Efficiency**

- Process thousands of images in minutes
- Parallel processing architecture
- Optimized network utilization

### 🎯 **Quality Assurance**

- Automated validation pipelines
- Comprehensive error handling
- Duplicate detection and removal

### 💰 **Cost Effective**

- Pay-per-use pricing model
- Optimized storage tiers
- No infrastructure overhead

### 🔒 **Secure & Reliable**

- Enterprise-grade security
- 99.9% uptime SLA
- Data privacy compliance

---

## 🤝 Support & Community

### 📞 **Get Help**

- 📧 Email Support
- 🐛 Bug Reports

### 🔄 **Stay Updated**

- 📈 Changelog

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---
