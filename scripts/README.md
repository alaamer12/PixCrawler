# PixCrawler Startup Scripts

This directory contains scripts for starting the PixCrawler development environment.

## Development Startup Scripts

These scripts start both the backend (FastAPI) and frontend (Next.js) services with a single command.

### Unix/Linux/Mac

```bash
./scripts/start-dev.sh
```

### Windows PowerShell

```powershell
.\scripts\start-dev.ps1
```

### Windows Command Prompt

```cmd
scripts\start-dev.cmd
```

## What the Scripts Do

1. **Dependency Checking**
   - Verifies Python 3.11+ is installed
   - Verifies Node.js 18+ is installed
   - Checks for UV package manager
   - Checks for Bun package manager
   - Checks if Redis is running (optional)
   - Checks if PostgreSQL client is available (optional)

2. **Environment Validation**
   - Verifies `.env` files exist in root, backend, and frontend directories
   - Checks that critical environment variables are set
   - Provides clear error messages if configuration is incomplete

3. **Backend Startup**
   - Navigates to backend directory
   - Installs dependencies with UV
   - Starts FastAPI with Uvicorn on port 8000
   - Waits for health check to confirm backend is ready

4. **Frontend Startup**
   - Navigates to frontend directory
   - Installs dependencies with Bun
   - Starts Next.js development server on port 3000
   - Waits for frontend to be accessible

5. **Service Monitoring**
   - Displays service URLs and status
   - Logs output to `backend.log` and `frontend.log`
   - Handles Ctrl+C gracefully to shutdown both services

## Prerequisites

Before running the startup scripts, ensure you have:

1. **Required Software**
   - Python 3.11 or higher
   - Node.js 18 or higher
   - UV package manager ([installation](https://github.com/astral-sh/uv))
   - Bun package manager ([installation](https://bun.sh))

2. **Optional Software**
   - Redis server (for caching and rate limiting)
   - PostgreSQL client (for database management)

3. **Environment Configuration**
   - Root `.env` file (copy from `.env.example`)
   - Backend `.env` file (copy from `backend/.env.example`)
   - Frontend `.env.local` file (copy from `frontend/.env.example`)

## Service URLs

Once started, the services will be available at:

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend App**: http://localhost:3000

## Logs

The scripts create log files in the project root:

- `backend.log` - Backend service logs
- `frontend.log` - Frontend service logs

View logs in real-time:

**Unix/Linux/Mac:**
```bash
tail -f backend.log
tail -f frontend.log
```

**Windows PowerShell:**
```powershell
Get-Content backend.log -Wait
Get-Content frontend.log -Wait
```

**Windows CMD:**
```cmd
type backend.log
type frontend.log
```

## Stopping Services

Press `Ctrl+C` in the terminal where the script is running. The script will gracefully shutdown both services.

## Troubleshooting

### Missing Dependencies

If you see errors about missing dependencies, install them:

- **UV**: `curl -LsSf https://astral.sh/uv/install.sh | sh` (Unix) or `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)
- **Bun**: `curl -fsSL https://bun.sh/install | bash` (Unix) or visit https://bun.sh for Windows
- **Redis**: https://redis.io/download
- **PostgreSQL**: https://www.postgresql.org/download/

### Environment Configuration Issues

If you see errors about missing environment variables:

1. Copy the example files:
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

2. Edit each file and fill in the required values (especially Supabase credentials)

### Port Already in Use

If ports 8000 or 3000 are already in use:

- **Backend**: Edit `backend/main.py` to change the port
- **Frontend**: Set `PORT=3001` in `frontend/.env.local`

### Redis Not Running

The backend will start without Redis, but caching and rate limiting will be disabled. To enable these features:

1. Install Redis
2. Start Redis server: `redis-server`
3. Restart the development environment

## Other Scripts

- `startup-azure.sh` - Production startup script for Azure App Service
- `start_workers.py` - Celery worker management script
