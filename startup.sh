#!/bin/bash
# Azure App Service startup script for PixCrawler FastAPI

# Install dependencies
pip install --upgrade pip
pip install -r requirements-azure.txt

# Start the FastAPI application with Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api_main:app --bind 0.0.0.0:8000 --timeout 300
