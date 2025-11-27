#!/bin/bash
# Azure App Service startup script for PixCrawler Production Backend

set -e  # Exit on error

echo "=========================================="
echo "🕷️  PixCrawler Backend - Azure Deployment"
echo "=========================================="
echo ""

# System Information
echo "📋 System Information:"
echo "   Hostname: $(hostname)"
echo "   Date: $(date)"
echo "   User: $(whoami)"
echo "   Working Directory: $(pwd)"
echo ""

# Python Information
echo "🐍 Python Environment:"
python --version
echo "   Python Path: $(which python)"
echo "   Pip Version: $(pip --version)"
echo ""

# Git Information
echo "📦 Deployment Information:"
if [ -d .git ]; then
    echo "   Last Commit: $(git log -1 --pretty=format:'%h - %s (%cr)' 2>/dev/null || echo 'N/A')"
    echo "   Branch: $(git branch --show-current 2>/dev/null || echo 'N/A')"
    echo "   Author: $(git log -1 --pretty=format:'%an' 2>/dev/null || echo 'N/A')"
else
    echo "   Git: Not a git repository"
fi
echo ""

# Disk Space
echo "💾 Disk Space:"
df -h / | tail -1 | awk '{print "   Total: "$2" | Used: "$3" | Available: "$4" | Usage: "$5}'
echo ""

# Install UV package manager
echo "📦 Installing UV..."
if ! command -v uv &> /dev/null; then
    pip install --upgrade pip
    pip install uv
    echo "✅ UV installed"
else
    echo "✅ UV already installed"
fi
echo ""

# Install dependencies using UV workspace
echo "📦 Installing Dependencies (UV Workspace)..."
cd /home/site/wwwroot

# Sync all workspace packages and their dependencies
uv sync --no-dev

echo "✅ Dependencies installed"
echo "   Installed packages:"
echo "   - backend (FastAPI API)"
echo "   - builder (Image crawler)"
echo "   - logging_config (Loguru)"
echo "   - celery_core (Task queue)"
echo "   - validator (Image validation)"
echo ""

# Install and start Redis
echo "🔴 Setting up Redis..."
apt-get update -qq > /dev/null 2>&1
apt-get install -y redis-server > /dev/null 2>&1
echo "✅ Redis installed"

# Start Redis in background
redis-server --daemonize yes --bind 127.0.0.1 --port 6379 --maxmemory 100mb --maxmemory-policy allkeys-lru
sleep 2

# Check if Redis is running
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running on localhost:6379"
else
    echo "⚠️  Redis failed to start"
fi
echo ""

# Start Celery worker in background (if celery_core exists)
if [ -d "celery_core" ]; then
    echo "🔄 Starting Celery worker..."
    uv run celery -A celery_core worker --loglevel=info --concurrency=2 &
    echo "✅ Celery worker started"
    echo ""
fi

# Application Configuration
echo "🚀 Starting Application:"
echo "   App: PixCrawler Backend API"
echo "   Entry Point: backend.main:app"
echo "   Workers: 4"
echo "   Timeout: 300s"
echo "   Bind: 0.0.0.0:8000"
echo "   Environment: ${ENVIRONMENT:-production}"
echo ""
echo "=========================================="
echo ""

# Start the FastAPI application with Gunicorn
exec uv run gunicorn backend.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
