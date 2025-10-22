#!/bin/bash
# Azure App Service startup script for PixCrawler FastAPI

echo "=========================================="
echo "🕷️  PixCrawler - Azure Deployment"
echo "=========================================="
echo ""

# System Information
echo "📋 System Information:"
echo "   Hostname: $(hostname)"
echo "   Date: $(date)"
echo "   User: $(whoami)"
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

# Install dependencies
echo "📦 Installing Dependencies..."
pip install --upgrade pip
pip install -r requirements-azure.txt
echo "✅ Dependencies installed"
echo ""

# Application Configuration
echo "🚀 Starting Application:"
echo "   App: PixCrawler FastAPI"
echo "   Workers: 4"
echo "   Timeout: 300s"
echo "   Bind: 0.0.0.0:8000"
echo ""
echo "=========================================="
echo ""

# Start the FastAPI application with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_main:app --bind 0.0.0.0:8000 --timeout 300
